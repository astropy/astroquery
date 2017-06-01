# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
MAST Portal
===========

TODO Add documentation/description (not sure this shows up everywhere)

"""

from __future__ import print_function, division

import warnings
import json
import time
import os

import numpy as np

try: # Python 3.x
    from urllib.parse import quote as urlencode
except ImportError:  # Python 2.x
    from urllib import pathname2url as urlencode

from requests import HTTPError

import astropy.units as u
import astropy.coordinates as coord
from astropy.table import Table, Row, vstack

from ..query import BaseQuery
from ..utils import commons, async_to_sync
from ..utils.class_or_instance import class_or_instance
from ..exceptions import TimeoutError, InvalidQueryError
from . import conf


__all__ = ['Mast', 'MastClass',
           'Raw',  'RawClass']


class ResolverError(Exception):
    pass


def _prepare_mashup_request_string(jsonObj):
    """
    Takes a mashup json request object and turns it into a url-safe string.

    Parameters
    ----------
    jsonObj : dict
        A Mashup request json object (python dictionary)
        
    Returns
    -------
    response : str
        URL encoded Mashup Request string.
    """
    requestString = json.dumps(jsonObj)
    requestString = urlencode(requestString)
    return "request="+requestString


def _mashup_json_to_table(jsonObj):
    """
    Takes a json object as returned from a Mashup request and turns it into an astropy Table.

    Parameters
    ----------
    jsonObj : dict
        A Mashup response json object (python dictionary)
        
    Returns
    -------
    response: `astropy.table.Table`
    """

    dataTable = Table()
    
    if not (jsonObj.get('fields') and jsonObj.get('data')):
        raise KeyError("Missing required key(s) 'data' and/or 'fields.'")  

    for col,atype in [(x['name'],x['type']) for x in jsonObj['fields']]:
        if atype=="string":
            atype="str"
        if atype=="boolean":
            atype="bool"
        dataTable[col] = np.array([x.get(col,None) for x in jsonObj['data']],dtype=atype)
        
    return dataTable


@async_to_sync
class RawClass(BaseQuery):
    """
    Class that allows direct programatic access to the MAST Portal, 
    more flexible but less user friendly than MastClass.
    """
    
    _SERVER = conf.server
    TIMEOUT = conf.timeout
    PAGESIZE = conf.pagesize
    
    def _request(self, method, url, params=None, data=None, headers=None,
                files=None, stream=False, auth=None, retrieve_all=True, verbose=False):        
        """
        Override of the parent method:
        A generic HTTP request method, similar to `requests.Session.request`
        
        This is a low-level method not generally intended for use by astroquery
        end-users.
        
        The main difference in this function is that it takes care of the long 
        polling requirements of the mashup server.
        Thus the cache parameter of the parent method is hard coded to false 
        (the mast server does it's own caching, no need to cache locally and it 
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
            See `requests.request`
        retrieve_all : bool
            Default True. Retrieve all pages of data or just the one indicated in the params value.
        verbose : bool
            Default False.  Setting to True provides more extensive output.
        
        Returns
        -------
        response : `requests.Response`
            The response from the server.
        """
        
        startTime = time.time()
        allResponses = []
        totalPages = 1
        curPage = 0
        
        while curPage < totalPages:
            status = "EXECUTING"
            
            while status == "EXECUTING":
                response = super()._request(method, url, params=params, data=data, headers=headers,
                                            files=files, cache=False,
                                            stream=stream, auth=auth)
                    
                if (time.time() - startTime) >=  self.TIMEOUT:
                    raise TimeoutError("Timeout limit of %f exceeded." % self.TIMEOUT)

                result = response.json()
                status = result.get("status")
                   
            allResponses.append(response)
            
            if (status != "COMPLETE") or (retrieve_all == False):
                break
            
            paging = result.get("paging")
            if not paging:
                break
            totalPages = paging['pagesFiltered']
            curPage = paging['page']
            
            data = data.replace("page%22%3A%20"+str(curPage)+"%2C","page%22%3A%20"+str(curPage+1)+"%2C")                                   
            
        return allResponses
    

    def _parse_result(self,responses,verbose=False):
        """
        Parse the results of a list of `requests.Response` objects and returns an `astropy.table.Table` of results.
        
        Parameters
        ----------
        responses : list(`requests.Response`)
            List of `requests.Response` objects.
        verbose : bool
            Default False. Setting to True provides more extensive output.
        """
    
       #NOTE (TODO) verbose does not currently have any affect
        
        resultList = []
        
        for resp in responses:  
            result = resp.json() 
            resTable = _mashup_json_to_table(result)
            resultList.append(resTable)
        
        return vstack(resultList)    
    
    
    @class_or_instance
    def mashup_request_async(self, service, params, pagesize=None, page=None, verbose=False):
        """
        Given a Mashup service and parameters, builds and excecutes a Mashup query.
        See documentation `here <https://masttest.stsci.edu/api/v0/class_mashup_1_1_mashup_request.html>`_ 
        for information about how to build a Mashup request.
        
        Parameters
        ----------
        service : str
            The Mashup service to query.
        params : dict
            Json object containing service parameters.
        pagesize : int or None
            Can be used to override the default pagesize (set in configs) for this query only. 
            E.g. when using a slow internet connection.
        page : int or None
            Can be used to override the default behavior of all results being returned to obtain 
            a sepcific page of results.
        verbose : bool
            Default False. Setting to True provides more extensive output. 
        See MashupRequest properties `here <https://masttest.stsci.edu/api/v0/class_mashup_1_1_mashup_request.html>`_ 
        for additional keyword arguments.
        
        
        Returns
        -------
            response: list(`requests.Response`)
        """
        
        # setting up pagination
        if not pagesize:
            pagesize=self.PAGESIZE
        if not page:
            page=1
            retrieveAll = True
        else:
            retrieveAll = False
        
        headers = {"User-Agent":self._session.headers["User-Agent"],
                   "Content-type": "application/x-www-form-urlencoded",
                   "Accept": "text/plain"}
        
    
        mashupRequest = {'service':service,
                         'params':params,
                         'format':'json',
                         'pagesize':pagesize, 
                         'page':page}
    
        reqString = _prepare_mashup_request_string(mashupRequest)
        response = self._request("POST",self._SERVER+"/api/v0/invoke",data=reqString,headers=headers,
                                 retrieve_all=retrieveAll,verbose=verbose)
        
        return response
        
        
    def _resolve_object(self,objectname,verbose=False):
        """
        Resolves an object name to a position on the sky.
        
        Parameters
        ----------
        objectname : str
            Name of astronimical object to resolve.
        verbose : bool
            Default False. Setting to True provides more extensive output.    
        """
        
        service = 'Mast.Name.Lookup'
        params ={'input':objectname,
                 'format':'json'}
        
        response = self.mashup_request_async(service,params)
        
        result = response[0].json() 
        
        if len(result['resolvedCoordinate']) == 0:
            raise ResolverError("Could not resolve %s to a sky position." % objectname)
            
        
        ra = result['resolvedCoordinate'][0]['ra']
        dec = result['resolvedCoordinate'][0]['decl']
        coordinates = coord.SkyCoord(ra, dec, unit="deg")
        
        return coordinates



@async_to_sync
class MastClass(RawClass):
    """Class that encapsulates all astroquery MAST Portal functionality"""
    
    _caomCols = None # Hold Mast.Caom.Cone columns config 
        
        
    def _get_caom_col_config(self):
        """
        Gets the columnsConfig entry for Mast.Caom.Cone and stores it in self.caomCols.
        """
        
        headers = {"User-Agent":self._session.headers["User-Agent"],
                   "Content-type": "application/x-www-form-urlencoded",
                   "Accept": "text/plain"}

        response = Mast._request("POST", self._SERVER+"/portal/Mashup/Mashup.asmx/columnsconfig", 
                                 data="colConfigId=Mast.Caom.Cone", headers=headers)
        
        self._caomCols = response[0].json()
        
        
    def _build_filter_set(self, filters):
        """
        Takes user input dicionary of filters and returns a filterlist that the Mashup can understand.
        
        Parameters
        ----------
        filters : dict
            Dictionary of filters to apply to a CAOM query.
            Filters are of the form {"filter1":"value","filter2":[val1,val2],"filter3":[minval,maxval]}
            
        Returns
        -------
        response: list(dict)
            The mashup json filter object.
        """
    
        if not self._caomCols:
            self._get_caom_col_config()
            

        mashupFilters = []
        for colname in filters:
            value = filters[colname]
            
            # make sure value is a list-like thing
            if np.isscalar(value,):
                value = [value]
            
            # Get the column type and seperator
            colInfo = self._caomCols.get(colname)
            if not colInfo:
                print("Filter %s does not exist. This filter will be skipped." % colname)
                continue
            
            colType = "discrete"
            if colInfo.get("vot.datatype",colInfo.get("type")) == "double":
                colType = "continuous"
                
            seperator = colInfo.get("seperator")
            
            # validate user input
            if colType == "continuous":
                if len(value) < 2:
                    print("%s is continuous, and filters based on min and max values." % colname)
                    print("Not enough values provided, skipping...")
                    continue
                elif len(value) > 2:
                    print("%s is continuous, and filters based on min and max values." % colname)
                    print("Too many values provided, the first two will be assumed to be the min and max values.")
            else: # coltype is discrete, all values should be represented as strings, even if numerical
                value = [str(x) for x in value]
            
            # craft mashup filter entry
            entry = {}
            entry["paramName"] = colname
            if seperator:
                entry["separator"] = seperator
            if colType == "continuous":
                entry["values"] = [{"min":value[0],"max":value[1]}]
            else:
                entry["values"] = value
                
            mashupFilters.append(entry)
            
        return mashupFilters        
        
        
    @class_or_instance
    def query_region_async(self, coordinates, radius="0.2 deg", pagesize=None, page=None, verbose=False):
        """
        Given a sky position and radius, returns a list of MAST observations.
        See column documentation `here <https://masttest.stsci.edu/api/v0/_c_a_o_mfields.html>`_.
        
        Parameters
        ----------
        coordinates : str or `astropy.coordinates` object
            The target around which to search. It may be specified as a
            string or as the appropriate `astropy.coordinates` object. 
        radius : str or `~astropy.units.Quantity` object, optional
            The string must be parsable by `astropy.coordinates.Angle`. The
            appropriate `~astropy.units.Quantity` object from
            `astropy.units` may also be used. Defaults to 0.2 deg.
        pagesize : int or None
            Can be used to override the default pagesize for (set in configs) this query only. E.g. when using a slow internet connection.
        page : int or None
            Can be used to override the default behavior of all results being returned to obtain a sepcific page of results.
        verbose : bool
            Default False. Setting to True provides more extensive output. 
        
        
        Returns
        -------
            response: list(`requests.Response`)
        """       
        
        # Put coordinates and radius into consitant format
        coordinates = commons.parse_coordinates(coordinates)
        radius = commons.parse_radius(radius.lower())
        
        service = 'Mast.Caom.Cone'
        params = {'ra':coordinates.ra.deg,
                  'dec':coordinates.dec.deg,
                  'radius':radius.deg}
        
        return self.mashup_request_async(service, params, pagesize, page, verbose)
        

        
    @class_or_instance
    def query_object_async(self, objectname, radius="0.2 deg", pagesize=None, page=None, verbose=False):
        """
        Given an object name, returns a list of MAST observations.
        See column documentation `here <https://masttest.stsci.edu/api/v0/_c_a_o_mfields.html>`_.
        
        Parameters
        ----------
        objectname : str 
            The name of the target around which to search. 
        radius : str or `~astropy.units.Quantity` object, optional
            The string must be parsable by `astropy.coordinates.Angle`. The
            appropriate `~astropy.units.Quantity` object from
            `astropy.units` may also be used. Defaults to 0.2 deg.
        pagesize : int or None
            Can be used to override the default pagesize for (set in configs) this query only. E.g. when using a slow internet connection.
        page : int or None
            Can be used to override the default behavior of all results being returned to obtain a sepcific page of results.
        verbose : bool
            Default False. Setting to True provides more extensive output. 
        
        
        Returns
        -------
        response: list(`requests.Response`)
        """
        
        coordinates = self._resolve_object(objectname,verbose=verbose)
        
        return self.query_region_async(coordinates, radius, pagesize, page, verbose)
    
    
    @class_or_instance
    def query_filter_async(self, filters, objectname=None, coordinates=None, radius="0.2 deg", 
                           pagesize=None, page=None, verbose=False):
        """
        Given an set of filters, returns a list of MAST observations.
        See column documentation `here <https://masttest.stsci.edu/api/v0/_c_a_o_mfields.html>`_.
        
        Parameters
        ----------
        filters : dict
            Dictionary of filters to apply to query.
            Filters are of the form {"filter1":"value","filter2":[val1,val2],"filter3":[minval,maxval]}
            See `documentation <../../mast/mast.html#filtered-queries>`_ for more information.
        coordinates : str or `astropy.coordinates` object
            Optional target position around which to search. It may be specified as a
            string or as the appropriate `astropy.coordinates` object. 
        objectname : str 
            Optional name of target around which to search. 
        radius : str or `~astropy.units.Quantity` object, optional
            Optional.  Only has an affect if coordinates or objectname are set.
            The string must be parsable by `astropy.coordinates.Angle`. The
            appropriate `~astropy.units.Quantity` object from
            `astropy.units` may also be used. Defaults to 0.2 deg.
        pagesize : int or None
            Can be used to override the default pagesize for (set in configs) this query only. 
            E.g. when using a slow internet connection.
        page : int or None
            Can be used to override the default behavior of all results being returned to obtain 
            a sepcific page of results.
        verbose : bool
            Default False. Setting to True provides more extensive output. 
        
        
        Returns
        -------
        response: list(`requests.Response`)
        """
        
        # Build the mashup filter object        
        mashupFilters = self._build_filter_set(filters)
            
        # handle position info (if any)
        position = None
        
        if objectname and coordinates:
            raise InvalidQueryError("Only one of objectname and coordinates may be specified.") 
        
        if objectname:
            coordinates = self._resolve_object(objectname,verbose=verbose)
        
        if coordinates:
            # Put coordinates and radius into consitant format
            coordinates = commons.parse_coordinates(coordinates)
            radius = commons.parse_radius(radius.lower())

            # build the coordinates string needed by Mast.Caom.Filtered.Position
            position = ', '.join([str(x) for x in (coordinates.ra.deg,coordinates.dec.deg,radius.deg)])
            
                  
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
            
        return self.mashup_request_async(service, params, verbose=verbose)
                

    def query_region_count(self, coordinates, radius="0.2 deg", pagesize=None, page=None, verbose=False):
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
        pagesize : int or None
            Can be used to override the default pagesize for (set in configs) this query only. E.g. when using a slow internet connection.
        page : int or None
            Can be used to override the default behavior of all results being returned to obtain a sepcific page of results.
        verbose : bool
            Default False. Setting to True provides more extensive output. 
        
        
        Returns
        -------
            response: int
        """       
        
        # build the coordinates string needed by Mast.Caom.Filtered.Position
        coordinates = commons.parse_coordinates(coordinates)
        radius = commons.parse_radius(radius.lower())
        
        # turn coordinates into the format 
        position = ', '.join([str(x) for x in (coordinates.ra.deg,coordinates.dec.deg,radius.deg)])
        
        service = "Mast.Caom.Filtered.Position"
        params = {"columns": "COUNT_BIG(*)",
                  "filters": [],
                  "position": position}
        
        return self.mashup_request(service, params, pagesize, page, verbose)[0][0].astype(int)
        
    
    
    def query_object_count(self, objectname, radius="0.2 deg", pagesize=None, page=None, verbose=False):
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
        pagesize : int or None
            Can be used to override the default pagesize for (set in configs) this query only. E.g. when using a slow internet connection.
        page : int or None
            Can be used to override the default behavior of all results being returned to obtain a sepcific page of results.
        verbose : bool
            Default False. Setting to True provides more extensive output. 
        
        
        Returns
        -------
        response: int
        """
        
        coordinates = self._resolve_object(objectname,verbose=verbose)
        
        return self.query_region_count(coordinates, radius, pagesize, page, verbose)
    
    
    def query_filter_count(self, filters, objectname=None, coordinates=None, radius="0.2 deg", 
                           pagesize=None, page=None, verbose=False):
        """
        Given an set of filters, returns the number of MAST observations meeting those criteria.
        
        Parameters
        ----------
        filters : dict
            Dictionary of filters to apply to query.
            Filters are of the form {"filter1":"value","filter2":[val1,val2],"filter3":[minval,maxval]}
            See `documentation <../../mast/mast.html#filtered-queries>`_ for more information.
        coordinates : str or `astropy.coordinates` object
            Optional target position around which to search. It may be specified as a
            string or as the appropriate `astropy.coordinates` object. 
        objectname : str 
            Optional name of target around which to search. 
        radius : str or `~astropy.units.Quantity` object, optional
            Optional.  Only has an affect if coordinates or objectname are set.
            The string must be parsable by `astropy.coordinates.Angle`. The
            appropriate `~astropy.units.Quantity` object from
            `astropy.units` may also be used. Defaults to 0.2 deg.
        pagesize : int or None
            Can be used to override the default pagesize for (set in configs) this query only. E.g. when using a slow internet connection.
        page : int or None
            Can be used to override the default behavior of all results being returned to obtain a sepcific page of results.
        verbose : bool
            Default False. Setting to True provides more extensive output. 
        
        
        Returns
        -------
        response: int
        """
        
        # Build the mashup filter object        
        mashupFilters = self._build_filter_set(filters)
            
        # handle position info (if any)
        position = None
        
        if objectname and coordinates:
            raise InvalidQueryError("Only one of objectname and coordinates may be specified.")
        
        if objectname:
            coordinates = self._resolve_object(objectname,verbose=verbose)
        
        if coordinates:
            # Put coordinates and radius into consitant format
            coordinates = commons.parse_coordinates(coordinates)
            radius = commons.parse_radius(radius.lower())

            # build the coordinates string needed by Mast.Caom.Filtered.Position
            position = ', '.join([str(x) for x in (coordinates.ra.deg,coordinates.dec.deg,radius.deg)])
            
                  
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
            
        return self.mashup_request(service, params, verbose=verbose)[0][0].astype(int)
    
    
    
    @class_or_instance
    def get_product_list_async(self,observation,verbose=False):
        """
        Given a "Product Group Id" (column name obsid) returns a list of associated data products.
        See column documentation `here <https://masttest.stsci.edu/api/v0/_productsfields.html>`_.
        
        Parameters
        ----------
        observation : str or `astropy.table.Row`
            Row of MAST query results table (e.g. as output from query_object) or MAST Product Group Id (obsid). 
            See description `here <https://masttest.stsci.edu/api/v0/_c_a_o_mfields.html>`_.
            
        Returns
        -------
            response: list(`requests.Response`)    
        """
        
        # getting the obsid
        obsid = observation
        if type(observation) == Row:
            obsid = observation['obsid']
            
            
        service = 'Mast.Caom.Products'
        params = {'obsid':obsid}
        
        return self.mashup_request_async(service, params, verbose=verbose)
    
   

    def filter_products(self, products,filters):
        """
        Takes an `astropy.table.Table` of MAST observation data products and filters it based on given dictionary of filters.
        Note: Filtering is done in place, the products Table is changes.
    
        Parameters
        ----------
        products: `astropy.table.Table`
            Table containing data products to be filtered.
        filters: dict
            Dictionary of filters to be applied.  Filter values may be strings or arrays of strings representing desired values.
        """
        
        filterDict = {"group":'productSubGroupDescription',
                      "extension":'productFilename', # this one is special (sigh)
                      "product type":'dataproduct_type',
                      "product category":'productType'}
        
        
        # Dealing with mrp first, b/c it's special
        if filters.get("mrp_only") == True:
            products.remove_rows(np.where(products['productGroupDescription'] != "Minimum Recommended Products"))
                
        filterMask = np.full(len(products),True,dtype=bool)
                
        for filt in filters.keys():
            
            colname = filterDict.get(filt.lower())
            if not colname:
                continue
            
            vals = filters[filt]
            if type(vals) == str:
                vals = [vals]
                
            mask = np.full(len(products[colname]),False,dtype=bool)
            for elt in vals:
                if colname == 'productFilename':
                    mask |= [x.endswith(elt) for x in products[colname]] 
                elif colname == "productGroupDescription":
                    mask |= [products[colname] == "Minimum Recommended Products"]
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
        params = {"urlList":",".join(urlList),
                  "filename":downloadFile,
                  "pathList":",".join(pathList),
                  "descriptionList":list(descriptionList),
                  "productTypeList":list(productTypeList),
                  "extension":'curl'}
        
        response = self.mashup_request_async(service, params)
        

        bundlerResponse = response[0].json() 
            
        localPath = outputDirectory.rstrip('/') + "/" + downloadFile + ".sh"
        Mast._download_file(bundlerResponse['url'],localPath)           
            
        status = "COMPLETE"
        msg = None
        url = None
            
        if not os.path.isfile(localPath):
            status = "ERROR"
            msg = "Curl could not be downloaded"
            url = bundlerResponse['url']
        else:
            missingFiles = [x for x in bundlerResponse['statusList'].keys() if bundlerResponse['statusList'][x] != 'COMPLETE']
            if len(missingFiles):
                msg = "%d files could not be added to the curl script" % len(missingFiles)
                url = ",".join(missingFiles)
            
            
        manifest = Table({'Local Path':[localPath],
                          'Status':[status],
                          'Message':[msg],
                          "URL":[url]})
        return manifest


   
        
    def _download_files(self, products, baseDir):
        """
        Takes an `astropy.table.Table` of data products and downloads them into the dirctor given by baseDir.
        
        Parameters
        ----------
        products : `astropy.table.Table`
            Table containing products to be downloaded.
        baseDir : str
            Directory in which files will be downloaded.
            
        Returns
        -------
            response : `astropy.table.Table`
        """
        manifestArray = []
        for dataProduct in products:
            
            localPath = baseDir + "/" + dataProduct['obs_collection'] + "/" + dataProduct['obs_id']

            dataUrl = dataProduct['dataURI']
            if "http" not in dataUrl: # url is actually a uri
                dataUrl = self._SERVER + "/api/v0/download/file/" + dataUrl.lstrip("mast:")
                
            if not os.path.exists(localPath):
                    os.makedirs(localPath)
                    
            localPath += '/' + dataProduct['productFilename']
                
            status = "COMPLETE"
            msg = None
            url = None
                    
            try:
                Mast._download_file(dataUrl, localPath)

                # check file size also this is where would perform md5
                if not os.path.isfile(localPath):
                    status = "ERROR"
                    msg = "File was not downloaded"
                    url = dataUrl
                else:
                    fileSize = os.stat(localPath).st_size
                    if fileSize != dataProduct["size"]:
                        status = "ERROR"
                        msg = "Downloaded filesize is %d, but should be %d, file may be partial or corrupt." % (fileSize,dataProduct['size'])
                        url = dataUrl
            except HTTPError as err:
                status = "ERROR"
                msg = "HTTPError: {0}".format(err)
                url = dataUrl
                    
            manifestArray.append([localPath,status,msg,url])
          
        manifest = Table(rows=manifestArray, names=('Local Path','Status','Message',"URL")) 
        
        return manifest
            
            
    
    def download_products(self,products,download_dir=None,filters={},curl_flag=False):
        """
        Download data products.

        Parameters
        ----------
        products : str, list, `astropy.table.Table`
            Either a single or list of obsids (as can be given to `get_product_list`), 
            or a Table of products (as is returned by `get_product_list`)
        download_dir : str
            Optional.  Directory to download files to.  Defaults to current directory.
        filters : dict
            Default is {'mrp_only':True}. Dictionary of filters to apply, see `TODO: ADD LINK`. 
        curl_flag : bool
            Default is False.  If true instead of downloading files directly, a curl script will be downloaded
            that can be used to download the data files at a later time.
        
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
        if "mrp_only" not in filters.keys():
            filters["mrp_only"] = True    
        products = self.filter_products(products,filters) 
            
        
        if not len(products):
            print("No products to download.")
            return
        
        # set up the download directory and paths
        if not download_dir:
            download_dir = '.'
                  
        if curl_flag: # don't want to download the files now, just the curl script
            manifest = self._download_curl_script(products, download_dir)
            
        else:
            baseDir = download_dir.rstrip('/') + "/mastDownload_" + time.strftime("%Y%m%d%H%M%S")
            manifest = self._download_files(products, baseDir)                     
            
        return manifest


Mast = MastClass()
Raw = RawClass()
