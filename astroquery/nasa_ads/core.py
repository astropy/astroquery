# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
Module to search the SAO/NASA Astrophysics Data System

:author: Magnus Persson <magnusp@vilhelm.nu>

"""
import os

from astropy.table import Table
from astropy.extern.six.moves.urllib.parse import quote as urlencode

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
    QUERY_SIMPLE_PATH = conf.simple_path
    TIMEOUT = conf.timeout
    ADS_FIELDS = conf.adsfields
    TOKEN = conf.token

    QUERY_SIMPLE_URL = SERVER + QUERY_SIMPLE_PATH

    def __init__(self, *args):
        """ set some parameters """
        super(ADSClass, self).__init__()

    @class_or_instance
    def query_simple(self, query_string, get_query_payload=False,
                     get_raw_response=True, cache=True):
        """
        Basic query.  Uses a string and the ADS generic query.
        """
        request_string = self._args_to_url(query_string)
        request_fields = self._fields_to_url()
        request_url = self.QUERY_SIMPLE_URL + request_string + request_fields
        headers = {'Authorization': 'Bearer ' + self._get_token()}

        response = self._request(method='GET', url=request_url,
                                 headers=headers, timeout=self.TIMEOUT,
                                 cache=cache)

        response.raise_for_status()

        # primarily for debug purposes, but also useful if you want to send
        # someone a URL linking directly to the data
        if get_query_payload:
            return request_url
        if get_raw_response:
            return response.json()
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

    def _args_to_url(self, query_string):
        # convert arguments to a valid requests payload
        # i.e. a dictionary
        request_string = 'q=' + urlencode(query_string)
        return request_string

    def _fields_to_url(self):
        request_fields = '&fl=' + ','.join(self.ADS_FIELDS)
        return request_fields

    def _get_token(self):
        """
        Try to get token from the places Andy Casey's python ADS client expects it, otherwise return an error
        """
        if self.TOKEN is not None:
            return self.TOKEN

        self.TOKEN = os.environ.get('ADS_DEV_KEY', None)
        if self.TOKEN is not None:
            return self.TOKEN

        token_file = os.path.expanduser(os.path.join('~','.ads','dev_key'))
        try:
            with open(token_file) as f:
                self.TOKEN = f.read().strip()
            return self.TOKEN
        except IOError:
            raise RuntimeError('No API token found! Get yours from: ' +
                               'https://ui.adsabs.harvard.edu/#user/settings/token ' +
                               'and store it in the API_DEV_KEY environment variable.')


ADS = ADSClass()
