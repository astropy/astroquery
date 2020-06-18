"""
Provide astroquery API access to OIR Lab Astro Data Archive (natica).

This does DB access through web-services.
"""

import astropy.table
from ..query import BaseQuery
from ..utils import async_to_sync
from ..utils.class_or_instance import class_or_instance
from . import conf


__all__ = ['Noirlab', 'NoirlabClass']  # specifies what to import


@async_to_sync
class NoirlabClass(BaseQuery):

    TIMEOUT = conf.timeout
    NAT_URL = conf.server
    ADS_URL = f'{NAT_URL}/api/adv_search/fasearch'
    SIA_URL = f'{NAT_URL}/api/sia/voimg'

    def __init__(self, which='file'):
        """Return object used for searching the NOIRLab Archive.

        Search either Files (which=file) or HDUs (which=hdu).
        Files will always be returned.  But if which=hdu,
        individual HDUs must have RA,DEC fields.  Typically this
        is only the case with some pipeline processed files.
        """
        self._api_version = None

        if which == 'hdu':
            self.url = f'{self.NAT_URL}/api/sia/vohdu'
        elif which == 'file':
            self.url = f'{self.NAT_URL}/api/sia/voimg'
        else:
            self.url = f'{self.NAT_URL}/api/sia/voimg'

        super().__init__()

    @property
    def api_version(self):
        """Return version of Rest API used by this module.

        If the Rest API changes such that the Major version increases,
        a new version of this module will likely need to be used.
        """
        if self._api_version is None:
            response = self._request('GET',
                                     f'{self.NAT_URL}/api/version',
                                     timeout=self.TIMEOUT,
                                     cache=True)
            self._api_version = float(response.content)
        return self._api_version

    def _validate_version(self):
        KNOWN_GOOD_API_VERSION = 2.0
        if (int(self.api_version) - int(KNOWN_GOOD_API_VERSION)) >= 1:
            msg = (f'The astroquery.noirlab module is expecting an older '
                   f'version of the {self.NAT_URL} API services. '
                   f'Please upgrade to latest astroquery.  '
                   f'Expected version {KNOWN_GOOD_API_VERSION} but got '
                   f'{self.api_version} from the API.')
            raise Exception(msg)

    @class_or_instance
    def query_region(self, coordinate, radius=0.1, *, cache=True):
        """Query for NOIRLab observations by region of the sky.

        Given a sky coordinate and radius, returns a `~astropy.table.Table`
        of NOIRLab observations.

        Parameters
        ----------
        coordinates : str or `~astropy.coordinates` object
            The target region which to search. It may be specified as a
            string or as the appropriate `~astropy.coordinates` object.
        radius : str or `~astropy.units.Quantity` object, optional
            Default 0.1 degrees.
            The string must be parsable by `~astropy.coordinates.Angle`. The
            appropriate `~astropy.units.Quantity` object from
            `~astropy.units` may also be used.

        Returns
        -------
        response : `~astropy.table.Table`
        """
        self._validate_version()
        ra, dec = coordinate.to_string('decimal').split()
        url = f'{self.url}?POS={ra},{dec}&SIZE={radius}&format=json'
        response = self._request('GET', url,
                                 timeout=self.TIMEOUT,
                                 cache=cache)
        response.raise_for_status()
        return astropy.table.Table(data=response.json())


Noirlab = NoirlabClass()
