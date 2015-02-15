# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
Module to search the SAO/NASA Astrophysics Data System

:author: Magnus Persson <magnusp@vilhelm.nu>

"""

import warnings
# example warning 
# warnings.warn("Band was specified, so blabla is overridden")
#~ from astropy.io import ascii
#~ from astropy import units as u
from ..query import BaseQuery
from ..utils import commons, async_to_sync
#~ from ..utils.docstr_chompers import prepend_docstr_noreturns
from . import conf
#~ from .utils import *
from astropy.table import Table, Column

from ..utils.class_or_instance import class_or_instance
from ..utils import commons, async_to_sync

#~ from BeautifulSoup import BeautifulSoup as bfs

from xml.dom import minidom

__all__ = ['ADS', 'ADSClass']

@async_to_sync
class ADSClass(BaseQuery):
    
    ####### FROM SPLATALOGUE
    SERVER = conf.server
    QUERY_ADVANCED_PATH = conf.advanced_path
    QUERY_SIMPLE_PATH = conf.simple_path
    TIMEOUT = conf.timeout
    
    QUERY_SIMPLE_URL = SERVER + QUERY_SIMPLE_PATH
    QUERY_ADVANCED_URL = SERVER + QUERY_ADVANCED_PATH

    ######## FROM API DOCS
    def __init__(self, *args):
        """ set some parameters """
        pass
    
    @class_or_instance
    def query_simple(self, query_string, get_query_payload=False, get_raw_response=False):
        self.query_string = query_string
        request_payload = self._args_to_payload(query_string)
        
        response = commons.send_request(self.QUERY_SIMPLE_URL, request_payload, self.TIMEOUT)
        
        # primarily for debug purposes, but also useful if you want to send
        # someone a URL linking directly to the data
        if get_query_payload:
            return request_payload
        if get_raw_response:
            return response
        # parse the XML response into Beautiful Soup
        #~ response_bfs = self._parse_response_to_bfs(response)
        # 
        #self._parse_bfs_to_table(response_bfs)
        self._parse_response(response)
        
        return response
    
    def _parse_response(self, response):
        xmlrepr = minidom.parseString(response.text.encode('utf-8'))
        
        
    def _parse_response_to_bfs(self, response):
        # do something, probably with regexp's
        
        adssoup_raw = bfs(response.text)
        adssoup_cooked = adssoup_raw.findAll('record')
        result = adssoup_cooked
        
        # number of hits
        nhits = len(adssoup_cooked)
        if nhits == 0:
            warnings.warn("No hits for the search \'{0}\'".format(self.query_string))
            return None
        
        """
        Developer, how do you get list with all the fields?
        Like this:
        [tag.name for tag in adssoup_cooked[0].findAll()]
        """
        return result

    def _args_to_payload(self, query_string):
        # convert arguments to a valid requests payload
        # i.e. a dictionary
        return {'qsearch' : query_string, 'data_type' : 'XML'}



ADS = ADSClass()
