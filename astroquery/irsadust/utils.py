# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
Utilities used by irsa_dust.py to query the dust service and parse the results.
"""
import re
import xml.etree.ElementTree as tree
import urllib
import urllib2
import astropy.units as u
from ..utils import progressbar

def parse_number(string):
    """
    Retrieve a number from the string.
    
    Parameters
    ----------
    string : str
        the string to parse
    
    Returns
    -------
    number : float
        the number contained in the string
    """
    num_str = string.split(None, 1)[0]
    number = float(num_str)
    return number

def parse_coords(string):
    """
    Retrieve coordinates from the string.

    Parameters
    ----------
    string : str
        the string to parse
    
    Returns
    -------
    coords : list(float, float, str)
        list containing RA, Dec, and coordinate system description
    """
    ra = float(string.split()[0])
    dec = float(string.split()[1])
    coord_sys = string.split(None, 2)[2].strip()
    coords = [ra, dec, coord_sys]
    return coords

def parse_units(string):
    """
    Retrieve units from the string.

    Parameters
    ----------
    string: str
        the string to parse

    Returns
    -------
    units : `astropy.units.Unit`
        the units contained in the string
    """
    unit_str = string.split(None, 1)[1]
    unit_str = re.sub("[()]", "", unit_str).strip()
    units = u.format.Generic().parse(unit_str)
    return units

def find_result_node(desc, xml_tree):
    """ 
    Returns the <result> node with a <desc> child matching the given text.
    Eg: if desc = "text to match", this function will find the following
        result node:
        <result>
            <desc>text to match</desc>
        </result>

    Parameters
    -----
    xmlTree : the xml tree to search for the <result> node
    desc : the text contained in the desc node
    
    Returns
    -----
    node : the <result> node containing the child with the given desc
    """
    result_nodes = xml_tree.findall("result")

    for result_node in result_nodes:
        result_desc = result_node.find("desc").text.strip()
        if result_desc == desc:
            return result_node
    return None

def query(options, url, debug=False):
    """
    Performs the actual IRSA dust service query and returns the raw xml response.
    
    Parameters
    ----------
    options : dictionary
        the parameters to use in the query
    url : str
        the url to use in the query
    debug : Boolean
        whether to print debugging messages

    Returns
    -------
    xmlTree : `xml.etree.ElementTree`
        the raw xml query response
    """
    
    url += "?" + "&".join(["%s=%s" % (x, urllib.quote_plus(str(options[x]))) for x in options])
    if debug:
        print(url)
    req = urllib2.Request(url)
    try:
        response = urllib2.urlopen(req)
    except urllib2.URLError as error:
        raise Exception("Error while trying to query dust service at: "
                        + url + "\n" + str(error) + "\n"
                        + "Check your internet connection.")
    except urllib2.HTTPError as error:
        raise Exception("Error while trying to query dust service at: "
                        + url + "\n" + str(error))
    return response

def xml(response):
    """
    Parse raw xml and return as an xml tree. If status is not `ok`, raise an exception.
    
    Parameters
    ----------
    response : file like object
        object containing xml

    Returns
    -------
    xml : `xml.etree.ElementTree`
        an xml tree
    """
    xml = tree.ElementTree().parse(response)
    status = xml.attrib["status"]
    if status == "error":
        message = xml.find("message").text
        raise Exception("The dust service responded with an error: " + message)
    elif status != "ok":
        raise Exception("Response status was not 'ok'.")

    return xml

def ext_detail_table(detail_table_url):
    """ 
    Get the detailed extinction table located at the given url.

    Parameters
    ----------
    detail_table_url : str
        the url of the detail table

    Returns
    -------
    response : the raw response to request for the table
    """
    req = urllib2.Request(detail_table_url)
    try:
        response = urllib2.urlopen(req)
        return response
    except urllib2.URLError as error:
        raise Exception("Error while trying to query dust service at: "
                        + detail_table_url + "\n" + str(error) + "\n"
                        + "Check your internet connection.")
    except urllib2.HTTPError as error:
        raise Exception("Failed to retrieve detail table: " + str(error))

def image(image_url):
    """
    Retrieve the FITS image located at the given url.
    
    Parameters
    ----------
    image_url : str
        the url where the image can be found
    
    Returns
    -------
    content : the raw response to the http get request
    """
    #if image_url == "test_url":
    #    req = "file:tests/t/test.fits"
        #req = DustTestCase().data("test.fits")
    #else:
    req = urllib2.Request(image_url)
    
    try:
        response = urllib2.urlopen(req)
        content = progressbar.chunk_read(response, report_hook=progressbar.chunk_report)
        return content
    except urllib2.URLError as error:
        raise Exception("Error while trying to query dust service at: "
                        + image_url + "\n" + str(error) + "\n"
                        + "Check your internet connection.")
    except urllib2.HTTPError as error:
        raise Exception("Failed to retrieve image: " + str(error))

