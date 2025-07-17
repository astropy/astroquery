# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
Provide astroquery API access to NSF NOIRLab Astro Data Archive.

This does DB access through web-services.
"""
import astropy.io.fits as fits
import astropy.table
from ..query import BaseQuery
from ..utils import async_to_sync
from ..exceptions import RemoteServiceError
# from ..utils.class_or_instance import class_or_instance
from . import conf


__all__ = ['NOIRLab', 'NOIRLabClass']  # specifies what to import


@async_to_sync
class NOIRLabClass(BaseQuery):
    """Search functionality for the NSF NOIRLab Astro Data Archive.
    """
    TIMEOUT = conf.timeout
    NAT_URL = conf.server

    def __init__(self):
        self._api_version = None
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
        """Ensure the API is compatible with the code.
        """
        KNOWN_GOOD_API_VERSION = 6.0
        if (int(self.api_version) - int(KNOWN_GOOD_API_VERSION)) >= 1:
            msg = (f'The astroquery.noirlab module is expecting an older '
                   f'version of the {self.NAT_URL} API services. '
                   f'Please upgrade to latest astroquery.  '
                   f'Expected version {KNOWN_GOOD_API_VERSION} but got '
                   f'{self.api_version} from the API.')
            raise RemoteServiceError(msg)

    def _sia_url(self, hdu=False):
        """Return the URL for SIA queries.

        Parameters
        ----------
        hdu : :class:`bool`, optional
            If ``True`` return the URL for HDU-based queries.

        Returns
        -------
        :class:`str`
            The query URL.
        """
        return f'{self.NAT_URL}/api/sia/vohdu' if hdu else f'{self.NAT_URL}/api/sia/voimg'

    def _fields_url(self, hdu=False, aux=False):
        """Return the URL for metadata queries.

        Parameters
        ----------
        hdu : :class:`bool`, optional
            If ``True`` return the URL for HDU-based queries.
        aux : :class:`bool`, optional
            If ``True`` return metadata on AUX fields.

        Returns
        -------
        :class:`str`
            The query URL.
        """
        file = 'hdu' if hdu else 'file'
        core = 'aux' if aux else 'core'
        return f'{self.NAT_URL}/api/adv_search/{core}_{file}_fields'

    def _response_to_table(self, response_json):
        """Convert a JSON response to a :class:`~astropy.table.Table`.

        Parameters
        ----------
        response_json : :class:`list`
            A query response formatted as a list of objects. The query
            metadata is the first item in the list.

        Returns
        -------
        :class:`~astropy.table.Table`
            The converted response. The column ordering will match the
            ordering of the `HEADER` metadata.
        """
        names = list(response_json[0]['HEADER'].keys())
        rows = [[row[n] for n in names] for row in response_json[1:]]
        return astropy.table.Table(names=names, rows=rows)

    def service_metadata(self, hdu=False, cache=True):
        """A SIA metadata query: no images are requested; only metadata
        should be returned.

        This feature is described in more detail in:
        https://www.ivoa.net/documents/PR/DAL/PR-SIA-1.0-20090521.html#mdquery

        Parameters
        ----------
        hdu : :class:`bool`, optional
            If ``True`` return the URL for HDU-based queries.
        cache : :class:`bool`, optional
            If ``True`` cache the result locally.

        Returns
        -------
        :class:`dict`
            A dictionary containing SIA metadata.
        """
        url = f'{self._sia_url(hdu=hdu)}?FORMAT=METADATA&format=json'
        response = self._request('GET', url, timeout=self.TIMEOUT, cache=cache)
        return response.json()

    def query_region(self, coordinate, radius=0.1, hdu=False, cache=True):
        """Query for NOIRLab observations by region of the sky.

        Given a sky coordinate and radius, returns a `~astropy.table.Table`
        of NOIRLab observations.

        Parameters
        ----------
        coordinate : :class:`str` or `~astropy.coordinates` object
            The target region which to search. It may be specified as a
            string or as the appropriate `~astropy.coordinates` object.
        radius : :class:`str` or `~astropy.units.Quantity` object, optional
            Default 0.1 degrees.
            The string must be parsable by `~astropy.coordinates.Angle`. The
            appropriate `~astropy.units.Quantity` object from
            `~astropy.units` may also be used.
        hdu : :class:`bool`, optional
            If ``True`` return the URL for HDU-based queries.
        cache : :class:`bool`, optional
            If ``True`` cache the result locally.

        Returns
        -------
        :class:`~astropy.table.Table`
            A table containing the results.
        """
        response = self.query_region_async(coordinate, radius=radius, hdu=hdu, cache=cache)
        response.raise_for_status()
        return self._response_to_table(response.json())

    def query_region_async(self, coordinate, radius=0.1, hdu=False, cache=True):
        """Query for NOIRLab observations by region of the sky.

        Given a sky coordinate and radius, returns a `~astropy.table.Table`
        of NOIRLab observations.

        Parameters
        ----------
        coordinate : :class:`str` or `~astropy.coordinates` object
            The target region which to search. It may be specified as a
            string or as the appropriate `~astropy.coordinates` object.
        radius : :class:`str` or `~astropy.units.Quantity` object, optional
            Default 0.1 degrees.
            The string must be parsable by `~astropy.coordinates.Angle`. The
            appropriate `~astropy.units.Quantity` object from
            `~astropy.units` may also be used.
        hdu : :class:`bool`, optional
            If ``True`` return the URL for HDU-based queries.
        cache : :class:`bool`, optional
            If ``True`` cache the result locally.

        Returns
        -------
        :class:`~requests.Response`
            Response object.
        """
        self._validate_version()
        ra, dec = coordinate.to_string('decimal').split()
        url = f'{self._sia_url(hdu=hdu)}?POS={ra},{dec}&SIZE={radius}&VERB=3&format=json'
        response = self._request('GET', url, timeout=self.TIMEOUT, cache=cache)
        # response.raise_for_status()
        return response

    def core_fields(self, hdu=False, cache=True):
        """List the available CORE fields for file or HDU searches.

        CORE fields are faster to search than AUX fields.

        Parameters
        ----------
        hdu : :class:`bool`, optional
            If ``True`` return the fields for HDU-based queries.
        cache : :class:`bool`, optional
            If ``True`` cache the result locally.

        Returns
        -------
        :class:`list`
            A list of field descriptions, each a :class:`dict`.
        """
        url = self._fields_url(hdu=hdu, aux=False)
        response = self._request('GET', url, timeout=self.TIMEOUT, cache=cache)
        response.raise_for_status()
        return response.json()

    def aux_fields(self, instrument, proctype, hdu=False, cache=True):
        """List the available AUX fields.

        AUX fields are any fields in the Archive FITS files that are not
        CORE DB fields.  These are generally common to a single instrument,
        proctype combination. AUX fields are slower to search than CORE fields.
        Acceptable values for ``instrument`` and ``proctype`` are listed in the
        results of the :meth:`astroquery.noirlab.core.NOIRLabClass.categoricals`
        method.

        Parameters
        ----------
        instrument : :class:`str`
            The specific instrument, *e.g.* '90prime' or 'decam'.
        proctype : :class:`str`
            A description of the type of image, *e.g.* 'raw' or 'instcal'.
        hdu : :class:`bool`, optional
            If ``True`` return the fields for HDU-based queries.
        cache : :class:`bool`, optional
            If ``True`` cache the result locally.

        Returns
        -------
        :class:`list`
            A list of field descriptions, each a :class:`dict`.
        """
        url = f'{self._fields_url(hdu=hdu, aux=True)}/{instrument}/{proctype}/'
        response = self._request('GET', url, timeout=self.TIMEOUT, cache=cache)
        response.raise_for_status()
        return response.json()

    def categoricals(self, cache=True):
        """List the currently acceptable values for each 'categorical field'
        associated with Archive files.

        A 'categorical field' is one in which the values are restricted to a
        specific set.  The specific set may grow over time, but not often.
        The categorical fields are: ``instrument``, ``obsmode``, ``obstype``,
        ``proctype``, ``prodtype``, ``site``, ``survey``, ``telescope``.

        Parameters
        ----------
        cache : :class:`bool`, optional
            If ``True`` cache the result locally.

        Returns
        -------
        :class:`dict`
            A dictionary containing the category metadata.
        """
        url = f'{self.NAT_URL}/api/adv_search/cat_lists/?format=json'
        response = self._request('GET', url, timeout=self.TIMEOUT, cache=cache)
        response.raise_for_status()
        return response.json()

    def query_metadata(self, qspec=None, sort=None, limit=1000, hdu=False, cache=True):
        """Query the archive database for details on available files.

        ``qspec`` should minimally contain a list of output columns and a list of
        search parameters, which could be empty. For example::

            qspec = {"outfields": ["md5sum", ], "search": []}

        Parameters
        ----------
        qspec : :class:`dict`, optional
            The query that will be passed to the API.
        sort : :class:`str`, optional
            Sort the results on one of the columns in ``qspec``.
        limit : :class:`int`, optional
            The number of results to return, default 1000.
        hdu : :class:`bool`, optional
            If ``True`` return the URL for HDU-based queries.
        cache : :class:`bool`, optional
            If ``True`` cache the result locally.

        Returns
        -------
        :class:`~astropy.table.Table`
            A Table containing the results.
        """
        self._validate_version()
        file = 'hdu' if hdu else 'file'
        url = f'{self.NAT_URL}/api/adv_search/find/?rectype={file}&limit={limit}'
        if sort:
            # TODO: write a test for this, which may involve refactoring async versus sync.
            url += f'&sort={sort}'

        if qspec is None:
            jdata = {"outfields": ["md5sum", ], "search": []}
        else:
            jdata = qspec

        response = self._request('POST', url, json=jdata,
                                 timeout=self.TIMEOUT, cache=cache)
        response.raise_for_status()
        return self._response_to_table(response.json())

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
        cache : :class:`bool`, optional
            If ``True`` cache the result locally.

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
