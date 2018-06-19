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
    SORT = conf.sort
    NROWS = conf.nrows
    NSTART = conf.nstart
    TOKEN = conf.token

    QUERY_SIMPLE_URL = SERVER + QUERY_SIMPLE_PATH

    def __init__(self, *args):
        """ set some parameters """
        super(ADSClass, self).__init__()

    @class_or_instance
    def query_simple(self, query_string, get_query_payload=False,
                     get_raw_response=False, cache=True):
        """
        Basic query.  Uses a string and the ADS generic query.
        """
        request_string = self._args_to_url(query_string)
        request_fields = self._fields_to_url()
        request_sort = self._sort_to_url()
        request_rows = self._rows_to_url(self.NROWS, self.NSTART)
        request_url = self.QUERY_SIMPLE_URL + request_string + request_fields + request_sort + request_rows

        # primarily for debug purposes, but also useful if you want to send
        # someone a URL linking directly to the data
        if get_query_payload:
            return request_url

        response = self._request(method='GET', url=request_url,
                                 headers={'Authorization': 'Bearer ' + self._get_token()},
                                 timeout=self.TIMEOUT, cache=cache)

        response.raise_for_status()

        if get_raw_response:
            return response
        # parse the XML response into AstroPy Table
        resulttable = self._parse_response(response.json())

        return resulttable

    def _parse_response(self, response):

        try:
            response['response']['docs'][0]['bibcode']
        except IndexError:
            raise RuntimeError('No results returned!')

        # get the list of hits
        hitlist = response['response']['docs']

        t = Table()
        # Grab the various fields and put into AstroPy table
        for field in self.ADS_FIELDS:
            tmp = _get_data_from_xml(hitlist, field)
            t[field] = tmp

        return t

    def _args_to_url(self, query_string):
        # convert arguments to a valid requests payload
        # i.e. a dictionary
        request_string = 'q=' + urlencode(query_string)
        return request_string

    def _fields_to_url(self):
        request_fields = '&fl=' + ','.join(self.ADS_FIELDS)
        return request_fields

    def _sort_to_url(self):
        request_sort = '&sort=' + urlencode(self.SORT)
        return request_sort

    def _rows_to_url(self, nrows=10, nstart=0):
        request_rows = '&rows=' + str(nrows) + '&start=' + str(nstart)
        return request_rows

    def _get_token(self):
        """
        Try to get token from the places Andy Casey's python ADS client expects it, otherwise return an error
        """
        if self.TOKEN is not None:
            return self.TOKEN

        self.TOKEN = os.environ.get('ADS_DEV_KEY', None)
        if self.TOKEN is not None:
            return self.TOKEN

        token_file = os.path.expanduser(os.path.join('~', '.ads', 'dev_key'))
        try:
            with open(token_file) as f:
                self.TOKEN = f.read().strip()
            return self.TOKEN
        except IOError:
            raise RuntimeError('No API token found! Get yours from: '
                               'https://ui.adsabs.harvard.edu/#user/settings/token '
                               'and store it in the API_DEV_KEY environment variable.')


ADS = ADSClass()
