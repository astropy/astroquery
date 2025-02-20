# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
MAST Observations
=================

This module contains various methods for querying MAST observations.
"""

from pathlib import Path
import warnings
import time
import os
from urllib.parse import quote

import numpy as np

from requests import HTTPError

import astropy.units as u
import astropy.coordinates as coord

from astropy.table import Table, Row, vstack
from astroquery import log
from astroquery.mast.cloud import CloudAccess

from ..utils import commons, async_to_sync
from ..utils.class_or_instance import class_or_instance
from ..exceptions import (InvalidQueryError, RemoteServiceError,
                          NoResultsWarning, InputWarning)

from . import utils
from .core import MastQueryWithLogin

__all__ = ['Observations', 'ObservationsClass',
           'MastClass', 'Mast']


@async_to_sync
class ObservationsClass(MastQueryWithLogin):
    """
    MAST Observations query class.

    Class for querying MAST observational data.
    """

    # Calling static class variables
    _caom_all = 'Mast.Caom.All'
    _caom_cone = 'Mast.Caom.Cone'
    _caom_filtered_position = 'Mast.Caom.Filtered.Position'
    _caom_filtered = 'Mast.Caom.Filtered'
    _caom_products = 'Mast.Caom.Products'

    def _parse_result(self, responses, *, verbose=False):  # Used by the async_to_sync decorator functionality
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
        Lists data missions archived by MAST and available through `astroquery.mast`.

        Returns
        -------
        response : list
            List of available missions.
        """

        # getting all the histogram information
        service = self._caom_all
        params = {}
        response = self._portal_api_connection.service_request_async(service, params, format='extjs')
        json_response = response[0].json()

        # getting the list of missions
        hist_data = json_response['data']['Tables'][0]['Columns']
        for facet in hist_data:
            if facet['text'] == "obs_collection":
                mission_info = facet['ExtendedProperties']['histObj']
                missions = sorted(mission_info)
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
        -------
        response : `~astropy.table.Table`
            The metadata table.
        """

        if query_type.lower() == "observations":
            colconf_name = self._caom_cone
        elif query_type.lower() == "products":
            colconf_name = self._caom_products
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

        # Separating any position info from the rest of the filters
        coordinates = criteria.pop('coordinates', None)
        objectname = criteria.pop('objectname', None)
        radius = criteria.pop('radius', 0.2*u.deg)

        # Build the mashup filter object and store it in the correct service_name entry
        if coordinates or objectname:
            mashup_filters = self._portal_api_connection.build_filter_set(self._caom_cone,
                                                                          self._caom_filtered_position,
                                                                          **criteria)
            coordinates = utils.parse_input_location(coordinates, objectname)
        else:
            mashup_filters = self._portal_api_connection.build_filter_set(self._caom_cone,
                                                                          self._caom_filtered,
                                                                          **criteria)

        # handle position info (if any)
        position = None

        if coordinates:
            # if radius is just a number we assume degrees
            radius = coord.Angle(radius, u.deg)

            # build the coordinates string needed by ObservationsClass._caom_filtered_position
            position = ', '.join([str(x) for x in (coordinates.ra.deg, coordinates.dec.deg, radius.deg)])

        return position, mashup_filters

    def enable_cloud_dataset(self, provider="AWS", profile=None, verbose=True):
        """
        Enable downloading public files from S3 instead of MAST.
        Requires the boto3 library to function.

        Parameters
        ----------
        provider : str
            Which cloud data provider to use.  We may in the future support multiple providers,
            though at the moment this argument is ignored.
        profile : str
            Profile to use to identify yourself to the cloud provider (usually in ~/.aws/config).
        verbose : bool
            Default True.
            Logger to display extra info and warning.
        """
        self._cloud_connection = CloudAccess(provider, profile, verbose)

    def disable_cloud_dataset(self):
        """
        Disables downloading public files from S3 instead of MAST.
        """
        self._cloud_connection = None

    @class_or_instance
    def query_region_async(self, coordinates, *, radius=0.2*u.deg, pagesize=None, page=None):
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

        # Put coordinates and radius into consistent format
        coordinates = commons.parse_coordinates(coordinates)

        # if radius is just a number we assume degrees
        radius = coord.Angle(radius, u.deg)

        service = self._caom_cone
        params = {'ra': coordinates.ra.deg,
                  'dec': coordinates.dec.deg,
                  'radius': radius.deg}

        return self._portal_api_connection.service_request_async(service, params, pagesize=pagesize, page=page)

    @class_or_instance
    def query_object_async(self, objectname, *, radius=0.2*u.deg, pagesize=None, page=None):
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

        return self.query_region_async(coordinates, radius=radius, pagesize=pagesize, page=page)

    @class_or_instance
    def query_criteria_async(self, *, pagesize=None, page=None, **criteria):
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
            one specific page of results.
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
            service = self._caom_filtered_position
            params = {"columns": "*",
                      "filters": mashup_filters,
                      "position": position}
        else:
            service = self._caom_filtered
            params = {"columns": "*",
                      "filters": mashup_filters}

        return self._portal_api_connection.service_request_async(service, params, pagesize=pagesize, page=page)

    def query_region_count(self, coordinates, *, radius=0.2*u.deg, pagesize=None, page=None):
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

        # build the coordinates string needed by ObservationsClass._caom_filtered_position
        coordinates = commons.parse_coordinates(coordinates)

        # if radius is just a number we assume degrees
        radius = coord.Angle(radius, u.deg)

        # turn coordinates into the format
        position = ', '.join([str(x) for x in (coordinates.ra.deg, coordinates.dec.deg, radius.deg)])

        service = self._caom_filtered_position
        params = {"columns": "COUNT_BIG(*)",
                  "filters": [],
                  "position": position}

        return int(self._portal_api_connection.service_request(service, params, pagesize, page)[0][0])

    def query_object_count(self, objectname, *, radius=0.2*u.deg, pagesize=None, page=None):
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
            one specific page of results.

        Returns
        -------
        response : int
        """

        coordinates = utils.resolve_object(objectname)

        return self.query_region_count(coordinates, radius=radius, pagesize=pagesize, page=page)

    def query_criteria_count(self, *, pagesize=None, page=None, **criteria):
        """
        Given an set of filters, returns the number of MAST observations meeting those criteria.

        Parameters
        ----------
        pagesize : int, optional
            Can be used to override the default pagesize.
            E.g. when using a slow internet connection.
        page : int, optional
            Can be used to override the default behavior of all results being returned to obtain
            one specific page of results.
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
            service = self._caom_filtered_position
            params = {"columns": "COUNT_BIG(*)",
                      "filters": mashup_filters,
                      "position": position}
        else:
            service = self._caom_filtered
            params = {"columns": "COUNT_BIG(*)",
                      "filters": mashup_filters}

        return self._portal_api_connection.service_request(service, params)[0][0].astype(int)

    def _filter_ffi_observations(self, observations):
        """
        Given a `~astropy.table.Row` or `~astropy.table.Table` of observations, filter out full-frame images (FFIs)
        from TESS and TICA. If any observations are filtered, warn the user.

        Parameters
        ----------
        observations : `~astropy.table.Row` or `~astropy.table.Table`
            Row/Table of MAST query results (e.g. output from `query_object`)

        Returns
        -------
        filtered_obs_table : filtered observations Table
        """
        obs_table = Table(observations)
        tess_ffis = obs_table[obs_table['target_name'] == 'TESS FFI']['obs_id']
        tica_ffis = obs_table[obs_table['target_name'] == 'TICA FFI']['obs_id']

        if tess_ffis.size:
            # Warn user if TESS FFIs exist
            log.warning("Because of their large size, Astroquery should not be used to "
                        "download TESS FFI products.\n"
                        "If you are looking for TESS image data for a specific target, "
                        "please use TESScut at https://mast.stsci.edu/tesscut/.\n"
                        "If you need a TESS image for an entire field, please see our "
                        "dedicated page for downloading larger quantities of TESS data at \n"
                        "https://archive.stsci.edu/tess/. Data products will not be fetched "
                        "for the following observations IDs: \n" + "\n".join(tess_ffis))

        if tica_ffis.size:
            # Warn user if TICA FFIs exist
            log.warning("Because of their large size, Astroquery should not be used to "
                        "download TICA FFI products.\n"
                        "Please see our dedicated page for downloading larger quantities of "
                        "TICA data: https://archive.stsci.edu/hlsp/tica.\n"
                        "Data products will not be fetched for the following "
                        "observation IDs: \n" + "\n".join(tica_ffis))

        # Filter out FFIs with a mask
        mask = (obs_table['target_name'] != 'TESS FFI') & (obs_table['target_name'] != 'TICA FFI')
        return obs_table[mask]

    @class_or_instance
    def get_product_list_async(self, observations):
        """
        Given a "Product Group Id" (column name obsid) returns a list of associated data products.
        Note that obsid is NOT the same as obs_id, and inputting obs_id values will result in
        an error. See column documentation `here <https://masttest.stsci.edu/api/v0/_productsfields.html>`__.

        To return unique data products, use ``Observations.get_unique_product_list``.

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
        if np.isscalar(observations):
            observations = np.array([observations])
        if isinstance(observations, Table) or isinstance(observations, Row):
            # Filter out TESS FFIs and TICA FFIs
            # Can only perform filtering on Row or Table because of access to `target_name` field
            observations = self._filter_ffi_observations(observations)
            observations = observations['obsid']
        if isinstance(observations, list):
            observations = np.array(observations)

        observations = observations[observations != ""]
        if observations.size == 0:
            raise InvalidQueryError("Observation list is empty, no associated products.")

        service = self._caom_products
        params = {'obsid': ','.join(observations)}

        return self._portal_api_connection.service_request_async(service, params)

    def filter_products(self, products, *, mrp_only=False, extension=None, **filters):
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
            if isinstance(extension, str):
                extension = [extension]

            mask = np.full(len(products), False, dtype=bool)
            for elt in extension:
                mask |= [False if isinstance(x, np.ma.core.MaskedConstant) else x.endswith(elt)
                         for x in products["productFilename"]]
            filter_mask &= mask

        # Applying the rest of the filters
        for colname, vals in filters.items():

            if isinstance(vals, str):
                vals = [vals]

            mask = np.full(len(products), False, dtype=bool)
            for elt in vals:
                mask |= (products[colname] == elt)

            filter_mask &= mask

        return products[np.where(filter_mask)]

    def download_file(self, uri, *, local_path=None, base_url=None, cache=True, cloud_only=False, verbose=True):
        """
        Downloads a single file based on the data URI

        Parameters
        ----------
        uri : str
            The product dataURI, e.g. mast:JWST/product/jw00736-o039_t001_miri_ch1-long_x1d.fits
        local_path : str
            Directory or filename to which the file will be downloaded.  Defaults to current working directory.
        base_url: str
            A base url to use when downloading.  Default is the MAST Portal API
        cache : bool
            Default is True. If file is found on disk it will not be downloaded again.
        cloud_only : bool, optional
            Default False. If set to True and cloud data access is enabled (see `enable_cloud_dataset`)
            files that are not found in the cloud will be skipped rather than downloaded from MAST
            as is the default behavior. If cloud access is not enables this argument as no affect.
        verbose : bool, optional
            Default True. Whether to show download progress in the console.

        Returns
        -------
        status: str
            download status message.  Either COMPLETE, SKIPPED, or ERROR.
        msg : str
            An error status message, if any.
        url : str
            The full url download path
        """

        # create the full data URL
        base_url = base_url if base_url else self._portal_api_connection.MAST_DOWNLOAD_URL
        data_url = base_url + "?uri=" + uri
        escaped_url = base_url + "?uri=" + quote(uri, safe=":/")

        # parse a local file path from local_path parameter.  Use current directory as default.
        filename = os.path.basename(uri)
        if not local_path:  # local file path is not defined
            local_path = filename
        else:
            path = Path(local_path)
            if not path.suffix:  # local_path is a directory
                local_path = path / filename  # append filename
                if not path.exists():  # create directory if it doesn't exist
                    path.mkdir(parents=True, exist_ok=True)

        # recreate the data_product key for cloud connection check
        data_product = {'dataURI': uri}

        status = "COMPLETE"
        msg = None
        url = None

        try:
            if self._cloud_connection is not None and self._cloud_connection.is_supported(data_product):
                try:
                    self._cloud_connection.download_file(data_product, local_path, cache, verbose)
                except Exception as ex:
                    log.exception("Error pulling from S3 bucket: {}".format(ex))
                    if cloud_only:
                        log.warning("Skipping file...")
                        local_path = ""
                        status = "SKIPPED"
                    else:
                        log.warning("Falling back to mast download...")
                        self._download_file(escaped_url, local_path,
                                            cache=cache, head_safe=True, continuation=False,
                                            verbose=verbose)
            else:
                self._download_file(escaped_url, local_path,
                                    cache=cache, head_safe=True, continuation=False,
                                    verbose=verbose)

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

        return status, msg, url

    def _download_files(self, products, base_dir, *, flat=False, cache=True, cloud_only=False, verbose=True):
        """
        Takes an `~astropy.table.Table` of data products and downloads them into the directory given by base_dir.

        Parameters
        ----------
        products : `~astropy.table.Table`
            Table containing products to be downloaded.
        base_dir : str
            Directory in which files will be downloaded.
        flat : bool
            Default is False.  If set to True, no subdirectories will be made for the
            downloaded files.
        cache : bool
            Default is True. If file is found on disk it will not be downloaded again.
        cloud_only : bool, optional
            Default False. If set to True and cloud data access is enabled (see `enable_cloud_dataset`)
            files that are not found in the cloud will be skipped rather than downloaded from MAST
            as is the default behavior. If cloud access is not enables this argument as no affect.
        verbose : bool, optional
            Default True. Whether to show download progress in the console.

        Returns
        -------
        response : `~astropy.table.Table`
        """

        manifest_array = []
        for data_product in products:

            # create the local file download path
            if not flat:
                local_path = os.path.join(base_dir, data_product['obs_collection'], data_product['obs_id'])
                if not os.path.exists(local_path):
                    os.makedirs(local_path)
            else:
                local_path = base_dir
            local_path = os.path.join(local_path, os.path.basename(data_product['productFilename']))

            # download the files
            status, msg, url = self.download_file(data_product["dataURI"], local_path=local_path,
                                                  cache=cache, cloud_only=cloud_only, verbose=verbose)

            manifest_array.append([local_path, status, msg, url])

        manifest = Table(rows=manifest_array, names=('Local Path', 'Status', 'Message', "URL"))

        return manifest

    def _download_curl_script(self, products, out_dir, verbose=True):
        """
        Takes an `~astropy.table.Table` of data products and downloads a curl script to pull the datafiles.

        Parameters
        ----------
        products : `~astropy.table.Table`
            Table containing products to be included in the curl script.
        out_dir : str
            Directory in which the curl script will be saved.
        verbose : bool, optional
            Default True. Whether to show download progress in the console.

        Returns
        -------
        response : `~astropy.table.Table`
        """

        url_list = [("uri", url) for url in products['dataURI']]
        download_file = "mastDownload_" + time.strftime("%Y%m%d%H%M%S") + ".sh"
        local_path = os.path.join(out_dir, download_file)

        self._download_file(self._portal_api_connection.MAST_BUNDLE_URL + ".sh",
                            local_path, data=url_list, method="POST", verbose=verbose)

        status = "COMPLETE"
        msg = None

        if not os.path.isfile(local_path):
            status = "ERROR"
            msg = "Curl could not be downloaded"

        manifest = Table({'Local Path': [local_path],
                          'Status': [status],
                          'Message': [msg]})
        return manifest

    def download_products(self, products, *, download_dir=None, flat=False,
                          cache=True, curl_flag=False, mrp_only=False, cloud_only=False, verbose=True,
                          **filters):
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
        flat : bool, optional
            Default is False.  If set to True, and download_dir is specified, it will put
            all files into download_dir without subdirectories.  Or if set to True and
            download_dir is not specified, it will put files in the current directory,
            again with no subdirs.  The default of False puts files into the standard
            directory structure of "mastDownload/<obs_collection>/<obs_id>/".  If
            curl_flag=True, the flat flag has no effect, as astroquery does not control
            how MAST generates the curl download script.
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
        verbose : bool, optional
            Default True. Whether to show download progress in the console.
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
        # If the products list is a row we need to cast it as a table
        if isinstance(products, Row):
            products = Table(products, masked=True)

        # If the products list is not already a table of products we need to
        # get the products and filter them appropriately
        if not isinstance(products, Table):

            if isinstance(products, str):
                products = [products]

            # collect list of products
            product_lists = []
            for oid in products:
                product_lists.append(self.get_product_list(oid))

            products = vstack(product_lists)

        # apply filters
        products = self.filter_products(products, mrp_only=mrp_only, **filters)

        # remove duplicate products
        products = utils.remove_duplicate_products(products, 'dataURI')

        if not len(products):
            warnings.warn("No products to download.", NoResultsWarning)
            return

        # set up the download directory and paths
        if not download_dir:
            download_dir = '.'

        if curl_flag:  # don't want to download the files now, just the curl script
            if flat:
                # flat=True doesn't work with curl_flag=True, so issue a warning
                warnings.warn("flat=True has no effect on curl downloads.", InputWarning)
            manifest = self._download_curl_script(products,
                                                  download_dir)

        else:
            if flat:
                base_dir = download_dir
            else:
                base_dir = os.path.join(download_dir, "mastDownload")
            manifest = self._download_files(products,
                                            base_dir=base_dir, flat=flat,
                                            cache=cache,
                                            cloud_only=cloud_only,
                                            verbose=verbose)

        return manifest

    def get_cloud_uris(self, data_products=None, *, include_bucket=True, full_url=False, pagesize=None, page=None,
                       mrp_only=False, extension=None, filter_products={}, **criteria):
        """
        Given an `~astropy.table.Table` of data products or query criteria and filter parameters,
        returns the associated cloud data URIs.

        Parameters
        ----------
        data_products : `~astropy.table.Table`, list
            Table containing products or list of MAST uris to be converted into cloud data uris.
            If provided, this will supercede page_size, page, or any keyword arguments passed in as criteria.
        include_bucket : bool
            Default True. When False, returns the path of the file relative to the
            top level cloud storage location.
            Must be set to False when using the full_url argument.
        full_url : bool
            Default False. Return an HTTP fetchable url instead of a cloud uri.
            Must set include_bucket to False to use this option.
        pagesize : int, optional
            Default None. Can be used to override the default pagesize when making a query.
            E.g. when using a slow internet connection. Query criteria must also be provided.
        page : int, optional
            Default None. Can be used to override the default behavior of all results being returned for a query
            to obtain one specific page of results. Query criteria must also be provided.
        mrp_only : bool, optional
            Default False. When set to True, only "Minimum Recommended Products" will be returned.
        extension : string or array, optional
            Default None. Option to filter by file extension.
        filter_products : dict, optional
            Filters to be applied to data products.  Valid filters are all products fields listed
            `here <https://masttest.stsci.edu/api/v0/_productsfields.html>`__.
            The column name as a string is the key. The corresponding value is one
            or more acceptable values for that parameter.
            Filter behavior is AND between the filters and OR within a filter set.
            For example: {"productType": "SCIENCE", "extension"=["fits","jpg"]}
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
        response : list
            List of URIs generated from the data products. May contain entries that are None
            if data_products includes products not found in the cloud.
        """

        if self._cloud_connection is None:
            raise RemoteServiceError(
                'Please enable anonymous cloud access by calling `enable_cloud_dataset` method. '
                'Refer to `~astroquery.mast.ObservationsClass.enable_cloud_dataset` documentation for more info.')

        if data_products is None:
            if not criteria:
                raise InvalidQueryError(
                    'Please provide either a `~astropy.table.Table` of data products or query criteria.'
                )
            else:
                # Get table of observations based on query criteria
                obs = self.query_criteria(pagesize=pagesize, page=page, **criteria)

                if not len(obs):
                    # Warning raised by ~astroquery.mast.ObservationsClass.query_criteria
                    return

                # Return list of associated data products
                data_products = self.get_product_list(obs)

        if isinstance(data_products, Table):
            # Filter product list
            data_products = self.filter_products(data_products, mrp_only=mrp_only, extension=extension,
                                                 **filter_products)
        else:  # data_products is a list of URIs
            # Warn if trying to supply filters
            if filter_products or extension or mrp_only:
                warnings.warn('Filtering is not supported when providing a list of MAST URIs. '
                              'To apply filters, please provide query criteria or a table of data products '
                              'as returned by `Observations.get_product_list`', InputWarning)

        if not len(data_products):
            warnings.warn('No matching products to fetch associated cloud URIs.', NoResultsWarning)
            return

        # Remove duplicate products
        data_products = utils.remove_duplicate_products(data_products, 'dataURI')
        return self._cloud_connection.get_cloud_uri_list(data_products, include_bucket, full_url)

    def get_cloud_uri(self, data_product, *, include_bucket=True, full_url=False):
        """
        For a given data product, returns the associated cloud URI.
        If the product is from a mission that does not support cloud access an
        exception is raised. If the mission is supported but the product
        cannot be found in the cloud, the returned path is None.

        Parameters
        ----------
        data_product : `~astropy.table.Row`, str
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
            raise RemoteServiceError(
                'Please enable anonymous cloud access by calling `enable_cloud_dataset` method. '
                'Refer to `~astroquery.mast.ObservationsClass.enable_cloud_dataset` documentation for more info.')

        # Query for product URIs
        return self._cloud_connection.get_cloud_uri(data_product, include_bucket, full_url)

    def get_unique_product_list(self, observations):
        """
        Given a "Product Group Id" (column name obsid), returns a list of associated data products with
        unique dataURIs. Note that obsid is NOT the same as obs_id, and inputting obs_id values will result in
        an error. See column documentation `here <https://masttest.stsci.edu/api/v0/_productsfields.html>`__.

        Parameters
        ----------
        observations : str or `~astropy.table.Row` or list/Table of same
            Row/Table of MAST query results (e.g. output from `query_object`)
            or single/list of MAST Product Group Id(s) (obsid).
            See description `here <https://masttest.stsci.edu/api/v0/_c_a_o_mfields.html>`__.

        Returns
        -------
        unique_products : `~astropy.table.Table`
            Table containing products with unique dataURIs.
        """
        products = self.get_product_list(observations)
        unique_products = utils.remove_duplicate_products(products, 'dataURI')
        if len(unique_products) < len(products):
            log.info("To return all products, use `Observations.get_product_list`")
        return unique_products


@async_to_sync
class MastClass(MastQueryWithLogin):
    """
    MAST query class.

    Class that allows direct programmatic access to the MAST Portal,
    more flexible but less user friendly than `ObservationsClass`.
    """

    def _parse_result(self, responses, *, verbose=False):  # Used by the async_to_sync decorator functionality
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
    def service_request_async(self, service, params, *, pagesize=None, page=None, **kwargs):
        """
        Given a Mashup service and parameters, builds and executes a Mashup query.
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

    def mast_query(self, service, columns=None, **kwargs):
        """
        Given a Mashup service and parameters as keyword arguments, builds and excecutes a Mashup query.

        Parameters
        ----------
        service : str
            The Mashup service to query.
        columns : str, optional
            Specifies the columns to be returned as a comma-separated list, e.g. "ID, ra, dec".
        **kwargs :
            Service-specific parameters and MashupRequest properties. See the
            `service documentation <https://mast.stsci.edu/api/v0/_services.html>`__ and the
            `MashupRequest Class Reference <https://mast.stsci.edu/api/v0/class_mashup_1_1_mashup_request.html>`__
            for valid keyword arguments.

        Returns
        -------
        response : `~astropy.table.Table`
        """
        # Specific keywords related to positional and MashupRequest parameters.
        position_keys = ['ra', 'dec', 'radius', 'position']
        request_keys = ['format', 'data', 'filename', 'timeout', 'clearcache',
                        'removecache', 'removenullcolumns', 'page', 'pagesize']

        # Explicit formatting for Mast's filtered services
        if 'filtered' in service.lower():

            # Separating the filter params from the positional and service_request method params.
            filters = [{'paramName': k, 'values': kwargs[k]} for k in kwargs
                       if k.lower() not in position_keys+request_keys]
            position_params = {k: v for k, v in kwargs.items() if k.lower() in position_keys}
            request_params = {k: v for k, v in kwargs.items() if k.lower() in request_keys}

            # Mast's filtered services require at least one filter
            if filters == []:
                raise InvalidQueryError("Please provide at least one filter.")

            # Building 'params' for Mast.service_request
            if columns is None:
                columns = '*'

            params = {'columns': columns,
                      'filters': filters,
                      **position_params
                      }
        else:

            # Separating service specific params from service_request method params
            params = {k: v for k, v in kwargs.items() if k.lower() not in request_keys}
            request_params = {k: v for k, v in kwargs.items() if k.lower() in request_keys}

            # Warning for wrong input
            if columns is not None:
                warnings.warn("'columns' parameter will not mask non-filtered services", InputWarning)

        return self.service_request(service, params, **request_params)


Observations = ObservationsClass()
Mast = MastClass()
