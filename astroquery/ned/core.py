# Licensed under a 3-clause BSD style license - see LICENSE.rst
#uncomment after removing old code
#from __future__ import print_function

import urllib
import tempfile
from xml.dom.minidom import parseString
import astropy.utils.data as aud
from astropy.table import Table
#-------------------------------------------
import os
import re
import warnings
import json
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
# TODO remove this after debugging
import traceback
#__all__ = ["Ned"]

class Ned(BaseQuery):
    #make configurable
    BASE_URL = 'http://nedwww.ipac.caltech.edu/cgi-bin/'
    OBJ_SEARCH_URL = BASE_URL + 'nph-objsearch'
    ALL_SKY_URL = BASE_URL + 'nph-allsky'
    DATA_SEARCH_URL = BASE_URL + 'nph-datasearch'
    IMG_DATA_URL = BASE_URL + 'imgdata'
    REF_KWD_URL = BASE_URL + 'SearchRefsByObjectName'
    TIMEOUT = 60
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
        request_payload = self._args_to_payload(object_name, caller='query_object_async')
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

        request_payload = self._args_to_payload(coordinates, radius=radius, equinox=equinox, caller='query_region_async')
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
        request_payload = self._args_to_payload(iau_name, frame=frame, equinox=equinox, caller='query_region_iau_async')
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
        request_payload = self._args_to_payload(refcode, caller='query_refcode_async')
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
    def get_image_list(self, object_name, get_query_payload=False):
        """
        Helper function that returns a list of urls from which to download the FITS images.

        Parameters
        ----------
        object_name : str
            name of the identifier to query.
        get_query_payload : bool, optional
            if set to `True` then returns the dictionary sent as the HTTP request.
            Defaults to `False`

        Returns
        -------
        list of image urls
        """
        request_payload = self._args_to_payload(object_name, caller='get_image_list')
        if get_query_payload:
            return request_payload
        response = commons.send_request(Ned.IMG_DATA_URL, request_payload, Ned.TIMEOUT, request_type='GET')
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
        pattern = re.compile('<a\s+href\s*?=\s*?(.+?fits.gz)\s*?>\s*?Retrieve', re.IGNORECASE)
        matched_urls = pattern.findall(html_in)
        url_list = [base_url + img_url for img_url in matched_urls]
        return url_list

    @class_or_instance
    def get_photometry(self, object_name,
                       output_table_format=1,
                       get_query_payload=False,
                       verbose=False):
        """
        Retrieves the photometry data for the given identifier from NED.

        Parameters
        ----------
        object_name : str
            name of the identifier to query.
        output_table_format : int, optional
            specifies teh format of the output table. Must be 1, 2 or 3.
            Defaults to 1. These options stand for:
            (1) Data as Published and Homogenized (mJy)
            (2) Data as Published
            (3) Homogenized Units (mJy)
        error_bars : bool, optional.
            When `True` displays error-bars
        #maybe these SED plot options aren't actually required for this
        #should remove them?
        #error_bars, sed_x, sed_y and autoscale...
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
        response = self.get_photometry_async(object_name,
                       output_table_format=output_table_format,
                       get_query_payload=get_query_payload)
        if get_query_payload:
            return response
        result = self._parse_result(response, verbose=verbose)
        return result

    @class_or_instance
    def get_photometry_async(self, object_name,
                       output_table_format=1,
                       get_query_payload=False):
        """
        Serves the same purpose as `Ned.get_photometry` but returns the raw HTTP response rather
        than the `astropy.table.Table` object.

        Parameters
        ----------
        object_name : str
            name of the identifier to query.
        output_table_format : int, optional
            specifies teh format of the output table. Must be 1, 2 or 3.
            Defaults to 1. These options stand for:
            (1) Data as Published and Homogenized (mJy)
            (2) Data as Published
            (3) Homogenized Units (mJy)
        get_query_payload : bool, optional
            if set to `True` then returns the dictionary sent as the HTTP request.
            Defaults to `False`

        Returns
        -------
        response : `requests.Response`
            The HTTP response returned from the service.

        """
        request_payload = self._args_to_payload(object_name,
                       output_table_format=output_table_format,
                       caller='get_photometry_async')
        if get_query_payload:
            return request_payload
        response = commons.send_request(Ned.DATA_SEARCH_URL, request_payload, Ned.TIMEOUT, request_type='GET')
        return response

    @class_or_instance
    def get_redshifts(self, object_name, get_query_payload=False, verbose=False):
        """
        Query the redshifts for the given identifier

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
        response = self.get_redshifts_async(object_name, get_query_payload=get_query_payload)
        if get_query_payload:
            return response
        result = self._parse_result(response, verbose=verbose)
        return result

    @class_or_instance
    def get_redshifts_async(self, object_name, get_query_payload=False):
        """
        Serves the same purpose as `Ned.get_redshifts` but returns the raw HTTP response rather
        than the `astropy.table.Table` object.

        Parameters
        ----------
        object_name : str
            name of the identifier to query.
        get_query_payload : bool, optional
            if set to `True` then returns the dictionary sent as the HTTP request.
            Defaults to `False`.

        Returns
        -------
        response : `requests.Response`
            The HTTP response returned from the service.
        """
        request_payload = self._args_to_payload(object_name, caller='get_redshifts_async')
        if get_query_payload:
            return request_payload
        response = commons.send_request(Ned.DATA_SEARCH_URL, request_payload, Ned.TIMEOUT, request_type='GET')
        return response

    @class_or_instance
    def get_positions(self, object_name, get_query_payload=False, verbose=False):
        """
        Query the positions for the given identifier.

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
        response = self.get_positions_async(object_name, get_query_payload=get_query_payload)
        if get_query_payload:
            return response
        result = self._parse_result(response, verbose=verbose)
        return result

    @class_or_instance
    def get_positions_async(self, object_name, get_query_payload=False):
        """
        Serves the same purpose as `Ned.get_positions` but returns the raw HTTP response rather
        than the `astropy.table.Table` object.

        Parameters
        ----------
        object_name : str
            name of the identifier to query.
        get_query_payload : bool, optional
            if set to `True` then returns the dictionary sent as the HTTP request.
            Defaults to `False`.

        Returns
        -------
        response : `requests.Response`
            The HTTP response returned from the service.
        """
        request_payload = self._args_to_payload(object_name, caller='get_positions_async')
        if get_query_payload:
            return request_payload
        response = commons.send_request(Ned.DATA_SEARCH_URL, request_payload, Ned.TIMEOUT, request_type='GET')
        return response

    @class_or_instance
    def get_diameters(self, object_name, get_query_payload=False, verbose=False):
        """
        Query the diameters for the given identifier.

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
        response = self.get_diameters_async(object_name, get_query_payload=get_query_payload)
        if get_query_payload:
            return response
        result = self._parse_result(response, verbose=verbose)
        return result

    @class_or_instance
    def get_diameters_async(self, object_name, get_query_payload=False):
        """
        Serves the same purpose as `Ned.get_diameters` but returns the raw HTTP response rather
        than the `astropy.table.Table` object.

        Parameters
        ----------
        object_name : str
            name of the identifier to query.
        get_query_payload : bool, optional
            if set to `True` then returns the dictionary sent as the HTTP request.
            Defaults to `False`.

        Returns
        -------
        response : `requests.Response`
            The HTTP response returned from the service.
        """
        request_payload = self._args_to_payload(object_name, caller='get_diameters_async')
        if get_query_payload:
            return request_payload
        response = commons.send_request(Ned.DATA_SEARCH_URL, request_payload, Ned.TIMEOUT, request_type='GET')
        return response

    @class_or_instance
    def get_references(self, object_name, topical_keywords=None, data_content_keywords=None, get_query_payload=False, verbose=False,
                       from_year=1800, to_year=datetime.now().year, extended_search=False):
        """
        Returns the references that contain the given object. Supports searching by topical keywords
        from ARIBIB and data content keywords from NED.

        Parameters
        ----------
        object_name : str
            name of the identifier to query.
        topical_keywords : list of `str`, optional
            list of ARIBIB keywords on which to search.
            Defaults to `None`.
        data_content_keywords : list of `str`, optional
            list of NED data content keywords on which to search.
            Defaults to `None`.
        get_query_payload : bool, optional
            if set to `True` then returns the dictionary sent as the HTTP request.
            Defaults to `False`.
        verbose : bool, optional.
            When set to `True` displays warnings if the returned VOTable does not
            conform to the standard. Defaults to `False`.
        from_year : int, optional
            4 digit year from which to get the references. Defaults to 1800
        to_year : int, optional
            4 digit year upto which to fetch the references. Defaults to the current year.
        extended_search : bool, optional
            If set to `True`, returns all objects beginning with the same identifier name.
            Defaults to `False`.
        """
        response = self.get_references_async(object_name, topical_keywords=topical_keywords,
                                             data_content_keywords=data_content_keywords,
                                             from_year=from_year,
                                             to_year=to_year,
                                             extended_search=extended_search,
                                             get_query_payload=get_query_payload)
        if get_query_payload:
            return response
        result = self._parse_result(response, verbose=verbose)
        return result

    @class_or_instance
    def get_references_async(self, object_name, topical_keywords=None, data_content_keywords=None, get_query_payload=False,
                             from_year=1800, to_year=datetime.now().year, extended_search=False):
        """
        Serves the same purpose as `Ned.get_references` but returns the raw HTTP response rather
        than the `astropy.table.Table` object.

        Parameters
        ----------
        object_name : str
            name of the identifier to query.
        topical_keywords : list of `str`, optional
            list of ARIBIB keywords on which to search.
            Defaults to `None`.
        data_content_keywords : list of `str`, optional
            list of NED data content keywords on which to search.
            Defaults to `None`.
        get_query_payload : bool, optional
            if set to `True` then returns the dictionary sent as the HTTP request.
            Defaults to `False`.
        from_year : int, optional
            4 digit year from which to get the references. Defaults to 1800
        to_year : int, optional
            4 digit year upto which to fetch the references. Defaults to the current year.
        extended_search : bool, optional
            If set to `True`, returns all objects beginning with the same identifier name.
            Defaults to `False`.

        Returns
        -------
        response : `requests.Response`
            The HTTP response returned from the service.

        """
        request_payload = self._args_to_payload(object_name, topical_keywords=topical_keywords,
                                             data_content_keywords=data_content_keywords,
                                             from_year=from_year,
                                             to_year=to_year,
                                             extended_search=extended_search,
                                             caller='get_references_async')
        if get_query_payload:
            return request_payload
        if topical_keywords or data_content_keywords is not None:
            url = Ned.REF_KWD_URL
        else:
            url = Ned.DATA_SEARCH_URL
        response = commons.send_request(url, request_payload, Ned.TIMEOUT, request_type='GET')
        return response

    @class_or_instance
    def get_object_notes(self, object_name, get_query_payload=False, verbose=False):
        """
        Returns object notes for the given identifier.

        Parameters
        ----------
        object_name : str
            name of the identifier to query.
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
        response = self.get_object_notes_async(object_name,
                                               get_query_payload=get_query_payload)
        if get_query_payload:
            return response
        result = self._parse_result(response, verbose=verbose)
        return result

    @class_or_instance
    def get_object_notes_async(self, object_name, get_query_payload=False):
        """
        Serves the same purpose as `Ned.get_object_notes` but returns the raw HTTP response rather
        than the `astropy.table.Table` object.

        Parameters
        ----------
        object_name : str
            name of the identifier to query.
        get_query_payload : bool, optional
            if set to `True` then returns the dictionary sent as the HTTP request.
            Defaults to `False`.

        Returns
        -------
        response : `requests.Response`
            The HTTP response returned from the service.
        """
        request_payload = self._args_to_payload(object_name,
                                                caller='get_object_notes_async')
        if get_query_payload:
            return request_payload
        response = commons.send_request(Ned.DATA_SEARCH_URL, request_payload, Ned.TIMEOUT, request_type='GET')
        return response

    @class_or_instance
    def _args_to_payload(self, *args, **kwargs):
        caller = kwargs['caller']
        del kwargs['caller']
        request_payload = {}
        # common settings for all queries as per NED guidelines
        # for more see <http://ned.ipac.caltech.edu/help/guidelines_auto.html>
        request_payload['img_stamp'] = 'NO'
        request_payload['extend'] = 'no'
        request_payload['list_limit'] = 0
        # set input and output options for some queries
        if caller in ['query_object_async',
                      'query_region_async',
                      'query_region_iau_async',
                      'query_refcode_async',
                      'query_allsky_async']:
            # input settings
            request_payload['hconst'] = HUBBLE_CONSTANT()
            request_payload['omegam'] = 0.27
            request_payload['omegav'] = 0.73
            request_payload['corr_z'] = CORRECT_REDSHIFT()
            # output settings
            request_payload['out_csys'] = OUTPUT_COORDINATE_FRAME()
            request_payload['out_equinox'] = OUTPUT_EQUINOX()
            request_payload['obj_sort'] = SORT_OUTPUT_BY()
        # all queries other than image queries should return votable
        if caller != 'get_image_list':
             request_payload['of'] = 'xml_main'
        if caller == 'query_object_async':
            request_payload['objname'] = args[0]
        elif caller == 'query_region_async':
            # if its a name then query near name
            coordinates = args[0]
            try:
                coord.name_resolve.get_icrs_coordinates(coordinates)
                request_payload['objname'] = coordinates
                request_payload['search_type'] = 'Near Name Search'
            # otherwise treat it as a coordinate
            except coord.name_resolve.NameResolveError:
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
                    request_payload['in_equinox'] = kwargs['equinox']
                    request_payload['radius'] = _parse_radius(kwargs['radius'])
                except (u.UnitsException, TypeError):
                    traceback.print_exc()
                    raise TypeError("Coordinates not specified correctly")
        elif caller == 'query_region_iau_async':
            request_payload['search_type'] = 'IAU Search'
            request_payload['iau_name'] = args[0]
            request_payload['in_csys'] = kwargs['frame']
            request_payload['in_equinox'] = kwargs['equinox']
        elif caller == 'query_refcode_async':
            request_payload['search_type'] = 'Search'
            request_payload['refcode'] = args[0]
        elif caller == 'get_image_list':
            request_payload['objname'] = args[0]
        elif caller == 'get_photometry_async':
            request_payload['objname'] = args[0]
            request_payload['meas_type'] = Ned.PHOTOMETRY_OUT[kwargs['output_table_format']].cgi_name
            request_payload['ebars_spec'] = 'ebars' if kwargs['error_bars'] else 'noebars'
            request_payload['label_spec'] = 'yes' if kwargs['point_labels'] else 'no'
            request_payload['x_spec'] = Ned.SED_X[kwargs['sed_x']].cgi_name
            request_payload['y_spec'] = Ned.SED_Y[kwargs['sed_y']].cgi_name
            request_payload['xr'] = -2 if kwargs['autoscale'] else -1
            request_payload['search_type'] = 'Photometry'
        elif caller == 'get_redshifts_async':
            request_payload['objname'] = args[0]
            request_payload['search_type'] = 'Redshifts'
        elif caller == 'get_positions_async':
            request_payload['objname'] = args[0]
            request_payload['search_type'] = 'Positions'
        elif caller == 'get_diameters_async':
            request_payload['objname'] = args[0]
            request_payload['search_type'] = 'Diameters'
        elif caller == 'get_references_async':
            request_payload['objname'] = args[0]
            request_payload['ref_extend'] = 'yes' if kwargs['extended_search'] else 'no'
            request_payload['begin_year'] = kwargs['from_year']
            request_payload['end_year'] = kwargs['to_year']
            request_payload['search_type'] = 'Search References (With Keywords)' if kwargs.get('topical_keywords') or kwargs.get('data_content_keywords') else 'Reference'
            if kwargs.get('topical_keywords') is not None:
                file_name = aud.get_pkg_data_filename(os.path.join("data", "keywords_dict.json"))
                with open(file_name, mode="r") as f:
                    keywords_dict = json.load(f)
                valid_keywords = _validate_keywords(kwargs['topical_keywords'], keywords_dict.keys())
                for kwd in valid_keywords:
                    request_payload[keywords_dict[kwd]] = kwd
                request_payload['arib_filter'] = 'yes'
            if kwargs.get('data_content_keywords') is not None:
                all_data_keywords = ["diameters", "pofg", "images", "kinematics",
                                     "notes", "photometry", "positions", "spectroscopy"]
                valid_keywords = _validate_keywords(kwargs['data_content_keywords'], all_data_keywords)
                for kwd in valid_keywords:
                    request_payload[kwd] = 'ON'
                request_payload['filters'] = 'yes'
        elif caller == 'get_object_notes_async':
            request_payload['objname'] = args[0]
            request_payload['search_type'] = 'Notes'
        return request_payload

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
        except Exception:
            (is_valid, err_msg) = _check_ned_valid(response.content)
            if not is_valid:
                if err_msg:
                    print("The remote service returned the following error message.\nERROR: {err_msg}".format(err_msg=err_msg))
                else:
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
#--------------
def query_ned_by_objname(objname='M31',
                         root_url='http://nedwww.ipac.caltech.edu/cgi-bin/nph-objsearch',
                         TID=0):
    """
    Acquire a table of NED basic data for a celestial object

    The table ID number (tid) determines the data product returned from NED:

    Parameters
    ----------
    tid=0 : Main Information Table for object (default)
    tid=1 : Table of all names in NED for object
        All aliases available from the NED name resolver service
    tid=2 : Table of Position Data in NED for object
        Data available in variety of coordinate systems and epochs
    tid=3 : Table of Derived Values in NED for object
        Includes velocities, distances, distance moduli, cosmology dependent parameters
    tid=4 : Table of Basic Data in NED for object.
        .. warning:: Doesn't currently work; error of "two fields with the same name"
    tid=5 : Table of External Links for the object
        Vizier, IRSA, Simbad, etc. Some links appear to be deprecated

    """

    # Create dictionary of search parameters, then parse into query URL
    request_dict = {'extend':'no','of':'xml_all','objname':objname}
    query_url = "%s?%s" % (root_url,urllib.urlencode(request_dict))

    # Retrieve handler object from NED
    # Write the data to a file, flush it to get the proper VO table format, and read it into an Astropy table
    with aud.get_readable_fileobj(query_url) as f:
        R = f.read().encode('utf-8')

    """
    There should be 91 columns in the Derived Values table, based on the
    headers. The data here are cosmological values based on the redshift.

    For non-extragalactic objects, these are all blank; however, there seems to
    be an error in the tables in that only 88 blank cells are supplied, instead
    of the required 91. This results in an error when astropy.io.votable tries
    to parse the XML string. This crude kluge adds empty cells to the table so
    it can be read properly.
    """

    tid_derived = 3
    tdparts = R.split(b'<TABLEDATA>',tid_derived+1)
    if len(tdparts) > tid_derived+1:
        tdind = len(R) - len(tdparts[-1]) - len(b'<TABLEDATA>')
        rseg = R[tdind:tdind+R[tdind:].find(b'</TABLEDATA>')]
        cellcount = rseg.count(b'TD')/2
        if cellcount < 91:
            nrepeats = 91 - cellcount
            newseg = rseg[:-6] + b'<TD></TD>'*nrepeats + rseg[-6:]
            newR = R[:tdind] + newseg + R[tdind+R[tdind:].find(b'</TABLEDATA>'):]
            R = newR

    # Check to see if NED returns a valid query

    validtable = check_ned_valid(R)

    if validtable:
        tf = tempfile.NamedTemporaryFile()
        tf.write(R)
        tf.file.flush()
        t = Table.read(tf.name, format='votable', table_id=TID)

        return t

    else:
        print ""
        print "The object name that you submitted is not currently recognized"
        print "by the NED name interpreter."
        print ""
        print "In general, naming conventions employ a prefix (usually an"
        print "acronym for the first author(s) or the survey name) followed"
        print "by a numerical string based on a tabular sequence or a position"
        print "on the sky. For more specifics, see the document at"
        print "http://vizier.u-strasbg.fr/Dic/iau-spec.htx"
        print ""

        return None

def query_ned_nearname(objname='M31',radius=2.0,
        root_url='http://nedwww.ipac.caltech.edu/cgi-bin/nph-objsearch'):
    """
    Query objects within a specified angular distance of another target

    Parameters
    ----------
    objname : str
        target on which the position search is centered
    radius : float
        radius (in arcminutes) within which to search

    Returns
    -------
    NED_MainTable with the following information for each target within the
    search radius.

    Examples
    --------
    >>> print query_ned_nearname()

    ::

        +----------------------+---------+---------+--------+
        |                 Name |    Unit |    Type | Format |
        +======================+=========+=========+========+
        |                  No. |    None |   int32 |    12i |
        |          Object Name |    None |    |S30 |    30s |
        |              RA(deg) | degrees | float64 | 25.17e |
        |             DEC(deg) | degrees | float64 | 25.17e |
        |                 Type |    None |     |S6 |     6s |
        |             Velocity |  km/sec | float64 | 25.17e |
        |             Redshift |    None | float64 | 25.17e |
        |        Redshift Flag |    None |     |S4 |     4s |
        | Magnitude and Filter |    None |     |S5 |     5s |
        |    Distance (arcmin) |  arcmin | float64 | 25.17e |
        |           References |    None |   int32 |    12i |
        |                Notes |    None |   int32 |    12i |
        |    Photometry Points |    None |   int32 |    12i |
        |            Positions |    None |   int32 |    12i |
        |      Redshift Points |    None |   int32 |    12i |
        |      Diameter Points |    None |   int32 |    12i |
        |         Associations |    None |   int32 |    12i |
        +----------------------+---------+---------+--------+


    """

    # Create dictionary of search parameters, then parse into query URL
    request_dict = {'search_type':'Near Name Search','radius':'%f' % radius,'of':'xml_main','objname':objname}
    query_url = "%s?%s" % (root_url,urllib.urlencode(request_dict))

    # Retrieve handler object from NED
    # Write the data to a file, flush it to get the proper VO table format, and
    # read it into an Astropy table
    with aud.get_readable_fileobj(query_url) as f:
        R = f.read().encode('utf-8')

    validtable = check_ned_valid(R)

    if validtable:
        tf = tempfile.NamedTemporaryFile()
        tf.write(R)
        tf.file.flush()
        t = Table.read(tf.name, format='votable')

        # Return Astropy Table

        return t

    else:
        print ""
        print "The object name that you submitted is not currently recognized"
        print "by the NED name interpreter."
        print ""
        print "In general, naming conventions employ a prefix (usually an"
        print "acronym for the first author(s) or the survey name) followed"
        print "by a numerical string based on a tabular sequence or a position"
        print "on the sky. For more specifics, see the document at"
        print "http://vizier.u-strasbg.fr/Dic/iau-spec.htx"
        print ""

        return None

def query_ned_near_iauname(iauname='1234-423',radius=2.0,
        root_url='http://nedwww.ipac.caltech.edu/cgi-bin/nph-objsearch'):
    """
    Query objects near another target based on IAU name (truncated coordinates).

    Parameters
    ----------
    iauname : str
        IAU coordinate-based name of target on which search is centered. Definition of IAU coordinates at http://cdsweb.u-strasbg.fr/Dic/iau-spec.html
    radius : str
        radius (in arcminutes) within which to search

    Returns
    -------
    NED_MainTable with the following information for each target within the
    search radius

    Examples
    --------

    ::

        -----------------------------------------------------
        |                 Name |    Unit |    Type | Format |
        -----------------------------------------------------
        |                  No. |    None |   int32 |    12i |
        |          Object Name |    None |    |S30 |    30s |
        |              RA(deg) | degrees | float64 | 25.17e |
        |             DEC(deg) | degrees | float64 | 25.17e |
        |                 Type |    None |     |S6 |     6s |
        |             Velocity |  km/sec | float64 | 25.17e |
        |             Redshift |    None | float64 | 25.17e |
        |        Redshift Flag |    None |     |S4 |     4s |
        | Magnitude and Filter |    None |     |S5 |     5s |
        |    Distance (arcmin) |  arcmin | float64 | 25.17e |
        |           References |    None |   int32 |    12i |
        |                Notes |    None |   int32 |    12i |
        |    Photometry Points |    None |   int32 |    12i |
        |            Positions |    None |   int32 |    12i |
        |      Redshift Points |    None |   int32 |    12i |
        |      Diameter Points |    None |   int32 |    12i |
        |         Associations |    None |   int32 |    12i |
        -----------------------------------------------------

    """

    # Create dictionary of search parameters, then parse into query URL
    request_dict = {'search_type':'IAU Search','iau_name':iauname,'radius':'%f' % radius,'of':'xml_main'}
    query_url = "%s?%s" % (root_url,urllib.urlencode(request_dict))

    # Retrieve handler object from NED
    # Write the data to a file, flush it to get the proper VO table format, and read it into an Astropy table
    with aud.get_readable_fileobj(query_url) as f:
        R = f.read().encode('utf-8')

    validtable = check_ned_valid(R)

    if validtable:
        tf = tempfile.NamedTemporaryFile()
        tf.write(R)
        tf.file.flush()
        t = Table.read(tf.name, format='votable')

        # Return Astropy table

        return t

    else:
        print ""
        print "The object name that you submitted is not currently recognized"
        print "by the NED name interpreter."
        print ""
        print "This function requires an IAU coordinate-based name of the target on which search is centered."
        print "Example: query_ned_near_iauname(iauname = '1234-423')"
        print "The definition of IAU coordinates is found at http://cdsweb.u-strasbg.fr/Dic/iau-spec.html"
        print ""
        print "In general, naming conventions employ a prefix (usually an"
        print "acronym for the first author(s) or the survey name) followed"
        print "by a numerical string based on a tabular sequence or a position"
        print "on the sky. For more specifics, see the document at"
        print "http://vizier.u-strasbg.fr/Dic/iau-spec.htx"
        print ""

        return None

def query_ned_by_refcode(refcode='2011ApJS..193...18W',
        root_url='http://nedwww.ipac.caltech.edu/cgi-bin/nph-objsearch'):
    """
    Query NED for basic data on objects cited in a particular reference.

    Parameters
    ----------
    refcode : str
        19-digit reference code for journal article.
        Example: 2011ApJS..193...18W is the reference code for Willett et al. (2011), ApJS, 193, 18

    Returns
    -------
    NED_MainTable with the following information for each target within the search radius

    Examples
    --------

    ::

        -----------------------------------------------------
        |                 Name |    Unit |    Type | Format |
        -----------------------------------------------------
        |                  No. |    None |   int32 |    12i |
        |          Object Name |    None |    |S30 |    30s |
        |              RA(deg) | degrees | float64 | 25.17e |
        |             DEC(deg) | degrees | float64 | 25.17e |
        |                 Type |    None |     |S6 |     6s |
        |             Velocity |  km/sec | float64 | 25.17e |
        |             Redshift |    None | float64 | 25.17e |
        |        Redshift Flag |    None |     |S4 |     4s |
        | Magnitude and Filter |    None |     |S5 |     5s |
        |    Distance (arcmin) |  arcmin | float64 | 25.17e |
        |           References |    None |   int32 |    12i |
        |                Notes |    None |   int32 |    12i |
        |    Photometry Points |    None |   int32 |    12i |
        |            Positions |    None |   int32 |    12i |
        |      Redshift Points |    None |   int32 |    12i |
        |      Diameter Points |    None |   int32 |    12i |
        |         Associations |    None |   int32 |    12i |
        -----------------------------------------------------

    """

    # Create dictionary of search parameters, then parse into query URL
    request_dict = {'search_type':'Search','refcode':refcode,'of':'xml_main'}
    query_url = "%s?%s" % (root_url,urllib.urlencode(request_dict))

    # Check to see if NED returns a valid query
    # Write the data to a file, flush it to get the proper VO table format, and read it into an Astropy table
    with aud.get_readable_fileobj(query_url) as f:
        R = f.read().encode('utf-8')

    try:
        parseString(R)
    except:
        print ""
        print "The refcode that you submitted was not recognized by the NED interpreter."
        print ""
        print "refcode: %s" % refcode
        print ""
        print "A valid refcode is a 19-digit string for a unique journal article."
        print "Example: 2011ApJS..193...18W is the refcode for Willett et al. (2011), ApJS, 193, 18"
        print ""

        return None

    tf = tempfile.NamedTemporaryFile()
    tf.write(R)
    tf.file.flush()
    t = Table.read(tf.name, format='votable')

    # Return Astropy Table

    return t

def query_ned_names(objname='M31',
        root_url='http://nedwww.ipac.caltech.edu/cgi-bin/nph-objsearch'):
    """
    Retrieve multi-wavelength cross-IDs with corresponding object types for a particular target
        Equivalent to query_ned_by_objname(objname,tid=1)

    keywords:
        objname - astronomical object to search for

    Returns
    -------
    NED_NamesTable with the following information

    Examples
    --------

    ::

        ----------------------------------
        |    Name | Unit | Type | Format |
        ----------------------------------
        | objname | None | |S30 |    30s |
        | objtype | None |  |S6 |     6s |
        ----------------------------------

    """

    # Create dictionary of search parameters, then parse into query URL
    request_dict = {'extend':'no','of':'xml_names','objname':objname}
    query_url = "%s?%s" % (root_url,urllib.urlencode(request_dict))

    # Check to see if NED returns a valid query
    # Write the data to a file, flush it to get the proper VO table format, and read it into an Astropy table
    with aud.get_readable_fileobj(query_url) as f:
        R = f.read().encode('utf-8')

    validtable = check_ned_valid(R)

    if validtable:
        tf = tempfile.NamedTemporaryFile()
        tf.write(R)
        tf.file.flush()
        t = Table.read(tf.name, format='votable')

        # Return Astropy Table

        return t

    else:
        print ""
        print "The object name that you submitted is not currently recognized"
        print "by the NED name interpreter."
        print ""
        print "In general, naming conventions employ a prefix (usually an"
        print "acronym for the first author(s) or the survey name) followed"
        print "by a numerical string based on a tabular sequence or a position"
        print "on the sky. For more specifics, see the document at"
        print "http://vizier.u-strasbg.fr/Dic/iau-spec.htx"
        print ""

        return None

def query_ned_basic_posn(objname='M31',
        root_url='http://nedwww.ipac.caltech.edu/cgi-bin/nph-objsearch'):
    """
    Retrieve best available position data from NED for a particular target
        Equivalent to query_ned_by_objname(objname,tid=2)

    keywords:
        objname - astronomical object to search for

    Returns
    -------
    NED_PositionDataTable with the following information:

    Examples
    --------

    ::

        -----------------------------------------------------------
        |                    Name |       Unit |    Type | Format |
        -----------------------------------------------------------
        |                 pos_ref |       None |    |S19 |    19s |
        |      pos_ra_equ_B1950_d |    degrees | float64 | 25.17e |
        |     pos_dec_equ_B1950_d |    degrees | float64 | 25.17e |
        |      pos_ra_equ_B1950_s |       None |    |S14 |    14s |
        |     pos_dec_equ_B1950_s |       None |    |S14 |    14s |
        |  maj_axis_unc_equ_B1950 | arcseconds | float64 | 25.17e |
        |  min_axis_unc_equ_B1950 | arcseconds | float64 | 25.17e |
        | pos_angle_unc_equ_B1950 | arcseconds | float64 | 25.17e |
        |      pos_ra_equ_J2000_d |    degrees | float64 | 25.17e |
        |     pos_dec_equ_J2000_d |    degrees | float64 | 25.17e |
        |      pos_ra_equ_J2000_s |       None |    |S14 |    14s |
        |     pos_dec_equ_J2000_s |       None |    |S14 |    14s |
        |  maj_axis_unc_equ_J2000 | arcseconds | float64 | 25.17e |
        |  min_axis_unc_equ_J2000 | arcseconds | float64 | 25.17e |
        | pos_angle_unc_equ_J2000 | arcseconds | float64 | 25.17e |
        |     pos_lon_ecl_B1950_d |    degrees | float64 | 25.17e |
        |     pos_lat_ecl_B1950_d |    degrees | float64 | 25.17e |
        |  maj_axis_unc_ecl_B1950 | arcseconds | float64 | 25.17e |
        |  min_axis_unc_ecl_B1950 | arcseconds | float64 | 25.17e |
        | pos_angle_unc_ecl_B1950 | arcseconds | float64 | 25.17e |
        |     pos_lon_ecl_J2000_d |    degrees | float64 | 25.17e |
        |     pos_lat_ecl_J2000_d |    degrees | float64 | 25.17e |
        |  maj_axis_unc_ecl_J2000 | arcseconds | float64 | 25.17e |
        |  min_axis_unc_ecl_J2000 | arcseconds | float64 | 25.17e |
        | pos_angle_unc_ecl_J2000 | arcseconds | float64 | 25.17e |
        |           pos_lon_gal_d |    degrees | float64 | 25.17e |
        |           pos_lat_gal_d |    degrees | float64 | 25.17e |
        |        maj_axis_unc_gal | arcseconds | float64 | 25.17e |
        |        min_axis_unc_gal | arcseconds | float64 | 25.17e |
        |       pos_angle_unc_gal | arcseconds | float64 | 25.17e |
        |       pos_lon_sup_gal_d |    degrees | float64 | 25.17e |
        |       pos_lat_sup_gal_d |    degrees | float64 | 25.17e |
        |     maj_axis_unc_supgal | arcseconds | float64 | 25.17e |
        |    min_axis_unc_sup_gal | arcseconds | float64 | 25.17e |
        |   pos_angle_unc_sup_gal | arcseconds | float64 | 25.17e |
        -----------------------------------------------------------

    """

    # Create dictionary of search parameters, then parse into query URL
    request_dict = {'extend':'no','of':'xml_posn','objname':objname}
    query_url = "%s?%s" % (root_url,urllib.urlencode(request_dict))

    # Retrieve handler object from NED
    # Write the data to a file, flush it to get the proper VO table format, and read it into an Astropy table
    with aud.get_readable_fileobj(query_url) as f:
        R = f.read().encode('utf-8')

    # Check to see if NED returns a valid query

    validtable = check_ned_valid(R)

    if validtable:
        tf = tempfile.NamedTemporaryFile()
        tf.write(R)
        tf.file.flush()
        t = Table.read(tf.name, format='votable')

        # Return Astropy Table

        return t

    else:
        print ""
        print "The object name that you submitted is not currently recognized"
        print "by the NED name interpreter."
        print ""
        print "In general, naming conventions employ a prefix (usually an"
        print "acronym for the first author(s) or the survey name) followed"
        print "by a numerical string based on a tabular sequence or a position"
        print "on the sky. For more specifics, see the document at"
        print "http://vizier.u-strasbg.fr/Dic/iau-spec.htx"
        print ""

        return None

def query_ned_external(objname='M31',
        root_url='http://nedwww.ipac.caltech.edu/cgi-bin/nph-objsearch'):
    """
    Retrieve web links to external data at distributed centers for a particular target
        Equivalent to query_ned_by_objname(objname,tid=5)

    keywords:
        objname - astronomical object to search for

    Returns
    -------
    NED_ExternalLinksTable with the following information:

    Examples
    --------

    ::

        ------------------------------------------------
        |                 Name | Unit |  Type | Format |
        ------------------------------------------------
        |   external_query_url | None | |S871 |   871s |
        |             location | None |  |S30 |    30s |
        | external_service_url | None |  |S48 |    48s |
        ------------------------------------------------

    """

    # Create dictionary of search parameters, then parse into query URL
    request_dict = {'extend':'no','of':'xml_extern','objname':objname}
    query_url = "%s?%s" % (root_url,urllib.urlencode(request_dict))

    # Retrieve handler object from NED
    # Write the data to a file, flush it to get the proper VO table format, and read it into an Astropy table
    with aud.get_readable_fileobj(query_url) as f:
        R = f.read().encode('utf-8')

    # Check to see if NED returns a valid query

    validtable = check_ned_valid(R)

    if validtable:
        tf = tempfile.NamedTemporaryFile()
        tf.write(R)
        tf.file.flush()
        t = Table.read(tf.name, format='votable')

        # Return Astropy Table

        return t

    else:
        print ""
        print "The object name that you submitted is not currently recognized"
        print "by the NED name interpreter."
        print ""
        print "In general, naming conventions employ a prefix (usually an"
        print "acronym for the first author(s) or the survey name) followed"
        print "by a numerical string based on a tabular sequence or a position"
        print "on the sky. For more specifics, see the document at"
        print "http://vizier.u-strasbg.fr/Dic/iau-spec.htx"
        print ""

        return None

def query_ned_allsky(ra_constraint='Unconstrained', ra_1='', ra_2='',
        dec_constraint='Unconstrained', dec_1='', dec_2='',
        glon_constraint='Unconstrained', glon_1='', glon_2='',
        glat_constraint='Unconstrained', glat_1='', glat_2='',
        hconst='70.5', omegam='0.27', omegav='0.73', corr_z='1',
        z_constraint='Unconstrained',z_value1='',z_value2='',z_unit='z',
        flux_constraint='Unconstrained', flux_value1='', flux_value2='',flux_unit='Jy',
        flux_band=None,
        frat_constraint='Unconstrained',
        ot_include='ANY',
        in_objtypes1=None,in_objtypes2=None,in_objtypes3=None,
        ex_objtypes1=None,ex_objtypes2=None,ex_objtypes3=None,
        nmp_op='ANY',
        name_prefix1=None,name_prefix2=None,name_prefix3=None,name_prefix4=None,
        out_csys='Equatorial', out_equinox='J2000.0',
        obj_sort='RA or Longitude',
        zv_breaker='30000.0',
        list_limit='5',
        of='xml_main',
        root_url='http://nedwww.ipac.caltech.edu/cgi-bin/nph-allsky'):
    """
    Query objects with joint constraints on redshift, sky area, object types,
    survey names, and flux density/magnitude to construct galaxy samples

    Parameters
    ----------
    ra_constraint :
		constraint on right ascension. Options are 'Unconstrained','Between'
    ra_1,ra_2 :
		limits for RA in J2000 equatorial coordinates. Acceptable format includes '00h00m00.0'.
    dec_constraint :
		constraint on declination. Options are 'Unconstrained','Between'
    dec_1,dec2 :
		limits for declination in J2000 equatorial coordinates. Acceptable format includes '00d00m00.0'
    glon_constraint :
		constraint on Galactic longitude. Options are 'Unconstrained','Between'
    glon_1,glon_2 :
		limits for RA in J2000 equatorial coordinates. Acceptable format includes '00h00m00.0'.
    glat_constraint :
		constraint on Galactic latitude. Options are 'Unconstrained','Between'
    glat_1,glat2 :
		limits for declination in J2000 equatorial coordinates. Acceptable format includes '00d00m00.0'
    hconst :
		Hubble constant. Default is 70.5 km/s/Mpc (WMAP5)
    omegam :
		Omega_matter. Default is 0.27 (WMAP5)
    omegav :
		Omega_vacuum. Default is 0.73 (WMAP5)
    corr_z :
		integer keyword for correcting redshift to various velocity frames. Available frames are:
            1: reference frame defined by 3K CMB (default)
            2: reference frame defined by the Virgo Infall
            3: reference frame defined by the Virgo Infall + Great Attractor
            4: reference frame defined by the Virgo Infall + Great Attractor + Shapley Supercluster
    z_constraint :
        constraint on redshift. Options are 'Unconstrained','Available','Unavailable','Larger Than','Less Than','Between','Not Between'
    z_value1,zvalue2 :
        upper and lower boundaries for z_constraint. If 'Larger Than' or 'Less Than' are specified, only set z_value1
    z_unit :
		units of redshift constraint. Options are 'z' or 'km/s'
    flux_constraint :
		constraints on flux density. Options are 'Unconstrained','Available','Brighter Than','Fainter Than','Between','Not Between'
    flux_value1,flux_value2 :
		limits for flux density. If 'Brighter Than' or 'Fainter Than' is specified, only set flux_value1
    flux_unit :
		units of the flux density constraint. Options are 'Jy','mJy','mag','Wm2Hz'
    flux_band :
        specify a particular band of flux density to constrain search.
        Example: flux_band='HST-WFPC2-F814' searches the F814W channel (7937
        AA) on WFPC2 on Hubble.  Setting this keyword searches for objects with
        any data in the bandpass frequency range; it is not limited to the
        particular instrument.
    frat_constraint :
		option for specifying a flux ratio. Not currently enabled in the web version of NED; implementation here is uncertain.
    in_objtypes1 :
        list of classified extragalactic object types to include. Options are
        galaxies ('G'), galaxy pairs, triples, groups, clusters
        ('GPair','GTrpl','GGroup','GClstr'), QSOs and QSO groups
        ('QSO','QGroup'), gravitational lenses ('GravLens'), absorption line
        systems ('AbLS'), emission line sources ('EmLS')
    in_objtypes2 :
		list of unclassified extragalactic candidates to include. Options are sources detected in the radio ('RadioS'), sub-mm ('SmmS'), infrared ('IrS'), visual ('VisS'), ultraviolet excess ('UvES'), X-ray ('XrayS'), gamma-ray ('GammaS')
    in_objtypes3 :
		list of components of galaxies to include. Options are supernovae ('SN'), HII regions ('HII'), planetary nebulae ('PN'), supernova remnants ('SNR'), stellar associations ('\*Ass'), star clusters ('\*Cl'), molecular clouds ('MCld'), novae ('Nova'), variable stars ('V\*'), and Wolf-Rayet stars ('WR\*')
    ot_include :
		option for selection of included object types. Options are 'ANY' (default) or 'ALL'
    ex_objtypes1 :
		list of classified extragalactic object types to exclude. Options are the same as for in_objtypes1.
    ex_objtypes2 :
		list of unclassified extragalactic candidates to exclude. Options are the same as for in_objtypes2.
    ex_objtypes3 :
		list of components of galaxies to exclude. Options are the same as for in_objtypes3.
    nmp_op :
		option for selection of name prefixes. Options are 'ANY' (default) or 'ALL'. Full list of prefixes available at http://ned.ipac.caltech.edu/samples/NEDmdb.html
    name_prefix1 :
		list of name prefixes from ABELLPN - GB
    name_prefix2 :
		list of name prefixes from GB1 - PISCES
    name_prefix3 :
		list of name prefixes from Pisces Austrinus - 87GB[BWE91]
    name_prefix4 :
		list of name prefixes from [A2001] - [ZZL96]
    out_csys :
		output format for coordinate system. Options are 'Equatorial' (default), 'Ecliptic', 'Galactic', 'SuperGalactic'
    out_equinox :
		output format for equinox. Options are 'B1950.0','J2000.0' (default)
    obj_sort :
		format for sorting the output list. Options are 'RA or Longitude' (default), 'DEC or Latitude', 'Galactic Longitude', 'Galactic Latitude', 'Redshift - ascending', 'Redshift - descending'
    of :
		VOTable format of data. Options include 'xml_main' (default),'xml_names','xml_posn','xml_extern','xml_basic','xml_dervd'
    zv_breaker :
		velocity will be displayed as a lower limit when above this value. Default is 30000.0 km/s
    list_limit :
		lists with fewer than this number will return detailed information. Default is 5.

    """

    # Create dictionary of search parameters, then parse into query URL
    request_dict = {'ra_constraint':ra_constraint, 'ra_1':ra_1, 'ra_2':ra_2,
    'dec_constraint':dec_constraint, 'dec_1':dec_1, 'dec_2':dec_2,
    'glon_constraint':glon_constraint, 'glon_1':glon_1, 'glon_2':glon_2,
    'glat_constraint':glat_constraint, 'glat_1':glat_1, 'glat_2':glat_2,
    'hconst':hconst, 'omegam':omegam, 'omegav':omegav, 'corr_z':corr_z,
        'z_constraint':z_constraint,'z_value1':z_value1,'z_value2':z_value2,'z_unit':z_unit,
    'flux_constraint':flux_constraint, 'flux_value1':flux_value1, 'flux_value2':flux_value2,'flux_unit':flux_unit,
    'ot_include':ot_include,
    'nmp_op':nmp_op,
    'out_csys':out_csys, 'out_equinox':out_equinox,
    'obj_sort':obj_sort,
    'zv_breaker':zv_breaker,
    'list_limit':list_limit,
    'img_stamp':'NO',
    'of':of}
    if flux_band is not None: request_dict['flux_band']=flux_band
    if in_objtypes1 is not None: request_dict['in_objtypes1']=in_objtypes1
    if in_objtypes2 is not None: request_dict['in_objtypes2']=in_objtypes2
    if in_objtypes3 is not None: request_dict['in_objtypes3']=in_objtypes3
    if ex_objtypes1 is not None: request_dict['ex_objtypes1']=ex_objtypes1
    if ex_objtypes2 is not None: request_dict['ex_objtypes2']=ex_objtypes2
    if ex_objtypes3 is not None: request_dict['ex_objtypes3']=ex_objtypes3
    if name_prefix1 is not None: request_dict['name_prefix1']=name_prefix1
    if name_prefix2 is not None: request_dict['name_prefix2']=name_prefix2
    if name_prefix3 is not None: request_dict['name_prefix3']=name_prefix3
    if name_prefix4 is not None: request_dict['name_prefix4']=name_prefix4
    query_url = "%s?%s" % (root_url,urllib.urlencode(request_dict,doseq=1))

    # Retrieve handler object from NED
    # Write the data to a file, flush it to get the proper VO table format, and read it into an Astropy table
    with aud.get_readable_fileobj(query_url) as f:
        R = f.read().encode('utf-8')

    try:
        parseString(R)
    except:
        print ""
        print "The constraints that you submitted were not recognized by the NED interpreter."
        print ""
        print "constraints: %s" % request_dict
        print ""
        print "See the header of this function for permitted formats for constraints."
        print ""

        return None

    tf = tempfile.NamedTemporaryFile()
    tf.write(R)
    tf.file.flush()
    t = Table.read(tf.name, format='votable')

    # Return Astropy Table

    return t

def query_ned_photometry(objname='M31',
        root_url='http://nedwww.ipac.caltech.edu/cgi-bin/nph-datasearch'):
    """
    Query NED for photometric data on a given object.

    Returns
    -------
    NED_PhotometricData table with following information:

    Examples
    --------

    ::

        --------------------------------------------------------
        |                       Name | Unit |    Type | Format |
        --------------------------------------------------------
        |                        No. | None |   int32 |    12i |
        |          Observed Passband | None |    |S20 |    20s |
        |     Photometry Measurement | None | float64 | 25.17e |
        |                Uncertainty | None |    |S11 |    11s |
        |                      Units | None |    |S20 |    20s |
        |                  Frequency |   Hz | float64 | 25.17e |
        | NED Photometry Measurement |   Jy | float64 | 25.17e |
        |            NED Uncertainty | None |    |S11 |    11s |
        |                  NED Units | None |     |S2 |     2s |
        |                    Refcode | None |    |S19 |    19s |
        |               Significance | None |    |S23 |    23s |
        |        Published frequency | None |    |S17 |    17s |
        |             Frequency Mode | None |    |S71 |    71s |
        |       Coordinates Targeted | None |    |S31 |    31s |
        |               Spatial Mode | None |    |S24 |    24s |
        |                 Qualifiers | None |    |S40 |    40s |
        |                   Comments | None |   |S161 |   161s |
        --------------------------------------------------------

    """

    # Create dictionary of search parameters, then parse into query URL
    request_dict = {'search_type':'Photometry','of':'xml_main','objname':objname}
    query_url = "%s?%s" % (root_url,urllib.urlencode(request_dict))

    # Retrieve handler object from NED
    # Write the data to a file, flush it to get the proper VO table format, and read it into an Astropy table
    with aud.get_readable_fileobj(query_url) as f:
        R = f.read().encode('utf-8')

    # Check to see if NED returns a valid query

    validtable = check_ned_valid(R)

    if validtable:
        tf = tempfile.NamedTemporaryFile()
        tf.write(R)
        tf.file.flush()
        t = Table.read(tf.name, format='votable')

        # Return Astropy Table

        return t

    else:
        print ""
        print "The object name that you submitted is not currently recognized"
        print "by the NED name interpreter."
        print ""
        print "In general, naming conventions employ a prefix (usually an"
        print "acronym for the first author(s) or the survey name) followed"
        print "by a numerical string based on a tabular sequence or a position"
        print "on the sky. For more specifics, see the document at"
        print "http://vizier.u-strasbg.fr/Dic/iau-spec.htx"
        print ""

        return None

def query_ned_diameters(objname='M31',
        root_url='http://nedwww.ipac.caltech.edu/cgi-bin/nph-datasearch'):
    """
    Query NED for multi-wavelength diameter (size) data on a given object.

    Returns
    -------
    NED_Diameters_Data table with following information:

    Examples
    --------

    ::

        --------------------------------------------------------------
        |                           Name |   Unit |    Type | Format |
        --------------------------------------------------------------
        |                            No. |   None |   int32 |    12i |
        |             Frequency targeted |   None |    |S25 |    25s |
        |                        Refcode |   None |    |S19 |    19s |
        |                     Major Axis |   None | float64 | 25.17e |
        |                Major Axis Flag |   None |     |S3 |     3s |
        |                Major Axis Unit |   None |    |S11 |    11s |
        |                     Minor Axis |   None | float64 | 25.17e |
        |                Minor Axis Flag |   None |     |S4 |     4s |
        |                Minor Axis Unit |   None |     |S6 |     6s |
        |                     Axis Ratio |   None | float64 | 25.17e |
        |                Axis Ratio Flag |   None |     |S8 |     8s |
        |         Major Axis Uncertainty |   None | float64 | 25.17e |
        |                    Ellipticity |   None | float64 | 25.17e |
        |                   Eccentricity |   None | float64 | 25.17e |
        |                 Position Angle |    deg | float64 | 25.17e |
        |                        Equinox |   None |     |S5 |     5s |
        |                Reference Level |   None |    |S30 |    30s |
        |                  NED Frequency |  hertz | float64 | 25.17e |
        |                 NED Major Axis | arcsec | float64 | 25.17e |
        |     NED Major Axis Uncertainty | arcsec | float64 | 25.17e |
        |                 NED Axis Ratio |   None | float64 | 25.17e |
        |                NED Ellipticity |   None | float64 | 25.17e |
        |               NED Eccentricity |   None | float64 | 25.17e |
        |           NED cos-1_axis_ratio |   None | float64 | 25.17e |
        |             NED Position Angle |    deg | float64 | 25.17e |
        |                 NED Minor Axis | arcsec | float64 | 25.17e |
        |         Minor Axis Uncertainty |   None | float64 | 25.17e |
        |     NED Minor Axis Uncertainty | arcsec | float64 | 25.17e |
        |         Axis Ratio Uncertainty |   None | float64 | 25.17e |
        |     NED Axis Ratio Uncertainty |   None | float64 | 25.17e |
        |        Ellipticity Uncertainty |   None | float64 | 25.17e |
        |    NED Ellipticity Uncertainty |   None | float64 | 25.17e |
        |       Eccentricity Uncertainty |   None | float64 | 25.17e |
        |   NED Eccentricity Uncertainty |   None | float64 | 25.17e |
        |     Position Angle Uncertainty |   None | float64 | 25.17e |
        | NED Position Angle Uncertainty |    deg | float64 | 25.17e |
        |                   Significance |   None |    |S23 |    23s |
        |                      Frequency |   None | float64 | 25.17e |
        |                 Frequency Unit |   None |     |S7 |     7s |
        |                 Frequency Mode |   None |    |S45 |    45s |
        |                  Detector Type |   None |    |S34 |    34s |
        |              Fitting Technique |   None |    |S24 |    24s |
        |                       Features |   None |     |S4 |     4s |
        |              Measured Quantity |   None |    |S18 |    18s |
        |         Measurement Qualifiers |   None |    |S44 |    44s |
        |                    Targeted RA |   None |     |S9 |     9s |
        |                   Targeted DEC |   None |     |S9 |     9s |
        |               Targeted Equinox |   None |     |S5 |     5s |
        |                 NED Qualifiers |   None |    |S42 |    42s |
        |                    NED Comment |   None |    |S37 |    37s |
        --------------------------------------------------------------

    """

    # Create dictionary of search parameters, then parse into query URL
    request_dict = {'search_type':'Diameters','of':'xml_main','objname':objname}
    query_url = "%s?%s" % (root_url,urllib.urlencode(request_dict))

    # Retrieve handler object from NED
    # Write the data to a file, flush it to get the proper VO table format, and read it into an Astropy table
    with aud.get_readable_fileobj(query_url) as f:
        R = f.read().encode('utf-8')

    # Check to see if NED returns a valid query

    validtable = check_ned_valid(R)

    if validtable:
        tf = tempfile.NamedTemporaryFile()
        tf.write(R)
        tf.file.flush()
        t = Table.read(tf.name, format='votable')

        # Return Astropy Table

        return t

    else:
        print ""
        print "The object name that you submitted is not currently recognized"
        print "by the NED name interpreter."
        print ""
        print "In general, naming conventions employ a prefix (usually an"
        print "acronym for the first author(s) or the survey name) followed"
        print "by a numerical string based on a tabular sequence or a position"
        print "on the sky. For more specifics, see the document at"
        print "http://vizier.u-strasbg.fr/Dic/iau-spec.htx"
        print ""

        return None

def query_ned_redshifts(objname='M31',
        root_url='http://nedwww.ipac.caltech.edu/cgi-bin/nph-datasearch'):
    """
    Query NED for multi-wavelength redshift data on a given object.

    Returns
    -------
    NED_Redshifts_Data table with following information:

    Examples
    --------

    ::

        --------------------------------------------------------------
        |                           Name |   Unit |    Type | Format |
        --------------------------------------------------------------
        |                            No. |   None |   int32 |    12i |
        |             Frequency Targeted |   None |    |S13 |    13s |
        |             Published Velocity | km/sec |   int32 |    12i |
        | Published Velocity Uncertainty | km/sec |   int32 |    12i |
        |             Published Redshift |   None | float64 | 25.17e |
        | Published Redshift Uncertainty |   None | float64 | 25.17e |
        |                        Refcode |   None |    |S19 |    19s |
        |            Name in publication |   None |    |S20 |    20s |
        |                   Published RA |   None |     |S8 |     8s |
        |                  Published Dec |   None |     |S8 |     8s |
        |              Published Equinox |   None |     |S5 |     5s |
        |              Unc. Significance |   None |    |S17 |    17s |
        |                 Spectral Range |   None |     |S7 |     7s |
        |                   Spectrograph |   None |    |S18 |    18s |
        |      Measurement Mode Features |   None |    |S34 |    34s |
        |     Measurement Mode Technique |   None |    |S42 |    42s |
        |                   Spatial Mode |   None |    |S28 |    28s |
        |                          Epoch |   None |     |S4 |     4s |
        |                Reference Frame |   None |    |S33 |    33s |
        |                           Apex |   None |     |S4 |     4s |
        |          Longitude of the Apex |   None |     |S4 |     4s |
        |           Latitude of the Apex |   None |     |S4 |     4s |
        |         Apex Coordinate System |   None |     |S4 |     4s |
        |                     Qualifiers |   None |    |S50 |    50s |
        |                       Comments |   None |    |S24 |    24s |
        --------------------------------------------------------------

    """

    # Create dictionary of search parameters, then parse into query URL
    request_dict = {'search_type':'Redshifts','of':'xml_main','objname':objname}
    query_url = "%s?%s" % (root_url,urllib.urlencode(request_dict))

    # Retrieve handler object from NED
    # Write the data to a file, flush it to get the proper VO table format, and read it into an Astropy table
    with aud.get_readable_fileobj(query_url) as f:
        R = f.read().encode('utf-8')

    # Check to see if there is a valid redshift frame for this object

    strdom = parseString(R)
    p = strdom.getElementsByTagName('PARAM')
    if len(p) > 1:
        if 'value' in p[1].attributes.keys():
            n = p[1].attributes['value']
            errstr = n.value

            if errstr == ' No redshift data frame found.':
                print ""
                print "No redshift data frame found for this object."
                print ""
                return None

    # Check to see if NED returns a valid query

    validtable = check_ned_valid(R)
    if validtable:
        tf = tempfile.NamedTemporaryFile()
        tf.write(R)
        tf.file.flush()
        t = Table.read(tf.name, format='votable')

        # Return Astropy Table

        return t

    else:
        print ""
        print "The object name that you submitted is not currently recognized"
        print "by the NED name interpreter."
        print ""
        print "In general, naming conventions employ a prefix (usually an"
        print "acronym for the first author(s) or the survey name) followed"
        print "by a numerical string based on a tabular sequence or a position"
        print "on the sky. For more specifics, see the document at"
        print "http://vizier.u-strasbg.fr/Dic/iau-spec.htx"
        print ""

        return None


def query_ned_notes(objname='M31',
        root_url='http://nedwww.ipac.caltech.edu/cgi-bin/nph-datasearch'):
    """
    Query NED for detailed notes on a given object (often excerpts from a paper).

    Returns
    -------
    NED_Note_Data table with following information:

    Examples
    --------

    ::

        ----------------------------------------
        |        Name | Unit |   Type | Format |
        ----------------------------------------
        |         No. | None |  int32 |    12i |
        |     Refcode | None |   |S19 |    19s |
        | Object Name | None |   |S21 |    21s |
        |        Note | None | |S3556 |  3556s |
        ----------------------------------------

    """

    # Create dictionary of search parameters, then parse into query URL
    request_dict = {'search_type':'Notes','of':'xml_main','objname':objname}
    query_url = "%s?%s" % (root_url,urllib.urlencode(request_dict))

    # Retrieve handler object from NED
    # Write the data to a file, flush it to get the proper VO table format, and read it into an Astropy table
    with aud.get_readable_fileobj(query_url) as f:
        R = f.read().encode('utf-8')

    # Check to see if there is a note for this object

    strdom = parseString(R)
    p = strdom.getElementsByTagName('PARAM')
    if len(p) > 1:
        if 'value' in p[1].attributes.keys():
            n = p[1].attributes['value']
            errstr = n.value

            if errstr == ' No note found.':
                print ""
                print "No note found for this object."
                print ""
                return None

    # Check to see if NED returns a valid query

    validtable = check_ned_valid(R)
    if validtable:
        tf = tempfile.NamedTemporaryFile()
        tf.write(R)
        tf.file.flush()
        t = Table.read(tf.name, format='votable')

        return t

    else:
        print ""
        print "The object name that you submitted is not currently recognized"
        print "by the NED name interpreter."
        print ""
        print "In general, naming conventions employ a prefix (usually an"
        print "acronym for the first author(s) or the survey name) followed"
        print "by a numerical string based on a tabular sequence or a position"
        print "on the sky. For more specifics, see the document at"
        print "http://vizier.u-strasbg.fr/Dic/iau-spec.htx"
        print ""

        return None

def query_ned_position(objname='M31',
        root_url='http://nedwww.ipac.caltech.edu/cgi-bin/nph-datasearch'):
    """
    Query NED for multi-wavelength position data on a given object.

    Returns
    -------
    NED_Positions_Data table with following information:

    Examples
    --------

    ::

        -------------------------------------------------------------------
        |                                Name |   Unit |    Type | Format |
        -------------------------------------------------------------------
        |                                 No. |   None |   int32 |    12i |
        |                                  RA |   None |    |S14 |    14s |
        |                                 DEC |   None |    |S14 |    14s |
        |                           Frequency |   None |    |S18 |    18s |
        | Uncertainty Ellipse Semi-Major Axis | arcsec | float64 | 25.17e |
        | Uncertainty Ellipse Semi-Minor Axis | arcsec | float64 | 25.17e |
        |              Uncertainty Ellipse PA |   None |     |S2 |     2s |
        |                             Refcode |   None |    |S19 |    19s |
        |                      Published Name |   None |    |S21 |    21s |
        |                        Published RA |   None |     |S8 |     8s |
        |                       Published Dec |   None |     |S8 |     8s |
        |            Published RA Uncertainty |   None |     |S3 |     3s |
        |           Published Dec Uncertainty |   None |     |S4 |     4s |
        |            Published PA Uncertainty |   None |     |S2 |     2s |
        |            Uncertainty Significance |   None |    |S59 |    59s |
        |                   Published Equinox |   None |     |S7 |     7s |
        |                     Published Epoch |   None |     |S6 |     6s |
        |                       NED Frequency |     Hz | float64 | 25.17e |
        |         Published System Coordinate |   None |    |S10 |    10s |
        |                      Published Unit |   None |    |S11 |    11s |
        |                     Published Frame |   None |     |S3 |     3s |
        |            Published Frequence Mode |   None |    |S22 |    22s |
        |                          Qualifiers |   None |    |S42 |    42s |
        -------------------------------------------------------------------
    """

    # Create dictionary of search parameters, then parse into query URL
    request_dict = {'search_type':'Positions','of':'xml_main','objname':objname}
    query_url = "%s?%s" % (root_url,urllib.urlencode(request_dict))

    # Retrieve handler object from NED
    # Write the data to a file, flush it to get the proper VO table format, and read it into an Astropy table
    with aud.get_readable_fileobj(query_url) as f:
        R = f.read().encode('utf-8')

    # Check to see if NED returns a valid query

    validtable = check_ned_valid(R)

    if validtable:
        tf = tempfile.NamedTemporaryFile()
        tf.write(R)
        tf.file.flush()
        t = Table.read(tf.name, format='votable')

        # Return Astropy Table

        return t

    else:
        print ""
        print "The object name that you submitted is not currently recognized"
        print "by the NED name interpreter."
        print ""
        print "In general, naming conventions employ a prefix (usually an"
        print "acronym for the first author(s) or the survey name) followed"
        print "by a numerical string based on a tabular sequence or a position"
        print "on the sky. For more specifics, see the document at"
        print "http://vizier.u-strasbg.fr/Dic/iau-spec.htx"
        print ""

        return None

def query_ned_nearpos(ra=0.000,dec=0.000,sr=2.0,
        root_url='http://nedwww.ipac.caltech.edu/cgi-bin/nph-objsearch'):
    """
    Query objects within a specified angular distance of a position on the sky

    keywords:
        ra - right ascension (decimal degrees, J2000.0)

        dec - declination (decimal degrees, J2000.0)

        radius - radius (in arcminutes) within which to search

    Returns
    -------
    NED_MainTable with the following information for each target within the search radius:

    Examples
    --------

    ::

        -----------------------------------------------------
        |                 Name |    Unit |    Type | Format |
        -----------------------------------------------------
        |                  No. |    None |   int32 |    12i |
        |          Object Name |    None |    |S30 |    30s |
        |              RA(deg) | degrees | float64 | 25.17e |
        |             DEC(deg) | degrees | float64 | 25.17e |
        |                 Type |    None |     |S6 |     6s |
        |             Velocity |  km/sec | float64 | 25.17e |
        |             Redshift |    None | float64 | 25.17e |
        |        Redshift Flag |    None |     |S4 |     4s |
        | Magnitude and Filter |    None |     |S5 |     5s |
        |    Distance (arcmin) |  arcmin | float64 | 25.17e |
        |           References |    None |   int32 |    12i |
        |                Notes |    None |   int32 |    12i |
        |    Photometry Points |    None |   int32 |    12i |
        |            Positions |    None |   int32 |    12i |
        |      Redshift Points |    None |   int32 |    12i |
        |      Diameter Points |    None |   int32 |    12i |
        |         Associations |    None |   int32 |    12i |
        -----------------------------------------------------

    """

    assert type(sr) in (int,float), \
        "Search radius must be either a float or an integer"
    sr_deg = sr / 60.

    # Create dictionary of search parameters, then parse into query URL
    request_dict = {'search_type':'Near Position Search','of':'xml_main','RA':'%f' % ra, 'DEC':'%f' % dec, 'SR':'%f' % sr_deg,}
    query_url = "%s?%s" % (root_url,urllib.urlencode(request_dict))

    # Retrieve handler object from NED
    # Write the data to a file, flush it to get the proper VO table format, and read it into an Astropy table
    with aud.get_readable_fileobj(query_url) as f:
        R = f.read().encode('utf-8')

    # Check to see if NED returns a valid query

    validtable = check_ned_valid(R)

    if validtable:
        tf = tempfile.NamedTemporaryFile()
        tf.write(R)
        tf.file.flush()
        t = Table.read(tf.name, format='votable')

        # Return Astropy Table

        return t

    else:
        print ""
        print "No objects found within %f arcmin of position RA = %f, dec = %f" % (sr,ra,dec)
        print "by NED. Try either changing the position or using a larger search radius."
        print ""

        return None

"""
def query_ned_basic(objname='M31',
        root_url='http://nedwww.ipac.caltech.edu/cgi-bin/nph-objsearch'):

    Retrieve basic data from NED for a particular target

    ** Deprecated - returns error of "two fields with same name"

    keywords:
        objname - astronomical object to search for



    # Create dictionary of search parameters, then parse into query URL
    request_dict = {'extend':'no','of':'xml_basic','objname':objname}
    query_url = "%s?%s" % (root_url,urllib.urlencode(request_dict))

    # Retrieve handler object from NED
    U = urllib2.urlopen(query_url)

    # Write the data to a file, flush it to get the proper VO table format, and read it into an Astropy table

    R = U.read()
    U.close()
    # Check to see if NED returns a valid query

    validtable = check_ned_valid(R)

    if validtable:
        tf = tempfile.NamedTemporaryFile()
        tf.write(R)
        tf.file.flush()
        t = Table.read(tf.name, format='votable')

        # Return Astropy Table

        return t

    else:
        return None
"""

"""
def query_ned_references(objname='M31',
        root_url='http://nedwww.ipac.caltech.edu/cgi-bin/nph-datasearch'):
    Query NED for references to a particular object.

    Not currently working with NED; returns empty VOTable saying no reference found. - KW, Jun 2011

    # Create dictionary of search parameters, then parse into query URL
    request_dict = {'search_type':'Reference','of':'xml_main','objname':objname}
    query_url = "%s?%s" % (root_url,urllib.urlencode(request_dict))

    # Retrieve handler object from NED
    U = urllib2.urlopen(query_url)

    # Write the data to a file, flush it to get the proper VO table format, and read it into an Astropy Table

    R = U.read()
    U.close()
    # Check to see if NED returns a valid query

    validtable = check_ned_valid(R)

    if validtable:
        tf = tempfile.NamedTemporaryFile()
        tf.write(R)
        tf.file.flush()
        t = Table.read(tf.name, format='votable')

        # Return Astropy Table

        return t

    else:
        return None
"""
