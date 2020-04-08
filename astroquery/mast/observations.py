# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
MAST Observations
=================

This module contains various methods for querying MAST observations.
"""


import warnings
import json
import time
import os
import uuid

import numpy as np

from requests import HTTPError

import astropy.units as u
import astropy.coordinates as coord

from astropy.table import Table, Row, vstack, MaskedColumn
from astropy.logger import log

from astropy.utils import deprecated
from astropy.utils.console import ProgressBarOrSpinner
from astropy.utils.exceptions import AstropyDeprecationWarning

from six.moves.urllib.parse import quote as urlencode

from ..query import QueryWithLogin
from ..utils import commons, async_to_sync
from ..utils.class_or_instance import class_or_instance
from ..exceptions import (TimeoutError, InvalidQueryError, RemoteServiceError,
                          ResolverError, MaxResultsWarning,
                          NoResultsWarning, InputWarning, AuthenticationWarning)

from . import conf, utils
from .core import MastQueryWithLogin


__all__ = ['Observations', 'ObservationsClass',
           'MastClass', 'Mast']


@async_to_sync
class ObservationsClass(MastQueryWithLogin):
    """
    MAST Observations query class.

    Class for querying MAST observational data.
    """

    def _parse_result(self, responses, verbose=False):  # Used by the async_to_sync decorator functionality
        """
        Parse the results of a list of `~requests.Response` objects and returns an `~astropy.table.Table` of results.

        Parameters
        ----------
        responses : list of `~requests.Response`
            List of `~requests.Response` objects.
        verbose : bool
            (presently does nothing - there is no output with verbose set to
            True or False)
            Default False.  Setting to True provides more extensive output.

        Returns
        -------
        response : `~astropy.table.Table`
        """

        return self._portal_api_connection._parse_result(responses, verbose)

    def list_missions(self):
        """
        Lists data missions archived by MAST and avaiable through `astroquery.mast`.

        Returns
        --------
        response : list
            List of available missions.
        """

        # getting all the histogram information
        service = "Mast.Caom.All"
        params = {}
        response = self._portal_api_connection.service_request_async(service, params, format='extjs')
        json_response = response[0].json()

        # getting the list of missions
        hist_data = json_response['data']['Tables'][0]['Columns']
        for facet in hist_data:
            if facet['text'] == "obs_collection":
                mission_info = facet['ExtendedProperties']['histObj']
                missions = list(mission_info.keys())
                missions.remove('hist')
                return missions

    def get_metadata(self, query_type):
        """
        Returns metadata about the requested query type.

        Parameters
        ----------
        query_type : str
            The query to get metadata for. Options are observations, and products.

        Returns
        --------
        response : `~astropy.table.Table`
            The metadata table.
        """

        if query_type.lower() == "observations":
            colconf_name = "Mast.Caom.Cone"
        elif query_type.lower() == "products":
            colconf_name = "Mast.Caom.Products"
        else:
            raise InvalidQueryError("Unknown query type.")

        return self._portal_api_connection._get_columnsconfig_metadata(colconf_name)

    def _parse_caom_criteria(self, **criteria):
        """
        Helper function that takes dictionary of criteria and parses them into
        position (none if there are no coordinates/object name) and a filter set.

        Parameters
        ----------
        **criteria
            Criteria to apply.
            Valid criteria are coordinates, objectname, radius (as in `query_region` and `query_object`),
            and all observation fields returned by the ``get_metadata("observations")``.
            The Column Name is the keyword, with the argument being one or more acceptable values for that parameter,
            except for fields with a float datatype where the argument should be in the form [minVal, maxVal].
            For non-float type criteria wildcards maybe used (both * and % are considered wildcards), however
            only one wildcarded value can be processed per criterion.
            RA and Dec must be given in decimal degrees, and datetimes in MJD.
            For example: filters=["FUV","NUV"],proposal_pi="Ost*",t_max=[52264.4586,54452.8914]

        Returns
        -------
        response : tuple
            Tuple of the form (position, filter_set), where position is either None (coordinates and objectname
            not given) or a string, and filter_set is list of filters dictionaries.
        """

        # Seperating any position info from the rest of the filters
        coordinates = criteria.pop('coordinates', None)
        objectname = criteria.pop('objectname', None)
        radius = criteria.pop('radius', 0.2*u.deg)

        # Dealing with observation type (science vs calibration)
        if ('obstype' in criteria) and ('intentType' in criteria):
            warn_string = ("Cannot specify both obstype and intentType, "
                           "obstype is the deprecated version of intentType and will be ignored.")
            warnings.warn(warn_string, InputWarning)
            criteria.pop('obstype', None)

        # Temporarily issuing warning about change in behavior
        # continuing old behavior
        # grabbing the observation type (science vs calibration)
        obstype = criteria.pop('obstype', None)
        if obstype:
            warn_string = ("Criteria obstype argument disappeared in May 2019. "
                          "Criteria 'obstype' is now 'intentType', options are 'science' or 'calibration', "
                          "if intentType is not supplied all observations (science and calibration) are returned.")
            warnings.warn(warn_string, AstropyDeprecationWarning)

            if obstype == "science":
                criteria["intentType"] = "science"
            elif obstype == "cal":
                criteria["intentType"] = "calibration"

        # Build the mashup filter object and store it in the correct service_name entry
        if coordinates or objectname:
            mashup_filters = self._portal_api_connection.build_filter_set("Mast.Caom.Cone",
                                                                           "Mast.Caom.Filtered.Position",
                                                                           **criteria)
            coordinates = utils.parse_input_location(coordinates, objectname)
        else:
            mashup_filters = self._portal_api_connection.build_filter_set("Mast.Caom.Cone",
                                                                           "Mast.Caom.Filtered",
                                                                           **criteria)

        # handle position info (if any)
        position = None

        if coordinates:
            # if radius is just a number we assume degrees
            radius = coord.Angle(radius, u.deg)

            # build the coordinates string needed by Mast.Caom.Filtered.Position
            position = ', '.join([str(x) for x in (coordinates.ra.deg, coordinates.dec.deg, radius.deg)])

        return position, mashup_filters

    @class_or_instance
    def query_region_async(self, coordinates, radius=0.2*u.deg, pagesize=None, page=None):
        """
        Given a sky position and radius, returns a list of MAST observations.
        See column documentation `here <https://mast.stsci.edu/api/v0/_c_a_o_mfields.html>`__.

        Parameters
        ----------
        coordinates : str or `~astropy.coordinates` object
            The target around which to search. It may be specified as a
            string or as the appropriate `~astropy.coordinates` object.
        radius : str or `~astropy.units.Quantity` object, optional
            Default 0.2 degrees.
            The string must be parsable by `~astropy.coordinates.Angle`. The
            appropriate `~astropy.units.Quantity` object from
            `~astropy.units` may also be used. Defaults to 0.2 deg.
        pagesize : int, optional
            Default None.
            Can be used to override the default pagesize for (set in configs) this query only.
            E.g. when using a slow internet connection.
        page : int, optional
            Default None.
            Can be used to override the default behavior of all results being returned to
            obtain a specific page of results.

        Returns
        -------
        response : list of `~requests.Response`
        """

        # Put coordinates and radius into consistant format
        coordinates = commons.parse_coordinates(coordinates)

        # if radius is just a number we assume degrees
        radius = coord.Angle(radius, u.deg)

        service = 'Mast.Caom.Cone'
        params = {'ra': coordinates.ra.deg,
                  'dec': coordinates.dec.deg,
                  'radius': radius.deg}

        return self._portal_api_connection.service_request_async(service, params, pagesize, page)

    @class_or_instance
    def query_object_async(self, objectname, radius=0.2*u.deg, pagesize=None, page=None):
        """
        Given an object name, returns a list of MAST observations.
        See column documentation `here <https://mast.stsci.edu/api/v0/_c_a_o_mfields.html>`__.

        Parameters
        ----------
        objectname : str
            The name of the target around which to search.
        radius : str or `~astropy.units.Quantity` object, optional
            Default 0.2 degrees.
            The string must be parsable by `~astropy.coordinates.Angle`.
            The appropriate `~astropy.units.Quantity` object from
            `~astropy.units` may also be used. Defaults to 0.2 deg.
        pagesize : int, optional
            Default None.
            Can be used to override the default pagesize for (set in configs) this query only.
            E.g. when using a slow internet connection.
        page : int, optional
            Defaulte None.
            Can be used to override the default behavior of all results being returned
            to obtain a specific page of results.

        Returns
        -------
        response : list of `~requests.Response`
        """

        coordinates = utils.resolve_object(objectname)

        return self.query_region_async(coordinates, radius, pagesize, page)

    @class_or_instance
    def query_criteria_async(self, pagesize=None, page=None, **criteria):
        """
        Given an set of criteria, returns a list of MAST observations.
        Valid criteria are returned by ``get_metadata("observations")``

        Parameters
        ----------
        pagesize : int, optional
            Can be used to override the default pagesize.
            E.g. when using a slow internet connection.
        page : int, optional
            Can be used to override the default behavior of all results being returned to obtain
            one sepcific page of results.
        **criteria
            Criteria to apply. At least one non-positional criteria must be supplied.
            Valid criteria are coordinates, objectname, radius (as in `query_region` and `query_object`),
            and all observation fields returned by the ``get_metadata("observations")``.
            The Column Name is the keyword, with the argument being one or more acceptable values for that parameter,
            except for fields with a float datatype where the argument should be in the form [minVal, maxVal].
            For non-float type criteria wildcards maybe used (both * and % are considered wildcards), however
            only one wildcarded value can be processed per criterion.
            RA and Dec must be given in decimal degrees, and datetimes in MJD.
            For example: filters=["FUV","NUV"],proposal_pi="Ost*",t_max=[52264.4586,54452.8914]


        Returns
        -------
        response : list of `~requests.Response`
        """

        position, mashup_filters = self._parse_caom_criteria(**criteria)

        if not mashup_filters:
            raise InvalidQueryError("At least one non-positional criterion must be supplied.")

        if position:
            service = "Mast.Caom.Filtered.Position"
            params = {"columns": "*",
                      "filters": mashup_filters,
                      "position": position}
        else:
            service = "Mast.Caom.Filtered"
            params = {"columns": "*",
                      "filters": mashup_filters}

        return self._portal_api_connection.service_request_async(service, params)

    def query_region_count(self, coordinates, radius=0.2*u.deg, pagesize=None, page=None):
        """
        Given a sky position and radius, returns the number of MAST observations in that region.

        Parameters
        ----------
        coordinates : str or `~astropy.coordinates` object
            The target around which to search. It may be specified as a
            string or as the appropriate `~astropy.coordinates` object.
        radius : str or `~astropy.units.Quantity` object, optional
            The string must be parsable by `~astropy.coordinates.Angle`. The
            appropriate `~astropy.units.Quantity` object from
            `~astropy.units` may also be used. Defaults to 0.2 deg.
        pagesize : int, optional
            Can be used to override the default pagesize for.
            E.g. when using a slow internet connection.
        page : int, optional
            Can be used to override the default behavior of all results being returned to
            obtain a specific page of results.

        Returns
        -------
        response : int
        """

        # build the coordinates string needed by Mast.Caom.Filtered.Position
        coordinates = commons.parse_coordinates(coordinates)

        # if radius is just a number we assume degrees
        radius = coord.Angle(radius, u.deg)

        # turn coordinates into the format
        position = ', '.join([str(x) for x in (coordinates.ra.deg, coordinates.dec.deg, radius.deg)])

        service = "Mast.Caom.Filtered.Position"
        params = {"columns": "COUNT_BIG(*)",
                  "filters": [],
                  "position": position}

        return int(self._portal_api_connection.service_request(service, params, pagesize, page)[0][0])

    def query_object_count(self, objectname, radius=0.2*u.deg, pagesize=None, page=None):
        """
        Given an object name, returns the number of MAST observations.

        Parameters
        ----------
        objectname : str
            The name of the target around which to search.
        radius : str or `~astropy.units.Quantity` object, optional
            The string must be parsable by `~astropy.coordinates.Angle`. The
            appropriate `~astropy.units.Quantity` object from
            `~astropy.units` may also be used. Defaults to 0.2 deg.
        pagesize : int, optional
            Can be used to override the default pagesize.
            E.g. when using a slow internet connection.
        page : int, optional
            Can be used to override the default behavior of all results being returned to obtain
            one sepcific page of results.

        Returns
        -------
        response : int
        """

        coordinates = utils.resolve_object(objectname)

        return self.query_region_count(coordinates, radius, pagesize, page)

    def query_criteria_count(self, pagesize=None, page=None, **criteria):
        """
        Given an set of filters, returns the number of MAST observations meeting those criteria.

        Parameters
        ----------
        pagesize : int, optional
            Can be used to override the default pagesize.
            E.g. when using a slow internet connection.
        page : int, optional
            Can be used to override the default behavior of all results being returned to obtain
            one sepcific page of results.
        **criteria
            Criteria to apply. At least one non-positional criterion must be supplied.
            Valid criteria are coordinates, objectname, radius (as in `query_region` and `query_object`),
            and all observation fields listed `here <https://mast.stsci.edu/api/v0/_c_a_o_mfields.html>`__.
            The Column Name is the keyword, with the argument being one or more acceptable values for that parameter,
            except for fields with a float datatype where the argument should be in the form [minVal, maxVal].
            For non-float type criteria wildcards maybe used (both * and % are considered wildcards), however
            only one wildcarded value can be processed per criterion.
            RA and Dec must be given in decimal degrees, and datetimes in MJD.
            For example: filters=["FUV","NUV"],proposal_pi="Ost*",t_max=[52264.4586,54452.8914]


        Returns
        -------
        response : int
        """

        position, mashup_filters = self._parse_caom_criteria(**criteria)

        # send query
        if position:
            service = "Mast.Caom.Filtered.Position"
            params = {"columns": "COUNT_BIG(*)",
                      "filters": mashup_filters,
                      "position": position}
        else:
            service = "Mast.Caom.Filtered"
            params = {"columns": "COUNT_BIG(*)",
                      "filters": mashup_filters}

        return self._portal_api_connection.service_request(service, params)[0][0].astype(int)

    @class_or_instance
    def get_product_list_async(self, observations):
        """
        Given a "Product Group Id" (column name obsid) returns a list of associated data products.
        See column documentation `here <https://masttest.stsci.edu/api/v0/_productsfields.html>`__.

        Parameters
        ----------
        observations : str or `~astropy.table.Row` or list/Table of same
            Row/Table of MAST query results (e.g. output from `query_object`)
            or single/list of MAST Product Group Id(s) (obsid).
            See description `here <https://masttest.stsci.edu/api/v0/_c_a_o_mfields.html>`__.

        Returns
        -------
            response : list of `~requests.Response`
        """

        # getting the obsid list
        if type(observations) == Row:
            observations = observations["obsid"]
        if np.isscalar(observations):
            observations = [observations]
        if type(observations) == Table:
            observations = observations['obsid']

        service = 'Mast.Caom.Products'
        params = {'obsid': ','.join(observations)}

        return self._portal_api_connection.service_request_async(service, params)

    def filter_products(self, products, mrp_only=False, extension=None, **filters):
        """
        Takes an `~astropy.table.Table` of MAST observation data products and filters it based on given filters.

        Parameters
        ----------
        products : `~astropy.table.Table`
            Table containing data products to be filtered.
        mrp_only : bool, optional
            Default False. When set to true only "Minimum Recommended Products" will be returned.
        extension : string or array, optional
            Default None. Option to filter by file extension.
        **filters :
            Filters to be applied.  Valid filters are all products fields listed
            `here <https://masttest.stsci.edu/api/v0/_productsfields.html>`__.
            The column name is the keyword, with the argument being one or more acceptable values
            for that parameter.
            Filter behavior is AND between the filters and OR within a filter set.
            For example: productType="SCIENCE",extension=["fits","jpg"]

        Returns
        -------
        response : `~astropy.table.Table`
        """

        filter_mask = np.full(len(products), True, dtype=bool)

        # Applying the special filters (mrp_only and extension)
        if mrp_only:
            filter_mask &= (products['productGroupDescription'] == "Minimum Recommended Products")

        if extension:
            if type(extension) == str:
                extension = [extension]

            mask = np.full(len(products), False, dtype=bool)
            for elt in extension:
                mask |= [False if isinstance(x, np.ma.core.MaskedConstant) else x.endswith(elt)
                         for x in products["productFilename"]]
            filter_mask &= mask

        # Applying the rest of the filters
        for colname, vals in filters.items():

            if type(vals) == str:
                vals = [vals]

            mask = np.full(len(products), False, dtype=bool)
            for elt in vals:
                mask |= (products[colname] == elt)

            filter_mask &= mask

        return products[np.where(filter_mask)]

    def _download_files(self, products, base_dir, cache=True, cloud_only=False,):
        """
        Takes an `~astropy.table.Table` of data products and downloads them into the directory given by base_dir.

        Parameters
        ----------
        products : `~astropy.table.Table`
            Table containing products to be downloaded.
        base_dir : str
            Directory in which files will be downloaded.
        cache : bool
            Default is True. If file is found on disk it will not be downloaded again.
        cloud_only : bool, optional
            Default False. If set to True and cloud data access is enabled (see `enable_cloud_dataset`)
            files that are not found in the cloud will be skipped rather than downloaded from MAST
            as is the default behavior. If cloud access is not enables this argument as no affect.

        Returns
        -------
        response : `~astropy.table.Table`
        """

        manifest_array = []
        for data_product in products:

            local_path = os.path.join(base_dir, data_product['obs_collection'], data_product['obs_id'])
            data_url = self._portal_api_connection.MAST_DOWNLOAD_URL + "?uri=" + data_product["dataURI"]

            if not os.path.exists(local_path):
                os.makedirs(local_path)

            local_path = os.path.join(local_path, data_product['productFilename'])

            status = "COMPLETE"
            msg = None
            url = None

            try:
                if self._cloud_connection is not None and self._cloud_connection.is_supported(data_product):
                    try:
                        self._cloud_connection.download_file(data_product, local_path, cache)
                    except Exception as ex:
                        log.exception("Error pulling from S3 bucket: {}".format(ex))
                        if cloud_only:
                            log.warn("Skipping file...")
                            local_path = ""
                            status = "SKIPPED"
                        else:
                            log.warn("Falling back to mast download...")
                            self._download_file(data_url, local_path,
                                                cache=cache, head_safe=True, continuation=False)
                else:
                    self._download_file(data_url, local_path,
                                        cache=cache, head_safe=True, continuation=False)

                # check if file exists also this is where would perform md5,
                # and also check the filesize if the database reliably reported file sizes
                if (not os.path.isfile(local_path)) and (status != "SKIPPED"):
                    status = "ERROR"
                    msg = "File was not downloaded"
                    url = data_url

            except HTTPError as err:
                status = "ERROR"
                msg = "HTTPError: {0}".format(err)
                url = data_url

            manifest_array.append([local_path, status, msg, url])

        manifest = Table(rows=manifest_array, names=('Local Path', 'Status', 'Message', "URL"))

        return manifest

    def _download_curl_script(self, products, out_dir):
        """
        Takes an `~astropy.table.Table` of data products and downloads a curl script to pull the datafiles.

        Parameters
        ----------
        products : `~astropy.table.Table`
            Table containing products to be included in the curl script.
        out_dir : str
            Directory in which the curl script will be saved.

        Returns
        -------
        response : `~astropy.table.Table`
        """

        url_list = [("uri", url) for url in products['dataURI']]
        download_file = "mastDownload_" + time.strftime("%Y%m%d%H%M%S")
        local_path = os.path.join(out_dir.rstrip('/'), download_file + ".sh")

        response = self._download_file(self._portal_api_connection.MAST_BUNDLE_URL + ".sh",
                                       local_path, data=url_list, method="POST")

        status = "COMPLETE"
        msg = None

        if not os.path.isfile(local_path):
            status = "ERROR"
            msg = "Curl could not be downloaded"

        manifest = Table({'Local Path': [local_path],
                          'Status': [status],
                          'Message': [msg]})
        return manifest

    def download_products(self, products, download_dir=None,
                          cache=True, curl_flag=False, mrp_only=False, cloud_only=False, **filters):
        """
        Download data products.
        If cloud access is enabled, files will be downloaded from the cloud if possible.

        Parameters
        ----------
        products : str, list, `~astropy.table.Table`
            Either a single or list of obsids (as can be given to `get_product_list`),
            or a Table of products (as is returned by `get_product_list`)
        download_dir : str, optional
            Optional.  Directory to download files to.  Defaults to current directory.
        cache : bool, optional
            Default is True. If file is found on disc it will not be downloaded again.
            Note: has no affect when downloading curl script.
        curl_flag : bool, optional
            Default is False.  If true instead of downloading files directly, a curl script
            will be downloaded that can be used to download the data files at a later time.
        mrp_only : bool, optional
            Default False. When set to true only "Minimum Recommended Products" will be returned.
        cloud_only : bool, optional
            Default False. If set to True and cloud data access is enabled (see `enable_cloud_dataset`)
            files that are not found in the cloud will be skipped rather than downloaded from MAST
            as is the default behavior. If cloud access is not enables this argument as no affect.
        **filters :
            Filters to be applied.  Valid filters are all products fields returned by
            ``get_metadata("products")`` and 'extension' which is the desired file extension.
            The Column Name (or 'extension') is the keyword, with the argument being one or
            more acceptable values for that parameter.
            Filter behavior is AND between the filters and OR within a filter set.
            For example: productType="SCIENCE",extension=["fits","jpg"]

        Returns
        -------
        response : `~astropy.table.Table`
            The manifest of files downloaded, or status of files on disk if curl option chosen.
        """

        # If the products list is not already a table of products we need to
        # get the products and filter them appropriately
        if type(products) != Table:

            if type(products) == str:
                products = [products]

            # collect list of products
            product_lists = []
            for oid in products:
                product_lists.append(self.get_product_list(oid))

            products = vstack(product_lists)

        # apply filters
        products = self.filter_products(products, mrp_only, **filters)

        if not len(products):
            warnings.warn("No products to download.", NoResultsWarning)
            return

        # set up the download directory and paths
        if not download_dir:
            download_dir = '.'

        if curl_flag:  # don't want to download the files now, just the curl script
            manifest = self._download_curl_script(products, download_dir)

        else:
            base_dir = download_dir.rstrip('/') + "/mastDownload"
            manifest = self._download_files(products, base_dir, cache, cloud_only)

        return manifest

    @deprecated(since="v0.3.9", alternative="get_cloud_uris")
    def get_hst_s3_uris(self, data_products, include_bucket=True, full_url=False):
        return self.get_cloud_uris(data_products, include_bucket, full_url)

    def get_cloud_uris(self, data_products, include_bucket=True, full_url=False):
        """
        Takes an `~astropy.table.Table` of data products and returns the associated cloud data uris.

        Parameters
        ----------
        data_products : `~astropy.table.Table`
            Table containing products to be converted into cloud data uris.
        include_bucket : bool
            Default True. When false returns the path of the file relative to the
            top level cloud storage location.
            Must be set to False when using the full_url argument.
        full_url : bool
            Default False. Return an HTTP fetchable url instead of a cloud uri.
            Must set include_bucket to False to use this option.

        Returns
        -------
        response : list
            List of URIs generated from the data products, list way contain entries that are None
            if data_products includes products not found in the cloud.
        """

        if self._cloud_connection is None:
            raise AttributeError("Must enable s3 dataset before attempting to query the s3 information")

        return self._cloud_connection.get_cloud_uri_list(data_products, include_bucket, full_url)

    @deprecated(since="v0.3.9", alternative="get_cloud_uri")
    def get_hst_s3_uri(self, data_product, include_bucket=True, full_url=False):
        return self.get_cloud_uri(data_product, include_bucket, full_url)

    def get_cloud_uri(self, data_product, include_bucket=True, full_url=False):
        """
        For a given data product, returns the associated cloud URI.
        If the product is from a mission that does not support cloud access an
        exception is raised. If the mission is supported but the product
        cannot be found in the cloud, the returned path is None.

        Parameters
        ----------
        data_product : `~astropy.table.Row`
            Product to be converted into cloud data uri.
        include_bucket : bool
            Default True. When false returns the path of the file relative to the
            top level cloud storage location.
            Must be set to False when using the full_url argument.
        full_url : bool
            Default False. Return an HTTP fetchable url instead of a cloud uri.
            Must set include_bucket to False to use this option.

        Returns
        -------
        response : str or None
            Cloud URI generated from the data product. If the product cannot be
            found in the cloud, None is returned.
        """

        if self._cloud_connection is None:
            raise AttributeError("Must enable s3 dataset before attempting to query the s3 information")

        return self._cloud_connection.get_cloud_uri(data_product, include_bucket, full_url)


@async_to_sync
class MastClass(MastQueryWithLogin):
    """
    MAST query class.

    Class that allows direct programatic access to the MAST Portal,
    more flexible but less user friendly than `ObservationsClass`.
    """

    def _parse_result(self, responses, verbose=False):  # Used by the async_to_sync decorator functionality
        """
        Parse the results of a list of `~requests.Response` objects and returns an `~astropy.table.Table` of results.

        Parameters
        ----------
        responses : list of `~requests.Response`
            List of `~requests.Response` objects.
        verbose : bool
            (presently does nothing - there is no output with verbose set to
            True or False)
            Default False.  Setting to True provides more extensive output.

        Returns
        -------
        response : `~astropy.table.Table`
        """

        return self._portal_api_connection._parse_result(responses, verbose)

    @class_or_instance
    def service_request_async(self, service, params, pagesize=None, page=None, **kwargs):
        """
        Given a Mashup service and parameters, builds and excecutes a Mashup query.
        See documentation `here <https://mast.stsci.edu/api/v0/class_mashup_1_1_mashup_request.html>`__
        for information about how to build a Mashup request.

        Parameters
        ----------
        service : str
            The Mashup service to query.
        params : dict
            JSON object containing service parameters.
        pagesize : int, optional
            Default None.
            Can be used to override the default pagesize (set in configs) for this query only.
            E.g. when using a slow internet connection.
        page : int, optional
            Default None.
            Can be used to override the default behavior of all results being returned to obtain
            a specific page of results.
        **kwargs :
            See MashupRequest properties
            `here <https://mast.stsci.edu/api/v0/class_mashup_1_1_mashup_request.html>`__
            for additional keyword arguments.

        Returns
        -------
        response : list of `~requests.Response`
        """

        return self._portal_api_connection.service_request_async(service, params, pagesize, page, **kwargs)


Observations = ObservationsClass()
Mast = MastClass()
