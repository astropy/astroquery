# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
Query fucntion for the Open Exoplanet Catalogue 
-----------------------------------------------

The function query_system_xml simply returns the xml file from one of the servers and returns it. 

The function query_planet searches for a planet and returns its properties as a python dictionary.


------------------
:Author: Hanno Rein (hanno@hanno-rein.de)
"""
from __future__ import print_function
from . import OEC_SERVER
from . import OEC_META_SERVER
import sys,urllib2
import csv
import xml.etree.ElementTree as ET


class CatalogueOpeningError(Exception):
    """Exception for error in opening open exoplanet catalogue"""
    pass

__all__ = ['query_system_xml','query_planet']

aliases = None

def find_system_for_alias(alias):
    global aliases
    alias = alias.strip()
    if aliases is None:
        metaserver = OEC_META_SERVER()
        metaurl = metaserver+"aliases.csv"
        try:
            metacsv = urllib2.urlopen(metaurl)
            aliases = list(csv.reader(metacsv))
        except:
            raise CatalogueOpeningError("Error getting Open Exoplanet Catalogue file '"+metaurl+\
			    "'.\nCheck system_id and server.")
    for a in aliases:
        if a[0] == alias:
            return a[1]
    
def get_xml_for_system(system,category='systems'):
    try:
        url = OEC_SERVER() + category + "/" +\
                urllib2.quote(system) + ".xml"
        xml = urllib2.urlopen(url).read()
    except TypeError:
        raise TypeError("Error, system or category not defined")
    except:
        raise CatalogueOpeningError("Error getting Open Exoplanet Catalogue file '" + url +\
			"'.\nCheck system_id and server.")
    else:
        return xml

def xml_element_to_dict(e):
    """Converts xml tree to dictionary"""
    d = {}
    for c in e.getchildren():
        d[c.tag] = c.text
    return d
    
def query_system_xml(system_id,category='systems'):
    """ Queries the database and returns the XML data of the system """

    system = find_system_for_alias(system_id)
    return get_xml_for_system(system,category)


def query_planet(planet_id,category='systems'):
    """ Queries the database and returns the planet data as a python dictionary """

    system = find_system_for_alias(planet_id)
    xml = get_xml_for_system(system,category)
    systemroot = ET.fromstring(xml)
    planets = systemroot.findall(".//planet")
    for planet in planets:
        names = planet.findall("./name")
        for name in names:
            if name.text == planet_id.strip():
                return xml_element_to_dict(planet)

    return None



