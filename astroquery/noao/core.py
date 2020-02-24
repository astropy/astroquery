"""
Provide astroquery API access to OIR Lab Astro Data Archive (natica).

This does DB access through web-services.
"""

import astropy.table
from ..query import BaseQuery
from ..utils import async_to_sync
from ..utils.class_or_instance import class_or_instance
from . import conf


__all__ = ['Noao', 'NoaoClass']  # specifies what to import


@async_to_sync
class NoaoClass(BaseQuery):

    NAT_URL = conf.server
    ADS_URL = f'{NAT_URL}/api/adv_search/fasearch'
    SIA_URL = f'{NAT_URL}/api/sia/voimg'

    def __init__(self, which='voimg'):
        """ set some parameters """
        self._api_version = None

        if which == 'vohdu':
            self.url = f'{self.NAT_URL}/api/sia/vohdu'
        if which == 'voimg':
            self.url = f'{self.NAT_URL}/api/sia/voimg'
        else:
            self.url = f'{self.NAT_URL}/api/sia/voimg'

        super().__init__()

    @property
    def api_version(self):
        if self._api_version is None:
            response = self._request('GET',
                                     f'{self.NAT_URL}/api/version',
                                     cache=True)
            self._api_version = float(response.content)
        return self._api_version

    def validate_version(self):
        KNOWN_GOOD_API_VERSION = 2.0
        if (int(self.api_version) - int(KNOWN_GOOD_API_VERSION)) >= 1:
            msg = (f'The astroquery.noao module is expecting an older version '
                   f'of the {self.NAT_URL} API services.  '
                   f'Please upgrade to latest astroquery.  '
                   f'Expected version {KNOWN_GOOD_API_VERSION} but got '
                   f'{self.api_version} from the API.')
            raise Exception(msg)

    @class_or_instance
    def query_region(self, coordinate, radius='1'):
        self.validate_version()
        ra, dec = coordinate.to_string('decimal').split()
        size = radius
        url = f'{self.url}?POS={ra},{dec}&SIZE={size}&format=json'
        response = self._request('GET', url, cache=True)
        return astropy.table.Table(data=response.json())

    def _args_to_payload(self, *args):
        # convert arguments to a valid requests payload
        return dict


Noao = NoaoClass()
