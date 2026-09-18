# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""Download of Fermi LAT (Large Area Telescope) data.

This module talks to the Fermi LAT Data Query REST API::

    POST /query              -> {"query_id": ...}
    GET  /query/{id}/status  -> {"state": ...}
    GET  /query/{id}/results -> {"files": [{"name": ...}, ...]}

which is replacing the legacy ``LATDataQuery.cgi`` form endpoint whose HTML
response pages this module used to scrape with regular expressions.
"""

import re
import time
from urllib.parse import urljoin

import astropy.units as u
from astropy.utils.decorators import deprecated

from ..query import BaseQuery
from ..utils import commons, async_to_sync
from ..exceptions import RemoteServiceError, TimeoutError
from . import conf

__all__ = ['FermiLAT', 'FermiLATClass',
           'GetFermilatDatafile', 'get_fermilat_datafile',
           ]

# The API reports free-form, human-readable states ("Query completed",
# "Query in progress", ...).  Rather than hard-coding the exact strings -
# which is what made the previous scraping implementation so brittle - we
# match on substrings and treat anything unrecognised as "still running".
_DONE_TOKENS = ('complet', 'done', 'finished', 'ready')
_ERROR_TOKENS = ('error', 'fail', 'reject', 'invalid', 'abort', 'cancel')

# "128.836,-45.1764" and friends: already a coordinate pair, no name
# resolution needed (also covers the all-sky "0.0,0.0" convention).
_COORD_PAIR_RE = re.compile(r'^\s*[-+]?\d+(\.\d*)?\s*,\s*[-+]?\d+(\.\d*)?\s*$')


@async_to_sync
class FermiLATClass(BaseQuery):
    """
    Query the Fermi LAT Data Server.

    The server runs queries asynchronously: `query_object_async` submits a
    query and returns its ``query_id``, and `query_object` additionally waits
    for the query to finish and returns the URLs of the staged data files.
    """

    base_url = conf.url
    TIMEOUT = conf.timeout
    RETRIEVAL_TIMEOUT = conf.retrieval_timeout

    #: minutes between status polls while waiting for a query to finish
    check_frequency = 1

    # ------------------------------------------------------------------
    # submission
    # ------------------------------------------------------------------
    def query_object_async(self, *args, **kwargs):
        """
        Submit a query to the Fermi LAT Data Server.

        Accepts the same arguments as `_parse_args`.

        Returns
        -------
        query_id : str
            The identifier of the submitted query, e.g.
            ``'L2601082002167F48EE3069'``.  Pass it to `get_file_urls` (or
            just use `query_object`, which does the waiting for you).

        Notes
        -----
        Prior to the REST API migration this method returned the URL of an
        HTML results page.  It now returns the server-assigned ``query_id``.
        """
        payload = self._parse_args(*args, **kwargs)

        if kwargs.get('get_query_payload'):
            return payload

        response = self._request(
            "POST", url=f"{self.base_url}/query", json=payload,
            timeout=self.TIMEOUT, cache=False)
        _raise_for_status(response, context="Fermi LAT query submission")

        result = response.json()

        if 'query_id' not in result:
            raise RemoteServiceError(
                "The query response did not contain a 'query_id'. "
                f"Server said: {result!r}")

        return result['query_id']

    def _parse_args(self, name_or_coords, *, searchradius='', obsdates='',
                    timesys='Gregorian', energyrange_MeV='',
                    LATdatatype='Photon', spacecraftdata=True,
                    coordsystem='J2000', zenithangle=None,
                    get_query_payload=False):
        """
        Parameters
        ----------
        name_or_coords : str or `~astropy.coordinates.SkyCoord`
            An object name, a coordinate specification, or a literal
            ``"RA,Dec"`` string.  Names are resolved locally (via SESAME)
            before submission.
        searchradius : str or float
            The search radius in degrees around the object/coordinates
            specified.  Must be in the range [1, 60], or > 60 (typically 180)
            for an all-sky query - note that all-sky queries are restricted by
            the server to observation windows of <= 24 hours.

            .. warning::
                Defaults to 1 degree if left blank.
        obsdates : str
            Observation window, as ``"start,stop"``.
        timesys : 'Gregorian' or 'MET' or 'MJD'
            Time system associated with ``obsdates``.
        energyrange_MeV : str
            Energy range in MeV, as ``"min,max"``.
        LATdatatype : 'Photon' or 'Extended' or 'None'
            Which LAT event class to retrieve.
        spacecraftdata : bool
            Whether to also retrieve the spacecraft (SC) file.
        coordsystem : 'J2000' or 'B1950' or 'Galactic'
            Coordinate system of the submitted coordinates.  Resolved names
            and `~astropy.coordinates.SkyCoord` inputs are transformed into
            this frame.
        zenithangle : float, optional
            Maximum zenith angle in degrees.  The server default is 180.

        Returns
        -------
        payload : dict
            The JSON payload posted to ``/query``.
        """
        # The API requires a radius; the CGI form silently defaulted to 1 deg,
        # so preserve that behaviour rather than sending an empty string.
        if searchradius in ('', None):
            searchradius = 1

        payload = {
            'coordfield': _parse_coordinates(name_or_coords,
                                             coordsystem=coordsystem),
            'coordsystem': coordsystem,
            # the API kept the legacy CGI-form name for the search radius
            'shapefield': searchradius,
            'timefield': obsdates,
            'timetype': timesys,
            'energyfield': energyrange_MeV,
            'photonOrExtendedOrNone': LATdatatype,
            'spacecraft': 'on' if spacecraftdata else 'off',
        }

        if zenithangle is not None:
            payload['zenithangle'] = zenithangle

        return payload

    # ------------------------------------------------------------------
    # status / results
    # ------------------------------------------------------------------
    def get_status(self, query_id):
        """
        Return the raw status document for ``query_id``.

        Returns
        -------
        status : dict
            The parsed ``/query/{id}/status`` response.  The overall state is
            in ``status['state']``; per-server detail is in ``queue_status``,
            ``running_status`` and ``servers_status``.
        """
        response = self._request(
            "GET", url=f"{self.base_url}/query/{query_id}/status",
            timeout=self.TIMEOUT, cache=False)
        _raise_for_status(response, context=f"Fermi LAT status ({query_id})")
        return response.json()

    def list_results(self, query_id):
        """
        Return the file metadata for a completed query.

        Returns
        -------
        files : list of dict
            The ``files`` entries of the ``/query/{id}/results`` response.
        """
        response = self._request(
            "GET", url=f"{self.base_url}/query/{query_id}/results",
            timeout=self.RETRIEVAL_TIMEOUT, cache=False)
        _raise_for_status(response, context=f"Fermi LAT results ({query_id})")
        return response.json().get('files', [])

    def wait_for_completion(self, query_id, *, check_frequency=None,
                            max_wait=None, verbose=False):
        """
        Poll ``/query/{id}/status`` until the query finishes.

        Parameters
        ----------
        check_frequency : float, optional
            Minutes between polls.  Defaults to `check_frequency`.
        max_wait : float, optional
            Give up after this many minutes.  ``None`` (default) waits
            indefinitely.
        verbose : bool
            Print the elapsed time on completion.

        Returns
        -------
        status : dict
            The final status document.
        """
        if check_frequency is None:
            check_frequency = self.check_frequency

        elapsed_time = 0.0

        while True:
            status = self.get_status(query_id)
            state = str(status.get('state', ''))
            lowered = state.lower()

            if any(token in lowered for token in _ERROR_TOKENS):
                raise RemoteServiceError(
                    f"Fermi LAT query {query_id} failed with state {state!r}")

            if any(token in lowered for token in _DONE_TOKENS):
                if verbose:
                    print(f"Query completed in {elapsed_time:0.1f} minutes")
                return status

            if max_wait is not None and elapsed_time >= max_wait:
                raise TimeoutError(
                    f"Fermi LAT query {query_id} did not complete within "
                    f"{max_wait} minutes (last state: {state!r})")

            time.sleep(check_frequency * 60)
            elapsed_time += check_frequency

    def get_file_urls(self, query_id, *, check_frequency=None, max_wait=None,
                      verbose=False):
        """
        Wait for ``query_id`` to complete and return the result file URLs.

        Returns
        -------
        urls : list of str
        """
        self.wait_for_completion(query_id, check_frequency=check_frequency,
                                 max_wait=max_wait, verbose=verbose)
        return [_file_url(entry) for entry in self.list_results(query_id)]

    def _parse_result(self, result, *, verbose=False, **kwargs):
        """
        Turn the ``query_id`` returned by `query_object_async` into a list of
        downloadable file URLs, waiting for the query to complete.
        """
        return self.get_file_urls(result, verbose=verbose)


FermiLAT = FermiLATClass()


def _raise_for_status(response, *, context):
    """
    Raise a `RemoteServiceError` carrying the server's error message.

    The Fermi API signals bad requests with an HTTP error status and a JSON
    body of the form ``{"error": "..."}``.  ``requests.raise_for_status`` only
    reports the status code, so this helper pulls the message out of the body
    (trying the ``error``, ``detail`` and ``message`` keys, then falling back
    to the raw text) and surfaces it, as recommended by the astroquery API
    specification.
    """
    status_code = getattr(response, 'status_code', None)
    if status_code is None or status_code < 400:
        return

    message = None
    try:
        body = response.json()
    except ValueError:
        body = None

    if isinstance(body, dict):
        for key in ('error', 'detail', 'message'):
            if body.get(key):
                message = body[key]
                break
    if message is None:
        text = getattr(response, 'text', '') or ''
        message = text.strip() or f"HTTP {status_code}"

    raise RemoteServiceError(f"{context} failed ({status_code}): {message}")


def _file_url(entry):
    """
    Build an absolute URL for one entry of the ``results`` file list.

    The API is documented as returning ``{"name": "..._PH00.fits"}``; if a
    future revision also returns an absolute ``url``/``href``/``path``, prefer
    that over reconstructing the location from `conf.file_base_url`.
    """
    if isinstance(entry, str):
        name = entry
    else:
        for key in ('url', 'href', 'path', 'location'):
            value = entry.get(key)
            if value:
                if value.startswith('http'):
                    return value
                return urljoin(conf.file_base_url, value.lstrip('/'))
        name = entry.get('name')

    if not name:
        raise RemoteServiceError(
            f"Could not determine a file URL from results entry {entry!r}")

    return urljoin(conf.file_base_url, name)


def _parse_coordinates(coordinates, *, coordsystem='J2000'):
    # A literal "RA,Dec" pair (including the all-sky "0.0,0.0" convention) is
    # passed straight through - no name resolution, no frame transform.
    if isinstance(coordinates, str) and _COORD_PAIR_RE.match(coordinates):
        return coordinates.replace(' ', '')

    try:
        c = commons.parse_coordinates(coordinates)
    except (u.UnitsError, TypeError):
        raise ValueError("Coordinates not specified correctly")

    return _fermi_format_coords(c, coordsystem=coordsystem)


def _fermi_format_coords(c, *, coordsystem='J2000'):
    frames = {'j2000': 'fk5', 'b1950': 'fk4', 'galactic': 'galactic'}

    try:
        frame = frames[coordsystem.lower()]
    except KeyError:
        raise ValueError(
            f"Unsupported coordsystem {coordsystem!r}; "
            f"expected one of {', '.join(sorted(frames))}")

    c = c.transform_to(frame)

    if frame == 'galactic':
        lon, lat = c.l.degree, c.b.degree
    else:
        lon, lat = c.ra.degree, c.dec.degree

    return "{0:0.5f},{1:0.5f}".format(lon, lat)


@deprecated(since='0.4.12',
            alternative='FermiLAT.query_object or FermiLAT.get_file_urls')
class GetFermilatDatafile:
    """
    Deprecated.  Retained so that code written against the pre-REST module
    keeps importing; it now delegates to `FermiLATClass.get_file_urls`.
    """

    TIMEOUT = conf.retrieval_timeout
    check_frequency = 1

    def __call__(self, query_id, *, check_frequency=None, verbose=False):
        if check_frequency is None:
            check_frequency = self.check_frequency
        return FermiLAT.get_file_urls(query_id,
                                      check_frequency=check_frequency,
                                      verbose=verbose)


@deprecated(since='0.4.12',
            alternative='FermiLAT.query_object or FermiLAT.get_file_urls')
def get_fermilat_datafile(query_id, *, check_frequency=1, verbose=False):
    """
    Deprecated.  Wait for a query to finish and return its data file URLs.

    Note that this takes a ``query_id`` - the pre-REST version took the URL of
    an HTML results page, which no longer exists.
    """
    return FermiLAT.get_file_urls(query_id, check_frequency=check_frequency,
                                  verbose=verbose)
