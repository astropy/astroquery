# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import print_function

import json
import time
import warnings
import tempfile

import astropy.units as u
import astropy.coordinates as coord
from astropy.table import Table
from astropy.io import fits
from astropy.extern.six import BytesIO
from astropy.utils.console import Spinner

from ..query import QueryWithLogin
from ..exceptions import InvalidQueryError, TimeoutError, NoResultsWarning, LoginError
from ..utils import commons
from ..utils import prepend_docstr_nosections
from ..utils import async_to_sync
from . import conf

# export all the public classes and methods
__all__ = ['Hsc', 'HscClass']


@async_to_sync
class HscClass(QueryWithLogin):
    """
    The HscQuery class. A valid account for the HSC Archive is needed
    to use this service. See `HSC Online Registration
    <https://hsc-release.mtk.nao.ac.jp/datasearch/new_user/new>`_.
    """
    ARCHIVE_URL = conf.archive_server
    BASE_URL = conf.api_server
    DOWNLOAD_URL = conf.download_server
    IMAGE_URL = conf.image_server
    CUTOUT_URL = conf.cutout_server
    CANCEL_URL = BASE_URL + 'cancel'
    DELETE_URL = BASE_URL + 'delete'
    PREVIEW_URL = BASE_URL + 'preview'
    STATUS_URL = BASE_URL + 'status'
    SUBMIT_URL = BASE_URL + 'submit'
    TIMEOUT = conf.timeout

    surveys = ['wide', 'deep', 'udeep']
    all_databases = ['pdr1']
    filters = ['g', 'r', 'i', 'z', 'y', 'NB0921', 'NB0816']

    def __init__(self, username=None, password=None,
                 survey='wide', release_version='pdr1'):

        super(HscClass, self).__init__()

        self.credentials = None
        if username is not None:
            self.login(username, password)

        self.survey = survey
        self.release_version = release_version
        self.cache_query_region = False

        assert self.survey in self.surveys
        assert self.release_version in self.all_databases

    def _login(self, username=None, password=None):
        """
        Login to the HSC Archive.

        Parameters
        ----------
        username : str
        password : str or `None`
        """
        self.credentials = self._get_credentials(username, password)
        self._session.auth = tuple(self.credentials.values())
        response = self._request('GET', self.ARCHIVE_URL)

        if response.status_code == 401:
            raise LoginError('Unable to log in with your given credentials.\n'
                             'Please try again.')
        else:
            response.raise_for_status()

        return True

    def query_region_async(self, coordinates, radius=1*u.arcmin,
                           columns='default', get_query_payload=False):
        """
        Queries a region around the specified coordinates.

        Parameters
        ----------
        coordinates : str or `astropy.coordinates`.
            coordinates around which to query
        radius : str or `astropy.units.Quantity`.
            the radius of the cone search. Default to 1 arcmin.
        columns : str or list, optional
            list of selected columns for query results.
            See the `HSP-SSP schema <https://hsc-release.mtk.nao.ac.jp/schema/>`_
            for details. By default is 'object_id, ra, dec'.
        get_query_payload : bool, optional
            Just return the dict of HTTP request parameters.

        Returns
        -------
        response : `requests.Response`
            The HTTP response returned from the service.
            All async methods should return the raw HTTP response.
        """
        request_payload = self._args_to_payload(coordinates, radius, columns,
                                                search_type='cone_search')
        if get_query_payload:
            return request_payload

        response = self._hsc_request(self.SUBMIT_URL, request_payload, cache=False)

        return response

    def get_images(self, coordinates, radius=None, image_width=1*u.arcmin,
                   image_height=None, filters='all', get_query_payload=False):
        """
        A query function that searches for images around coordinates. If no
        radius is passed, returns an image cut out of image_width x image_height.

        Parameters
        ----------
        coordinates : str or `astropy.coordinates`.
            coordinates around which to query
        radius : str or `~astropy.units.Quantity`, optional.
            the radius of the cone search.
        image_width : str or `~astropy.units.Quantity` object, optional.
            image size (along X). Cannot exceed 35 arcmin. If missing,
            defaults to 1 arcmin.
        image_height : str or `~astropy.units.Quantity` object, optional.
             image size (along Y). Cannot exceed 35 arcmin. If missing,
             same as image_width.
        filters : str or list, optional.
            list of filters. If 'all', returns images in all available filters.
            Defaults to 'all'. For cut outs, only the first filter is used.
        get_query_payload : bool, optional
            If true than returns the dictionary of query parameters, posted to
            remote server. Defaults to `False`.

        Returns
        -------
        A list of `astropy.fits.HDUList` objects
        """
        readable_objs = self.get_images_async(coordinates, radius, image_width,
                                              image_height, filters=filters,
                                              get_query_payload=get_query_payload)
        if get_query_payload:
            return readable_objs

        # I use self.get_fits() to allow accessing
        # the url images through the active session
        # return [obj.get_fits() for obj in readable_objs]
        return [self.get_fits(obj) for obj in readable_objs]

    @prepend_docstr_nosections(get_images.__doc__)
    def get_images_async(self, coordinates, radius=None, image_width=1*u.arcmin,
                         image_height=None, filters='all', get_query_payload=False,
                         cache=True):
        """
        Returns
        -------
        A list of context-managers that yield readable file-like objects
        """
        image_urls = self.get_image_list(coordinates, radius, image_width,
                                         image_height, filters=filters,
                                         get_query_payload=get_query_payload,
                                         cache=cache)
        if get_query_payload:
            return image_urls

        return [commons.FileContainer(U) for U in image_urls]

    @prepend_docstr_nosections(get_images.__doc__)
    def get_image_list(self, coordinates, radius=None, image_width=1*u.arcmin,
                       image_height=None, filters='all', get_query_payload=False,
                       cache=True):
        """
        Returns
        -------
        list of image urls
        """
        if radius is None:
            search_type = 'cutout_search'
            query_url = self.CUTOUT_URL
        else:
            search_type = 'image_search'
            query_url = self.IMAGE_URL + self.release_version + '/cgi-bin/dasQuery'

        request_payload = self._args_to_payload(coordinates, radius,
                                                image_width, image_height,
                                                filters=filters,
                                                search_type=search_type)
        if get_query_payload:
            return request_payload

        response = self._hsc_request(query_url, request_payload,
                                     search_type, cache=cache)

        return self.extract_image_urls(response, search_type)

    def extract_image_urls(self, response, search_type):
        """
        Helper function that builds the image urls from the given response.

        Parameters
        ----------
        response : `requests.Response`
            The HTTP response returned from the service.

        Returns
        -------
        list of image URLs
        """
        if search_type == 'cutout_search':
            url_list = _cutout_urls(response)

        elif search_type == 'image_search':
            rerun = _parse_table(self.release_version, self.survey)
            url_list = _image_urls(response, self.ARCHIVE_URL, rerun)

        return url_list

    def get_data(self, response_json, delete_remote=True):
        """
        Helper function for downloding the results of a database query.

        Parameters
        ----------
        response_json : dict
            json dictionary.
        delete_remote : bool, optional
            Defaults to `True`.

        Returns
        -------
        binary string
        """
        try:
            self._block_until_query_finishes(response_json['id'])

            raw_data = self._download_query_result(response_json['download_key'])

            if delete_remote:
                self._delete_query(response_json['id'])

        except (TimeoutError, KeyboardInterrupt):
            self._delete_query(response_json['id'])

        return raw_data

    def get_fits(self, readable_obj):
        """
        Helper function for downloading fits images using the active session.

        Parameters
        ----------
        readable_obj : `FileContainer` object
            readable file-like object.

        Returns
        -------
        `astropy.fits.HDUList` object
        """
        with tempfile.NamedTemporaryFile() as temp:
            self._download_file(readable_obj._target, temp.name)
            temp.seek(0)

            return fits.open(temp.name)

    def list_surveys(self):
        """
        Returns a list of available surveys in the HSC-SSP archive.
        These can be used as ``survey`` in queries.

        Returns
        -------
        list : list containing survey name strings.
        """
        return self.surveys

    def list_releases(self):
        """
        Returns a list of available public releases in the HSC-SSP archive.
        These can be used as ``release_version`` in queries.

        Returns
        -------
        list : list containing public release name strings.
        """
        return self.all_databases

    def _get_credentials(self, username, password):
        if username is None:
            username = input('HSC Archive user: ')

        if password is None:
            password = self._get_password('hscssp', username)
            # For some reason, I get a tuple when the password is read from keyring
            if isinstance(password, tuple):
                password = password[0]

        return {'account_name': username, 'password': password}

    def _hsc_request(self, url, request_payload,
                     search_type='cone_search', cache=False):

        if search_type == 'cone_search':
            request_payload['credential'] = self.credentials
            request_payload['clientVersion'] = 20181012.1

            response = self._request('POST', url, data=json.dumps(request_payload),
                                     timeout=self.TIMEOUT, cache=cache,
                                     headers={'Content-type': 'application/json'})

        elif search_type == 'cutout_search':
            # Use HEAD to avoid downloading the file with the request
            response = self._request('HEAD', url, params=request_payload,
                                     timeout=self.TIMEOUT, cache=cache,
                                     stream=True)

        elif search_type == 'image_search':
            response = self._request('POST', url, data=request_payload,
                                     timeout=self.TIMEOUT, cache=cache)
        else:
            raise ValueError('Unknown search type: {}'.format(search_type))

        return response

    def _args_to_payload(self, *args, **kwargs):
        # args[0] is always coordinates and args[1] the search radius
        search_type = kwargs['search_type']

        # TODO: implement box search
        if search_type == 'cone_search':
            catalog_job = self._cone_search_query(args[0], args[1], args[2])

            request_payload = {'catalog_job': catalog_job,
                               'nomail': True,
                               'skip_syntax_check': True}

        elif search_type == 'cutout_search':
            request_payload = self._cutout_search_query(args[0], args[2], args[3],
                                                        kwargs['filters'])

        elif search_type == 'image_search':
            query = self._image_search_query(args[0], args[1], kwargs['filters'])

            request_payload = {'query': json.dumps(query)}

        else:
            raise ValueError('Unknown search type: {}'.format(kwargs['search_type']))

        return request_payload

    def _parse_result(self, response, verbose=False):
        # if verbose is False then suppress any VOTable related warnings
        if not verbose:
            commons.suppress_vo_warnings()

        try:
            raw_data = self.get_data(response.json())
            data = Table.read(BytesIO(raw_data))

            # Remove _isnull columns
            columns = [col for col in data.colnames if not col.endswith('_isnull')]
            data = data[columns]

            if len(data) == 0:
                warnings.warn('Query returned no results, so the table will '
                              'be empty', NoResultsWarning)
        except ValueError:
            # catch common errors here, but never use bare excepts
            # return raw result/ handle in some way
            return response

        return data

    def _cone_search_query(self, coords, radius, columns, table='forced'):
        if columns == 'default':
            columns = 'object_id, ra, dec'
        else:
            columns = ','.join(columns)

        ra, dec = _parse_coordinates(coords)
        table = _parse_table(self.release_version, self.survey, table)
        radius = commons.radius_to_unit(radius, unit='arcsec')

        sql = 'SELECT {} FROM {} WHERE coneSearch(coord, {}, {}, {})'
        query = {'sql': sql.format(columns, table, ra, dec, radius),
                 'out_format': 'fits',
                 'include_metainfo_to_body': True,
                 'release_version': self.release_version}

        return query

    def _cutout_search_query(self, coords, width, height, filters):
        ra, dec = _parse_coordinates(coords)
        sw, sh = _parse_image_size(width, height)
        filters = self._parse_filters(filters)
        rerun = _parse_table(self.release_version, self.survey)

        # Use only the first element in filters
        query = {'ra': ra, 'dec': dec, 'sw': sw, 'sh': sh,
                 'type': 'coadd', 'filter': filters[0],
                 'image': 'on', 'rerun': rerun}

        return query

    def _image_search_query(self, coords, radius, filters):
        ra, dec = _parse_coordinates(coords)
        radius = commons.radius_to_unit(radius, unit='deg')
        filters = self._parse_filters(filters)
        rerun = _parse_table(self.release_version, self.survey)

        query = {
            "sqlCondition": {
                "type": "and",
                "operands": [
                    {"type": "coord-disk", "ra": ra, "dec": dec, "radius": radius},
                    {"type": "filters", "list": filters}]
            },
            "frames": [],
            "coadds": ["exposures.deepCoadd_calexp"],
            "reruns": [rerun]
        }

        return query

    def _parse_filters(self, filters):
        if filters == 'all':
            filters = self.filters

        try:
            self._check_filters(filters)

            filters_narrow = [f for f in filters if f.startswith('NB')]
            filters_broad = ['HSC-{}'.format(f.upper()) for f in filters
                             if not f.startswith('NB')]
            return filters_broad + filters_narrow

        except ValueError:
            raise

    def _check_filters(self, filters):
        for f in filters:
            if f not in self.filters:
                raise ValueError('Unknown filter: {}'.format(f))

    def _query_status(self, job_id):
        job = self._hsc_request(self.STATUS_URL, {'id': job_id})
        status = job.json()

        return status

    def _block_until_query_finishes(self, job_id):
        interval = 1   # sec.

        with Spinner('Waiting for query to finish...', 'lightred') as s:
            while True:
                time.sleep(interval)
                status = self._query_status(job_id)

                if status['status'] == 'error':
                    raise InvalidQueryError('query error: {}'.format(status['error']))

                if status['status'] == 'done':
                    break

                interval *= 2
                if interval > self.TIMEOUT:
                    raise TimeoutError

                next(s)

    def _download_query_result(self, download_key):
        url = self.DOWNLOAD_URL + download_key
        with commons.get_readable_fileobj(url, encoding='binary') as f:
            content = f.read()

        return content

    def _delete_query(self, job_id):
        self._hsc_request(self.DELETE_URL, {'id': job_id})


def _parse_coordinates(coords):
    C = commons.parse_coordinates(coords).transform_to(coord.ICRS)
    return C.ra.degree, C.dec.degree


def _parse_table(release_version, survey, table=None):
    if table is None:
        full_table = '{}_{}'.format(release_version, survey)
    else:
        full_table = '{}_{}.{}'.format(release_version, survey, table)

    return full_table


def _parse_image_size(width, height):
    max_value = 35 * u.arcmin

    sw = commons.radius_to_unit(width, unit='deg')
    if height is None:
        sh = commons.radius_to_unit(width, unit='deg')
    else:
        sh = commons.radius_to_unit(height, unit='deg')

    if sw*u.deg > max_value or sh*u.deg > max_value:
        error_message = 'Cut outs cannot be larger than {}!'
        raise ValueError(error_message.format(max_value))

    return 0.5*sw, 0.5*sh


def _cutout_urls(response):
    if response.status_code == 404:
        warnings.warn('Source outside of the observed area of the survey!')
        url_list = []
    else:
        url_list = [response.url]

    return url_list


def _image_urls(response, base_url, rerun):
    response_json = response.json()
    if response_json is None:
        warnings.warn('Source outside of the observed area of the survey!')
        url_list = []
    else:
        image_path = '/deepCoadd/{0}/{1}/{2}/calexp-{0}-{1}-{2}.fits.gz'
        image_url = base_url + rerun + image_path

        url_list = [image_url.format(coadd[2], coadd[0], coadd[1])
                    for coadd in response_json['coadds']]

    return url_list


# the default tool for users to interact with is an instance of the Class
Hsc = HscClass()
