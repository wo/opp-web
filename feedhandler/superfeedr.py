import requests
import json
from django.conf import settings

"""

very basic module for managing superfeedr subscriptions; uses
settings.SUPERFEEDR_USERNAME and settings.SUPERFEEDR_PASSWORD or
settings.SUPERFEEDR_TOKEN for authentication.

import superfeedr
superfeedr.subscribe(url=x, callback_url=y)
superfeedr.unsubscribe(url=x)
superfeedr.subscribed_urls()

"""

SUPERFEEDR_API = "https://push.superfeedr.com"

def authenticate():
    user = settings.SUPERFEEDR_USER
    try:
        password = settings.SUPERFEEDR_TOKEN
    except AttributeError:
        try:
            password = settings.SUPERFEEDR_PASSWORD
        except AttributeError:
            raise AttributeError("Need either password or token parameter")
    return (user, password)

def subscribe(url=None, callback_url=None):
    """
    adds subscription for feed <url> with callback <callback_url>,
    returns True on success, otherwise raises an error.
    """
    (user, password) = authenticate()
    params = {
        'hub.mode': 'subscribe',
        'hub.topic': url,
        'hub.callback': callback_url,
        'format': 'json',
    }
    response = requests.post(
        SUPERFEEDR_API,
        params=params,
        auth=requests.auth.HTTPBasicAuth(user, password),
    )
    response.raise_for_status()
    return True

def unsubscribe(url=None):
    """
    removes subscription for feed <url>, returns True on success,
    otherwise raises an error.
    """ 
    (user, password) = authenticate()
    params = {
        'hub.mode': 'unsubscribe',
        'hub.topic': url,
    }
    response = requests.post(
        SUPERFEEDR_API,
        params=params,
        auth=requests.auth.HTTPBasicAuth(user, password),
    )
    response.raise_for_status()
    return True

def subscribed_urls():
    """
    returns list of currently subscribed feed urls; see
    https://documentation.superfeedr.com/subscribers.html#listing-subscriptions-with-pubsubhubbub
    """ 
    (user, password) = authenticate()
    params = {
        'hub.mode': 'list',
        'by_page': 500,
    }
    response = requests.get(
        SUPERFEEDR_API,
        params=params,
        auth=requests.auth.HTTPBasicAuth(user, password),
    )
    response.raise_for_status()
    urls = []
    for sub in response.json():
        try:
            urls.append(sub['subscription']['feed']['url'])
        except:
            pass
    return urls 



