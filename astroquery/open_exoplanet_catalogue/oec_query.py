# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
Query of Open Exoplanet Catalogue 
------------------

This is the simplest possible implementation. The function QuerySystem simply gets the xml file from one of the servers and returns it. More complicated (and sueful) query functions will follow.
"""
from __future__ import print_function
from . import OEC_SERVER
import sys,urllib2

__all__ = ['QuerySystem']

def QuerySystem(systemId,category='systems'):
    """ TODO Document """

    server = OEC_SERVER()
    url = server+"/"+category+"/"+urllib2.quote(systemId.strip())+".xml"
    try:
    	xml = urllib2.urlopen(url).read()
    except:
        print ("Error getting Open Exoplanet Catalogue file '"+url+"'.\nCheck systemId and server.")
	return

    return xml



