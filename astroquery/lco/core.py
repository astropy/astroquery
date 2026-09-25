# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
Provide astroquery API access to Las Cumbres Observatory (LCO)'s Archive.

This accesses the LCO's archive web service with or without an API Token.
"""

import contextlib
import os
import warnings
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

import keyring
import numpy as np
import requests

import astropy.units as u
from astropy.coordinates import Angle
from astropy.table import MaskedColumn, Table
from astropy.time import Time
from astropy.utils.console import ProgressBarOrSpinner, Spinner

from astroquery import cache_conf, log
from astroquery.exceptions import (LargeQueryWarning, LoginError, MaxResultsWarning,
                                   NoResultsWarning, RemoteServiceError)
from astroquery.lco import conf
from astroquery.query import QueryWithLogin
from astroquery.utils import commons


__all__ = ['LcoArchive', 'LcoArchiveClass']


# Filters accepted by the ``/frames/`` endpoint. Anything not in here is
# rejected client-side so that typos do not silently return the whole archive.
FRAME_FILTERS = (
    'basename',
    'basename_exact',
    'configuration_type',
    'covers',
    'empty_target_name',
    'end',
    'exclude_calibrations',
    'exclude_configuration_type',
    'exposure_time',
    'id__gt',
    'include_configuration_type',
    'instrument_id',
    'intersects',
    'observation_id',
    'primary_optical_element',
    'proposal_id',
    'public',
    'reduction_level',
    'request_id',
    'site_id',
    'start',
    'submitter',
    'target_name',
    'target_name_exact',
    'telescope_id',
)

# Scalar columns kept in the result table, in display order. The fields ``related_frames``,
# ``version_set`` and ``area`` do not fit a flat table, so ``ra`` and ``dec`` give the
# center of ``area`` instead.
RESULT_COLUMNS = (
    'id',
    'basename',
    'filename',
    'observation_date',
    'observation_day',
    'proposal_id',
    'target_name',
    'ra',
    'dec',
    'site_id',
    'telescope_id',
    'instrument_id',
    'configuration_type',
    'primary_optical_element',
    'exposure_time',
    'reduction_level',
    'observation_id',
    'request_id',
    'public_date',
    'url',
)

# The archive caps page size at 100 for anonymous users and 1000 for
# authenticated ones.
ANONYMOUS_PAGE_SIZE = 100
AUTHENTICATED_PAGE_SIZE = 1000

# Thumbnail sizes the archive publishes.
THUMBNAIL_SIZES = ('small', 'large')

# LCO Archive presigned URLs are only valid for this long, so only
# cache responses for this long.
CACHE_TIMEOUT = 48 * 60 * 60

# How many frames an unbounded query may collect before it warns that it is
# still going.
LARGE_RESULT_WARNING = 10000


class LcoArchiveClass(QueryWithLogin):
    """
    Search functionality for the LCO Archive.

    The archive is open to anonymous users, who see every frame whose
    proprietary period has expired. Logging in with an API token additionally
    exposes the proprietary frames belonging to your proposals.
    """

    ARCHIVE_URL = conf.archive_url
    TOKEN_URL = conf.token_url
    TIMEOUT = conf.timeout
    ROW_LIMIT = conf.row_limit

    @property
    def _frames_url(self):
        return f'{self.ARCHIVE_URL}/frames/'

    @property
    def _page_size(self):
        return (AUTHENTICATED_PAGE_SIZE if self.authenticated()
                else ANONYMOUS_PAGE_SIZE)

    def _request(self, *args, **kwargs):
        # Frame responses carry presigned download links, so no response from
        # the archive may be reused for longer than those stay valid.
        with cache_conf.set_temp('cache_timeout', CACHE_TIMEOUT):
            return super()._request(*args, **kwargs)

    def _login(self, *, token=None, username=None, password=None,
               store_password=False, reenter_password=False):
        """
        Authenticate against the LCO archive.

        Parameters
        ----------
        token : str, optional
            An LCO API token, as shown on your profile page at
            https://observe.lco.global/accounts/profile/. If given, the
            username and password are not used or needed.
        username : str, optional
            LCO observing portal username. Used to request a token when
            ``token`` is not supplied; the password is taken from the system
            keyring, or prompted for.
        password : str, optional
            Password for ``username``. Prompted for when omitted.
        store_password : bool, optional
            Store the password in the system keyring for later sessions.
            Default is `False`.
        reenter_password : bool, optional
            Prompt for the password even when one is already in the keyring,
            which is how you overwrite a stored password. Default is `False`.

        Returns
        -------
        success : bool
            Whether the session is now authenticated.
        """
        if token is None:
            if username is None:
                raise LoginError("One of 'token' or 'username' is required "
                                 "to log in to the LCO archive.")
            if password is None:
                password, password_from_keyring = self._get_password(
                    "astroquery:observe.lco.global", username, reenter=reenter_password)
            else:
                password_from_keyring = None

            # The token exchange happens against the observing portal,
            response = self._request('POST', self.TOKEN_URL,
                                     json={'username': username,
                                           'password': password},
                                     timeout=self.TIMEOUT, cache=False)
            if response.status_code != 200:
                log.error("Unable to log in to the LCO observing portal, "
                          "please check your credentials.")
                return False

            token = response.json().get('token')
            if not token:
                log.error("The LCO observing portal did not return a token.")
                return False

            if store_password and password_from_keyring is None and password and username:
                keyring.set_password("astroquery:observe.lco.global", username, password)

        self._session.headers['Authorization'] = f'Token {token}'

        # Confirm the token is actually good. An anonymous or rejected
        # session comes back with an empty username.
        profile = self._request('GET', f'{self.ARCHIVE_URL}/profile/',
                                timeout=self.TIMEOUT, cache=False)
        if profile.status_code != 200 or not profile.json().get('username'):
            log.error("The LCO archive rejected the supplied API token.")
            del self._session.headers['Authorization']
            return False

        log.info(f"Authenticated to the LCO archive as "
                 f"{profile.json()['username']}.")
        return True

    def logout(self):
        """Drop the API token and return the session to anonymous access."""
        self._session.headers.pop('Authorization', None)
        self._authenticated = False

    def query_region(self, coordinates, *, radius=None, width=None,
                     height=None, show_progress=True,
                     get_query_payload=False, cache=None, **criteria):
        """
        Query for frames covering, or overlapping, a position on the sky.

        With no ``radius``, ``width`` or ``height`` this returns frames whose
        footprint contains ``coordinates``. With any of them it returns frames
        whose footprint overlaps the requested region.

        Parameters
        ----------
        coordinates : str or `~astropy.coordinates.SkyCoord`
            The single position to search around.
        radius : str or `~astropy.units.Quantity`, optional
            Radius of a cone search. The circle is sent to the archive as a
            32-vertex polygon inscribed in it, so the region searched is
            accurate to 0.5% of the radius specified.
        width : str or `~astropy.units.Quantity`, optional
            Width of a box search. Must be given with ``height``.
        height : str or `~astropy.units.Quantity`, optional
            Height of a box search. Must be given with ``width``.
        show_progress : bool, optional
            Display progress while retrieving a query that needs more than one
            request. Default is `True`.
        get_query_payload : bool, optional
            Return the dict of HTTP request parameters without querying.
            Default is `False`.
        cache : bool, optional
            Cache the response. Defaults to `True` for anonymous queries and
            `False` for authenticated ones.
        **criteria
            Any other frame filter, as accepted by
            :meth:`~astroquery.lco.LcoArchiveClass.query_criteria`.

        Returns
        -------
        frames : `~astropy.table.Table`
            The matching frames, one row per frame.
        """
        coordinates = commons.parse_coordinates(coordinates).icrs

        if width is not None or height is not None:
            if width is None or height is None:
                raise ValueError("Both 'width' and 'height' are required for "
                                 "a box search.")
            if radius is not None:
                raise ValueError("Give either 'radius' or 'width' and "
                                 "'height', not both.")
            criteria['intersects'] = _box_to_wkt(coordinates, Angle(width),
                                                 Angle(height))
        elif radius is not None:
            criteria['intersects'] = _circle_to_wkt(coordinates, Angle(radius))
        else:
            criteria['covers'] = f'POINT({coordinates.ra.deg} {coordinates.dec.deg})'

        return self.query_criteria(get_query_payload=get_query_payload,
                                   cache=cache,
                                   show_progress=show_progress,
                                   **criteria)

    def query_object(self, object_name, *, exact=True,
                     show_progress=True, get_query_payload=False,
                     cache=None, **criteria):
        """
        Query for frames whose target name matches ``object_name``.

        This matches on the name the observer submitted with the observation
        request, and does not resolve the name or search on position. Use
        :meth:`~astroquery.lco.LcoArchiveClass.query_region` to search by
        position instead.

        Parameters
        ----------
        object_name : str
            Target name to search for.
        exact : bool, optional
            Require the target name to match exactly. `False` performs case-
            insensitive searches that contain ``object_name``. Default is `True`.
        show_progress : bool, optional
            Display progress while retrieving a query that needs more than one
            request. Default is `True`.
        get_query_payload : bool, optional
            Return the dict of HTTP request parameters without querying.
            Default is `False`.
        cache : bool, optional
            Cache the response. Defaults to `True` for anonymous queries and
            `False` for authenticated ones.
        **criteria
            Any other frame filter, as accepted by
            :meth:`~astroquery.lco.LcoArchiveClass.query_criteria`.

        Returns
        -------
        frames : `~astropy.table.Table`
            The matching frames, one row per frame.
        """
        name_filter = 'target_name_exact' if exact else 'target_name'
        return self.query_criteria(**{name_filter: object_name},
                                   get_query_payload=get_query_payload,
                                   cache=cache,
                                   show_progress=show_progress,
                                   **criteria)

    def query_criteria(self, *, get_query_payload=False, cache=None,
                       row_limit=None, include_thumbnails=False,
                       thumbnail_size='small', show_progress=True,
                       **criteria):
        """
        Query the archive on any combination of frame filters.

        Parameters
        ----------
        **criteria
            Frame filters to apply, as ``name=value`` pairs. Most are matched
            against the archive as given, e.g. ``site_id='lsc'`` or
            ``target_name_exact='M101'``;
            :meth:`~astroquery.lco.LcoArchiveClass.list_criteria` returns every
            accepted name, and the ``list_*`` methods give the accepted values
            for the code-valued ones. The criteria below are the ones that
            take a value you cannot guess from the name:

            ``start``, ``end``
                Bounds on the observation date. Accepts a string, an
                `~astropy.time.Time`, or a `~datetime.datetime`.
            ``covers``, ``intersects``
                A `Well-Known Text (WKT)
                <https://libgeos.org/specifications/wkt/>`_ region the frame
                footprint must contain, or overlap.
                :meth:`~astroquery.lco.LcoArchiveClass.query_region` builds
                these for you from a position and an optional extent.
            ``exposure_time``
                Seconds, either as a number or an
                `~astropy.units.Quantity` that can be converted to seconds.
            ``public``
                `True` allows selection to include public frames, `False` only
                returns frames from proposals which your account is a member of.
            ``reduction_level``
                ``0`` for raw and ``91`` for reduced data.
            ``empty_target_name``
                `True` selects only frames whose target name is blank. This
                is a flag rather than a choice: `False` does not select the
                frames that *have* a name, it simply leaves the filter off.
            ``include_configuration_type``, ``exclude_configuration_type``
                Keep, or drop, several exposure types at once. These are the
                only criteria that accept a sequence, e.g.
                ``exclude_configuration_type=['BIAS', 'DARK']``; anywhere else
                a sequence is rejected, because the archive would silently use
                only its last value.
        row_limit : int, optional
            Maximum number of frames to return, at least 1. Defaults to
            ``LcoArchiveClass.ROW_LIMIT``; ``-1`` retrieves every match.
        include_thumbnails : bool, optional
            Ask the archive for thumbnail links alongside the frame metadata,
            which adds ``thumbnail_url`` and ``thumbnail_filename`` columns to
            the result. Default is `False`.
        thumbnail_size : str, optional
            Which thumbnail to keep, ``'small'`` or ``'large'``. Only used
            when ``include_thumbnails`` is `True`. Default is ``'small'``.
        show_progress : bool, optional
            Display progress while retrieving a query that needs more than one
            request. Default is `True`.
        get_query_payload : bool, optional
            Return the dict of HTTP request parameters without querying.
            Default is `False`.
        cache : bool, optional
            Cache the response. Defaults to `True` for anonymous queries and
            `False` for authenticated ones.

        Returns
        -------
        frames : `~astropy.table.Table`
            The matching frames, one row per frame.
        """
        if include_thumbnails and thumbnail_size not in THUMBNAIL_SIZES:
            raise ValueError(f"'thumbnail_size' must be one of "
                             f"{', '.join(THUMBNAIL_SIZES)}.")
        row_limit = self.ROW_LIMIT if row_limit is None else row_limit
        if row_limit != -1 and row_limit < 1:
            # A page of no rows tells a cursor query nothing, so there is no
            # sensible request to make for it.
            raise ValueError("'row_limit' must be 1 or more, or -1 to "
                             f"retrieve every matching frame; got {row_limit}.")

        payload = self._args_to_payload(**criteria)
        if include_thumbnails:
            payload['include_thumbnails'] = 'true'
        if get_query_payload:
            return payload

        rows = self._fetch_pages(payload, row_limit=row_limit, cache=cache,
                                 show_progress=show_progress)
        return self._parse_result(rows, thumbnail_size=thumbnail_size)

    def _args_to_payload(self, **criteria):
        """Validate and normalise user criteria into archive query params."""
        payload = {}

        for key, value in criteria.items():
            if value is None:
                continue

            if key not in FRAME_FILTERS:
                raise ValueError(
                    f"'{key}' is not a supported LCO archive filter. "
                    f"Supported filters are: {', '.join(FRAME_FILTERS)}.")

            if key in ('exclude_configuration_type', 'include_configuration_type'):
                # Accepts either a single value, or a list of values.
                payload[key] = value if isinstance(value, str) else list(value)
                continue

            if key == 'empty_target_name':
                # The archive searches for targets with no defined name for any
                # truthy value, so only include the parameter if it is truthy
                if value:
                    payload[key] = 'true'
                continue

            if key in ('start', 'end') and not isinstance(value, str):
                # Time accepts a Time, a datetime, or anything else it can
                # parse; strings are passed through as the user wrote them.
                value = Time(value).isot
            elif key in ('public', 'exclude_calibrations'):
                value = 'true' if value else 'false'
            elif key == 'exposure_time' and isinstance(value, u.Quantity):
                value = value.to(u.s).value

            payload[key] = value

        return payload

    def _progress(self, row_limit, show_progress):
        """
        A progress display for a query that needs more than one request.

        A single-page query is over before any display would be useful, so
        those get nothing. ``row_limit`` is used to determine if we should
        show a progress bar, counting spinner, or nothing.
        """
        if not show_progress or 0 < row_limit <= self._page_size:
            return contextlib.nullcontext()
        return _ProgressBarOrCountingSpinner(
            row_limit if row_limit > 0 else None,
            'Retrieving frames from the LCO archive')

    def _fetch_pages(self, payload, *, row_limit, cache=None,
                     show_progress=True):
        """
        Retrieve as many pages as ``row_limit`` requires.

        Cursor pagination is used since it is more efficient on the server
        """
        if cache is None:
            # Never cache an authenticated request: the token would be
            # pickled along with the response, and the cache key does not
            # include session headers, so anonymous and authenticated results
            # for the same query would collide.
            cache = not self.authenticated()

        params = dict(payload, pagination_style='cursor')

        rows = []
        remaining = row_limit
        url = self._frames_url
        warned = False
        truncated = False

        with self._progress(row_limit, show_progress) as progress:
            while url is not None:
                # Ask for exactly what is still wanted, so the last page does
                # not fetch rows that would only be thrown away.
                page_size = (self._page_size if row_limit < 0
                             else min(remaining, self._page_size))
                if params is None:
                    # The 'next' link includes the previous limit, so we need
                    # to substitute the value in the url if it has changed.
                    url = _replace_limit(url, page_size)
                else:
                    params['limit'] = page_size

                response = self._request('GET', url, params=params,
                                         timeout=self.TIMEOUT, cache=cache)
                response.raise_for_status()

                # Keep the results from the response but drop the response to
                # save memory on large queries.
                page = response.json()
                del response
                rows.extend(page['results'])
                if progress is not None:
                    # Never report more than was asked for: the bar's total is
                    # the row limit, so going past it would read as over 100%.
                    progress.update(len(rows) if row_limit < 0
                                    else min(len(rows), row_limit))

                remaining -= len(page['results'])
                if row_limit > 0 and remaining <= 0:
                    # A 'next' link on the last page we keep means the archive
                    # holds more frames than the caller asked for.
                    truncated = bool(page.get('next'))
                    break

                # An unbounded query can page until it exhausts memory, so if
                # we exceed the LARGE_RESULT_WARNING number of results, report
                # the potential issue so users can stop it early if they want.
                if (row_limit < 0 and not warned
                        and len(rows) >= LARGE_RESULT_WARNING):
                    warnings.warn(
                        f"This query has returned {len(rows):,} frames so far "
                        "and is still paging. Narrow it with 'start' and "
                        "'end', or set 'row_limit', to stop it sooner.",
                        LargeQueryWarning)
                    warned = True

                # The 'next' link carries the cursor, so nothing else is needed.
                url, params = page.get('next'), None

        # At the end of the query, report if we truncated the results set.
        if truncated:
            warnings.warn(
                f"Results truncated to {row_limit} frames. Pass row_limit=-1 "
                "to retrieve every matching frame.", MaxResultsWarning)

        return rows

    def _parse_result(self, rows, *, thumbnail_size):
        """Turn the frame records from a query into a `~astropy.table.Table`."""
        if not rows:
            warnings.warn("Query returned no results.", NoResultsWarning)
            return Table(names=RESULT_COLUMNS,
                         dtype=[object] * len(RESULT_COLUMNS))

        table = Table([[row.get(name) for row in rows]
                       for name in RESULT_COLUMNS],
                      names=RESULT_COLUMNS)
        table['exposure_time'].unit = u.s

        # The footprint center is the mean of its vertices taken as unit
        # vectors, so footprints that straddle RA 0 or a pole come out right.
        # Frames without a polygon footprint are masked.
        ra = np.ma.masked_all(len(rows))
        dec = np.ma.masked_all(len(rows))
        for i, row in enumerate(rows):
            area = row.get('area')
            if not area or area.get('type') != 'Polygon':
                continue
            # GeoJSON repeats the first vertex to close the ring, which would
            # otherwise be counted twice.
            lon, lat = np.radians(area['coordinates'][0][:-1]).T
            x = np.mean(np.cos(lat) * np.cos(lon))
            y = np.mean(np.cos(lat) * np.sin(lon))
            z = np.mean(np.sin(lat))
            # The archive's longitudes run from -180 to 180.
            ra[i] = np.degrees(np.arctan2(y, x)) % 360
            dec[i] = np.degrees(np.arctan2(z, np.hypot(x, y)))
        table['ra'] = MaskedColumn(ra, unit=u.deg)
        table['dec'] = MaskedColumn(dec, unit=u.deg)

        # Thumbnails only come back when the query asked for them. The archive
        # returns every size, so keep the one the query asked for and flatten
        # it into columns download_thumbnails can use.
        if any('thumbnails' in row for row in rows):
            thumbnails = [next((t for t in row.get('thumbnails') or []
                                if t.get('size') == thumbnail_size), None)
                          for row in rows]
            table['thumbnail_url'] = [t['url'] if t else '' for t in thumbnails]
            table['thumbnail_filename'] = [
                f"{t['basename']}{t['extension']}" if t else ''
                for t in thumbnails]

        return table

    def get_metadata(self, frame_id, *, cache=None):
        """
        Retrieve the metadata for a single frame, including a fresh download URL.

        Parameters
        ----------
        frame_id : int
            The frame's ``id``.
        cache : bool, optional
            Cache the response. Defaults to `True` for anonymous queries and
            `False` for authenticated ones.

        Returns
        -------
        frame : dict
            The frame record as returned by the archive, including the nested
            ``version_set``, ``area`` and ``related_frames`` fields that the
            query methods drop.
        """
        if cache is None:
            cache = not self.authenticated()
        response = self._request('GET', f'{self._frames_url}{frame_id}/',
                                 timeout=self.TIMEOUT, cache=cache)
        response.raise_for_status()
        return response.json()

    def download_files(self, frames, *, download_dir='.', overwrite=False):
        """
        Download the data files for a set of frames.

        Parameters
        ----------
        frames : `~astropy.table.Table`, int, or list of int
            A table returned by one of the query methods, or one or more frame
            ids. Frame ids are looked up one by one.
        download_dir : str, optional
            Directory to write into. Defaults to the working directory.
        overwrite : bool, optional
            Re-download files that already exist locally. Default is `False`.

        Returns
        -------
        paths : list of str
            The local paths of the downloaded files.
        """
        if isinstance(frames, Table):
            records = [{'filename': row['filename'], 'url': row['url']}
                       for row in frames]
        else:
            if np.isscalar(frames):
                frames = [frames]
            records = [self.get_metadata(frame_id) for frame_id in frames]

        return self._download_records(records, download_dir=download_dir,
                                      overwrite=overwrite)

    def download_thumbnails(self, frames, *, download_dir='.',
                            overwrite=False):
        """
        Download the JPEG thumbnails for a set of frames.

        The table must have been produced by a query with
        ``include_thumbnails=True``, which is what puts the ``thumbnail_url``
        column in it. Frames with no thumbnail of the requested size are
        skipped.

        Parameters
        ----------
        frames : `~astropy.table.Table`
            A table returned by one of the query methods.
        download_dir : str, optional
            Directory to write into. Defaults to the working directory.
        overwrite : bool, optional
            Re-download thumbnails that already exist locally. Default is
            `False`.

        Returns
        -------
        paths : list of str
            The local paths of the downloaded thumbnails.
        """
        if 'thumbnail_url' not in frames.colnames:
            raise ValueError(
                "This table has no 'thumbnail_url' column. Re-run the query "
                "with include_thumbnails=True to request thumbnail links.")

        records = [{'filename': row['thumbnail_filename'],
                    'url': row['thumbnail_url']}
                   for row in frames if row['thumbnail_url']]
        return self._download_records(records, download_dir=download_dir,
                                      overwrite=overwrite)

    def _download_records(self, records, *, download_dir, overwrite):
        """Download ``{'filename', 'url'}`` records, skipping existing files."""
        paths = []
        for record in records:
            local_filepath = os.path.join(download_dir, record['filename'])
            if os.path.exists(local_filepath) and not overwrite:
                log.info(f"Found existing {local_filepath}, skipping download. "
                         f"Pass overwrite=True to download it again.")
            else:
                try:
                    # The URL carries its own credentials in the query string,
                    # and S3 rejects a request that also has an Authorization
                    # header with "Only one auth mechanism allowed". A None
                    # value drops the header for this request alone, leaving
                    # the logged-in session untouched.
                    self._download_file(record['url'], local_filepath,
                                        timeout=self.TIMEOUT, cache=False,
                                        continuation=False,
                                        headers={'Authorization': None})
                # The URLs are presigned and valid for 48 hours,
                # and return a 403 after their validity expires
                except requests.exceptions.HTTPError as exc:
                    if getattr(exc.response, 'status_code', None) != 403:
                        raise
                    raise RemoteServiceError(
                        f"The download link for {record['filename']} has "
                        "expired. LCO signs them for 48 hours; run the query "
                        "again to get fresh links.") from exc
            paths.append(local_filepath)
        return paths

    def list_criteria(self):
        """
        List the frame filters the query methods accept.

        Returns
        -------
        criteria : list of str
        """
        return list(FRAME_FILTERS)

    def _aggregate(self, field, *, cache=True):
        response = self._request('GET', f'{self._frames_url}aggregate/',
                                 timeout=self.TIMEOUT, cache=cache)
        response.raise_for_status()
        return sorted(response.json()[field])

    def list_sites(self):
        """List the site codes present in the archive."""
        return self._aggregate('sites')

    def list_telescopes(self):
        """List the telescope codes present in the archive."""
        return self._aggregate('telescopes')

    def list_instruments(self):
        """List the instrument codes present in the archive."""
        return self._aggregate('instruments')

    def list_filters(self):
        """List the ``primary_optical_element`` values present in the archive."""
        return self._aggregate('filters')

    def list_configuration_types(self):
        """List the ``configuration_type`` values present in the archive."""
        return self._aggregate('obstypes')

    def list_proposals(self):
        """List the proposal ids present in the archive."""
        return self._aggregate('proposals')


class _ProgressBarOrCountingSpinner(ProgressBarOrSpinner):
    """
    A `~astropy.utils.console.ProgressBarOrSpinner` that keeps a running count
    in its spinner form.

    This is used on an unbounded query (row_count = -1) so that the current
    number of rows retrieved is shown instead of just a spinner.
    """

    def __init__(self, total, msg, **kwargs):
        self._msg, self._kwargs = msg, kwargs
        super().__init__(total, msg, **kwargs)

    def update(self, value):
        if self._is_spinner:
            # Must instantiate a new spinner to give it an updated message.
            # Each subsequent message overwrites the previous one.
            self._obj = Spinner(f'{self._msg} ({value:,} so far)',
                                **self._kwargs)
        self._obj.update(value)


def _replace_limit(url, limit):
    """Return ``url`` with its ``limit`` query parameter replaced."""
    parts = urlparse(url)
    query = parse_qs(parts.query)
    query['limit'] = [str(limit)]
    return urlunparse(parts._replace(query=urlencode(query, doseq=True)))


def _ring_to_wkt(ra, dec):
    """Build a closed WKT polygon from arrays of RA and Dec in degrees."""
    vertices = ', '.join(f'{a} {d}' for a, d in zip(ra, dec))
    return f'POLYGON(({vertices}, {ra[0]} {dec[0]}))'


def _circle_to_wkt(coordinates, radius, *, nvertices=32):
    """Approximate a cone on the sky as a polygon."""
    position_angles = np.linspace(0, 360, nvertices, endpoint=False) * u.deg
    ring = coordinates.directional_offset_by(position_angles, radius)
    return _ring_to_wkt(ring.ra.deg, ring.dec.deg)


def _box_to_wkt(coordinates, width, height):
    """Build a polygon for a box centered on ``coordinates``."""
    half_height = height.to(u.deg) / 2
    half_width = width.to(u.deg) / 2 / np.cos(coordinates.dec.radian)

    ra = coordinates.ra.deg + np.array([-1, 1, 1, -1]) * half_width.value
    dec = coordinates.dec.deg + np.array([-1, -1, 1, 1]) * half_height.value
    return _ring_to_wkt(ra, np.clip(dec, -90, 90))


LcoArchive = LcoArchiveClass()
