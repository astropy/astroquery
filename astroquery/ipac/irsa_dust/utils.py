# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
Utilities used by irsa_dust.py to query the dust service and parse the results.
"""
import re
import xml.etree.ElementTree as tree
import astropy.units as u


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
    units : `~astropy.units.Unit`
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
    xmlTree : `xml.etree.ElementTree`
        the xml tree to search for the <result> node
    desc : string
        the text contained in the desc node

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


def xml(response):
    """
    Parse raw xml and return as an xml tree. If status is not ``ok``, raise
    an exception.

    Parameters
    ----------
    response : str
        unicode string containing xml

    Returns
    -------
    xml_tree : `xml.etree.ElementTree`
        an xml tree
    """
    # get the root element from the xml string
    root = tree.fromstring(response)
    status = root.attrib["status"]
    if status == "error":
        message = root.find("message").text
        raise Exception("The dust service responded with an error: " + message)
    elif status != "ok":
        raise Exception("Response status was not 'ok'.")
    # construct the ElementTree from the root
    xml_tree = tree.ElementTree(root)
    return xml_tree
