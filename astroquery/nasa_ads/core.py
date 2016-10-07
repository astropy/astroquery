# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
Module to search the SAO/NASA Astrophysics Data System

:author: Magnus Persson <magnusp@vilhelm.nu>

"""

from astropy.table import Table

from ..query import BaseQuery
from ..utils import async_to_sync
from ..utils.class_or_instance import class_or_instance

from .utils import _get_data_from_xml
from . import conf


from xml.dom import minidom

__all__ = ['ADS', 'ADSClass']


@async_to_sync
class ADSClass(BaseQuery):

    SERVER = conf.server
    QUERY_ADVANCED_PATH = conf.advanced_path
    QUERY_SIMPLE_PATH = conf.simple_path
    TIMEOUT = conf.timeout

    QUERY_SIMPLE_URL = SERVER + QUERY_SIMPLE_PATH
    QUERY_ADVANCED_URL = SERVER + QUERY_ADVANCED_PATH

    def __init__(self, *args):
        """ set some parameters """
        super(ADSClass, self).__init__()

    @class_or_instance
    def query_simple(self, query_string, get_query_payload=False,
                     get_raw_response=False, cache=True):
        """
        Basic query.  Uses a string and the ADS generic query.
        """
        request_payload = self._args_to_payload(query_string)

        response = self._request(method='POST', url=self.QUERY_SIMPLE_URL,
                                 data=request_payload, timeout=self.TIMEOUT,
                                 cache=cache)

        response.raise_for_status()

        # primarily for debug purposes, but also useful if you want to send
        # someone a URL linking directly to the data
        if get_query_payload:
            return request_payload
        if get_raw_response:
            return response
        # parse the XML response into AstroPy Table
        resulttable = self._parse_response(response)

        return resulttable

    def _parse_response(self, response):

        encoded_content = response.text.encode(response.encoding)

        xmlrepr = minidom.parseString(encoded_content)
        # Check if there are any results!

        # get the list of hits
        hitlist = xmlrepr.childNodes[0].childNodes
        hitlist = hitlist[1::2]  # every second hit is a "line break"

        # Grab the various fields
        titles = _get_data_from_xml(hitlist, 'title')
        bibcode = _get_data_from_xml(hitlist, 'bibcode')
        journal = _get_data_from_xml(hitlist, 'journal')
        volume = _get_data_from_xml(hitlist, 'volume')
        pubdate = _get_data_from_xml(hitlist, 'pubdate')
        page = _get_data_from_xml(hitlist, 'page')
        score = _get_data_from_xml(hitlist, 'score')
        citations = _get_data_from_xml(hitlist, 'citations')
        abstract = _get_data_from_xml(hitlist, 'abstract')
        doi = _get_data_from_xml(hitlist, 'DOI')
        eprintid = _get_data_from_xml(hitlist, 'eprintid')
        authors = _get_data_from_xml(hitlist, 'author')
        # put into AstroPy Table
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
        return {'qsearch': query_string, 'data_type': 'XML'}


ADS = ADSClass()
