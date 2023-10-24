# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
MAST Collections
================

This module contains various methods for querying MAST collections such as catalogs.
"""

import warnings
import os
import time

from requests import HTTPError

import astropy.units as u
import astropy.coordinates as coord

from astropy.table import Table, Row

from ..utils import commons, async_to_sync
from ..utils.class_or_instance import class_or_instance
from ..exceptions import InvalidQueryError, MaxResultsWarning, InputWarning

from . import utils
from .core import MastQueryWithLogin


__all__ = ['Catalogs', 'CatalogsClass']


@async_to_sync
class CatalogsClass(MastQueryWithLogin):
    """
    MAST catalog query class.

    Class for querying MAST catalog data.
    """

    def __init__(self):

        super().__init__()

        services = {"panstarrs": {"path": "panstarrs/{data_release}/{table}.json",
                                  "args": {"data_release": "dr2", "table": "mean"}}}

        self._service_api_connection.set_service_params(services, "catalogs", True)

        self.catalog_limit = None
        self._current_connection = None

    def _parse_result(self, response, *, verbose=False):

        results_table = self._current_connection._parse_result(response, verbose=verbose)

        if len(results_table) == self.catalog_limit:
            warnings.warn("Maximum catalog results returned, may not include all sources within radius.",
                          MaxResultsWarning)

        return results_table

    @class_or_instance
    def query_region_async(self, coordinates, *, radius=0.2*u.deg, catalog="Hsc",
                           version=None, pagesize=None, page=None, **kwargs):
        """
        Given a sky position and radius, returns a list of catalog entries.
        See column documentation for specific catalogs `here <https://mast.stsci.edu/api/v0/pages.html>`__.

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
        catalog : str, optional
            Default HSC.
            The catalog to be queried.
        version : int, optional
            Version number for catalogs that have versions. Default is highest version.
        pagesize : int, optional
            Default None.
            Can be used to override the default pagesize for (set in configs) this query only.
            E.g. when using a slow internet connection.
        page : int, optional
            Default None.
            Can be used to override the default behavior of all results being returned to obtain a
            specific page of results.
        **kwargs
            Other catalog-specific keyword args.
            These can be found in the (service documentation)[https://mast.stsci.edu/api/v0/_services.html]
            for specific catalogs. For example one can specify the magtype for an HSC search.

        Returns
        -------
        response : list of `~requests.Response`
        """

        # Put coordinates and radius into consistent format
        coordinates = commons.parse_coordinates(coordinates)

        # if radius is just a number we assume degrees
        radius = coord.Angle(radius, u.deg)

        # basic params
        params = {'ra': coordinates.ra.deg,
                  'dec': coordinates.dec.deg,
                  'radius': radius.deg}

        # Determine API connection and service name
        if catalog.lower() in self._service_api_connection.SERVICES:
            self._current_connection = self._service_api_connection
            service = catalog
        else:
            self._current_connection = self._portal_api_connection

            # Sorting out the non-standard portal service names
            if catalog.lower() == "hsc":
                if version == 2:
                    service = "Mast.Hsc.Db.v2"
                else:
                    if version not in (3, None):
                        warnings.warn("Invalid HSC version number, defaulting to v3.", InputWarning)
                    service = "Mast.Hsc.Db.v3"

                self.catalog_limit = kwargs.get('nr', 50000)

                # Hsc specific parameters (can be overridden by user)
                params['nr'] = 50000
                params['ni'] = 1
                params['magtype'] = 1

            elif catalog.lower() == "galex":
                service = "Mast.Galex.Catalog"
                self.catalog_limit = kwargs.get('maxrecords', 50000)

                # galex specific parameters (can be overridden by user)
                params['maxrecords'] = 50000

            elif catalog.lower() == "gaia":
                if version == 1:
                    service = "Mast.Catalogs.GaiaDR1.Cone"
                else:
                    if version not in (None, 2):
                        warnings.warn("Invalid Gaia version number, defaulting to DR2.", InputWarning)
                    service = "Mast.Catalogs.GaiaDR2.Cone"

            elif catalog.lower() == 'plato':
                if version in (None, 1):
                    service = "Mast.Catalogs.Plato.Cone"
                else:
                    warnings.warn("Invalid PLATO catalog version number, defaulting to DR1.", InputWarning)
                    service = "Mast.Catalogs.Plato.Cone"

            else:
                service = "Mast.Catalogs." + catalog + ".Cone"
                self.catalog_limit = None

        # adding additional user specified parameters
        for prop, value in kwargs.items():
            params[prop] = value

        # Parameters will be passed as JSON objects only when accessing the PANSTARRS API
        use_json = catalog.lower() == 'panstarrs'

        return self._current_connection.service_request_async(service, params, pagesize=pagesize, page=page,
                                                              use_json=use_json)

    @class_or_instance
    def query_object_async(self, objectname, *, radius=0.2*u.deg, catalog="Hsc",
                           pagesize=None, page=None, version=None, **kwargs):
        """
        Given an object name, returns a list of catalog entries.
        See column documentation for specific catalogs `here <https://mast.stsci.edu/api/v0/pages.html>`__.

        Parameters
        ----------
        objectname : str
            The name of the target around which to search.
        radius : str or `~astropy.units.Quantity` object, optional
            Default 0.2 degrees.
            The string must be parsable by `~astropy.coordinates.Angle`.
            The appropriate `~astropy.units.Quantity` object from
            `~astropy.units` may also be used. Defaults to 0.2 deg.
        catalog : str, optional
            Default HSC.
            The catalog to be queried.
        pagesize : int, optional
            Default None.
            Can be used to override the default pagesize for (set in configs) this query only.
            E.g. when using a slow internet connection.
        page : int, optional
            Defaulte None.
            Can be used to override the default behavior of all results being returned
            to obtain a specific page of results.
        version : int, optional
            Version number for catalogs that have versions. Default is highest version.
        **kwargs
            Catalog-specific keyword args.
            These can be found in the `service documentation <https://mast.stsci.edu/api/v0/_services.html>`__.
            for specific catalogs. For example one can specify the magtype for an HSC search.

        Returns
        -------
        response : list of `~requests.Response`
        """

        coordinates = utils.resolve_object(objectname)

        return self.query_region_async(coordinates,
                                       radius=radius,
                                       catalog=catalog,
                                       version=version,
                                       pagesize=pagesize,
                                       page=page,
                                       **kwargs)

    @class_or_instance
    def query_criteria_async(self, catalog, *, pagesize=None, page=None, **criteria):
        """
        Given an set of filters, returns a list of catalog entries.
        See column documentation for specific catalogs `here <https://mast.stsci.edu/api/v0/pages.html>`__.

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
            and all fields listed in the column documentation for the catalog being queried.
            The Column Name is the keyword, with the argument being one or more acceptable values for that parameter,
            except for fields with a float datatype where the argument should be in the form [minVal, maxVal].
            For non-float type criteria wildcards maybe used (both * and % are considered wildcards), however
            only one wildcarded value can be processed per criterion.
            RA and Dec must be given in decimal degrees, and datetimes in MJD.
            For example: filters=["FUV","NUV"],proposal_pi="Ost*",t_max=[52264.4586,54452.8914]
            For catalogs available through Catalogs.MAST (PanSTARRS), the Column Name is the keyword, and the argument
            should be either an acceptable value for that parameter, or a list consisting values, or  tuples of
            decorator, value pairs (decorator, value). In addition, columns may be used to select the return columns,
            consisting of a list of column names. Results may also be sorted through the query with the parameter
            sort_by composed of either a single Column Name to sort ASC, or a list of Column Nmaes to sort ASC or
            tuples of Column Name and Direction (ASC, DESC) to indicate sort order (Column Name, DESC).
            Detailed information of Catalogs.MAST criteria usage can
            be found `here <https://catalogs.mast.stsci.edu/docs/index.html>`__.

        Returns
        -------
        response : list of `~requests.Response`
        """

        # Separating any position info from the rest of the filters
        coordinates = criteria.pop('coordinates', None)
        objectname = criteria.pop('objectname', None)
        radius = criteria.pop('radius', 0.2*u.deg)

        if objectname or coordinates:
            coordinates = utils.parse_input_location(coordinates, objectname)

        # if radius is just a number we assume degrees
        radius = coord.Angle(radius, u.deg)

        # build query
        params = {}
        if coordinates:
            params["ra"] = coordinates.ra.deg
            params["dec"] = coordinates.dec.deg
            params["radius"] = radius.deg

        # Determine API connection, service name, and build filter set
        filters = None
        if catalog.lower() in self._service_api_connection.SERVICES:
            self._current_connection = self._service_api_connection
            service = catalog

            if not self._current_connection.check_catalogs_criteria_params(criteria):
                raise InvalidQueryError("At least one non-positional criterion must be supplied.")

            for prop, value in criteria.items():
                params[prop] = value

        else:
            self._current_connection = self._portal_api_connection

            if catalog.lower() == "tic":
                service = "Mast.Catalogs.Filtered.Tic"
                if coordinates or objectname:
                    service += ".Position"
                service += ".Rows"  # Using the rowstore version of the query for speed
                filters = self._current_connection.build_filter_set("Mast.Catalogs.Tess.Cone",
                                                                    service, **criteria)
                params["columns"] = "*"
            elif catalog.lower() == "ctl":
                service = "Mast.Catalogs.Filtered.Ctl"
                if coordinates or objectname:
                    service += ".Position"
                service += ".Rows"  # Using the rowstore version of the query for speed
                filters = self._current_connection.build_filter_set("Mast.Catalogs.Tess.Cone",
                                                                    service, **criteria)
                params["columns"] = "*"
            elif catalog.lower() == "diskdetective":
                service = "Mast.Catalogs.Filtered.DiskDetective"
                if coordinates or objectname:
                    service += ".Position"
                filters = self._current_connection.build_filter_set("Mast.Catalogs.Dd.Cone",
                                                                    service, **criteria)
            else:
                raise InvalidQueryError("Criteria query not available for {}".format(catalog))

            if not filters:
                raise InvalidQueryError("At least one non-positional criterion must be supplied.")
            params["filters"] = filters

        # Parameters will be passed as JSON objects only when accessing the PANSTARRS API
        use_json = catalog.lower() == 'panstarrs'

        return self._current_connection.service_request_async(service, params, pagesize=pagesize, page=page,
                                                              use_json=use_json)

    @class_or_instance
    def query_hsc_matchid_async(self, match, *, version=3, pagesize=None, page=None):
        """
        Returns all the matches for a given Hubble Source Catalog MatchID.

        Parameters
        ----------
        match : int or `~astropy.table.Row`
            The matchID or HSC entry to return matches for.
        version : int, optional
            The HSC version to match against. Default is v3.
        pagesize : int, optional
            Can be used to override the default pagesize.
            E.g. when using a slow internet connection.
        page : int, optional
            Can be used to override the default behavior of all results being returned to obtain
            one specific page of results.

        Returns
        -------
        response : list of `~requests.Response`
        """

        self._current_connection = self._portal_api_connection

        if isinstance(match, Row):
            match = match["MatchID"]
        match = str(match)  # np.int64 gives json serializer problems, so stringify right here

        if version == 2:
            service = "Mast.HscMatches.Db.v2"
        else:
            if version not in (3, None):
                warnings.warn("Invalid HSC version number, defaulting to v3.", InputWarning)
            service = "Mast.HscMatches.Db.v3"

        params = {"input": match}

        return self._current_connection.service_request_async(service, params, pagesize=pagesize, page=page)

    @class_or_instance
    def get_hsc_spectra_async(self, *, pagesize=None, page=None):
        """
        Returns all Hubble Source Catalog spectra.

        Parameters
        ----------
        pagesize : int, optional
            Can be used to override the default pagesize.
            E.g. when using a slow internet connection.
        page : int, optional
            Can be used to override the default behavior of all results being returned to obtain
            one specific page of results.

        Returns
        -------
        response : list of `~requests.Response`
        """

        self._current_connection = self._portal_api_connection

        service = "Mast.HscSpectra.Db.All"
        params = {}

        return self._current_connection.service_request_async(service, params, pagesize, page)

    def download_hsc_spectra(self, spectra, *, download_dir=None, cache=True, curl_flag=False):
        """
        Download one or more Hubble Source Catalog spectra.

        Parameters
        ----------
        spectra : `~astropy.table.Table` or `~astropy.table.Row`
            One or more HSC spectra to be downloaded.
        download_dir : str, optional
           Specify the base directory to download spectra into.
           Spectra will be saved in the subdirectory download_dir/mastDownload/HSC.
           If download_dir is not specified the base directory will be '.'.
        cache : bool, optional
            Default is True. If file is found on disc it will not be downloaded again.
            Note: has no affect when downloading curl script.
        curl_flag : bool, optional
            Default is False.  If true instead of downloading files directly, a curl script
            will be downloaded that can be used to download the data files at a later time.

        Returns
        -------
        response : list of `~requests.Response`
        """

        # if spectra is not a Table, put it in a list
        if isinstance(spectra, Row):
            spectra = [spectra]

        # set up the download directory and paths
        if not download_dir:
            download_dir = '.'

        if curl_flag:  # don't want to download the files now, just the curl script

            download_file = "mastDownload_" + time.strftime("%Y%m%d%H%M%S")

            url_list = []
            path_list = []
            for spec in spectra:
                if spec['SpectrumType'] < 2:
                    url_list.append('https://hla.stsci.edu/cgi-bin/getdata.cgi?config=ops&dataset={0}'
                                    .format(spec['DatasetName']))

                else:
                    url_list.append('https://hla.stsci.edu/cgi-bin/ecfproxy?file_id={0}'
                                    .format(spec['DatasetName']) + '.fits')

                path_list.append(download_file + "/HSC/" + spec['DatasetName'] + '.fits')

            description_list = [""]*len(spectra)
            producttype_list = ['spectrum']*len(spectra)

            service = "Mast.Bundle.Request"
            params = {"urlList": ",".join(url_list),
                      "filename": download_file,
                      "pathList": ",".join(path_list),
                      "descriptionList": list(description_list),
                      "productTypeList": list(producttype_list),
                      "extension": 'curl'}

            response = self._portal_api_connection.service_request_async(service, params)
            bundler_response = response[0].json()

            local_path = os.path.join(download_dir, "{}.sh".format(download_file))
            self._download_file(bundler_response['url'], local_path, head_safe=True, continuation=False)

            status = "COMPLETE"
            msg = None
            url = None

            if not os.path.isfile(local_path):
                status = "ERROR"
                msg = "Curl could not be downloaded"
                url = bundler_response['url']
            else:
                missing_files = [x for x in bundler_response['statusList'].keys()
                                 if bundler_response['statusList'][x] != 'COMPLETE']
                if len(missing_files):
                    msg = "{} files could not be added to the curl script".format(len(missing_files))
                    url = ",".join(missing_files)

            manifest = Table({'Local Path': [local_path],
                              'Status': [status],
                              'Message': [msg],
                              "URL": [url]})

        else:
            base_dir = download_dir.rstrip('/') + "/mastDownload/HSC"

            if not os.path.exists(base_dir):
                os.makedirs(base_dir)

            manifest_array = []
            for spec in spectra:

                if spec['SpectrumType'] < 2:
                    data_url = f'https://hla.stsci.edu/cgi-bin/getdata.cgi?config=ops&dataset={spec["DatasetName"]}'
                else:
                    data_url = f'https://hla.stsci.edu/cgi-bin/ecfproxy?file_id={spec["DatasetName"]}.fits'

                local_path = os.path.join(base_dir, f'{spec["DatasetName"]}.fits')

                status = "COMPLETE"
                msg = None
                url = None

                try:
                    self._download_file(data_url, local_path, cache=cache, head_safe=True)

                    # check file size also this is where would perform md5
                    if not os.path.isfile(local_path):
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


Catalogs = CatalogsClass()
