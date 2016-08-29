"""
emails: functions for working with experiment factory results

"""

from __future__ import print_function
import base64
import httplib2
import json
import os
import re

from apiclient import discovery
import oauth2client
from oauth2client import client
from oauth2client import tools

from utils import get_installdir, create_homedir

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

base = get_installdir()

SCOPES = 'https://www.googleapis.com/auth/gmail.readonly'
CLIENT_SECRET_FILE = '%s/data/client_id.json' %(base)
APPLICATION_NAME = 'Expfactory Analysis'

def get_cache():
    '''get_cache will prepare a cache directory
    '''
    cache_dir = create_homedir('.expfactory')
    return cache_dir

def get_id_cache():
    cache_dir = get_cache()
    return os.path.join(cache_dir,'expfactory-analysis-gmail-ids.json')


def get_credentials():
    """Gets valid user credentials from storage.
    From: https://developers.google.com/gmail/api/quickstart/python

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    credential_dir = create_homedir('.credentials')
    credential_path = os.path.join(credential_dir,'expfactory-analysis-gmail.json')

    store = oauth2client.file.Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else: # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials



def get_results():
    """get_results will retrieve emails flagged with results from the users email
    """
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('gmail', 'v1', http=http)

    # Get all messages
    results = service.users().messages().list(userId='me').execute()
    messages = results.get('messages', [])

    # Load ids from cache
    id_cache = get_id_cache()
    if os.path.exists(id_cache):
        message_ids = json.loads(open(id_cache,'r'))
    else:
        message_ids = []

    #TODO: will need to add in next page token
    #TODO: need better way to filter emails
    message_ids = []
    if not messages:
        print('No data found found.')
    else:
        for message in messages:
            if message['id'] not in message_ids:
                meta = service.users().messages().get(userId='me',
                                                      id=message["id"],
                                                      format='metadata').execute()

                subject = [x['value'] for x in meta['payload']['headers'] if x['name']=="Subject"]
                if len(subject) > 0:
                    subject = subject[0]
                    if re.search('[[]EXPFACTORY[]][[]RESULT[]]',subject):
                        print("Found result %s" %(subject))
                        message_ids.append(message['id'])            

    # Get attachments from emails
    data = dict()
    for message_id in message_ids:
        meta = service.users().messages().get(userId='me',id=message_id).execute()
        payloads = [x['body'] for x in meta['payload']['parts'] if 'body' in x]
        for payload in payloads:
            if "data" in payload:
                body = base64.urlsafe_b64decode(payload['data'].encode('ASCII')).decode('utf-8')
                json_str = re.findall('<pre>(.+?)</pre>',body)
                if len(json_str) > 0:
                    result = dict()
                    result['data'] = json.loads(json_str[0])
                    #TODO: This should just be a json object too
                    result['meta'] = [x for x in body.split('<pre>')[0].replace('\r','').split('\n') if len(x)>0]
                    data[message_id] = result            

    # Rewrite the cache
    json.dumps(message_ids,open(id_cache,'w'))
    return data
