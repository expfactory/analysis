"""
expanalysis.api: functions for retrieving experiment factory results

"""

from expanalysis.utils import get_pages

def get_base(url,uid=None):
    '''get_base is the base retrieval function for other api get functions,
    adding an optional uid variable if it's defined, otherwise returning the
    url
    :param url: the url to retrieve
    :param uid: the unique id
    '''
    if uid != None:
        url = "%s/%s" %(url,uid)
    return get_pages(url=url)

def get_battery(uid=None):
    '''get_battery is a wrapper for get_pages, specifying the battery json endpoint
    '''
    url = "http://www.expfactory.org/api/battery"
    return get_base(url=url,uid=uid)
   

def get_experiment(uid=None):
    '''get_experiment is a wrapper for get_pages, specifying the battery json endpoint
    '''
    url = "http://www.expfactory.org/api/experiment"
    return get_base(url=url,uid=uid)
