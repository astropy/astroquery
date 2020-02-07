"""
Provide astroquery API access to OIR Lab Astro Data Archive (natica).

This does DB access through web-services. It allows query against ALL
fields in FITS file headers.

Also possible but not provided here: query through Elasticsearch DSL.  ES will
be much faster but much more limitted in what can be used in query.  """

# Python library
# External packages
import requests
import astropy.table
# Local packages

# 3. local imports - use relative imports
# commonly required local imports shown below as example
# all Query classes should inherit from BaseQuery.
from ..query import BaseQuery
# has common functions required by most modules
from ..utils import commons
# prepend_docstr is a way to copy docstrings between methods
from ..utils import prepend_docstr_nosections
# async_to_sync generates the relevant query tools from _async methods
from ..utils import async_to_sync
from ..utils.class_or_instance import class_or_instance
# import configurable items declared in __init__.py
from . import conf


__all__ = ['Noao', 'NoaoClass']  # specifies what to import


@async_to_sync
class NoaoClass(BaseQuery):

    NAT_URL = conf.server
    ADS_URL = f'{NAT_URL}/api/adv_search/fasearch'
    SIA_URL = f'{NAT_URL}/api/sia/voimg'

    def __init__(self, which='voimg'):
        """ set some parameters """
        # Change following to match current https://<root>/api/version
        KNOWN_GOOD_API_VERSION = 2.0
        # #!response = self._request('GET', f'{self.NAT_URL}/api/version',
        # #!                         cache=False)
        response = requests.get(f'{self.NAT_URL}/api/version')
        api_version = float(response.content)
        if (int(api_version) - int(KNOWN_GOOD_API_VERSION)) >= 1:
            msg = (f'The astroquery.noao module is expecting an older version '
                   f'of the {self.NAT_URL} API services.  '
                   f'Please upgrade to latest astroquery.  '
                   f'Expected version {KNOWN_GOOD_API_VERSION} but got '
                   f'{api_version} from the API.')
            raise Exception(msg)

        if which == 'vohdu':
            self.url = f'{self.NAT_URL}/api/sia/vohdu'
        if which == 'voimg':
            self.url = f'{self.NAT_URL}/api/sia/voimg'
        else:
            self.url = f'{self.NAT_URL}/api/sia/voimg'

    @class_or_instance
    def query_region(self, coordinate, radius='1'):
        ra, dec = coordinate.to_string('decimal').split()
        size = radius
        url = f'{self.url}?POS={ra},{dec}&SIZE={size}&format=json'
        response = requests.get(url)
        # #!response = self._request('GET', url)
        return astropy.table.Table(data=response.json())

    def _args_to_payload(self, *args):
        # convert arguments to a valid requests payload
        return dict


Noao = NoaoClass()
