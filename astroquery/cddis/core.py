# Licensed under a 3-clause BSD style license - see LICENSE.rst

import os
import re
from pathlib import Path

from astropy.table import Table
from bs4 import BeautifulSoup

from ..exceptions import LoginError, RemoteServiceError
from ..query import BaseQuery
from ..utils import async_to_sync
from . import conf

__all__ = ['CDDIS', 'CDDISClass']


@async_to_sync
class CDDISClass(BaseQuery):
    """
    Browse and download GNSS data from NASA's CDDIS archive.

    CDDIS requires an Earthdata Login account. Configure an Earthdata Login
    ``.netrc`` entry and authorize the CDDIS application before making requests.
    """

    URL = conf.server
    TIMEOUT = conf.timeout

    def _archive_url(self, path, *, directory=False):
        if not isinstance(path, str):
            raise TypeError("archive path must be a string")
        if path.startswith('/') or '\\' in path or not re.fullmatch(
                r'[A-Za-z0-9._+@/-]*', path):
            raise ValueError("archive path must be relative to the GNSS archive")

        parts = path.split('/')
        if any(part in ('.', '..') for part in parts):
            raise ValueError("archive path cannot contain '.' or '..' components")
        if any(part == '' for part in parts[:-1]):
            raise ValueError("archive path cannot contain empty components")
        if not path and not directory:
            raise ValueError("file path cannot be empty")
        if path.endswith('/') and not directory:
            raise ValueError("file path must not end with '/'")

        url = self.URL + path
        if directory and not url.endswith('/'):
            url += '/'
        return url

    @staticmethod
    def _check_response(response):
        host = response.url.split('://', 1)[-1].split('/', 1)[0].split(':', 1)[0]
        if host.lower() != 'cddis.nasa.gov':
            raise LoginError(
                "CDDIS requires an Earthdata Login account and CDDIS application "
                "authorization. See the CDDIS archive access documentation for "
                "Earthdata Login setup.")
        if response.status_code in (401, 403):
            raise LoginError(
                "CDDIS access was denied. Check your Earthdata Login credentials "
                "and CDDIS application authorization.")
        response.raise_for_status()

    def _clear_cached_query(self):
        query = getattr(self, '_last_query', None)
        if query is not None:
            query.request_file(self.cache_location).unlink(missing_ok=True)

    def query_files_async(self, directory='', *, cache=True):
        """
        Query the contents of a directory in the CDDIS GNSS archive.

        Parameters
        ----------
        directory : str, optional
            Directory path relative to the GNSS archive root, such as
            ``'data/daily/2025/001/25d'`` or ``'products'``.
        cache : bool, optional
            Whether to cache the HTTP response.

        Returns
        -------
        response : `requests.Response`
            The raw response from the CDDIS archive.
        """
        url = self._archive_url(directory, directory=True)
        response = self._request(
            'GET', url, timeout=self.TIMEOUT, cache=cache)
        try:
            self._check_response(response)
        except LoginError:
            self._clear_cached_query()
            raise
        return response

    def _parse_result(self, response, *, verbose=False):
        soup = BeautifulSoup(response.content, 'html.parser')
        anchors = soup.find_all('a', href=True)
        if not anchors:
            raise RemoteServiceError(
                "CDDIS response did not contain an archive directory listing.")

        directory = response.url.split('?', 1)[0]
        if not directory.endswith('/'):
            directory += '/'
        prefix = self.URL
        current_path = directory[len(prefix):]
        archive_prefixes = (
            prefix,
            'https://cddis.nasa.gov/archive/gnss/',
            'http://cddis.nasa.gov/archive/gnss/',
            '//cddis.nasa.gov/archive/gnss/',
            '/archive/gnss/',
        )
        rows = []
        for anchor in anchors:
            href = anchor['href'].strip().split('#', 1)[0].split('?', 1)[0]
            name = anchor.get_text(strip=True)
            if not name or name in ('Parent Directory', '../') or href.startswith('../'):
                continue

            relative_path = None
            for archive_prefix in archive_prefixes:
                if href.startswith(archive_prefix):
                    relative_path = href[len(archive_prefix):]
                    break
            if relative_path is None:
                if href.startswith(('/', 'http:', 'https:', '//')):
                    continue
                relative_path = current_path + href

            is_directory = href.endswith('/')
            relative_path = relative_path.rstrip('/') if is_directory else relative_path
            try:
                self._archive_url(relative_path, directory=is_directory)
            except (TypeError, ValueError):
                continue
            rows.append((name, relative_path, is_directory))

        name_width = max((len(row[0]) for row in rows), default=1)
        path_width = max((len(row[1]) for row in rows), default=1)
        if not rows:
            return Table(names=('name', 'path', 'is_directory'),
                         dtype=('U1', 'U1', bool))
        return Table(rows=rows, names=('name', 'path', 'is_directory'),
                     dtype=(f'U{name_width}', f'U{path_width}', bool))

    def download_file(self, path, *, savedir='', cache=True):
        """
        Download a file from the CDDIS GNSS archive.

        Parameters
        ----------
        path : str
            File path relative to the GNSS archive root.
        savedir : str, optional
            Directory in which to save the file. By default, Astroquery's
            CDDIS cache directory is used.
        cache : bool, optional
            Whether to reuse a previously downloaded file.

        Returns
        -------
        filepath : str
            Path to the downloaded file.
        """
        url = self._archive_url(path)
        local_directory = savedir or self.cache_location
        local_path = Path(local_directory) / os.path.basename(path)
        already_exists = local_path.exists()
        filepath, response = self._request(
            'GET', url, timeout=self.TIMEOUT, save=True, savedir=savedir,
            cache=cache, return_response_on_save=True)
        if not isinstance(response, str):
            try:
                self._check_response(response)
            except LoginError:
                if not already_exists:
                    Path(filepath).unlink(missing_ok=True)
                raise
        return filepath


CDDIS = CDDISClass()
