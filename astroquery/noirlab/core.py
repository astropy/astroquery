"""
Provide astroquery API access to NSF NOIRLab Astro Data Archive.

This does DB access through web-services.
"""
import astropy.io.fits as fits
import astropy.table
from ..query import BaseQuery
from ..utils import async_to_sync
from ..exceptions import RemoteServiceError
from ..utils.class_or_instance import class_or_instance
from . import conf


__all__ = ['NOIRLab', 'NOIRLabClass']  # specifies what to import


@async_to_sync
class NOIRLabClass(BaseQuery):
    """Search functionality for the NSF NOIRLab Astro Data Archive.

    Parameters
    ----------
    hdu : :class:`bool`, optional
        If ``True``, search HDUs in files. THe HDUs must have RA, DEC header
        keywords. This is not guaranteed for all files.
        The default is to just search for files.
    """
    TIMEOUT = conf.timeout
    NAT_URL = conf.server

    def __init__(self, hdu=False):
        self._api_version = None
        self._adsurl = f'{self.NAT_URL}/api/adv_search'

        if hdu:
            self.siaurl = f'{self.NAT_URL}/api/sia/vohdu'
            self._adss_url = f'{self._adsurl}/hasearch'
            self._adsc_url = f'{self._adsurl}/core_hdu_fields'
            self._adsa_url = f'{self._adsurl}/aux_hdu_fields'
        else:
            self.siaurl = f'{self.NAT_URL}/api/sia/voimg'
            self._adss_url = f'{self._adsurl}/fasearch'
            self._adsc_url = f'{self._adsurl}/core_file_fields'
            self._adsa_url = f'{self._adsurl}/aux_file_fields'

        super().__init__()

    @property
    def api_version(self):
        """Return version of REST API used by this module.

        If the REST API changes such that the major version increases,
        a new version of this module will likely need to be used.
        """
        if self._api_version is None:
            self._api_version = float(self.version())
        return self._api_version

    def _validate_version(self):
        KNOWN_GOOD_API_VERSION = 6.0
        if (int(self.api_version) - int(KNOWN_GOOD_API_VERSION)) >= 1:
            msg = (f'The astroquery.noirlab module is expecting an older '
                   f'version of the {self.NAT_URL} API services. '
                   f'Please upgrade to latest astroquery.  '
                   f'Expected version {KNOWN_GOOD_API_VERSION} but got '
                   f'{self.api_version} from the API.')
            raise RemoteServiceError(msg)

    def service_metadata(self, cache=True):
        """Denotes a Metadata Query: no images are requested; only metadata
        should be returned. This feature is described in more detail in:
        http://www.ivoa.net/documents/PR/DAL/PR-SIA-1.0-20090521.html#mdquery
        """
        url = f'{self.siaurl}?FORMAT=METADATA&format=json'
        response = self._request('GET', url, timeout=self.TIMEOUT, cache=cache)
        return response.json()[0]

    @class_or_instance
    def query_region(self, coordinate, radius=0.1, cache=True):
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
        `~astropy.table.Table`
        """
        self._validate_version()
        ra, dec = coordinate.to_string('decimal').split()
        url = f'{self.siaurl}?POS={ra},{dec}&SIZE={radius}&format=json'
        response = self._request('GET', url,
                                 timeout=self.TIMEOUT,
                                 cache=cache)
        response.raise_for_status()
        return astropy.table.Table(data=response.json())

    def query_region_async(self, coordinate, radius=0.1, cache=True):
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
        `requests.Response`
        """
        self._validate_version()

        ra, dec = coordinate.to_string('decimal').split()
        url = f'{self.siaurl}?POS={ra},{dec}&SIZE={radius}&format=json'
        response = self._request('GET', url,
                                 timeout=self.TIMEOUT,
                                 cache=cache)
        response.raise_for_status()
        return response

    def core_fields(self, cache=True):
        """List the available CORE fields.

        CORE fields are faster to search than AUX fields.

        Parameters
        ----------
        cache : :class:`bool`, optional
            If ``True`` cache the result locally.

        Returns
        -------
        :class:`list`
            A list of field descriptions, each a :class:`dict`.
        """
        response = self._request('GET', self._adsc_url,
                                 timeout=self.TIMEOUT,
                                 cache=cache)
        response.raise_for_status()
        return response.json()

    def aux_fields(self, instrument, proctype, cache=True):
        """List the available AUX fields. AUX fields are ANY fields in the
        Archive FITS files that are not core DB fields.  These are generally
        common to a single Instrument, Proctype combination. AUX fields are
        slower to search than CORE fields.  Acceptable values for INSTRUMENT and PROCTYPE
        are listed in the results of the CATEGORICALS method.
        """
        url = f'{self._adsa_url}/{instrument}/{proctype}/'
        response = self._request('GET', url, timeout=self.TIMEOUT, cache=cache)
        response.raise_for_status()
        return response.json()

    def categoricals(self, cache=True):
        """List the currently acceptable values for each 'categorical field'
        associated with Archive files.  A 'categorical field' is one in
        which the values are restricted to a specific set.  The specific
        set may grow over time, but not often. The categorical fields are:
        collection, instrument, obs_mode, proc_type, prod_type, site, survey,
        telescope.
        """
        url = f'{self._adsurl}/cat_lists/?format=json'
        response = self._request('GET', url, timeout=self.TIMEOUT, cache=cache)
        response.raise_for_status()
        return response.json()

    @class_or_instance
    def query_metadata(self, qspec, limit=1000, cache=True):
        # self._validate_version()
        url = f'{self._adss_url}/?limit={limit}'

        if qspec is None:
            jdata = {"outfields": ["md5sum", ], "search": []}
        else:
            jdata = qspec

        response = self._request('POST', url, json=jdata,
                                 timeout=self.TIMEOUT, cache=cache)
        response.raise_for_status()
        return astropy.table.Table(rows=response.json())

    def retrieve(self, fileid):
        """Simply fetch a file by MD5 ID.

        Parameters
        ----------
        fileid : :class:`str`
            The MD5 ID of the file.

        Returns
        -------
        :class:`~astropy.io.fits.HDUList`
            The open FITS file. Call ``.close()`` on this object when done.
        """
        url = f'{self.NAT_URL}/api/retrieve/{fileid}/'
        hdulist = fits.open(url)
        return hdulist

    def version(self, cache=False):
        """Return the version of the REST API.

        Parameters
        ----------
        cache : :class:`bool`, optional
            If ``True`` cache the result locally.

        Returns
        -------
        :class:`float`
            The API version as a number.
        """
        url = f'{self.NAT_URL}/api/version/'
        response = self._request('GET', url, timeout=self.TIMEOUT, cache=cache)
        response.raise_for_status()
        return response.json()

    def get_token(self, email, password, cache=True):
        """Get an access token to use with proprietary data.

        Parameters
        ----------
        email : :class:`str`
            Email for account access.
        password : :class:`str`
            Password associated with `email`. *Please* never hard-code your
            password *anywhere*.

        Returns
        -------
        :class:`str`
            The access token as a string.
        """
        url = f'{self.NAT_URL}/api/get_token/'
        response = self._request('POST', url,
                                 json={"email": email, "password": password},
                                 timeout=self.TIMEOUT, cache=cache)
        response.raise_for_status()
        return response.json()


NOIRLab = NOIRLabClass()
