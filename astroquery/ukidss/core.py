# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import print_function

import warnings
import re
import time
from math import cos, radians
import requests
from bs4 import BeautifulSoup

from astropy.extern.six import BytesIO
import astropy.units as u
import astropy.coordinates as coord
import astropy.io.votable as votable

from ..query import QueryWithLogin
from ..exceptions import InvalidQueryError, TimeoutError, NoResultsWarning
from ..utils import commons
from . import conf
from ..exceptions import TableParseError

__all__ = ['Ukidss', 'UkidssClass', 'clean_catalog']


def validate_frame(func):
    def wrapper(*args, **kwargs):
        frame_type = kwargs.get('frame_type')
        if frame_type not in UkidssClass.frame_types:
            raise ValueError("Invalid frame type. Valid frame types are: {!s}"
                             .format(UkidssClass.frame_types))
        return func(*args, **kwargs)
    return wrapper


def validate_filter(func):
    def wrapper(*args, **kwargs):
        waveband = kwargs.get('waveband')
        if waveband not in UkidssClass.filters:
            raise ValueError("Invalid waveband. Valid wavebands are: {!s}"
                             .format(UkidssClass.filters.keys()))
        return func(*args, **kwargs)
    return wrapper


class UkidssClass(QueryWithLogin):

    """
    The UKIDSSQuery class.  Must instantiate this class in order to make any
    queries.  Allows registered users to login, but defaults to using the
    public UKIDSS data sets.
    """
    BASE_URL = conf.server
    LOGIN_URL = BASE_URL + "DBLogin"
    IMAGE_URL = BASE_URL + "GetImage"
    ARCHIVE_URL = BASE_URL + "ImageList"
    REGION_URL = BASE_URL + "WSASQL"
    TIMEOUT = conf.timeout

    filters = {'all': 'all', 'J': 3, 'H': 4, 'K': 5, 'Y': 2,
               'Z': 1, 'H2': 6, 'Br': 7}

    frame_types = {'stack': 'stack', 'normal': 'normal', 'interleave': 'leav',
                   'deep_stack': 'deep%stack', 'confidence': 'conf',
                   'difference': 'diff', 'leavstack': 'leavstack',
                   'all': 'all'}

    ukidss_programmes_short = {'LAS': 101,
                               'GPS': 102,
                               'GCS': 103,
                               'DXS': 104,
                               'UDS': 105, }

    ukidss_programmes_long = {'Large Area Survey': 101,
                              'Galactic Plane Survey': 102,
                              'Galactic Clusters Survey': 103,
                              'Deep Extragalactic Survey': 104,
                              'Ultra Deep Survey': 105}

    all_databases = ("UKIDSSDR9PLUS", "UKIDSSDR8PLUS", "UKIDSSDR7PLUS",
                     "UKIDSSDR6PLUS", "UKIDSSDR5PLUS", "UKIDSSDR4PLUS",
                     "UKIDSSDR3PLUS", "UKIDSSDR2PLUS", "UKIDSSDR1PLUS",
                     "UKIDSSDR1", "UKIDSSEDRPLUS", "UKIDSSEDR", "UKIDSSSV",
                     "WFCAMCAL08B", "U09B8v20120403", "U09B8v20100414")

    def __init__(self, username=None, password=None, community=None,
                 database='UKIDSSDR7PLUS', programme_id='all'):
        self.database = database
        self.programme_id = programme_id  # 102 = GPS
        self.session = None
        if username is None or password is None or community is None:
            pass
        else:
            self.login(username, password, community)

    def _login(self, username, password, community):
        """
        Login to non-public data as a known user.

        Parameters
        ----------
        username : str
        password : str
        community : str
        """

        # Construct cookie holder, URL opener, and retrieve login page
        self.session = requests.session()

        credentials = {'user': username, 'passwd': password,
                       'community': ' ', 'community2': community}
        response = self.session.post(self.LOGIN_URL, data=credentials)
        if not response.ok:
            self.session = None
            response.raise_for_status()
        if 'FAILED to log in' in response.text:
            self.session = None
            raise Exception("Unable to log in with your given credentials.\n"
                            "Please try again.\n Note that you can continue "
                            "to access public data without logging in.\n")

    def logged_in(self):
        """
        Determine whether currently logged in.
        """
        if self.session is None:
            return False
        for cookie in self.session.cookies:
            if cookie.is_expired():
                return False
        return True

    def _args_to_payload(self, *args, **kwargs):
        request_payload = {}

        request_payload['database'] = kwargs.get('database', self.database)

        programme_id = kwargs.get('programme_id', self.programme_id)

        request_payload['programmeID'] = verify_programme_id(
            programme_id, query_type=kwargs['query_type'])
        sys = self._parse_system(kwargs.get('system'))
        request_payload['sys'] = sys
        if sys == 'J':
            C = commons.parse_coordinates(args[0]).transform_to(coord.ICRS)
            request_payload['ra'] = C.ra.degree
            request_payload['dec'] = C.dec.degree
        elif sys == 'G':
            C = commons.parse_coordinates(args[0]).transform_to(coord.Galactic)
            request_payload['ra'] = C.l.degree
            request_payload['dec'] = C.b.degree
        return request_payload

    def _parse_system(self, system):
        if system is None:
            return 'J'
        elif system.lower() in ('g', 'gal', 'galactic'):
            return 'G'
        elif system.lower() in ('j', 'j2000', 'celestical', 'radec'):
            return 'J'

    def get_images(self, coordinates, waveband='all', frame_type='stack',
                   image_width=1 * u.arcmin, image_height=None, radius=None,
                   database='UKIDSSDR7PLUS', programme_id='all',
                   verbose=True, get_query_payload=False,
                   show_progress=True):
        """
        Get an image around a target/ coordinates from UKIDSS catalog.

        Parameters
        ----------
        coordinates : str or `astropy.coordinates` object
            The target around which to search. It may be specified as a
            string in which case it is resolved using online services or as
            the appropriate `astropy.coordinates` object. ICRS coordinates
            may also be entered as strings as specified in the
            `astropy.coordinates` module.
        waveband  : str
            The color filter to download. Must be one of  ``'all'``, ``'J'``,
            ``'H'``, ``'K'``, ``'H2'``, ``'Z'``, ``'Y'``, ``'Br'``].
        frame_type : str
            The type of image. Must be one of ``'stack'``, ``'normal'``,
            ``'interleave'``, ``'deep_stack'``, ``'confidence'``,
            ``'difference'``, ``'leavstack'``, ``'all'``]
        image_width : str or `~astropy.units.Quantity` object, optional
            The image size (along X). Cannot exceed 15 arcmin. If missing,
            defaults to 1 arcmin.
        image_height : str or `~astropy.units.Quantity` object, optional
             The image size (along Y). Cannot exceed 90 arcmin. If missing,
             same as image_width.
        radius : str or `~astropy.units.Quantity` object, optional
            The string must be parsable by `~astropy.coordinates.Angle`. The
            appropriate `~astropy.units.Quantity` object from `astropy.units`
            may also be used. When missing only image around the given position
            rather than multi-frames are retrieved.
        programme_id : str
            The survey or programme in which to search for.
        database : str
            The UKIDSS database to use.
        verbose : bool
            Defaults to `True`. When `True` prints additional messages.
        get_query_payload : bool, optional
            If `True` then returns the dictionary sent as the HTTP request.
            Defaults to `False`.

        Returns
        -------
        list : A list of `~astropy.io.fits.HDUList` objects.
        """
        readable_objs = self.get_images_async(
            coordinates, waveband=waveband, frame_type=frame_type,
            image_width=image_width, image_height=image_height,
            database=database, programme_id=programme_id, radius=radius,
            verbose=verbose, get_query_payload=get_query_payload,
            show_progress=show_progress)

        if get_query_payload:
            return readable_objs
        return [obj.get_fits() for obj in readable_objs]

    def get_images_async(self, coordinates, waveband='all', frame_type='stack',
                         image_width=1 * u.arcmin, image_height=None,
                         radius=None, database='UKIDSSDR7PLUS',
                         programme_id='all', verbose=True,
                         get_query_payload=False,
                         show_progress=True):
        """
        Serves the same purpose as `get_images` but
        returns a list of file handlers to remote files.

        Parameters
        ----------
        coordinates : str or `astropy.coordinates` object
            The target around which to search. It may be specified as a
            string in which case it is resolved using online services or as
            the appropriate `astropy.coordinates` object. ICRS coordinates
            may also be entered as strings as specified in the
            `astropy.coordinates` module.
        waveband  : str
            The color filter to download. Must be one of  ``'all'``, ``'J'``,
            ``'H'``, ``'K'``, ``'H2'``, ``'Z'``, ``'Y'``, ``'Br'``].
        frame_type : str
            The type of image. Must be one of ``'stack'``, ``'normal'``,
            ``'interleave'``, ``'deep_stack'``, ``'confidence'``,
            ``'difference'``, ``'leavstack'``, ``'all'``]
        image_width : str or `~astropy.units.Quantity` object, optional
            The image size (along X). Cannot exceed 15 arcmin. If missing,
            defaults to 1 arcmin.
        image_height : str or `~astropy.units.Quantity` object, optional
             The image size (along Y). Cannot exceed 90 arcmin. If missing,
             same as image_width.
        radius : str or `~astropy.units.Quantity` object, optional
            The string must be parsable by `~astropy.coordinates.Angle`. The
            appropriate `~astropy.units.Quantity` object from `astropy.units`
            may also be used. When missing only image around the given position
            rather than multi-frames are retrieved.
        programme_id : str
            The survey or programme in which to search for. See
            `list_catalogs`.
        database : str
            The UKIDSS database to use.
        verbose : bool
            Defaults to `True`. When `True` prints additional messages.
        get_query_payload : bool, optional
            If `True` then returns the dictionary sent as the HTTP request.
            Defaults to `False`.

        Returns
        -------
        list : list
            A list of context-managers that yield readable file-like objects.
        """

        image_urls = self.get_image_list(coordinates, waveband=waveband,
                                         frame_type=frame_type,
                                         image_width=image_width,
                                         image_height=image_height,
                                         database=database, radius=radius,
                                         programme_id=programme_id,
                                         get_query_payload=get_query_payload)
        if get_query_payload:
            return image_urls

        if verbose:
            print("Found {num} targets".format(num=len(image_urls)))

        return [commons.FileContainer(U, encoding='binary',
                                      remote_timeout=self.TIMEOUT,
                                      show_progress=show_progress)
                for U in image_urls]

    @validate_frame
    @validate_filter
    def get_image_list(self, coordinates, waveband='all', frame_type='stack',
                       image_width=1 * u.arcmin, image_height=None,
                       radius=None, database='UKIDSSDR7PLUS',
                       programme_id='all', get_query_payload=False):
        """
        Function that returns a list of urls from which to download the FITS
        images.

        Parameters
        ----------
        coordinates : str or `astropy.coordinates` object
            The target around which to search. It may be specified as a
            string in which case it is resolved using online services or as
            the appropriate `astropy.coordinates` object. ICRS coordinates
            may also be entered as strings as specified in the
            `astropy.coordinates` module.
        waveband  : str
            The color filter to download. Must be one of  ``'all'``, ``'J'``,
            ``'H'``, ``'K'``, ``'H2'``, ``'Z'``, ``'Y'``, ``'Br'``].
        frame_type : str
            The type of image. Must be one of ``'stack'``, ``'normal'``,
            ``'interleave'``, ``'deep_stack'``, ``'confidence'``,
            ``'difference'``, ``'leavstack'``, ``'all'``]
        image_width : str or `~astropy.units.Quantity` object, optional
            The image size (along X). Cannot exceed 15 arcmin. If missing,
            defaults to 1 arcmin.
        image_height : str or `~astropy.units.Quantity` object, optional
             The image size (along Y). Cannot exceed 90 arcmin. If missing,
             same as image_width.
        radius : str or `~astropy.units.Quantity` object, optional
            The string must be parsable by `~astropy.coordinates.Angle`. The
            appropriate `~astropy.units.Quantity` object from
            `astropy.units` may also be used. When missing only image around
            the given position rather than multi-frames are retrieved.
        programme_id : str
            The survey or programme in which to search for. See
            `list_catalogs`.
        database : str
            The UKIDSS database to use.
        verbose : bool
            Defaults to `True`. When `True` prints additional messages.
        get_query_payload : bool, optional
            If `True` then returns the dictionary sent as the HTTP request.
            Defaults to `False`.

        Returns
        -------
        url_list : list of image urls

        """

        request_payload = self._args_to_payload(coordinates, database=database,
                                                programme_id=programme_id,
                                                query_type='image')
        request_payload['filterID'] = self.filters[waveband]
        request_payload['obsType'] = 'object'
        request_payload['frameType'] = self.frame_types[frame_type]
        request_payload['mfid'] = ''
        if radius is None:
            request_payload['xsize'] = _parse_dimension(image_width)
            if image_height is None:
                request_payload['ysize'] = _parse_dimension(image_width)
            else:
                request_payload['ysize'] = _parse_dimension(image_height)
            query_url = self.IMAGE_URL
        else:
            query_url = self.ARCHIVE_URL
            ra = request_payload.pop('ra')
            dec = request_payload.pop('dec')
            radius = commons.parse_radius(radius).degree
            del request_payload['sys']
            request_payload['userSelect'] = 'default'
            request_payload['minRA'] = str(
                round(ra - radius / cos(radians(dec)), 2))
            request_payload['maxRA'] = str(
                round(ra + radius / cos(radians(dec)), 2))
            request_payload['formatRA'] = 'degrees'
            request_payload['minDec'] = str(dec - radius)
            request_payload['maxDec'] = str(dec + radius)
            request_payload['formatDec'] = 'degrees'
            request_payload['startDay'] = 0
            request_payload['startMonth'] = 0
            request_payload['startYear'] = 0
            request_payload['endDay'] = 0
            request_payload['endMonth'] = 0
            request_payload['endYear'] = 0
            request_payload['dep'] = 0
            request_payload['lmfid'] = ''
            request_payload['fsid'] = ''
            request_payload['rows'] = 1000

        if get_query_payload:
            return request_payload

        response = self._ukidss_send_request(query_url, request_payload)
        response = self._check_page(response.url, "row")

        image_urls = self.extract_urls(response.text)
        # different links for radius queries and simple ones
        if radius is not None:
            image_urls = [link for link in image_urls if
                          ('fits_download' in link and '_cat.fits'
                           not in link and '_two.fit' not in link)]
        else:
            image_urls = [link.replace("getImage", "getFImage")
                          for link in image_urls]

        return image_urls

    def extract_urls(self, html_in):
        """
        Helper function that uses regexps to extract the image urls from the
        given HTML.

        Parameters
        ----------
        html_in : str
            source from which the urls are to be extracted.

        Returns
        -------
        links : list
            The list of URLS extracted from the input.
        """
        # Parse html input for links
        ahref = re.compile('href="([a-zA-Z0-9_\.&\?=%/:-]+)"')
        links = ahref.findall(html_in)
        return links

    def query_region(self, coordinates, radius=1 * u.arcmin,
                     programme_id='GPS', database='UKIDSSDR7PLUS',
                     verbose=False, get_query_payload=False, system='J2000'):
        """
        Used to query a region around a known identifier or given
        coordinates from the catalog.

        Parameters
        ----------
        coordinates : str or `astropy.coordinates` object
            The target around which to search. It may be specified as a string
            in which case it is resolved using online services or as the
            appropriate `astropy.coordinates` object. ICRS coordinates may also
            be entered as strings as specified in the `astropy.coordinates`
            module.
        radius : str or `~astropy.units.Quantity` object, optional
            The string must be parsable by `~astropy.coordinates.Angle`. The
            appropriate `~astropy.units.Quantity` object from
            `astropy.units` may also be used. When missing defaults to 1
            arcmin. Cannot exceed 90 arcmin.
        programme_id : str
            The survey or programme in which to search for. See
            `list_catalogs`.
        database : str
            The UKIDSS database to use.
        verbose : bool, optional.
            When set to `True` displays warnings if the returned VOTable does
            not conform to the standard. Defaults to `False`.
        get_query_payload : bool, optional
            If `True` then returns the dictionary sent as the HTTP request.
            Defaults to `False`.
        system : 'J2000' or 'Galactic'
            The system in which to perform the query. Can affect the output
            data columns.

        Returns
        -------
        result : `~astropy.table.Table`
            Query result table.
        """

        response = self.query_region_async(coordinates, radius=radius,
                                           programme_id=programme_id,
                                           database=database,
                                           get_query_payload=get_query_payload,
                                           system=system)
        if get_query_payload:
            return response

        result = self._parse_result(response, verbose=verbose)
        return result

    def query_region_async(self, coordinates, radius=1 * u.arcmin,
                           programme_id='GPS',
                           database='UKIDSSDR7PLUS', get_query_payload=False,
                           system='J2000'):
        """
        Serves the same purpose as `query_region`. But
        returns the raw HTTP response rather than the parsed result.

        Parameters
        ----------
        coordinates : str or `astropy.coordinates` object
            The target around which to search. It may be specified as a
            string in which case it is resolved using online services or as
            the appropriate `astropy.coordinates` object. ICRS coordinates
            may also be entered as strings as specified in the
            `astropy.coordinates` module.
        radius : str or `~astropy.units.Quantity` object, optional
            The string must be parsable by `~astropy.coordinates.Angle`. The
            appropriate `~astropy.units.Quantity` object from
            `astropy.units` may also be used. When missing defaults to 1
            arcmin. Cannot exceed 90 arcmin.
        programme_id : str
            The survey or programme in which to search for. See
            `list_catalogs`.
        database : str
            The UKIDSS database to use.
        get_query_payload : bool, optional
            If `True` then returns the dictionary sent as the HTTP request.
            Defaults to `False`.

        Returns
        -------
        response : `requests.Response`
            The HTTP response returned from the service.
        """

        request_payload = self._args_to_payload(coordinates,
                                                programme_id=programme_id,
                                                database=database,
                                                system=system,
                                                query_type='catalog')
        request_payload['radius'] = _parse_dimension(radius)
        request_payload['from'] = 'source'
        request_payload['formaction'] = 'region'
        request_payload['xSize'] = ''
        request_payload['ySize'] = ''
        request_payload['boxAlignment'] = 'RADec'
        request_payload['emailAddress'] = ''
        request_payload['format'] = 'VOT'
        request_payload['compress'] = 'NONE'
        request_payload['rows'] = 1
        request_payload['select'] = 'default'
        request_payload['where'] = ''

        if get_query_payload:
            return request_payload

        response = self._ukidss_send_request(self.REGION_URL, request_payload)
        response = self._check_page(response.url, "query finished")

        return response

    def _parse_result(self, response, verbose=False):
        """
        Parses the raw HTTP response and returns it as a
        `~astropy.table.Table`.

        Parameters
        ----------
        response : `requests.Response`
            The HTTP response object
        verbose : bool, optional
            Defaults to `False`. If `True` it displays warnings whenever the
            VOtable returned from the service doesn't conform to the standard.

        Returns
        -------
        table : `~astropy.table.Table`
        """
        table_links = self.extract_urls(response.text)
        # keep only one link that is not a webstart
        if len(table_links) == 0:
            raise Exception("No VOTable found on returned webpage!")
        table_link = [link for link in table_links if "8080" not in link][0]
        with commons.get_readable_fileobj(table_link) as f:
            content = f.read()

        if not verbose:
            commons.suppress_vo_warnings()

        try:
            io_obj = BytesIO(content.encode('utf-8'))
            parsed_table = votable.parse(io_obj, pedantic=False)
            first_table = parsed_table.get_first_table()
            table = first_table.to_table()
            if len(table) == 0:
                warnings.warn("Query returned no results, so the table will "
                              "be empty", NoResultsWarning)
            return table
        except Exception as ex:
            self.response = content
            self.table_parse_error = ex
            raise
            raise TableParseError("Failed to parse UKIDSS votable! The raw "
                                  "response can be found in self.response, "
                                  "and the error in self.table_parse_error.  "
                                  "Exception: " + str(self.table_parse_error))

    def list_catalogs(self, style='short'):
        """
        Returns a list of available catalogs in UKIDSS.
        These can be used as ``programme_id`` in queries.

        Parameters
        ----------
        style : str, optional
            Must be one of ``'short'``, ``'long'``. Defaults to ``'short'``.
            Determines whether to print long names or abbreviations for
            catalogs.

        Returns
        -------
        list : list containing catalog name strings in long or short style.
        """
        if style == 'short':
            return list(self.ukidss_programmes_short.keys())
        elif style == 'long':
            return list(self.ukidss_programmes_long.keys())
        else:
            warnings.warn("Style must be one of 'long', 'short'.\n"
                          "Returning catalog list in short format.\n")
            return list(self.ukidss_programmes_short.keys())

    def _get_databases(self):
        if self.logged_in():
            response = self.session.get(
                'http://surveys.roe.ac.uk:8080/wsa/getImage_form.jsp')
        else:
            response = requests.get(
                'http://surveys.roe.ac.uk:8080/wsa/getImage_form.jsp')
        root = BeautifulSoup(response.content)
        databases = [x.attrs['value'] for x in
                     root.find('select').findAll('option')]
        return databases

    def list_databases(self):
        """
        List the databases available from the UKIDSS WFCAM archive.
        """
        self.databases = set(self.all_databases + self._get_databases())
        return self.databases

    def _ukidss_send_request(self, url, request_payload):
        """
        Helper function that sends the query request via a session or simple
        HTTP GET request.

        Parameters
        ----------
        url : str
            The url to send the request to.
        request_payload : dict
            The dict of parameters for the GET request

        Returns
        -------
        response : `requests.Response` object
            The response for the HTTP GET request
        """
        if hasattr(self, 'session') and self.logged_in():
            response = self.session.get(url, params=request_payload,
                                        timeout=self.TIMEOUT)
        else:
            response = commons.send_request(url, request_payload, self.TIMEOUT,
                                            request_type='GET')
        return response

    def _check_page(self, url, keyword, wait_time=1, max_attempts=30):
        page_loaded = False
        while not page_loaded and max_attempts > 0:
            if self.logged_in():
                response = self.session.get(url)
            else:
                response = requests.get(url)
            self.response = response
            content = response.text
            if re.search("error", content, re.IGNORECASE):
                raise InvalidQueryError(
                    "Service returned with an error!  "
                    "Check self.response for more information.")
            elif re.search(keyword, content, re.IGNORECASE):
                page_loaded = True
            max_attempts -= 1
            # wait for wait_time seconds before checking again
            time.sleep(wait_time)
        if page_loaded is False:
            raise TimeoutError("Page did not load.")
        return response

Ukidss = UkidssClass()


def clean_catalog(ukidss_catalog, clean_band='K_1', badclass=-9999,
                  maxerrbits=41, minerrbits=0, maxpperrbits=60):
    """
    Attempt to remove 'bad' entries in a catalog.

    Parameters
    ----------
    ukidss_catalog : `~astropy.io.fits.BinTableHDU`
        A FITS binary table instance from the UKIDSS survey.
    clean_band : ``'K_1'``, ``'K_2'``, ``'J'``, ``'H'``
        The band to use for bad photometry flagging.
    badclass : int
        Class to exclude.
    minerrbits : int
    maxerrbits : int
        Inside this range is the accepted number of error bits.
    maxpperrbits : int
        Exclude this type of error bit.

    Examples
    --------
    """

    band = clean_band
    mask = ((ukidss_catalog[band + 'ERRBITS'] <= maxerrbits) *
            (ukidss_catalog[band + 'ERRBITS'] >= minerrbits) *
            ((ukidss_catalog['PRIORSEC'] == ukidss_catalog['FRAMESETID']) +
             (ukidss_catalog['PRIORSEC'] == 0)) *
            (ukidss_catalog[band + 'PPERRBITS'] < maxpperrbits)
            )
    if band + 'CLASS' in ukidss_catalog.colnames:
        mask *= (ukidss_catalog[band + 'CLASS'] != badclass)
    elif 'mergedClass' in ukidss_catalog.colnames:
        mask *= (ukidss_catalog['mergedClass'] != badclass)

    return ukidss_catalog.data[mask]


def verify_programme_id(pid, query_type='catalog'):
    """
    Verify the programme ID is valid for the query being executed.

    Parameters
    ----------
    pid : int or str
        The programme ID, either an integer (i.e., the # that will get passed
        to the URL) or a string using the three-letter acronym for the
        programme or its long name

    Returns
    -------
    pid : int
        Returns the integer version of the programme ID

    Raises
    ------
    ValueError if the pid is 'all' and the query type is a catalog.
    You can query all surveys for images, but not all catalogs.
    """
    if pid == 'all' and query_type == 'image':
        return 'all'
    elif pid == 'all' and query_type == 'catalog':
        raise ValueError(
            "Cannot query all catalogs at once. Valid catalogs are: {0}.\n"
            "Change programmeID to one of these."
            .format(",".join(UkidssClass.ukidss_programmes_short.keys())))
    elif pid in UkidssClass.ukidss_programmes_long:
        return UkidssClass.ukidss_programmes_long[pid]
    elif pid in UkidssClass.ukidss_programmes_short:
        return UkidssClass.ukidss_programmes_short[pid]
    elif query_type != 'image':
        raise ValueError("programme_id {0} not recognized".format(pid))


def _parse_dimension(dim):
    """
    Parses the radius and returns it in the format expected by UKIDSS.

    Parameters
    ----------
    dim : str, `~astropy.units.Quantity`

    Returns
    -------
    dim_in_min : float
        The value of the radius in arcminutes.
    """
    if (isinstance(dim, u.Quantity) and
            dim.unit in u.deg.find_equivalent_units()):
        dim_in_min = dim.to(u.arcmin).value
    # otherwise must be an Angle or be specified in hours...
    else:
        try:
            new_dim = commons.parse_radius(dim).degree
            dim_in_min = u.Quantity(
                value=new_dim, unit=u.deg).to(u.arcmin).value
        except (u.UnitsError, coord.errors.UnitsError, AttributeError):
            raise u.UnitsError("Dimension not in proper units")
    return dim_in_min
