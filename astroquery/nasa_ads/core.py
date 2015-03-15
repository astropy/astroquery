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
from .utils import *
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
        resulttable = self._parse_response(response)
        
        return resulttable 
    
    def _parse_response(self, response):
        xmlrepr = minidom.parseString(response.text.encode('utf-8'))
        # Check if there are any results!
        
        # get the list of hits
        hitlist = xmlrepr.childNodes[0].childNodes
        hitlist = hitlist[1::2] # every second hit is a "line break"
        
        # Parse the results
        # first single items
        titles = get_data_from_xml(hitlist, 'title')
        bibcode = get_data_from_xml(hitlist, 'bibcode')
        journal = get_data_from_xml(hitlist, 'journal')
        volume = get_data_from_xml(hitlist, 'volume')
        pubdate = get_data_from_xml(hitlist, 'pubdate')
        page = get_data_from_xml(hitlist, 'page')
        score = get_data_from_xml(hitlist, 'score')
        citations = get_data_from_xml(hitlist, 'citations')
        abstract = get_data_from_xml(hitlist, 'abstract')
        doi = get_data_from_xml(hitlist, 'DOI')
        eprintid = get_data_from_xml(hitlist, 'eprintid')
        #~ = get_data_from_xml(hitlist, '')
        authors = get_data_from_xml(hitlist, 'author')
 
        t = Table()
        t['title'] = titles
        t['bibcode'] = bibcode
        t['journal'] = journal
        t['volume'] = volume
        t['pubdate'] = pubdate
        t['page'] = page
        t['score'] = score
        t['citations'] = citations
        t['abstract'] = abstract 
        t['doi'] = doi
        t['eprintid'] = eprintid 
        t['authors'] = authors
        
        return t
         
    def _args_to_payload(self, query_string):
        # convert arguments to a valid requests payload
        # i.e. a dictionary
        return {'qsearch' : query_string, 'data_type' : 'XML'}



ADS = ADSClass()


"""
typical fields available:

[u'bibcode',
 u'title',
 u'author',
 u'author',
 u'author',
 u'affiliation',
 u'journal',
 u'volume',
 u'pubdate',
 u'page',
 u'keywords',
 u'keyword',
 u'keyword',
 u'keyword',
 u'keyword',
 u'keyword',
 u'origin',
 u'link',
 u'name',
 u'url',
 u'link',
 u'name',
 u'url',
 u'link',
 u'name',
 u'url',
 u'link',
 u'name',
 u'url',
 u'link',
 u'name',
 u'url',
 u'count',
 u'link',
 u'name',
 u'url',
 u'count',
 u'link',
 u'name',
 u'url',
 u'count',
 u'link',
 u'name',
 u'url',
 u'link',
 u'name',
 u'url',
 u'count',
 u'link',
 u'name',
 u'url',
 u'url',
 u'score',
 u'citations',
 u'abstract',
 u'doi',
 u'eprintid']


"""
