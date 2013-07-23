# Licensed under a 3-clause BSD style license - see LICENSE.rst
#from __future__ import print_function

import tempfile
from xml.dom.minidom import parseString
import astropy.utils.data as aud
from astropy.table import Table
import re
import warnings
from collections import namedtuple
from ..query import BaseQuery
from ..utils.class_or_instance import class_or_instance
from ..utils import commons
import astropy.units as u
import astropy.coordinates as coord
from astropy.io import fits
from datetime import datetime
from . import (HUBBLE_CONSTANT,
               CORRECT_REDSHIFT,
               OUTPUT_COORDINATE_FRAME,
               OUTPUT_EQUINOX,
               SORT_OUTPUT_BY)
from . import NED_SERVER, NED_TIMEOUT

__all__ = ["Ned"]

class Ned(BaseQuery):
    #make configurable
    BASE_URL = NED_SERVER()
    OBJ_SEARCH_URL = BASE_URL + 'nph-objsearch'
    ALL_SKY_URL = BASE_URL + 'nph-allsky'
    DATA_SEARCH_URL = BASE_URL + 'nph-datasearch'
    IMG_DATA_URL = BASE_URL + 'imgdata'
    SPECTRA_URL = BASE_URL + 'NEDspectra'
    TIMEOUT = NED_TIMEOUT()
    Options = namedtuple('Options', ('display_name', 'cgi_name'))

    PHOTOMETRY_OUT = {1 : Options('Data as Published and Homogenized (mJy)', 'bot'),
                      2 : Options('Data as Published', 'pub'),
                      3 : Options('Homogenized Units (mJy)', 'mjy')}

    @class_or_instance
    def query_object(self, object_name, get_query_payload=False, verbose=False):
        """
        Queries objects by name from the NED Service and returns the Main Source Table.

        Parameters
        ----------
        object_name : str
            name of the identifier to query.
        get_query_payload : bool, optional
            if set to `True` then returns the dictionary sent as the HTTP request.
            Defaults to `False`
        verbose : bool, optional.
            When set to `True` displays warnings if the returned VOTable does not
            conform to the standard. Defaults to `False`.

        Returns
        -------
        result : `astropy.table.Table`
            The result of the query as an `astropy.table.Table` object.

        """
        # for NED's object by name
        response = self.query_object_async(object_name, get_query_payload=get_query_payload)
        if get_query_payload:
            return response
        result = self._parse_result(response, verbose=verbose)
        return result

    @class_or_instance
    def query_object_async(self, object_name, get_query_payload=False):
        """
        Serves the same purpose as `Ned.query_object` but returns the raw HTTP response rather
        than the `astropy.table.Table` object.

        Parameters
        ----------
        object_name : str
            name of the identifier to query.
        get_query_payload : bool, optional
            if set to `True` then returns the dictionary sent as the HTTP request.
            Defaults to `False`

        Returns
        -------
        response : `requests.Response`
            The HTTP response returned from the service

        """
        request_payload = self._request_payload_init()
        self._set_input_options(request_payload)
        self._set_output_options(request_payload)
        request_payload['objname'] = object_name
        if get_query_payload:
            return request_payload
        response = commons.send_request(Ned.OBJ_SEARCH_URL, request_payload, Ned.TIMEOUT, request_type='GET')
        return response

    @class_or_instance
    def query_region(self, coordinates, radius= 1 * u.arcmin, equinox='J2000.0', get_query_payload=False,
                     verbose=False):
        """
        Used to query a region around a known identifier or given coordinates. Equivalent to
        the near position and near name queries from the Ned web interface.

        Parameters
        ----------
        coordinates : str or `astropy.coordinates` object
            The target around which to search. It may be specified as a string
            in which case it is resolved using online services or as the appropriate
            `astropy.coordinates` object. ICRS coordinates may also be entered as strings
            as specified in the `astropy.coordinates` module.
        radius : str or `astropy.units.Quantity` object, optional
            The string must be parsable by `astropy.coordinates.Angle`. The appropriate
            `Quantity` object from `astropy.units` may also be used. Defaults to 1 arcmin.
        equinox : str, optional
            The equinox may be either J2000.0 or B1950.0. Defaults to J2000.0
        get_query_payload : bool, optional
            if set to `True` then returns the dictionary sent as the HTTP request.
            Defaults to `False`.
        verbose : bool, optional.
            When set to `True` displays warnings if the returned VOTable does not
            conform to the standard. Defaults to `False`.

        Returns
        -------
        result : `astropy.table.Table`
            The result of the query as an `astropy.table.Table` object.
        """
        # for NED's object near name/ near region
        response = self.query_region_async(coordinates, radius=radius, equinox=equinox,
                                           get_query_payload=get_query_payload)
        if get_query_payload:
            return response
        result = self._parse_result(response, verbose=verbose)
        return result

    @class_or_instance
    def query_region_async(self, coordinates, radius= 1 * u.arcmin, equinox='J2000.0', get_query_payload=False):
        """
        Serves the same purpose as `Ned.query_region` but returns the raw HTTP response rather
        than the `astropy.table.Table` object.

        Parameters
        ----------
        coordinates : str or `astropy.coordinates` object
            The target around which to search. It may be specified as a string
            in which case it is resolved using online services or as the appropriate
            `astropy.coordinates` object. ICRS coordinates may also be entered as strings
            as specified in the `astropy.coordinates` module.
        radius : str or `astropy.units.Quantity` object, optional
            The string must be parsable by `astropy.coordinates.Angle`. The appropriate
            `Quantity` object from `astropy.units` may also be used. Defaults to 1 arcmin.
        equinox : str, optional
            The equinox may be either J2000.0 or B1950.0. Defaults to J2000.0
        get_query_payload : bool, optional
            if set to `True` then returns the dictionary sent as the HTTP request.
            Defaults to `False`.

        Returns
        -------
        response : `requests.Response`
            The HTTP response returned from the service
        """
        request_payload = self._request_payload_init()
        self._set_input_options(request_payload)
        self._set_output_options(request_payload)
        # if its a name then query near name
        if _is_name(coordinates):
            request_payload['objname'] = coordinates
            request_payload['search_type'] = 'Near Name Search'
        else:
            try:
                c = commons.parse_coordinates(coordinates)
                if isinstance(c, coord.GalacticCoordinates):
                    request_payload['in_csys'] = 'Galactic'
                    request_payload['lon'] = c.lonangle.degrees
                    request_payload['lat'] = c.latangle.degrees
                # for any other, convert to ICRS and send
                else:
                    request_payload['in_csys'] = 'Equatorial'
                    request_payload['lon'] = c.icrs.ra.format(u.hour)
                    request_payload['lat'] = c.icrs.dec.format(u.degree)
                request_payload['search_type'] = 'Near Position Search'
                request_payload['in_equinox'] = equinox
                request_payload['radius'] = _parse_radius(radius)
            except (u.UnitsException, TypeError):
                raise TypeError("Coordinates not specified correctly")
        if get_query_payload:
            return request_payload
        response = commons.send_request(Ned.OBJ_SEARCH_URL, request_payload, Ned.TIMEOUT, request_type='GET')
        return response

    @class_or_instance
    def query_region_iau(self, iau_name, frame='Equatorial', equinox='B1950.0',
                         get_query_payload=False, verbose=False):
        """
        Used to query the Ned service via the IAU name. Equivalent to the IAU format
        queries of the Web interface.

        Parameters
        ----------
        iau_name : str
            IAU coordinate-based name of target on which search is centered. Definition of IAU coordinates at
            http://cdsweb.u-strasbg.fr/Dic/iau-spec.html.
        frame : str, optional
            May be one of 'Equatorial', 'Ecliptic', 'Galactic', 'SuperGalactic'.
            Defaults to 'Equatorial'.
        equinox : str, optional
            The equinox may be one of J2000.0 or B1950.0. Defaults to B1950.0
        get_query_payload : bool, optional
            if set to `True` then returns the dictionary sent as the HTTP request.
            Defaults to `False`
        verbose : bool, optional.
            When set to `True` displays warnings if the returned VOTable does not
            conform to the standard. Defaults to `False`.

        Returns
        -------
        result : `astropy.table.Table`
            The result of the query as an `astropy.table.Table` object.

        """
        response = self.query_region_iau_async(iau_name, frame='Equatorial',
                                               equinox='B1950.0', get_query_payload=get_query_payload)
        if get_query_payload:
            return response
        result = self._parse_result(response, verbose=verbose)
        return result

    @class_or_instance
    def query_region_iau_async(self, iau_name, frame='Equatorial', equinox='B1950.0',
                         get_query_payload=False):
        """
        Serves the same purpose as `Ned.query_region_iau` but returns the raw HTTP response rather
        than the `astropy.table.Table` object.

        Parameters
        ----------
        iau_name : str
            IAU coordinate-based name of target on which search is centered. Definition of IAU coordinates at
            http://cdsweb.u-strasbg.fr/Dic/iau-spec.html.
        frame : str, optional
            May be one of 'Equatorial', 'Ecliptic', 'Galactic', 'SuperGalactic'.
            Defaults to 'Equatorial'.
        equinox : str, optional
            The equinox may be one of J2000.0 or B1950.0. Defaults to B1950.0
        get_query_payload : bool, optional
            if set to `True` then returns the dictionary sent as the HTTP request.
            Defaults to `False`

        Returns
        -------
        response : `requests.Response`
            The HTTP response returned from the service.
        """
        request_payload = self._request_payload_init()
        self._set_input_options(request_payload)
        self._set_output_options(request_payload)
        request_payload['search_type'] = 'IAU Search'
        request_payload['iau_name'] = iau_name
        request_payload['in_csys'] = frame
        request_payload['in_equinox'] = equinox
        if get_query_payload:
            return request_payload
        response = commons.send_request(Ned.OBJ_SEARCH_URL, request_payload, Ned.TIMEOUT, request_type='GET')
        return response

    @class_or_instance
    def query_refcode(self, refcode, get_query_payload=False, verbose=False):
        """
        Used to retrieve all objects contained in a particular reference. Equivalent
        to by refcode queries of the web interface.

        Parameters
        ----------
        refcode : str
            19 digit reference code.  Example: 1997A&A...323...31K.
        get_query_payload : bool, optional
            if set to `True` then returns the dictionary sent as the HTTP request.
            Defaults to `False`.
        verbose : bool, optional.
            When set to `True` displays warnings if the returned VOTable does not
            conform to the standard. Defaults to `False`.

        Returns
        -------
        result : `astropy.table.Table`
            The result of the query as an `astropy.table.Table` object.

        """
        response = self.query_refcode_async(refcode, get_query_payload=get_query_payload)
        if get_query_payload:
            return response
        result = self._parse_result(response, verbose=verbose)
        return result

    @class_or_instance
    def query_refcode_async(self, refcode, get_query_payload=False):
        """
        Serves the same purpose as `Ned.query_region` but returns the raw HTTP response rather
        than the `astropy.table.Table` object.

        Parameters
        ----------
        refcode : str
            19 digit reference code.  Example: 1997A&A...323...31K.
        get_query_payload : bool, optional
            if set to `True` then returns the dictionary sent as the HTTP request.
            Defaults to `False`.

        Returns
        -------
        response : `requests.Response`
            The HTTP response returned from the service.
        """
        request_payload = self._request_payload_init()
        self._set_input_options(request_payload)
        self._set_output_options(request_payload)
        request_payload['search_type'] = 'Search'
        request_payload['refcode'] = refcode
        if get_query_payload:
            return request_payload
        response = commons.send_request(Ned.OBJ_SEARCH_URL, request_payload, Ned.TIMEOUT, request_type='GET')
        return response

    @class_or_instance
    def get_images(self, object_name, get_query_payload=False):
        """
        Query function to fetch FITS images for a given identifier.

        Parameters
        ----------
        object_name : str
            name of the identifier to query.
        get_query_payload : bool, optional
            if set to `True` then returns the dictionary sent as the HTTP request.
            Defaults to `False`

        Returns
        -------
        A list of `astropy.fits.HDUList` objects

        """
        readable_objs = self.get_images_async(object_name, get_query_payload=get_query_payload)
        if get_query_payload:
            return readable_objs
        return [fits.open(obj.__enter__(), ignore_missing_end=True) for obj in readable_objs]

    @class_or_instance
    def get_images_async(self, object_name, get_query_payload=False):
        """
        Serves the same purpose as `Ned.get_images` but returns file-handlers to
        the remote files rather than downloading them.

        Parameters
        ----------
        object_name : str
            name of the identifier to query.
        get_query_payload : bool, optional
            if set to `True` then returns the dictionary sent as the HTTP request.
            Defaults to `False`

        Returns
        --------
        A list of context-managers that yield readable file-like objects
        """
        image_urls = self.get_image_list(object_name, get_query_payload=get_query_payload)
        if get_query_payload:
            return image_urls
        return [aud.get_readable_fileobj(U) for U in image_urls]

    @class_or_instance
    def get_spectra(self, object_name, get_query_payload=False):
        """
        Query function to fetch FITS files of spectra for a given identifier.

        Parameters
        ----------
        object_name : str
            name of the identifier to query.
        get_query_payload : bool, optional
            if set to `True` then returns the dictionary sent as the HTTP request.
            Defaults to `False`

        Returns
        -------
        A list of `astropy.fits.HDUList` objects

        """
        readable_objs = self.get_spectra_async(object_name, get_query_payload=get_query_payload)
        if get_query_payload:
            return readable_objs
        return [fits.open(obj.__enter__(), ignore_missing_end=True) for obj in readable_objs]

    @class_or_instance
    def get_spectra_async(self, object_name, get_query_payload=False):
        """
        Serves the same purpose as `Ned.get_spectra` but returns file-handlers to
        the remote files rather than downloading them.

        Parameters
        ----------
        object_name : str
            name of the identifier to query.
        get_query_payload : bool, optional
            if set to `True` then returns the dictionary sent as the HTTP request.
            Defaults to `False`

        Returns
        --------
        A list of context-managers that yield readable file-like objects
        """
        image_urls = self.get_image_list(object_name, item='spectra', get_query_payload=get_query_payload)
        if get_query_payload:
            return image_urls
        return [aud.get_readable_fileobj(U) for U in image_urls]

    @class_or_instance
    def get_image_list(self, object_name, item='image', get_query_payload=False):
        """
        Helper function that returns a list of urls from which to download the FITS images.

        Parameters
        ----------
        object_name : str
            name of the identifier to query.
        get_query_payload : bool, optional
            if set to `True` then returns the dictionary sent as the HTTP request.
            Defaults to `False`
        item : str, optional
            Can be either 'image' or 'spectra'. Defaults to 'image'.
            Required to decide the right URL to query.

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
        if get_query_payload:
            return request_payload
        url = Ned.SPECTRA_URL if item == 'spectra' else Ned.IMG_DATA_URL
        response = commons.send_request(url, request_payload, Ned.TIMEOUT, request_type='GET')
        return self.extract_image_urls(response.content)

    @class_or_instance
    def extract_image_urls(self, html_in):
        """
        Helper function that uses reges to extract the image urls from the given HTML.

        Parameters
        ----------
        html_in : str
            source from which the urls are to be extracted
        """
        base_url = 'http://ned.ipac.caltech.edu'
        pattern = re.compile('<a\s+href\s*?="?\s*?(.+?fits.gz)"?\s*?>\s*?(?:Retrieve|FITS)</a>', re.IGNORECASE)
        matched_urls = pattern.findall(html_in)
        url_list = [base_url + img_url for img_url in matched_urls]
        return url_list

    @class_or_instance
    def get_table(self, object_name, table='photometry', get_query_payload=False,
                  verbose=False, **kwargs):
        """
        Fetches the specified data table for the object from NED and returns it as
        an `astropy.table.Table`.

        Parameters
        ----------
        object_name : str
            name of the identifier to query.
        table : str, optional
            Must be one of ['photometry'|'positions'|'diameters'|'redshifts'|'references'|'object_notes'].
            Specifies the type of data-table that must be fetched for the given object. Defaults to
            'photometry'.
        output_table_format : int, [optional for photometry]
            specifies teh format of the output table. Must be 1, 2 or 3.
            Defaults to 1. These options stand for:
            (1) Data as Published and Homogenized (mJy)
            (2) Data as Published
            (3) Homogenized Units (mJy)
        from_year : int, [optional for references]
            4 digit year from which to get the references. Defaults to 1800
        to_year : int, [optional for references]
            4 digit year upto which to fetch the references. Defaults to the current year.
        extended_search : bool, [optional for references]
            If set to `True`, returns all objects beginning with the same identifier name.
            Defaults to `False`.
        get_query_payload : bool, optional
            if set to `True` then returns the dictionary sent as the HTTP request.
            Defaults to `False`.
        verbose : bool, optional.
            When set to `True` displays warnings if the returned VOTable does not
            conform to the standard. Defaults to `False`.

        Returns
        -------
        result : `astropy.table.Table`
            The result of the query as an `astropy.table.Table` object.

        Notes
        -----
        .. warning:: table=references does not work correctly (astropy issue#1266)
        """
        response = self.get_table_async(object_name, table=table, get_query_payload=get_query_payload,
                                        **kwargs)
        if get_query_payload:
            return response
        result = self._parse_result(response, verbose=verbose)
        return result

    @class_or_instance
    def get_table_async(self, object_name, table='photometry', get_query_payload=False, **kwargs):
        """
        Serves the same purpose as `Ned.query_region` but returns the raw HTTP response rather
        than the `astropy.table.Table` object.

        Parameters
        ----------
        object_name : str
            name of the identifier to query.
        table : str, optional
            Must be one of ['photometry'|'positions'|'diameters'|'redshifts'|'references'|'object_notes'].
            Specifies the type of data-table that must be fetched for the given object. Defaults to
            'photometry'.
        from_year : int, [optional for references]
            4 digit year from which to get the references. Defaults to 1800
        to_year : int, [optional for references]
            4 digit year upto which to fetch the references. Defaults to the current year.
        extended_search : bool, [optional for references]
            If set to `True`, returns all objects beginning with the same identifier name.
            Defaults to `False`.
        get_query_payload : bool, optional
            if set to `True` then returns the dictionary sent as the HTTP request.
            Defaults to `False`.

        Returns
        -------
        response : `requests.Response`
            The HTTP response returned from the service.
        """
        SEARCH_TYPE = dict(photometry='Photometry',
                           diameters='Diameters',
                           positions='Positions',
                           redshifts='Redshifts',
                           references='Reference',
                           object_notes='Notes')
        request_payload = dict(of='xml_main')
        request_payload['objname'] = object_name
        request_payload['search_type'] = SEARCH_TYPE[table]
        if table == 'photometry':
            output_table_format = 1
            request_payload['meas_type'] = Ned.PHOTOMETRY_OUT[output_table_format].cgi_name
        if table == 'references':
            request_payload['ref_extend'] = 'yes' if kwargs.get('extended_search', False) else 'no'
            request_payload['begin_year'] = kwargs.get('from_year', 1800)
            request_payload['end_year'] = kwargs.get('to_year', datetime.now().year)
        if get_query_payload:
            return request_payload
        response = commons.send_request(Ned.DATA_SEARCH_URL, request_payload, Ned.TIMEOUT, request_type='GET')
        return response


    @class_or_instance
    def _request_payload_init(self):
        request_payload = dict(of='xml_main')
        # common settings for all queries as per NED guidelines
        # for more see <http://ned.ipac.caltech.edu/help/guidelines_auto.html>
        request_payload['img_stamp'] = 'NO'
        request_payload['extend'] = 'no'
        request_payload['list_limit'] = 0
        return request_payload

    @class_or_instance
    def _set_input_options(self, request_payload):
        request_payload['hconst'] = HUBBLE_CONSTANT()
        request_payload['omegam'] = 0.27
        request_payload['omegav'] = 0.73
        request_payload['corr_z'] = CORRECT_REDSHIFT()

    @class_or_instance
    def _set_output_options(self, request_payload):
        request_payload['out_csys'] = OUTPUT_COORDINATE_FRAME()
        request_payload['out_equinox'] = OUTPUT_EQUINOX()
        request_payload['obj_sort'] = SORT_OUTPUT_BY()

    @class_or_instance
    def _parse_result(self, response, verbose=False):
        if not verbose:
            commons.suppress_vo_warnings()
        try:
            tf = tempfile.NamedTemporaryFile()
            tf.write(response.content.encode('utf-8'))
            tf.flush()
            table = Table.read(tf.name, format='votable')
            return table
        except Exception as ex:
            (is_valid, err_msg) = _check_ned_valid(response.content)
            if not is_valid:
                if err_msg:
                    print("The remote service returned the following error message.\nERROR: {err_msg}".format(err_msg=err_msg))
            else:
                print (str(ex))
                warnings.warn("Error in parsing Ned result. "
                     "Returning raw result instead.")
                return response.content

def _validate_keywords(kwds, kwd_dict_keys):
    values = [kwd.lower() for kwd in kwds]
    keys = [ key.lower() for key in kwd_dict_keys]
    for val in set(values) - set(keys):
            warnings.warn("{val} : No such keyword".format(val=val))
    valid_keys = [key for key in kwd_dict_keys if key.lower() in values]
    return valid_keys

def _parse_radius(radius):

    if isinstance(radius, u.Quantity) and radius.unit in u.deg.find_equivalent_units():
        radius_in_min = radius.to(u.arcmin).value
    # otherwise must be an Angle or be specified in hours...
    else:
        try:
            new_radius = commons.parse_radius(radius).degrees
            radius_in_min = u.Quantity(value=new_radius, unit=u.deg).to(u.arcmin).value
        except (u.UnitsException, coord.errors.UnitsError, AttributeError):
            raise u.UnitsException("Dimension not in proper units")
    return radius_in_min

def _is_name(coordinates):
    try:
        coord.ICRSCoordinates(coordinates)
        return False
    except ValueError:
        return True


def _check_ned_valid(str):

    # Routine assumes input is valid Table unless error parameter is found.
    retval = True
    errmsg = None
    strdom = parseString(str)
    p = strdom.getElementsByTagName('PARAM')

    if len(p) > 1:
        if 'name' in p[1].attributes.keys():
            n = p[1].attributes['name']
            errstr = n.value

            if errstr == 'Error':
                if 'value' in p[1].attributes.keys():
                    m = p[1].attributes['value']
                    errmsg = m.value
                retval = False

    return (retval, errmsg)
