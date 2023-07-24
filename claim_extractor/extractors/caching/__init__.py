from typing import Dict, Optional
import time
import requests
from redis import Redis

from claim_extractor import Claim

redis = Redis(decode_responses=True)


def get(url: str, headers: Dict[str, str] = None, timeout: int = None):

    """
    Sends an HTTP GET request to the specified URL and returns the page text.

    Parameters:
        url (str): The URL to send the GET request to.
        headers (Dict[str, str], optional): A dictionary of HTTP headers to include in the request.
        timeout (int, optional): The maximum time in seconds to wait for the request to complete.

    Returns:
        Optional[str]: The text of the response page, or None if the request fails or encounters an error.
    """
    page_text = redis.get(url)
    
    try:
        if not page_text:
            result = requests.get(url, headers=headers, timeout=timeout)
            if result.status_code < 400:
                page_text = result.text
                redis.set(url, page_text)
            elif result.status_code ==403:
            
                time.sleep(10)
                page_text = get(url, headers, timeout)
            elif result.status_code ==404:
                page_text = "no text"
                            
            else:
          
                return None
    except requests.exceptions.ReadTimeout:
        page_text = None
      
    except requests.exceptions.MissingSchema:
        page_text = None
    
    except requests.exceptions.ConnectTimeout:
        page_text = None
      
    return page_text


def post(url: str, headers: Dict[str, str] = None, data: Dict[str, str] = None, timeout: int = None):
    """
    Sends an HTTP POST request to the specified URL and returns the page text.

    Parameters:
        url (str): The URL to send the POST request to.
        headers (Dict[str, str], optional): A dictionary of HTTP headers to include in the request.
        data (Dict[str, str], optional): A dictionary of data to send in the POST request body.
        timeout (int, optional): The maximum time in seconds to wait for the request to complete.

    Returns:
        Optional[str]: The text of the response page, or None if the request fails or encounters an error.
    """
    page_text = redis.get(url)
    try:
        if not page_text:
            result = requests.post(url, headers=headers, data=data, timeout=timeout)
            if result.status_code < 400:
                page_text = result.text
                redis.set(url, page_text)
            else:
                print("test3")
                return None
    except requests.exceptions.ReadTimeout:
        page_text = None
    except requests.exceptions.MissingSchema:
        page_text = None
    return page_text


def head(url: str, headers: Dict[str, str] = None, timeout: int = None):
    """
    Sends an HTTP HEAD request to the specified URL and returns a dictionary containing
    information about the response.

    Parameters:
        url (str): The URL to send the HEAD request to.
        headers (Dict[str, str], optional): A dictionary of HTTP headers to include in the request.
        timeout (int, optional): The maximum time in seconds to wait for the request to complete.

    Returns:
        Dict[str, any]: A dictionary containing information about the response, including the URL and status code.
    """
    page_text = redis.get(url)
    try:
        if not page_text:
            result = requests.head(url)
            if 3 <= result.status_code / 100 < 4:
                url = result.headers['Location']
                x = {'url': url, 'status_code': 200, 'text': ''}
            elif result.status_code < 300:
                x = {'url': result.url, 'status_code': result.status_code}
            else:
                x = {'url': url, 'status_code': result.status_code}
        else:
            x = {'url': url, 'status_code': 200}
        return x
    except requests.exceptions.ReadTimeout:
        page_text = None
    except requests.exceptions.MissingSchema:
        page_text = None

    x = {'url': url, 'status_code': 1000}

    return x


def get_claim_from_cache(url: str) -> Optional[Claim]:
    """
    Retrieves a cached Claim object from Redis based on the URL.

    Parameters:
        url (str): The URL of the claim.

    Returns:
        Optional[Claim]: The cached Claim object if found, or None if not cached.
    """
    result = redis.hgetall("___cached___claim___" + url)

    if result:
        claim = Claim.from_dictionary(result)
        return claim
    else:
        return None


def cache_claim(claim: Claim):
    """
    Caches a Claim object in Redis.

    Parameters:
        claim (Claim): The Claim object to be cached.
    """
    if claim is not None:
        dictionary = claim.generate_dictionary()
        url = claim.url
        if url is not None and dictionary is not None:
            redis.hmset("___cached___claim___" + url, dictionary)
