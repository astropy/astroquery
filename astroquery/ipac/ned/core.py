"""This module provides functions to send query to IPAC NED DBR services."""
# Licensed under a 3-clause BSD style license - see LICENSE.rst

import re
from io import BytesIO
from xml.dom.minidom import parseString
from xml.parsers.expat import ExpatError

import astropy.units as u
import astropy.coordinates as coord
import astropy.io.votable as votable
from astropy.coordinates import FK5

from astroquery.query import BaseQuery
from astroquery.utils import commons
from astroquery.ipac.ned import conf
from astroquery.exceptions import (
    TableParseError,
    RemoteServiceError,
    InvalidQueryError
)

__all__ = ["Ned", "NedClass"]
NED_COORD_FRAMES = {'equ': 'Equatorial', 'ecl': 'Ecliptic',
                    'gal': 'Galactic', 'sgal': 'SuperGalactic'}
NED_COORD_EQUINOX = {'j': 'J2000', 'b': 'B1950'}


class NedClass(BaseQuery):
    """
    Class for querying the NED (NASA/IPAC Extragalactic Database) system.

    https://ned.ipac.caltech.edu/
    """
    # make configurable
    DBR_BASE_URL = conf.server_dbr
    BASE_URL = conf.server
    SPECTRA_URL = BASE_URL + 'NEDspectra'
    IMG_DATA_URL = BASE_URL + 'imgdata'
    TIMEOUT = conf.timeout

    # NED DBR API service
    OBJSEARCH_POSITIONS = "PositionsOfObject"
    OBJSEARCH_REDSHIFTS = "RedshiftsOfObject"
    OBJSEARCH_DISTANCES = "DistancesOfObject"
    OBJSEARCH_PHOTOMETRY = "PhotometryOfObject"
    OBJSEARCH_DIAMETERS = "DiametersOfObject"
    OBJSEARCH_CROSSIDS = "CrossidsOfObject"
    OBJSEARCH_EXTINCTION = "ExtinctionAtTarget"
    OBJSEARCH_REFERENCES = "ReferencesOfObject"
    OBJSEARCH_NOTES = "NotesOfObject"
    OBJSEARCH_INREFCODE = "ObjectsInRefcode"
    CONESEARCH_TARGET = "ConeSearchByTarget"
    CONESEARCH_POSITION = "ConeSearchByPosition"
    CONESEARCH_IAU = "ConeSearchByIAUstyle"

    DBR_TARGET = 'TARGET'
    DBR_LON = 'LON'
    DBR_LAT = 'LAT'
    DBR_RADIUS = 'RADIUS'
    DBR_CSYS = 'CSYS'
    DBR_EQUINOX = 'EQUINOX'
    DBR_MAXREC = 'MAXREC'
    DBR_ISLINE = "SPECLINES"
    DBR_IAU = 'IAU_NAME'
    DBR_REFCODE = 'REFCODE'

    SEARCH_TYPE = ''

    def query_object(self, object_name, *,
                     get_query_payload=False, verbose=False):
        """
        Query object by name from the NED DBR Service and returns the Main
        Source Table.

        Parameters
        ----------
        object_name : str
            name of the identifier to query.
        get_query_payload : bool, optional
            If set to `True` then returns the dictionary sent as the HTTP
            request.  Defaults to `False`.
        verbose : bool, optional.
            When set to `True` displays warnings if the returned VOTable
            does not conform to the standard. Defaults to `False`.

        Returns
        -------
        response : dict, if get_query_payload is `True`.
            The service query key/value set.
        result : `~astropy.table.Table`
            The result of the query as an `~astropy.table.Table` object,
            or None if an error occurs.
        """
        # for NED's object by name
        response = self.query_object_async(object_name,
                                           get_query_payload=get_query_payload)
        if get_query_payload:
            return response
        result = self._parse_result(response, verbose=verbose)
        return result

    def query_object_async(self, object_name, *, get_query_payload=False):
        """
        Query objects by name from the NED DBR Service and returns the raw
        HTTP response.

        Serves the same purpose as `~NedClass.query_object` but returns the
        raw HTTP response
        rather than the `~astropy.table.Table` object.

        Parameters
        ----------
        object_name : str
            name of the identifier to query.
        get_query_payload : bool, optional
            If set to `True` then returns the dictionary sent as the HTTP
            request.  Defaults to `False`

        Returns
        -------
        dict, if get_query_payload is `True`.
            The service query key/value set.
        `~requests.models.Response`
            The HTTP response returned from the service.
        """
        request_payload = self._request_payload_init(target_name=object_name)
        request_payload[self.DBR_RADIUS] = 0
        self.SEARCH_TYPE = "object"

        return self.handle_response(get_query_payload,
                                    self.DBR_BASE_URL + self.CONESEARCH_TARGET,
                                    request_payload)

    def query_region(self, coordinates, *, radius=1 * u.arcmin,
                     get_query_payload=False, verbose=False, **kwargs):
        """
        Query the objects in a region around a known identifier or given
        coordinates.

        Equivalent to the near position and near name queries from the NED
        web interface.

        Parameters
        ----------
        coordinates : str or `~astropy.coordinates` object
            The target around which to search. It may be specified as a
            string in which case it is resolved using online services or as
            the appropriate `~astropy.coordinates` object. ICRS coordinates
            may also be entered as strings as specified in the
            `~astropy.coordinates` module.
        radius : str or `~astropy.units.Quantity` object, optional
            The string must be parsable by `~astropy.coordinates.Angle`. The
            appropriate `~astropy.units.Quantity` object from
            `~astropy.units` may also be used. Defaults to 1 arcmin.
            ex: "3.0 arcmin" (str) or
            2.0 * u.arcmin (`~astropy.units.Quantity`)
        get_query_payload : bool, optional
            If set to `True` then returns the dictionary sent as the HTTP
            request.  Defaults to `False`.
        verbose : bool, optional.
            When set to `True` displays warnings if the returned VOTable
            does not conform to the standard. Defaults to `False`.
        kwargs : Keyword Arguments
            z_constraint: str, optional
                redshift constraint may be ``Unconstrained``, ``Available``,
                ``Unavailable``, ``Larger Than``, ``Less Than`` or ``Between``.
            z_value1, z_value2: float, optional.
                z_value1 is the redshift bound for the constraint
                ``Larger Than``, ``Less Than``, or the minimum value within
                a range for ``Between``.
                z_value2 is the maximum value within a range for ``Between``.
            z_unit: str, optional
                redshift value unit may be ``z`` or ``km/s``.
                Defaults to ``z``.
            max_rec: int, optional
                Maximum records to return from the query.
                Defaults to all records if not specified.

        Returns
        -------
        response : dict, if get_query_payload is `True`.
            The service query key/value set, or None if an error occurs.
        result : `~astropy.table.Table`
            The result of the query as an `~astropy.table.Table` object
            or None if an error occurs.
        """
        # for NED's object near name/ near region
        response = self.query_region_async(
            coordinates, radius=radius, get_query_payload=get_query_payload,
            **kwargs)
        if get_query_payload:
            return response
        result = self._parse_result(response, verbose=verbose)
        return result

    def query_region_async(self, coordinates, *, radius=1 * u.arcmin,
                           get_query_payload=False, **kwargs):
        """
        Query the objects in a region around a known identifier or given
        coordinates.

        Serves the same purpose as `~NedClass.query_region` but returns the
        raw HTTP response rather than the `~astropy.table.Table` object.

        Parameters
        ----------
        coordinates : str or `~astropy.coordinates` object
            The target around which to search. It may be specified as a
            string in which case it is resolved using online services or as
            the appropriate `~astropy.coordinates` object. ICRS coordinates
            may also be entered as strings as specified in the
            `~astropy.coordinates` module.
        radius : str or `~astropy.units.Quantity` object, optional
            The string must be parsable by `~astropy.coordinates.Angle`. The
            appropriate `~astropy.units.Quantity` object from
            `~astropy.units` may also be used. Defaults to 1 arcmin.
            ex: "3.0 arcmin" (str) or 2.0 * u.arcmin
            (`~astropy.units.Quantity`)
        get_query_payload : bool, optional
            If set to `True` then returns the dictionary sent as the HTTP
            request.  Defaults to `False`.
        kwargs : Keyword Arguments
            z_constraint: str, optional
                redshift constraint may be ``Unconstrained``, ``Available``,
                ``Unavailable``, ``Larger Than``, ``Less Than`` or ``Between``.
            z_value1, z_value2: float, optional.
                z_value1 is the redshift bound for the constraint
                ``Larger Than``, ``Less Than``, or the minimum value within
                a range for ``Between``.
                z_value2 is the maximum value within a range for ``Between``.
            z_unit: str, optional
                redshift value unit may be ``z`` or ``km/s``.
                Defaults to ``z``.
            max_rec: int, optional
                Maximum records to return from the query.
                Defaults to all records if not specified.

        Returns
        -------
        dict, if get_query_payload is `True`.
            The service query key/value set.
        `~requests.models.Response`
            The HTTP response returned from the service.

        Raises
        ------
        TypeError : if there is type error in the coordinate.
        InvalidQueryError : if there is error in the redshift constraint.
        """
        decimal_digits = 8
        request_payload = self._request_payload_init(
            max_rec=self._get_maxrec(**kwargs))

        # if its a name then query near name
        if not commons._is_coordinate(coordinates):
            request_payload[self.DBR_TARGET] = coordinates
            self.SEARCH_TYPE = Ned.CONESEARCH_TARGET
        else:
            try:
                c = commons.parse_coordinates(coordinates)
                ra, dec, equ, frame = get_coord_for_ned(c)
                frame_name = c.frame.name.lower()
                if (frame_name == NED_COORD_FRAMES['gal'].lower()
                        or frame_name == NED_COORD_FRAMES['sgal'].lower()):
                    request_payload[self.DBR_CSYS] = frame
                    request_payload[self.DBR_LON] = self._fixed_float(
                        ra, digits=decimal_digits)
                    request_payload[self.DBR_LAT] = self._fixed_float(
                        dec, digits=decimal_digits)
                else:
                    request_payload[self.DBR_CSYS] = frame
                    request_payload[self.DBR_EQUINOX] = equ
                    request_payload[self.DBR_LON] = self._fixed_float(
                        ra, unit='h', digits=decimal_digits)
                    request_payload[self.DBR_LAT] = self._fixed_float(
                        dec, unit='d', digits=decimal_digits)
                self.SEARCH_TYPE = Ned.CONESEARCH_POSITION
            except (u.UnitsError, TypeError, ValueError):
                raise TypeError("Coordinates not specified correctly")

        z_constraint, msg = self._check_redshift_constraints(**kwargs)
        if z_constraint is None and msg:
            raise InvalidQueryError(msg)
        elif z_constraint:
            for k, v in z_constraint.items():
                request_payload[k] = v

        request_payload[self.DBR_RADIUS] = coord.Angle(radius).arcmin
        return self.handle_response(
            get_query_payload,
            self.DBR_BASE_URL + self.SEARCH_TYPE,
            request_payload)

    def query_region_iau(self, iau_name, *, equinox='B1950',
                         get_query_payload=False, verbose=False, **kwargs):
        """
        Query the Ned service to do cone search via the IAU name in the
        equatorial coordinate system.

        Equivalent to the IAU format queries of the Web interface.

        Parameters
        ----------
        iau_name : str
            IAU coordinate-based name of target on which search is
            centered. Definition of IAU coordinates at
            https://cds.unistra.fr/Dic/iau-spec.html.
        equinox : str, optional
            The equinox may be one of ``J2000`` or ``B1950``.
            Defaults to ``B1950``.
        get_query_payload : bool, optional
            If set to `True` then returns the dictionary sent as the HTTP
            request.  Defaults to `False`
        verbose : bool, optional.
            When set to `True` displays warnings if the returned VOTable
            does not conform to the standard. Defaults to `False`.
        kwargs : Keyword Argumants
            z_constraint: str, optional
                redshift constraint may be ``Unconstrained``, ``Available``,
                ``Unavailable``, ``Larger Than``, ``Less Than`` or ``Between``.
            z_value1, z_value2: float, optional.
                z_value1 is for ``Larger Than``, ``Less Than``, or the minimum
                of ``Between``.
                z_value2 is for the maximum of ``Between``.
            z_unit: str, optional
                redshift value unit may be ``z`` or ``km/s``.
                Defaults to ``z``.
            max_rec: int, optional
                Maximum records to return from the query.

        Returns
        -------
        response : dict, if get_query_payload is `True`.
            The service query key/value set, or None if an error occurs.
        result : `~astropy.table.Table`
            The result of the query as an `~astropy.table.Table` object,
            or None if an error occurs.
        """
        response = self.query_region_iau_async(
            iau_name, equinox=equinox,
            get_query_payload=get_query_payload, **kwargs)
        if get_query_payload:
            return response
        result = self._parse_result(response, verbose=verbose)
        return result

    def query_region_iau_async(self, iau_name, *,
                               equinox='B1950',
                               get_query_payload=False, **kwargs):
        """
        Query the NED services to do cone search via the IAU name in the
        equatorial coordinate system.

        Serves the same purpose as `~NedClass.query_region_iau` but returns
        the raw HTTP response rather than the `~astropy.table.Table` object.

        Parameters
        ----------
        iau_name : str
            IAU coordinate-based name of target on which search is
            centered. Definition of IAU coordinates at
            https://cds.unistra.fr/Dic/iau-spec.html.
        equinox : str, optional
            The equinox may be one of ``J2000`` or ``B1950``.
            Defaults to ``B1950``.
        get_query_payload : bool, optional
            If set to `True` then returns the dictionary sent as the HTTP
            request.  Defaults to `False`
        kwargs : Keyword Arguments
            z_constraint: str, optional
                redshift constraint may be ``Unconstrained``, ``Available``,
                ``Unavailable``, ``Larger Than``, ``Less Than`` or ``Between``.
            z_value1, z_value2: float, optional.
                z_value1 is for ``Larger Than``, ``Less Than``, or
                the minimum of ``Between``.
                z_value2 is for the maximum of ``Between``.
            z_unit: str, optional
                redshift value unit may be ``z`` or ``km/s``.
                Defaults to ``z``.
            max_rec: int, optional
                Maximum records to return from the query.

        Returns
        -------
        dict, if get_query_payload is `True`.
            The service query key/value set.
        `~requests.models.Response`
            The HTTP response returned from the service, or None if an error
            occurs.

        Raises
        ------
        InvalidQueryError : if there is error in redshift constraint.
        """
        request_payload = self._request_payload_init(
            max_rec=self._get_maxrec(**kwargs))
        request_payload[self.DBR_IAU] = iau_name
        if equinox:
            request_payload[self.DBR_EQUINOX] = equinox
        self.SEARCH_TYPE = self.CONESEARCH_IAU

        z_constraint, msg = self._check_redshift_constraints(**kwargs)
        if z_constraint is None and msg:
            raise InvalidQueryError(msg)
        elif z_constraint:
            for k, v in z_constraint.items():
                request_payload[k] = v

        return self.handle_response(
            get_query_payload,
            self.DBR_BASE_URL + self.CONESEARCH_IAU,
            request_payload)

    def query_refcode(self, refcode, *, get_query_payload=False,
                      verbose=False, **kwargs):
        """
        Query to retrieve all objects contained in a particular reference.

        Equivalent to by refcode queries of the web interface.

        Parameters
        ----------
        refcode : str
            19 digit reference code.  Example: ``1997A&A...323...31K``.
        get_query_payload : bool, optional
            If set to `True` then returns the dictionary sent as the HTTP
            request.  Defaults to `False`.
        verbose : bool, optional.
            When set to `True` displays warnings if the returned VOTable
            does not conform to the standard. Defaults to `False`.
        kwargs : Keyword Arguments
            max_rec: int, optional
                Maximum records to return from the query.

        Returns
        -------
        response : dict, if get_query_payload is `True`.
            The service query key/value set.
        result : `~astropy.table.Table`
            The result of the query as an `~astropy.table.Table` object,
            or None if an error occurs.
        """
        response = self.query_refcode_async(
            refcode, get_query_payload=get_query_payload, **kwargs)
        if get_query_payload:
            return response
        result = self._parse_result(response, verbose=verbose)
        return result

    def query_refcode_async(self, refcode, *,
                            get_query_payload=False, **kwargs):
        """
        Query to retrieve all objects contained in a particular reference.

        Serves the same purpose as `~NedClass.query_refcode` but returns the
        raw HTTP response rather than the `~astropy.table.Table` object.

        Parameters
        ----------
        refcode : str
            19 digit reference code.  Example:``1997A&A...323...31K``.
        get_query_payload : bool, optional
            If set to `True` then returns the dictionary sent as the HTTP
            request.  Defaults to `False`.
        kwargs : Keyword Arguments
            max_rec: int, optional
                Maximum records to return from the query.

        Returns
        -------
        dict, if get_query_payload is `True`
            The service query key/value set.
        `~requests.models.Response`
            The HTTP response returned from the service.
        """
        request_payload = self._request_payload_init(
            max_rec=self._get_maxrec(**kwargs))
        request_payload[self.DBR_REFCODE] = refcode
        self.SEARCH_TYPE = self.OBJSEARCH_INREFCODE

        return self.handle_response(
            get_query_payload,
            self.DBR_BASE_URL + self.OBJSEARCH_INREFCODE,
            request_payload)

    def get_images(self, object_name, *, get_query_payload=False,
                   show_progress=True):
        """
        Query function to fetch FITS images for a given identifier.

        Parameters
        ----------
        object_name : str
            name of the identifier to query.
        get_query_payload : bool, optional
            If set to `True` then returns the dictionary sent as the HTTP
            request.  Defaults to `False`
        show_progress : bool
            display the progress.

        Returns
        -------
        A list of `~astropy.io.fits.HDUList` objects

        """
        readable_objs = self.get_images_async(
            object_name, get_query_payload=get_query_payload,
            show_progress=show_progress)

        if get_query_payload:
            return readable_objs
        return [obj.get_fits() for obj in readable_objs]

    def get_images_async(self, object_name, *, get_query_payload=False,
                         show_progress=True):
        """
        Query function to fetch FITS images for a given identifier.

        Serves the same purpose as `~NedClass.get_images` but returns
        file-handlers to the remote files rather than downloading them.

        Parameters
        ----------
        object_name : str
            name of the identifier to query.
        get_query_payload : bool, optional
            If set to `True` then returns the dictionary sent as the HTTP
            request.  Defaults to `False`
        show_progress : bool
            display the progress

        Returns
        -------
        A list of context-managers that yield readable file-like objects

        """
        image_urls = self.get_image_list(object_name,
                                         get_query_payload=get_query_payload)
        if get_query_payload:
            return image_urls

        return [commons.FileContainer(U, encoding='binary',
                                      show_progress=show_progress)
                for U in image_urls]

    def get_spectra(self, object_name, *, get_query_payload=False,
                    show_progress=True):
        """
        Query function to fetch FITS files of spectra for a given identifier.

        Parameters
        ----------
        object_name : str
            name of the identifier to query.
        get_query_payload : bool, optional
            If set to `True` then returns the dictionary sent as the HTTP
            request.  Defaults to `False`
        show_progress : bool
            display the progress.

        Returns
        -------
        A list of `~astropy.io.fits.HDUList` objects

        """
        readable_objs = self.get_spectra_async(
            object_name, get_query_payload=get_query_payload,
            show_progress=show_progress)

        if get_query_payload:
            return readable_objs
        return [obj.get_fits() for obj in readable_objs]

    def get_spectra_async(self, object_name, *, get_query_payload=False,
                          show_progress=True):
        """
        Query function to fetch FITS files of spectra for a given identifier.

        Serves the same purpose as `~NedClass.get_spectra` but returns
        file-handlers to the remote fits files rather than downloading them.

        Parameters
        ----------
        object_name : str
            name of the identifier to query.
        get_query_payload : bool, optional
            If set to `True` then returns the dictionary sent as the HTTP
            request.  Defaults to `False`
        show_progress : bool
            display the progress.

        Returns
        -------
        A list of context-managers that yield readable file-like objects
        """
        image_urls = self.get_image_list(object_name, item='spectra',
                                         get_query_payload=get_query_payload,
                                         file_format='fits')
        if get_query_payload:
            return image_urls
        return [commons.FileContainer(U, encoding='binary',
                                      show_progress=show_progress)
                for U in image_urls]

    def get_image_list(self, object_name, *, item='image', file_format='fits',
                       get_query_payload=False):
        """
        Return a list of URLs from which to download the FITS images.

        Parameters
        ----------
        object_name : str
            name of the identifier to query.
        get_query_payload : bool, optional
            If set to `True` then returns the dictionary sent as the HTTP
            request.  Defaults to `False`
        item : str, optional
            Can be either ``image`` or ``spectra``. Defaults to ``image``.
            Required to decide the right URL to query.
        file_format : str, optional
            Format of images/spectra to return. Defaults to ``fits``.
            Other options available: ``author-ascii``, ``NED-ascii``,
            ``VO-table``.

        Returns
        -------
        list of image urls
        """
        request_payload = dict(objname=object_name)
        if item == 'spectra':
            request_payload['extend'] = 'multi'
            request_payload['detail'] = 0
            request_payload['numpp'] = 50
            request_payload['preview'] = 0
        self.SEARCH_TYPE = item
        if get_query_payload:
            return request_payload
        url = self.SPECTRA_URL if item == 'spectra' else self.IMG_DATA_URL
        response = self._request("GET", url=url, params=request_payload,
                                 timeout=self.TIMEOUT)
        response.raise_for_status()
        return self._extract_image_urls(response.text, file_format=file_format)

    @staticmethod
    def _extract_image_urls(html_in, *, file_format='fits'):
        """
        Use regexps to extract the image URLs from the given HTML.

        Parameters
        ----------
        html_in : str
            source from which the urls are to be extracted

        format : str, optional
            Format of spectra to return. Defaults to ``fits``.
            Other options available: ``author-ascii``, ``NED-ascii``,
            ``VO-table``.

        Returns
        -------
        url_list : list
            a list containing URLs.

        """
        base_url = 'https://ned.ipac.caltech.edu'

        extensions = {'fits': 'fits.gz',
                      'author-ascii': 'txt',
                      'NED-ascii': '_NED.txt',
                      'VO-table': '_votable.xml'}

        names = {'fits': 'FITS',
                 'author-ascii': 'Author-ASCII',
                 'NED-ascii': 'NED-ASCII',
                 'VO-table': 'VOTable'}

        pattern = re.compile(
            fr'<a\s+href\s*?="?\s*?(.+?{extensions[file_format]})'
            fr'"?\s*?>\s*?(?:Retrieve|{names[file_format]})</a>',
            re.IGNORECASE)
        matched_urls = pattern.findall(html_in)
        url_list = [base_url + img_url for img_url in matched_urls]
        return url_list

    def get_table(self, object_name, *, table='photometry',
                  get_query_payload=False, verbose=False, **kwargs):
        """
        Fetch the specified data table for the object from NED DBR service.

        The returned table is in the form of `~astropy.table.Table`.

        Parameters
        ----------
        object_name : str
            name of the identifier to query.
        table : str, optional
            Must be one of ``crossids``, ``positions``, ``redshifts``,
            ``distances``, ``photometry``, ``extinctions``, ``notes``
            (or ``object_notes``), ``diameters``, and ``references``.
            Specifies the type of data-table that must be fetched for the
            given object. Defaults to ``photometry``.
        get_query_payload : bool, optional
            If set to `True` then returns the dictionary sent as the HTTP
            request.  Defaults to `False`.
        verbose : bool, optional.
            When set to `True` displays warnings if the returned VOTable
            does not conform to the standard. Defaults to `False`.
        kwargs : Keyword Arguments
            max_rec: int, optional
                Maximum records to return from the query.
            is_line: bool, optional for photometry service
                If set to `True` then gets photometry data of line component.
                Defaults to `False`.

        Returns
        -------
        response : dict, if get_query_payload is `True`.
            The service query key/value set.
        result : `~astropy.table.Table`
            The result of the query as an `~astropy.table.Table` object,
            or None if an error occurs.
        """
        response = self.get_table_async(object_name, table=table,
                                        get_query_payload=get_query_payload,
                                        **kwargs)
        if get_query_payload:
            return response

        result = self._parse_result(response, verbose=verbose)
        return result

    def get_table_async(self, object_name, *, table='photometry',
                        get_query_payload=False, **kwargs):
        """
        Fetch the specified data table for the object from NED DBR service.

        Serves the same purpose as `~NedClass.get_table` but returns the
        raw HTTP response rather than the `~astropy.table.Table` object.

        Parameters
        ----------
        object_name : str
            name of the identifier to query.
        table : str, optional
            Must be one of ``crossids``, ``positions``, ``redshifts``,
            ``distances``, ``photometry``, ``extinctions``, ``notes``
            (or ``object_notes``), ``diameters``, and ``references``.
            Specifies the type of data-table that must be fetched for the
            given object. Defaults to ``photometry``.
        get_query_payload : bool, optional
            If set to `True` then returns the dictionary sent as the HTTP
            request.  Defaults to `False`.
        kwargs : Keyword Arguments
            max_rec: int, optional
                Maximum records to return from the query.
            is_line: bool, optional for photometry service
                If set to `True` then gets photometry data of line component.
                Defaults to `False`.

        Returns
        -------
        dict, if get_query_payload is `True`.
            The service query key/value set.
        `~requests.models.Response`
            The HTTP response returned from the table service.

        Raises
        ------
        InvalidQueryError : if there is error in the specified table service.
        """
        _SEARCH_TYPE = dict(
            crossids=self.OBJSEARCH_CROSSIDS,
            positions=self.OBJSEARCH_POSITIONS,
            redshifts=self.OBJSEARCH_REDSHIFTS,
            distances=self.OBJSEARCH_DISTANCES,
            photometry=self.OBJSEARCH_PHOTOMETRY,
            diameters=self.OBJSEARCH_DIAMETERS,
            extinctions=self.OBJSEARCH_EXTINCTION,
            object_notes=self.OBJSEARCH_NOTES,
            notes=self.OBJSEARCH_NOTES,
            references=self.OBJSEARCH_REFERENCES)

        if table not in _SEARCH_TYPE.keys():
            raise InvalidQueryError("The get_table service for "
                                    + table + " is not supported.")

        request_payload = self._request_payload_init(
            target_name=object_name,
            max_rec=self._get_maxrec(**kwargs))
        if table == 'photometry' and "is_line" in kwargs and kwargs['is_line']:
            request_payload[self.DBR_ISLINE] = 'yes'
        self.SEARCH_TYPE = _SEARCH_TYPE[table]

        return self.handle_response(get_query_payload,
                                    self.DBR_BASE_URL + _SEARCH_TYPE[table],
                                    request_payload)

    def handle_response(self, get_query_payload, service_url, request_payload):
        """
        Form the URL and parameters to send the http query.

        Parameters
        ----------
        get_query_payload : bool, optional
            If set to `True` then returns the dictionary sent as
            the HTTP request.  Defaults to `False`.
        service_url : str
            for the URL part containing the server path and the service name
        request_payload : dict
            parameters for the key/value in the URL.

        Returns
        -------
        response : `~requests.models.Response`
            The HTTP response returned from the query.
        """
        if get_query_payload:
            return request_payload

        # query_url = service_url + '?'
        # + urllib.parse.urlencode(request_payload)

        response = self._request("GET", url=service_url,
                                 params=request_payload, timeout=self.TIMEOUT)
        response.raise_for_status()
        return response

    @staticmethod
    def _fixed_float(num, digits=-1, unit=''):
        """
        Form a string containing a float number with specified
        precision and the unit.

        Parameters
        ----------
        digits : int, optional
            precision after the floating point.
            Defaults to `-1`, meaning no precision specified.
        unit : str
            unit for the number. Default to empty string.

        Returns
        -------
        a string representing a float number
        """
        if digits >= 0:
            return str(round(num, digits))+unit
        else:
            return str(num)+unit

    @staticmethod
    def _get_maxrec(**kwargs):
        """
        Get maximum record specification from a list of keyword
        arguments if there is.

        Parameters
        ----------
        kwargs : Keyword Arguments

        Returns
        -------
        an integer number or None.
        """
        if "max_rec" in kwargs:
            m = int(kwargs["max_rec"])
            m = -1 if m < -1 else m
            return m
        else:
            return None

    @staticmethod
    def _check_redshift_constraints(**kwargs):
        """
        Validate redshift constraints from keyword arguments if there is.

        Parameters
        ----------
        kwargs : Keyword Arguments

        Returns
        -------
        dict : containing data for z_constraint, z_value1, z_value2 and z_unit.
        str : error message. Default to empty string if no error.
        """
        z_info = dict()

        key_z_c = 'z_constraint'
        key_z_v1 = 'z_value1'
        key_z_v2 = 'z_value2'
        key_z_u = 'z_unit'
        _Z_UC = 'Unconstrained'
        _Z_AV = 'Available'
        _Z_UA = 'Unavailable'
        _Z_LA = 'Larger Than'
        _Z_LE = 'Less Than'
        _Z_BW = 'Between'

        z_msg = ''

        if key_z_c not in kwargs:
            return None, ""
        caseless_constraint = kwargs[key_z_c].casefold()
        caseless_set = {t.casefold()
                        for t in [_Z_UC, _Z_AV, _Z_UA, _Z_LA, _Z_LE, _Z_BW]}
        if caseless_constraint not in caseless_set:
            return None, key_z_c + ' ' + kwargs[key_z_c] + ' is not recognized'
        else:
            z_info[key_z_c] = kwargs[key_z_c]
            if kwargs[key_z_c].casefold() in {
                    _Z_UC.casefold(), _Z_AV.casefold(), _Z_UA.casefold()}:
                return z_info, z_msg
            if kwargs[key_z_c].casefold() in {
                    _Z_LA.casefold(), _Z_LE.casefold(), _Z_BW.casefold()}:
                if key_z_v1 in kwargs:
                    z_info[key_z_v1] = kwargs[key_z_v1]
                else:
                    return (None,
                            f"{key_z_v1} has to be provided for "
                            f"{key_z_c} {kwargs[key_z_c]}")
                if key_z_u in kwargs and kwargs[key_z_u]:
                    z_info[key_z_u] = kwargs[key_z_u]
            if kwargs[key_z_c].casefold() in {item.casefold()
                                              for item in [_Z_BW]}:
                if key_z_v2 in kwargs:
                    z_info[key_z_v2] = kwargs[key_z_v2]
                else:
                    return (None, f"{key_z_v2} has to be provided for "
                            f"{key_z_c} {kwargs[key_z_c]}")

            return z_info, z_msg

    @staticmethod
    def _request_payload_init(target_name=None, max_rec=None):
        """
        Initialize the object to contain the query parameter.

        Parameters
        ----------
        target_name: str
            for object query, str, optional
        max_rec: int, optional
            Maximum record to retrieve from the table.

        Returns
        -------
        request_payload : dict

        """
        request_payload = dict()
        if target_name is not None:
            request_payload[NedClass.DBR_TARGET] = target_name
        if max_rec is not None:
            request_payload[NedClass.DBR_MAXREC] = max_rec

        return request_payload

    def _parse_result(self, response, *, verbose=False):
        """
        Parse the raw HTTP response and return it as an `~astropy.table.Table`.

        Parameters
        ----------
        response : `requests.models.Response`
            The HTTP response object
        verbose : bool, optional
            Defaults to `False`. When true it will display warnings whenever
            the VOTable returned from the service doesn't conform to the
            standard.

        Returns
        -------
        table : `~astropy.table.Table`

        Raises
        ------
        RemoteServiceError : there is error in the response from the service
        TableParseError : there is error in the return from the service
        """
        if not verbose:
            commons.suppress_vo_warnings()

        def _raise_service_or_parse_error(ex):
            (is_valid, err_msg) = _check_ned_valid(response.content)
            self.response = response.content
            if not is_valid:
                if err_msg:
                    raise RemoteServiceError(
                        "The remote service returned the following "
                        "message.\nERROR: {err_msg}".format(err_msg=err_msg))
                raise RemoteServiceError(
                    "The remote service returned an error with no message."
                )

            self.response = response
            self.table_parse_error = ex
            raise TableParseError(
                "Failed to parse NED result! The raw response can be "
                "found in Ned.response, and the error in "
                "Ned.table_parse_error.") from ex

        try:
            tf = BytesIO(response.content)
            p_table = votable.parse(tf, verify='warn')
            first_table = p_table.get_first_table()
            table = first_table.to_table(use_names_over_ids=True)
            return table
        except (ValueError, TypeError, AttributeError,
                IndexError, ExpatError) as ex:
            _raise_service_or_parse_error(ex)
        except Exception as ex:
            _raise_service_or_parse_error(ex)


Ned = NedClass()


def get_value_from_paths(obj, attr_paths):
    for attr_path in attr_paths:
        try:
            for attr in attr_path.split('.'):
                obj = getattr(obj, attr)
            return obj
        except AttributeError:
            continue
    return None


def get_coord_for_ned(c):
    frame_name = c.frame.name.lower()
    equ = None

    ra_attrs = ['ra.hour', 'ra.hourangle']
    dec_attrs = ['dec.degree']
    if frame_name == NED_COORD_FRAMES['gal'].lower():
        ra_attrs = ['l.degree']
        dec_attrs = ['b.degree']
        frame = NED_COORD_FRAMES['gal']
    elif frame_name == NED_COORD_FRAMES['sgal'].lower():
        ra_attrs = ['sgl.degree']
        dec_attrs = ['sgb.degree']
        frame = NED_COORD_FRAMES['sgal']
    elif frame_name == 'fk4' or frame_name == 'fk5':
        frame = NED_COORD_FRAMES['equ']
        def_equ = NED_COORD_EQUINOX['b'] \
            if frame_name == 'fk4' else NED_COORD_EQUINOX['j']
        equ = get_equinox(c, equinox=def_equ)

        # convert fk4/non B1950 or fk5/non J2000 to fk5/J2000
        if equ is None or def_equ not in equ:
            c = c.transform_to(FK5(equinox=NED_COORD_EQUINOX['j']))
            equ = NED_COORD_EQUINOX['j']
    else:
        c = c.transform_to(FK5(equinox=NED_COORD_EQUINOX['j']))
        frame = NED_COORD_FRAMES['equ']
        equ = NED_COORD_EQUINOX['j']

    ra = None
    dec = None
    if ra_attrs and dec_attrs:
        ra = get_value_from_paths(c, ra_attrs)
        dec = get_value_from_paths(c, dec_attrs)

    if ra is None or dec is None:
        raise ValueError("The coordinate is not available")

    return ra, dec, equ, frame


def get_equinox(c, equinox=NED_COORD_EQUINOX['j']):
    """
    Get the equinox from a coordinate object.

    Parameters
    ----------
    c : `astropy.coordinates.BaseCoordinateFrame`
        The coordinate object.
    equinox : str, optional
        The default equinox to use if the coordinate object does not have one.

    Returns
    -------
    equ : str or None
        The equinox.
    """
    equ = c.frame.equinox.value if hasattr(c.frame, 'equinox') else equinox
    j = NED_COORD_EQUINOX['j']
    b = NED_COORD_EQUINOX['b']
    pattern = rf'({j}|{b})(?:\.0)?'
    match = re.search(pattern, equ)
    if match:
        return match[1]
    return None


def _check_ned_valid(string):
    """
    Check if the VOTable returned has an error parameter.

    Parameters
    ---------
    string : The VOTable as a string

    Returns
    -------
    retval : bool
        `False` if error parameter found, `True` otherwise.
    errmsg : str
        The string containing the error message if it exists, `None` otherwise.

    """
    # Routine assumes input is valid Table unless error parameter is found.
    retval = True
    errmsg = None
    strdom = parseString(string)
    info_tags = strdom.getElementsByTagName('PARAM')
    is_param = True
    if not info_tags:
        is_param = False
        info_tags = strdom.getElementsByTagName('INFO')

    # find element <INFO name='QUERY_STATUS" velue='ERROR'>error message</INFO>
    # or <PARAM name='QUERY_STATUS" velue='ERROR'>
    #   <DESCRIPTION>error message</DESCRIPTION></PARAM>
    for info in info_tags:
        if 'name' in info.attributes.keys() and \
                info.getAttribute("name") == "QUERY_STATUS":
            status_error = "ERROR"
            if 'value' in info.attributes.keys() and \
                    info.getAttribute("value") == status_error:
                if is_param:
                    desc_child = info.getElementsByTagName('DESCRIPTION')
                    if desc_child:
                        errmsg = desc_child[0].firstChild.nodeValue.strip()
                else:
                    errmsg = info.firstChild.nodeValue.strip()
                retval = False
                return retval, errmsg

    return retval, errmsg
