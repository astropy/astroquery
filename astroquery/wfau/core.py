# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import print_function

import warnings
import re
import time
from math import cos, radians
import requests
from bs4 import BeautifulSoup
from io import StringIO

from six import BytesIO
import astropy.units as u
import astropy.coordinates as coord
import astropy.io.votable as votable

from ..query import QueryWithLogin
from ..exceptions import InvalidQueryError, TimeoutError, NoResultsWarning
from ..utils import commons
from ..exceptions import TableParseError

__all__ = ['BaseWFAUClass', 'clean_catalog']


class BaseWFAUClass(QueryWithLogin):

    """
    The BaseWFAUQuery class.  This is intended to be inherited by other classes
    that implement specific interfaces to Wide-Field Astronomy Unit
    (http://www.roe.ac.uk/ifa/wfau/) archives
    """
    BASE_URL = ""
    LOGIN_URL = BASE_URL + "DBLogin"
    IMAGE_URL = BASE_URL + "GetImage"
    ARCHIVE_URL = BASE_URL + "ImageList"
    REGION_URL = BASE_URL + "WSASQL"
    CROSSID_URL = BASE_URL + "CrossID"
    TIMEOUT = ""

    def __init__(self, username=None, password=None, community=None,
                 database='', programme_id='all'):
        """
        The BaseWFAUClass __init__ is meant to be overwritten
        """
        super(BaseWFAUClass, self).__init__()
        self.database = database
        self.programme_id = programme_id
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

        request_payload['programmeID'] = self._verify_programme_id(
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

    def _verify_programme_id(self, pid, query_type='catalog'):
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
        ValueError
            If the pid is 'all' and the query type is a catalog.  You can query
            all surveys for images, but not all catalogs.
        """
        if pid == 'all' and query_type == 'image':
            return 'all'
        elif pid == 'all' and query_type == 'catalog':
            raise ValueError(
                "Cannot query all catalogs at once. Valid catalogs are: {0}.\n"
                "Change programmeID to one of these."
                .format(",".join(self.programmes_short.keys())))
        elif pid in self.programmes_long:
            return self.programmes_long[pid]
        elif pid in self.programmes_short:
            return self.programmes_short[pid]
        elif query_type != 'image':
            raise ValueError("programme_id {0} not recognized".format(pid))

    def _parse_system(self, system):
        if system is None:
            return 'J'
        elif system.lower() in ('g', 'gal', 'galactic'):
            return 'G'
        elif system.lower() in ('j', 'j2000', 'celestical', 'radec'):
            return 'J'

    def get_images(self, coordinates, waveband='all', frame_type='stack',
                   image_width=1 * u.arcmin, image_height=None, radius=None,
                   database=None, programme_id=None,
                   verbose=True, get_query_payload=False,
                   show_progress=True):
        """
        Get an image around a target/ coordinates from a WFAU catalog.

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
            The WFAU database to use.
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
                         radius=None, database=None,
                         programme_id=None, verbose=True,
                         get_query_payload=False,
                         show_progress=True):
        """
        Serves the same purpose as
        `~astroquery.wfau.BaseWFAUClass.get_images` but returns a list of
        file handlers to remote files.

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
            The WFAU database to use.
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

        if database is None:
            database = self.database

        if programme_id is None:
            programme_id = self.programme_id

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

    def get_image_list(self, coordinates, waveband='all', frame_type='stack',
                       image_width=1 * u.arcmin, image_height=None,
                       radius=None, database=None,
                       programme_id=None, get_query_payload=False):
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
            The WFAU database to use.
        verbose : bool
            Defaults to `True`. When `True` prints additional messages.
        get_query_payload : bool, optional
            If `True` then returns the dictionary sent as the HTTP request.
            Defaults to `False`.

        Returns
        -------
        url_list : list of image urls

        """

        if frame_type not in self.frame_types:
            raise ValueError("Invalid frame type. Valid frame types are: {!s}"
                             .format(self.frame_types))

        if waveband not in self.filters:
            raise ValueError("Invalid waveband. Valid wavebands are: {!s}"
                             .format(self.filters.keys()))

        if database is None:
            database = self.database

        if programme_id is None:
            programme_id = self.programme_id

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
            radius = coord.Angle(radius).degree
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

        response = self._wfau_send_request(query_url, request_payload)
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
        ahref = re.compile(r'href="([a-zA-Z0-9_\.&\?=%/:-]+)"')
        links = ahref.findall(html_in)
        return links

    def query_region(self, coordinates, radius=1 * u.arcmin,
                     programme_id=None, database=None,
                     verbose=False, get_query_payload=False, system='J2000',
                     attributes=['default'], constraints=''):
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
            The WFAU database to use.
        verbose : bool, optional.
            When set to `True` displays warnings if the returned VOTable does
            not conform to the standard. Defaults to `False`.
        get_query_payload : bool, optional
            If `True` then returns the dictionary sent as the HTTP request.
            Defaults to `False`.
        system : 'J2000' or 'Galactic'
            The system in which to perform the query. Can affect the output
            data columns.
        attributes : list, optional.
            Attributes to select from the table.  See, e.g.,
            http://horus.roe.ac.uk/vsa/crossID_notes.html
        constraints : str, optional
            SQL constraints to the search. Default is empty (no constrains
            applied).

        Returns
        -------
        result : `~astropy.table.Table`
            Query result table.
        """

        if database is None:
            database = self.database

        if programme_id is None:
            if self.programme_id != 'all':
                programme_id = self.programme_id
            else:
                raise ValueError("Must specify a programme_id for region queries")

        response = self.query_region_async(coordinates, radius=radius,
                                           programme_id=programme_id,
                                           database=database,
                                           get_query_payload=get_query_payload,
                                           system=system, attributes=attributes,
                                           constraints=constraints)
        if get_query_payload:
            return response

        result = self._parse_result(response, verbose=verbose)
        return result

    def query_region_async(self, coordinates, radius=1 * u.arcmin,
                           programme_id=None,
                           database=None, get_query_payload=False,
                           system='J2000', attributes=['default'],
                           constraints=''):
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
            The WFAU database to use.
        get_query_payload : bool, optional
            If `True` then returns the dictionary sent as the HTTP request.
            Defaults to `False`.
        attributes : list, optional.
            Attributes to select from the table.  See, e.g.,
            http://horus.roe.ac.uk/vsa/crossID_notes.html
        constraints : str, optional
            SQL constraints to the search. Default is empty (no constrains
            applied).

        Returns
        -------
        response : `requests.Response`
            The HTTP response returned from the service.
        """

        if database is None:
            database = self.database

        if programme_id is None:
            if self.programme_id != 'all':
                programme_id = self.programme_id
            else:
                raise ValueError("Must specify a programme_id for region queries")

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
        request_payload['select'] = ','.join(attributes)
        request_payload['where'] = constraints

        # for some reason, this is required on the VISTA website
        if self.archive is not None:
            request_payload['archive'] = self.archive

        if get_query_payload:
            return request_payload

        response = self._wfau_send_request(self.REGION_URL, request_payload)
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
            raise TableParseError("Failed to parse WFAU votable! The raw "
                                  "response can be found in self.response, "
                                  "and the error in self.table_parse_error.  "
                                  "Exception: " + str(self.table_parse_error))

    def list_catalogs(self, style='short'):
        """
        Returns a list of available catalogs in WFAU.
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
            return list(self.programmes_short.keys())
        elif style == 'long':
            return list(self.programmes_long.keys())
        else:
            warnings.warn("Style must be one of 'long', 'short'.\n"
                          "Returning catalog list in short format.\n")
            return list(self.programmes_short.keys())

    def _get_databases(self):
        if self.logged_in():
            response = self.session.get(url="/".join([self.BASE_URL,
                                                      self.IMAGE_FORM]))
        else:
            response = requests.get(url="/".join([self.BASE_URL,
                                                  self.IMAGE_FORM]))

        root = BeautifulSoup(response.content, features='html5lib')
        databases = [x.attrs['value'] for x in
                     root.find('select').findAll('option')]
        return databases

    def list_databases(self):
        """
        List the databases available from the WFAU archive.
        """
        self.databases = set(self.all_databases + self._get_databases())
        return self.databases

    def _wfau_send_request(self, url, request_payload):
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
            response = self._request("GET", url=url, params=request_payload,
                                     timeout=self.TIMEOUT)
        return response

    def _check_page(self, url, keyword, wait_time=1, max_attempts=30):
        page_loaded = False
        while not page_loaded and max_attempts > 0:
            if self.logged_in():
                response = self.session.get(url)
            else:
                response = requests.get(url=url)
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

    def query_cross_id_async(self, coordinates, radius=1*u.arcsec,
                             programme_id=None, database=None, table="source",
                             constraints="", attributes='default',
                             pairing='all', system='J2000',
                             get_query_payload=False,
                             ):
        """
        Query the crossID server

        Parameters
        ----------
        coordinates : astropy.SkyCoord
            An array of one or more astropy SkyCoord objects specifying the
            objects to crossmatch against.
        radius : str or `~astropy.units.Quantity` object, optional
            The string must be parsable by `~astropy.coordinates.Angle`. The
            appropriate `~astropy.units.Quantity` object from
            `astropy.units` may also be used. When missing defaults to 1
            arcsec.
        programme_id : str
            The survey or programme in which to search for. See
            `list_catalogs`.
        database : str
            The WFAU database to use.
        table : str
            The table ID, one of: "source", "detection", "synopticSource"
        constraints : str
            SQL constraints.  If 'source' is selected, this will be expanded
            automatically
        attributes : str
            Additional attributes to select from the table.  See, e.g.,
            http://horus.roe.ac.uk/vsa/crossID_notes.html
        system : 'J2000' or 'Galactic'
            The system in which to perform the query. Can affect the output
            data columns.
        get_query_payload : bool, optional
            If `True` then returns the dictionary sent as the HTTP request.
            Defaults to `False`.
        """

        if table == "source":
            constraints += "(priOrSec<=0 OR priOrSec=frameSetID)"
        if database is None:
            database = self.database

        if programme_id is None:
            if self.programme_id != 'all':
                programme_id = self.programme_id
            else:
                raise ValueError("Must specify a programme_id")

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
        request_payload['disp'] = ''
        request_payload['baseTable'] = table
        request_payload['whereClause'] = constraints
        request_payload['qType'] = 'form'
        request_payload['selectList'] = attributes
        request_payload['uploadFile'] = 'file.txt'
        if pairing not in ('nearest', 'all'):
            raise ValueError("pairing must be one of 'nearest' or 'all'")
        request_payload['nearest'] = 0 if pairing == 'nearest' else 1

        # for some reason, this is required on the VISTA website
        if self.archive is not None:
            request_payload['archive'] = self.archive

        if get_query_payload:
            return request_payload

        fh = StringIO()
        assert len(coordinates) > 0
        for crd in coordinates:
            fh.write("{0} {1}\n".format(crd.ra.deg, crd.dec.deg))
        fh.seek(0)

        if hasattr(self, 'session') and self.logged_in():
            response = self.session.post(self.CROSSID_URL,
                                         params=request_payload,
                                         files={'file.txt': fh},
                                         timeout=self.TIMEOUT)
        else:
            response = self._request("POST", url=self.CROSSID_URL,
                                     params=request_payload,
                                     files={'file.txt': fh},
                                     timeout=self.TIMEOUT)

        raise NotImplementedError("It appears we haven't implemented the file "
                                  "upload correctly.  Help is needed.")

        # response = self._check_page(response.url, "query finished")

        return response

    def query_cross_id(self, *args, **kwargs):
        """
        See `query_cross_id_async`
        """
        get_query_payload = kwargs.get('get_query_payload', False)
        verbose = kwargs.get('verbose', False)

        response = self.query_cross_id_async(*args, **kwargs)

        if get_query_payload:
            return response

        result = self._parse_result(response, verbose=verbose)
        return result


def clean_catalog(wfau_catalog, clean_band='K_1', badclass=-9999,
                  maxerrbits=41, minerrbits=0, maxpperrbits=60):
    """
    Attempt to remove 'bad' entries in a catalog.

    Parameters
    ----------
    wfau_catalog : `~astropy.io.fits.BinTableHDU`
        A FITS binary table instance from the WFAU survey.
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
    mask = ((wfau_catalog[band + 'ERRBITS'] <= maxerrbits) *
            (wfau_catalog[band + 'ERRBITS'] >= minerrbits) *
            ((wfau_catalog['PRIORSEC'] == wfau_catalog['FRAMESETID']) +
             (wfau_catalog['PRIORSEC'] == 0)) *
            (wfau_catalog[band + 'PPERRBITS'] < maxpperrbits)
            )
    if band + 'CLASS' in wfau_catalog.colnames:
        mask *= (wfau_catalog[band + 'CLASS'] != badclass)
    elif 'mergedClass' in wfau_catalog.colnames:
        mask *= (wfau_catalog['mergedClass'] != badclass)

    return wfau_catalog.data[mask]


def _parse_dimension(dim):
    """
    Parses the radius and returns it in the format expected by WFAU.

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
            new_dim = coord.Angle(dim).degree
            dim_in_min = u.Quantity(
                value=new_dim, unit=u.deg).to(u.arcmin).value
        except (u.UnitsError, coord.errors.UnitsError, AttributeError):
            raise u.UnitsError("Dimension not in proper units")
    return dim_in_min
