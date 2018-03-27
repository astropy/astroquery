# Licensed under a 3-clause BSD style license - see LICENSE.rst
import xml.etree.ElementTree as ET
import gzip
import io
from .utils import Number

oec_server_url = "https://github.com/OpenExoplanetCatalogue/oec_gzip/raw/master/systems.xml.gz"

__all__ = ['xml_element_to_dict', 'findvalue', 'get_catalogue']

try:
    import urllib.request as urllib2
except ImportError:
    import urllib2


def get_catalogue(filepath=None):
    """
    Parses the Open Exoplanet Catalogue file.

    Parameters
    -----------
    filepath : str or None
        if no filepath is given, remote source is used.

    Returns
    -------
    An Element Tree containing the open exoplanet catalogue
    """

    if filepath is None:
        oec = ET.parse(gzip.GzipFile(
                fileobj=io.BytesIO(urllib2.urlopen(oec_server_url).read())))
    else:
        oec = ET.parse(gzip.GzipFile(filepath))
    return oec


def xml_element_to_dict(e):
    """
    Creates a dictionary of the given xml tree.

    Parameters
    ----------
    e : str
        str of an xml tree

    Returns
    -------
    A dictionary of the given xml tree
    """

    d = {}
    for c in e.getchildren():
        d[c.tag] = c.text
    return d


def findvalue(element, searchstring):
    """
    Searches given string in element.

    Parameters
    ----------
    element : Element
        Element from the ElementTree module.
    searchstring : str
        name of the tag to look for in element

    Returns
    -------
    None if tag does not exist.
    str if the tag cannot be expressed as a float.
    Number if the tag is a numerical value
    """
    if element is not None:
        res = element.find(searchstring)
        if res is None:
            return None
        tempnum = Number()
        if res.text is not None:
            try:
                float(res.text)
                setattr(tempnum, 'value', res.text)
            except ValueError:
                return res.text
        if "errorminus" in res.attrib:
            tempnum.errorminus = res.attrib["errorminus"]
        if "errorplus" in res.attrib:
            tempnum.errorplus = res.attrib["errorplus"]
        if "upperlimit" in res.attrib:
            tempnum.upperlimit = res.attrib["upperlimit"]
        if "lowerlimit" in res.attrib:
            tempnum.lowerlimit = res.attrib["lowerlimit"]
        return tempnum
