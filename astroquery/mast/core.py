# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
MAST Portal
===========

Module to query the Barbara A. Mikulski Archive for Space Telescopes (MAST).

"""

from __future__ import print_function, division

import warnings
import json
import time
import os

import numpy as np

from requests import HTTPError

import astropy.units as u
import astropy.coordinates as coord

from astropy.table import Table, Row, vstack
from astropy.extern.six.moves.urllib.parse import quote as urlencode
from astropy.utils.exceptions import AstropyWarning

from ..query import BaseQuery
from ..utils import commons, async_to_sync
from ..utils.class_or_instance import class_or_instance
from ..exceptions import TimeoutError, InvalidQueryError, NoResultsWarning
from . import conf


__all__ = ['Observations', 'ObservationsClass',
           'Mast', 'MastClass']


class ResolverError(Exception):
    pass


class InputWarning(AstropyWarning):
    pass


def _prepare_service_request_string(json_obj):
    """
    Takes a mashup JSON request object and turns it into a url-safe string.

    Parameters
    ----------
    json_obj : dict
        A Mashup request JSON object (python dictionary).

    Returns
    -------
    response : str
        URL encoded Mashup Request string.
    """
    requestString = json.dumps(json_obj)
    requestString = urlencode(requestString)
    return "request="+requestString


def _mashup_json_to_table(json_obj):
    """
    Takes a JSON object as returned from a Mashup request and turns it into an `astropy.table.Table`.

    Parameters
    ----------
    json_obj : dict
        A Mashup response JSON object (python dictionary)

    Returns
    -------
    response: `astropy.table.Table`
    """

    dataTable = Table()

    if not (json_obj.get('fields') and json_obj.get('data')):
        raise KeyError("Missing required key(s) 'data' and/or 'fields.'")

    for col, atype in [(x['name'], x['type']) for x in json_obj['fields']]:
        if atype == "string":
            atype = "str"
        if atype == "boolean":
            atype = "bool"
        dataTable[col] = np.array([x.get(col, None) for x in json_obj['data']], dtype=atype)

    # Removing "_selected_" column
    if "_selected_" in dataTable.colnames:
        dataTable.remove_column("_selected_")

    return dataTable


@async_to_sync
class MastClass(BaseQuery):
    """
    MAST query class.

    Class that allows direct programatic access to the MAST Portal,
    more flexible but less user friendly than `ObservationsClass`.
    """

    def __init__(self):

        super(MastClass, self).__init__()

        self._MAST_REQUEST_URL = conf.server + "/api/v0/invoke"
        self._MAST_DOWNLOAD_URL = conf.server + "/api/v0/download/file/"
        self._COLUMNS_CONFIG_URL = conf.server + "/portal/Mashup/Mashup.asmx/columnsconfig"

        self.TIMEOUT = conf.timeout
        self.PAGESIZE = conf.pagesize

    def _request(self, method, url, params=None, data=None, headers=None,
                 files=None, stream=False, auth=None, retrieve_all=True):
        """
        Override of the parent method:
        A generic HTTP request method, similar to ``requests.Session.request``

        This is a low-level method not generally intended for use by astroquery
        end-users.

        The main difference in this function is that it takes care of the long
        polling requirements of the mashup server.
        Thus the cache parameter of the parent method is hard coded to false
        (the MAST server does it's own caching, no need to cache locally and it
        interferes with follow requests after an 'Executing' response was returned.)
        Also parameters that allow for file download through this method are removed


        Parameters
        ----------
        method : 'GET' or 'POST'
        url : str
        params : None or dict
        data : None or dict
        headers : None or dict
        auth : None or dict
        files : None or dict
        stream : bool
            See ``requests.request``
        retrieve_all : bool
            Default True. Retrieve all pages of data or just the one indicated in the params value.

        Returns
        -------
        response : ``requests.Response``
            The response from the server.
        """

        startTime = time.time()
        allResponses = []
        totalPages = 1
        curPage = 0

        while curPage < totalPages:
            status = "EXECUTING"

            while status == "EXECUTING":
                response = super(MastClass, self)._request(method, url, params=params, data=data,
                                                           headers=headers, files=files, cache=False,
                                                           stream=stream, auth=auth)

                if (time.time() - startTime) >= self.TIMEOUT:
                    raise TimeoutError("Timeout limit of {} exceeded.".format(self.TIMEOUT))

                result = response.json()
                status = result.get("status")

            allResponses.append(response)

            if (status != "COMPLETE") or (not retrieve_all):
                break

            paging = result.get("paging")
            if paging is None:
                break
            totalPages = paging['pagesFiltered']
            curPage = paging['page']

            data = data.replace("page%22%3A%20"+str(curPage)+"%2C", "page%22%3A%20"+str(curPage+1)+"%2C")

        return allResponses

    def _parse_result(self, responses, verbose=False):
        """
        Parse the results of a list of ``requests.Response`` objects and returns an `astropy.table.Table` of results.

        Parameters
        ----------
        responses : list of ``requests.Response``
            List of ``requests.Response`` objects.
        verbose : bool
            (presently does nothing - there is no output with verbose set to
            True or False)
            Default False.  Setting to True provides more extensive output.
        """

        resultList = []

        for resp in responses:
            result = resp.json()
            resTable = _mashup_json_to_table(result)
            resultList.append(resTable)

        return vstack(resultList)

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
        response: list of ``requests.Response``
        """

        # setting up pagination
        if not pagesize:
            pagesize = self.PAGESIZE
        if not page:
            page = 1
            retrieveAll = True
        else:
            retrieveAll = False

        headers = {"User-Agent": self._session.headers["User-Agent"],
                   "Content-type": "application/x-www-form-urlencoded",
                   "Accept": "text/plain"}

        mashupRequest = {'service': service,
                         'params': params,
                         'format': 'json',
                         'pagesize': pagesize,
                         'page': page}

        for prop, value in kwargs.items():
            mashupRequest[prop] = value

        reqString = _prepare_service_request_string(mashupRequest)
        response = self._request("POST", self._MAST_REQUEST_URL, data=reqString, headers=headers,
                                 retrieve_all=retrieveAll)

        return response

    def _resolve_object(self, objectname):
        """
        Resolves an object name to a position on the sky.

        Parameters
        ----------
        objectname : str
            Name of astronomical object to resolve.
        """

        service = 'Mast.Name.Lookup'
        params = {'input': objectname,
                  'format': 'json'}

        response = self.service_request_async(service, params)

        result = response[0].json()

        if len(result['resolvedCoordinate']) == 0:
            raise ResolverError("Could not resolve {} to a sky position.".format(objectname))

        ra = result['resolvedCoordinate'][0]['ra']
        dec = result['resolvedCoordinate'][0]['decl']
        coordinates = coord.SkyCoord(ra, dec, unit="deg")

        return coordinates


@async_to_sync
class ObservationsClass(MastClass):
    """
    MAST Observations query class.

    Class for querying MAST observational data.
    """

    def __init__(self):

        super(ObservationsClass, self).__init__()

        self._caomCols = None  # Hold Mast.Caom.Cone columns config

    def _get_caom_col_config(self):
        """
        Gets the columnsConfig entry for Mast.Caom.Cone and stores it in self.caomCols.
        """

        headers = {"User-Agent": self._session.headers["User-Agent"],
                   "Content-type": "application/x-www-form-urlencoded",
                   "Accept": "text/plain"}

        response = Mast._request("POST", self._COLUMNS_CONFIG_URL,
                                 data="colConfigId=Mast.Caom.Cone", headers=headers)

        self._caomCols = response[0].json()

    def _build_filter_set(self, **filters):
        """
        Takes user input dictionary of filters and returns a filterlist that the Mashup can understand.

        Parameters
        ----------
        **filters :
            Filters to apply. At least one filter must be supplied.
            Valid criteria are coordinates, objectname, radius (as in `query_region` and `query_object`),
            and all observation fields listed `here <https://mast.stsci.edu/api/v0/_c_a_o_mfields.html>`__.
            The Column Name is the keyword, with the argument being one or more acceptable values for that parameter,
            except for fields with a float datatype where the argument should be in the form [minVal, maxVal].
            For example: filters=["FUV","NUV"],proposal_pi="Osten",t_max=[52264.4586,54452.8914]

        Returns
        -------
        response: list(dict)
            The mashup json filter object.
        """

        if not self._caomCols:
            self._get_caom_col_config()

        mashupFilters = []
        for colname, value in filters.items():

            # make sure value is a list-like thing
            if np.isscalar(value,):
                value = [value]

            # Get the column type and separator
            colInfo = self._caomCols.get(colname)
            if not colInfo:
                warnings.warn("Filter {} does not exist. This filter will be skipped.".format(colname), InputWarning)
                continue

            colType = "discrete"
            if colInfo.get("vot.datatype", colInfo.get("type")) in ("double", "float"):
                colType = "continuous"

            separator = colInfo.get("separator")
            freeText = None

            # validate user input
            if colType == "continuous":
                if len(value) < 2:
                    warningString = "{} is continuous, ".format(colname) + \
                                    "and filters based on min and max values.\n" + \
                                    "Not enough values provided, skipping..."
                    warnings.warn(warningString, InputWarning)
                    continue
                elif len(value) > 2:
                    warningString = "{} is continuous, ".format(colname) + \
                                    "and filters based on min and max values.\n" + \
                                    "Too many values provided, the first two will be " + \
                                    "assumed to be the min and max values."
                    warnings.warn(warningString, InputWarning)
            else:  # coltype is discrete, all values should be represented as strings, even if numerical
                value = [str(x) for x in value]

                # check for wildcards

                for i, val in enumerate(value):
                    if ('*' in val) or ('%' in val):
                        if freeText:  # freeText is already set cannot set again
                            warningString = "Only one wildcarded value may be used per filter, " + \
                                            "all others must be exact.\n" + \
                                            "Skipping {}...".format(val)
                            warnings.warn(warningString, InputWarning)
                        else:
                            freeText = val.replace('*', '%')
                        value.pop(i)

            # craft mashup filter entry
            entry = {}
            entry["paramName"] = colname
            if separator:
                entry["separator"] = separator
            if colType == "continuous":
                entry["values"] = [{"min": value[0], "max":value[1]}]
            else:
                entry["values"] = value
            if freeText:
                entry["freeText"] = freeText

            mashupFilters.append(entry)

        return mashupFilters

    @class_or_instance
    def query_region_async(self, coordinates, radius=0.2*u.deg, pagesize=None, page=None):
        """
        Given a sky position and radius, returns a list of MAST observations.
        See column documentation `here <https://mast.stsci.edu/api/v0/_c_a_o_mfields.html>`__.

        Parameters
        ----------
        coordinates : str or `astropy.coordinates` object
            The target around which to search. It may be specified as a
            string or as the appropriate `astropy.coordinates` object.
        radius : str or `~astropy.units.Quantity` object, optional
            Default 0.2 degrees.
            The string must be parsable by `astropy.coordinates.Angle`. The
            appropriate `~astropy.units.Quantity` object from
            `astropy.units` may also be used. Defaults to 0.2 deg.
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
        response: list of ``requests.Response``
        """

        # Put coordinates and radius into consistant format
        coordinates = commons.parse_coordinates(coordinates)

        # if radius is just a number we assume degrees
        if isinstance(radius, (int, float)):
            radius = radius * u.deg
        radius = coord.Angle(radius)

        service = 'Mast.Caom.Cone'
        params = {'ra': coordinates.ra.deg,
                  'dec': coordinates.dec.deg,
                  'radius': radius.deg}

        return self.service_request_async(service, params, pagesize, page)

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
            The string must be parsable by `astropy.coordinates.Angle`.
            The appropriate `~astropy.units.Quantity` object from
            `astropy.units` may also be used. Defaults to 0.2 deg.
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
        response: list of ``requests.Response``
        """

        coordinates = self._resolve_object(objectname)

        return self.query_region_async(coordinates, radius, pagesize, page)

    @class_or_instance
    def query_criteria_async(self, pagesize=None, page=None, **criteria):
        """
        Given an set of filters, returns a list of MAST observations.
        See column documentation `here <https://masttest.stsci.edu/api/v0/_c_a_o_mfields.html>`__.

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
            and all observation fields listed `here <https://mast.stsci.edu/api/v0/_c_a_o_mfields.html>`__.
            The Column Name is the keyword, with the argument being one or more acceptable values for that parameter,
            except for fields with a float datatype where the argument should be in the form [minVal, maxVal].
            For non-float type criteria wildcards maybe used (both * and % are considered wildcards), however
            only one wildcarded value can be processed per criterion.
            RA and Dec must be given in decimal degrees, and datetimes in MJD.
            For example: filters=["FUV","NUV"],proposal_pi="Ost*",t_max=[52264.4586,54452.8914]


        Returns
        -------
        response: list(`requests.Response`)
        """

        # Seperating any position info from the rest of the filters
        coordinates = criteria.pop('coordinates', None)
        objectname = criteria.pop('objectname', None)
        radius = criteria.pop('radius', 0.2*u.deg)

        # Build the mashup filter object
        mashupFilters = self._build_filter_set(**criteria)

        if not mashupFilters:
            raise InvalidQueryError("At least one non-positional criterion must be supplied.")

        # handle position info (if any)
        position = None

        if objectname and coordinates:
            raise InvalidQueryError("Only one of objectname and coordinates may be specified.")

        if objectname:
            coordinates = self._resolve_object(objectname)

        if coordinates:
            # Put coordinates and radius into consitant format
            coordinates = commons.parse_coordinates(coordinates)

            # if radius is just a number we assume degrees
            if isinstance(radius, (int, float)):
                radius = radius * u.deg
            radius = coord.Angle(radius)

            # build the coordinates string needed by Mast.Caom.Filtered.Position
            position = ', '.join([str(x) for x in (coordinates.ra.deg, coordinates.dec.deg, radius.deg)])

        # send query
        if position:
            service = "Mast.Caom.Filtered.Position"
            params = {"columns": "*",
                      "filters": mashupFilters,
                      "position": position}
        else:
            service = "Mast.Caom.Filtered"
            params = {"columns": "*",
                      "filters": mashupFilters}

        return self.service_request_async(service, params)

    def query_region_count(self, coordinates, radius=0.2*u.deg, pagesize=None, page=None):
        """
        Given a sky position and radius, returns the number of MAST observations in that region.

        Parameters
        ----------
        coordinates : str or `astropy.coordinates` object
            The target around which to search. It may be specified as a
            string or as the appropriate `astropy.coordinates` object.
        radius : str or `~astropy.units.Quantity` object, optional
            The string must be parsable by `astropy.coordinates.Angle`. The
            appropriate `~astropy.units.Quantity` object from
            `astropy.units` may also be used. Defaults to 0.2 deg.
        pagesize : int, optional
            Can be used to override the default pagesize for.
            E.g. when using a slow internet connection.
        page : int, optional
            Can be used to override the default behavior of all results being returned to
            obtain a specific page of results.

        Returns
        -------
            response: int
        """

        # build the coordinates string needed by Mast.Caom.Filtered.Position
        coordinates = commons.parse_coordinates(coordinates)

        # if radius is just a number we assume degrees
        if isinstance(radius, (int, float)):
            radius = radius * u.deg
        radius = coord.Angle(radius)

        # turn coordinates into the format
        position = ', '.join([str(x) for x in (coordinates.ra.deg, coordinates.dec.deg, radius.deg)])

        service = "Mast.Caom.Filtered.Position"
        params = {"columns": "COUNT_BIG(*)",
                  "filters": [],
                  "position": position}

        return int(self.service_request(service, params, pagesize, page)[0][0])

    def query_object_count(self, objectname, radius=0.2*u.deg, pagesize=None, page=None):
        """
        Given an object name, returns the number of MAST observations.

        Parameters
        ----------
        objectname : str
            The name of the target around which to search.
        radius : str or `~astropy.units.Quantity` object, optional
            The string must be parsable by `astropy.coordinates.Angle`. The
            appropriate `~astropy.units.Quantity` object from
            `astropy.units` may also be used. Defaults to 0.2 deg.
        pagesize : int, optional
            Can be used to override the default pagesize.
            E.g. when using a slow internet connection.
        page : int, optional
            Can be used to override the default behavior of all results being returned to obtain
            one sepcific page of results.

        Returns
        -------
        response: int
        """

        coordinates = self._resolve_object(objectname)

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
        response: int
        """

        # Seperating any position info from the rest of the filters
        coordinates = criteria.pop('coordinates', None)
        objectname = criteria.pop('objectname', None)
        radius = criteria.pop('radius', 0.2*u.deg)

        # Build the mashup filter object
        mashupFilters = self._build_filter_set(**criteria)

        # handle position info (if any)
        position = None

        if objectname and coordinates:
            raise InvalidQueryError("Only one of objectname and coordinates may be specified.")

        if objectname:
            coordinates = self._resolve_object(objectname)

        if coordinates:
            # Put coordinates and radius into consitant format
            coordinates = commons.parse_coordinates(coordinates)

            # if radius is just a number we assume degrees
            if isinstance(radius, (int, float)):
                radius = radius * u.deg
            radius = coord.Angle(radius)

            # build the coordinates string needed by Mast.Caom.Filtered.Position
            position = ', '.join([str(x) for x in (coordinates.ra.deg, coordinates.dec.deg, radius.deg)])

        # send query
        if position:
            service = "Mast.Caom.Filtered.Position"
            params = {"columns": "COUNT_BIG(*)",
                      "filters": mashupFilters,
                      "position": position}
        else:
            service = "Mast.Caom.Filtered"
            params = {"columns": "COUNT_BIG(*)",
                      "filters": mashupFilters}

        return self.service_request(service, params)[0][0].astype(int)

    @class_or_instance
    def get_product_list_async(self, observations):
        """
        Given a "Product Group Id" (column name obsid) returns a list of associated data products.
        See column documentation `here <https://masttest.stsci.edu/api/v0/_productsfields.html>`__.

        Parameters
        ----------
        observations : str or `astropy.table.Row` or list/Table of same
            Row/Table of MAST query results (e.g. output from `query_object`)
            or single/list of MAST Product Group Id(s) (obsid).
            See description `here <https://masttest.stsci.edu/api/v0/_c_a_o_mfields.html>`__.

        Returns
        -------
            response: list(`requests.Response`)
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

        return self.service_request_async(service, params)

    def filter_products(self, products, mrp_only=True, **filters):
        """
        Takes an `astropy.table.Table` of MAST observation data products and filters it based on given filters.

        Parameters
        ----------
        products: `astropy.table.Table`
            Table containing data products to be filtered.
        mrp_only: bool, optional
            Default True. When set to true only "Minimum Recommended Products" will be returned.
        **filters:
            Filters to be applied.  Valid filters are all products fields listed
            `here <https://masttest.stsci.edu/api/v0/_productsfields.html>`__ and 'extension'
            which is the desired file extension.
            The Column Name (or 'extension') is the keyword, with the argument being one or
            more acceptable values for that parameter.
            Filter behavior is AND between the filters and OR within a filter set.
            For example: productType="SCIENCE",extension=["fits","jpg"]

        Returns
        -------
            response : `astropy.table.Table`
        """

        # Dealing with mrp first, b/c it's special
        if mrp_only:
            products.remove_rows(np.where(products['productGroupDescription'] != "Minimum Recommended Products"))

        filterMask = np.full(len(products), True, dtype=bool)

        for colname, vals in filters.items():

            if type(vals) == str:
                vals = [vals]

            mask = np.full(len(products), False, dtype=bool)
            for elt in vals:
                if colname == 'extension':  # extension is not actually a column
                    mask |= [x.endswith(elt) for x in products["productFilename"]]
                else:
                    mask |= (products[colname] == elt)

            filterMask &= mask

        return products[np.where(filterMask)]

    def _download_curl_script(self, products, outputDirectory):
        """
        Takes an `astropy.table.Table` of data products and downloads a curl script to pull the datafiles.

        Parameters
        ----------
        products : `astropy.table.Table`
            Table containing products to be included in the curl script.
        outputDirectory : str
            Directory in which the curl script will be saved.

        Returns
        -------
            response : `astropy.table.Table`
        """

        urlList = products['dataURI']
        descriptionList = products['description']
        productTypeList = products['dataproduct_type']

        downloadFile = "mastDownload_" + time.strftime("%Y%m%d%H%M%S")
        pathList = [downloadFile+"/"+x['obs_collection']+'/'+x['obs_id']+'/'+x['productFilename'] for x in products]

        service = "Mast.Bundle.Request"
        params = {"urlList": ",".join(urlList),
                  "filename": downloadFile,
                  "pathList": ",".join(pathList),
                  "descriptionList": list(descriptionList),
                  "productTypeList": list(productTypeList),
                  "extension": 'curl'}

        response = self.service_request_async(service, params)

        bundlerResponse = response[0].json()

        localPath = outputDirectory.rstrip('/') + "/" + downloadFile + ".sh"
        Mast._download_file(bundlerResponse['url'], localPath)

        status = "COMPLETE"
        msg = None
        url = None

        if not os.path.isfile(localPath):
            status = "ERROR"
            msg = "Curl could not be downloaded"
            url = bundlerResponse['url']
        else:
            missingFiles = [x for x in bundlerResponse['statusList'].keys()
                            if bundlerResponse['statusList'][x] != 'COMPLETE']
            if len(missingFiles):
                msg = "{} files could not be added to the curl script".format(len(missingFiles))
                url = ",".join(missingFiles)

        manifest = Table({'Local Path': [localPath],
                          'Status': [status],
                          'Message': [msg],
                          "URL": [url]})
        return manifest

    def _download_files(self, products, baseDir, cache=True):
        """
        Takes an `astropy.table.Table` of data products and downloads them into the dirctor given by baseDir.

        Parameters
        ----------
        products : `astropy.table.Table`
            Table containing products to be downloaded.
        baseDir : str
            Directory in which files will be downloaded.
        cache : bool
            Default is True. If file is found on disc it will not be downloaded again.

        Returns
        -------
            response : `astropy.table.Table`
        """
        manifestArray = []
        for dataProduct in products:

            localPath = baseDir + "/" + dataProduct['obs_collection'] + "/" + dataProduct['obs_id']

            dataUrl = dataProduct['dataURI']
            if "http" not in dataUrl:  # url is actually a uri
                dataUrl = self._MAST_DOWNLOAD_URL + dataUrl.lstrip("mast:")

            if not os.path.exists(localPath):
                os.makedirs(localPath)

            localPath += '/' + dataProduct['productFilename']

            status = "COMPLETE"
            msg = None
            url = None

            try:
                Mast._download_file(dataUrl, localPath, cache=cache)

                # check file size also this is where would perform md5
                if not os.path.isfile(localPath):
                    status = "ERROR"
                    msg = "File was not downloaded"
                    url = dataUrl
                else:
                    fileSize = os.stat(localPath).st_size
                    if fileSize != dataProduct["size"]:
                        status = "ERROR"
                        msg = "Downloaded filesize is {},".format(dataProduct['size']) + \
                              "but should be {}, file may be partial or corrupt.".format(fileSize)
                        url = dataUrl
            except HTTPError as err:
                status = "ERROR"
                msg = "HTTPError: {0}".format(err)
                url = dataUrl

            manifestArray.append([localPath, status, msg, url])

        manifest = Table(rows=manifestArray, names=('Local Path', 'Status', 'Message', "URL"))

        return manifest

    def download_products(self, products, download_dir=None,
                          cache=True, curl_flag=False, mrp_only=True, **filters):
        """
        Download data products.

        Parameters
        ----------
        products : str, list, `astropy.table.Table`
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
            Default True. When set to true only "Minimum Recommended Products" will be returned.
        **filters :
            Filters to be applied.  Valid filters are all products fields listed
            `here <https://masttest.stsci.edu/api/v0/_productsfields.html>`__ and 'extension'
            which is the desired file extension.
            The Column Name (or 'extension') is the keyword, with the argument being one or
            more acceptable values for that parameter.
            Filter behavior is AND between the filters and OR within a filter set.
            For example: productType="SCIENCE",extension=["fits","jpg"]

        Return
        ------
        response: `astropy.table.Table`
            The manifest of files downloaded, or status of files on disk if curl option chosen.
        """

        # If the products list is not already a table of producs we need to  get the products and
        # filter them appropriately
        if type(products) != Table:

            if type(products) == str:
                products = [products]

            # collect list of products
            productLists = []
            for oid in products:
                productLists.append(self.get_product_list(oid))

            products = vstack(productLists)

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
            baseDir = download_dir.rstrip('/') + "/mastDownload"
            manifest = self._download_files(products, baseDir, cache)

        return manifest


Observations = ObservationsClass()
Mast = MastClass()
