# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
MAST Portal
===========

TODO Add documentation/description

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
from astropy.io import fits, votable
from astropy.utils.console import ProgressBarOrSpinner
from astropy.coordinates.name_resolve import NameResolveError

from ..query import BaseQuery
from ..utils import commons, async_to_sync
from ..utils.class_or_instance import class_or_instance
from ..exceptions import TableParseError, NoResultsWarning
from . import conf

__all__ = ['Mast', 'MastClass']

@async_to_sync
class MastClass(BaseQuery):
    """Class that encapsulates all astroquery MAST Portal functionality"""

    SERVER = conf.server
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
                    break

                try:
                    result = response.json()
                    status = result.get("status")
                except ValueError:
                    status = "ERROR"
                   
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
            try:
                result = resp.json() 
            except ValueError:
                print("JSON decode failure, output is non-standard, will be returned raw.") # FIGURE OUT PROPER METHOD FOR ERROR HANDLING
                return response.content()
            
            try:
                resTable = _mashup_json_to_table(result)
                resultList.append(resTable)
            except:
                print("JSON to Table failure, this result will be skipped")

        return vstack(resultList)
 

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
        
        headers = {"User-Agent":self._session.headers["User-Agent"],
                   "Content-type": "application/x-www-form-urlencoded",
                   "Accept": "text/plain"}
            
        resolverRequest = {'service':'Mast.Name.Lookup',
                           'params':{'input':objectname,
                                     'format':'json'}
                          }
        
        reqString = _prepare_mashup_request_string(resolverRequest)
       
        response = self._request("POST",self.SERVER+"/api/v0/invoke",data=reqString,headers=headers,
                                 retrieve_all=False,verbose=verbose)

        
        try:
            result = response[0].json() 
        except ValueError:
            return "ERROR" # TODO: Make this actually raise an error
        
        ra = result['resolvedCoordinate'][0]['ra']
        dec = result['resolvedCoordinate'][0]['decl']
        coordinates = coord.SkyCoord(ra, dec, unit="deg")
        
        return coordinates
        
     
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
            response: list(`request.response`)
        """
        
        headers = {"User-Agent":self._session.headers["User-Agent"],
                   "Content-type": "application/x-www-form-urlencoded",
                   "Accept": "text/plain"}
        
        
        # Put coordinates and radius into consitant format
        try:
            coordinates = commons.parse_coordinates(coordinates)
            radius = commons.parse_radius(radius.lower())
        except NameResolveError:
            print("Coordinates could not be resolved to a sky position, check your coordinates are an `astropy.coordinates` object or a properly formatted string.")
            return
        except ValueError:
            print("Could not parse radius, radius must be an `astropy.units.Quantity` or parsable by `astropy.coordinates.Angle`.")
            return
        except UnitsError:
            print("UnitsError: Remember to specify units for the radius.")
            return
             
        # setting up pagination
        if not pagesize:
            pagesize=self.PAGESIZE
        if not page:
            page=1
            retrieveAll = True
        else:
            retrieveAll = False
        
        mashupRequest = {'service':'Mast.Caom.Cone',
                         'params':{'ra':coordinates.ra.deg,
                                  'dec':coordinates.dec.deg,
                                  'radius':radius.deg},
                         'format':'json',
                         'pagesize':pagesize, 
                         'page':page}
    
        reqString = _prepare_mashup_request_string(mashupRequest)
        response = self._request("POST",self.SERVER+"/api/v0/invoke",data=reqString,headers=headers,
                                 retrieve_all=retrieveAll,verbose=verbose)
        
        return response

        
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
            response: list(`request.response`)
        """
        
        coordinates = self._resolve_object(objectname,verbose=verbose)
        
        if coordinates == "ERROR":
            print("Could not resolve %s to a position" % objectname)
            return
        
        return self.query_region_async(coordinates, radius, pagesize, page, verbose)
    
    
 
    def query_region_count(self, coordinates, radius="0.2 deg", verbose=False):
        """
        Given a sky position and radius, returns the number of observations in MAST collections.
        
        Parameters
        ----------
        coordinates : str or `astropy.coordinates` object
            The target around which to search. It may be specified as a
            string or as the appropriate `astropy.coordinates` object. 
        radius : str or `~astropy.units.Quantity` object, optional
            The string must be parsable by `astropy.coordinates.Angle`. The
            appropriate `~astropy.units.Quantity` object from
            `astropy.units` may also be used. Defaults to 0.2 deg.
        
        Returns
        -------
        response: int
            The number of observations found.
        """
        
        response = self.query_region_async(coordinates, radius=radius, pagesize=1, page=1, verbose=verbose)
        
        try:
            result = response[0].json() 
        except ValueError:
            print("JSON decode failure.")
            return 
        
        return result['paging']['rowsTotal']
    
    

    def query_object_count(self, objectname, radius="0.2 deg", verbose=False):
        """
        Given a sky position and radius, returns the number of observations in MAST collections.
        
        Parameters
        ----------
        objectname : str 
            The name of the target around which to search. 
        radius : str or `~astropy.units.Quantity` object, optional
            The string must be parsable by `astropy.coordinates.Angle`. The
            appropriate `~astropy.units.Quantity` object from
            `astropy.units` may also be used. Defaults to 0.2 deg.
        
        Returns
        -------
        response: int
            The number of observations found.
        """
        
        response = self.query_object_async(objectname, radius=radius, pagesize=1, page=1, verbose=verbose)
        
        try:
            result = response[0].json() 
        except ValueError:
            print("JSON decode failure.")
            return 
        
        return result['paging']['rowsTotal']

    
    
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
            response: list(`request.response`)    
        """
        
        # getting the obsid
        obsid = observation
        if type(observation) == Row:
            obsid = observation['obsid']
        
        headers = {"User-Agent":self._session.headers["User-Agent"],
                   "Content-type": "application/x-www-form-urlencoded",
                   "Accept": "text/plain"}
        
        mashupRequest = {'service':'Mast.Caom.Products',
                         'params':{'obsid':obsid},
                         'format':'json',
                         'pagesize':self.PAGESIZE, 
                         'page':1}

        reqString = _prepare_mashup_request_string(mashupRequest)
        
        response = self._request("POST",self.SERVER+"/api/v0/invoke",data=reqString,headers=headers,verbose=verbose)
        
        return response
   


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
        
        headers = {"User-Agent":self._session.headers["User-Agent"],
                   "Content-type": "application/x-www-form-urlencoded",
                   "Accept": "text/plain"}

        mashupRequest = {"service":"Mast.Bundle.Request",
                         "params":{"urlList":",".join(urlList),
                                   "filename":downloadFile,
                                   "pathList":",".join(pathList),
                                   "descriptionList":list(descriptionList),
                                   "productTypeList":list(productTypeList),
                                   "extension":'curl'},
                         "format":"json",
                         "page":1,
                         "pagesize":1000}  
        
        reqStr = _prepare_mashup_request_string(mashupRequest)
        response = Mast._request("POST", self.SERVER+"/api/v0/invoke", data=reqStr,headers=headers)
        
        try:
            bundlerResponse = response[0].json() # TODO another try/catch
        except ValueError:
            print("JSON decode failure, output in non-standard, will be returned raw.") 
            return response.content()
            
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
                dataUrl = self.SERVER + "/api/v0/download/file/" + dataUrl.lstrip("mast:")
                
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

            try:
                products = vstack(productLists) 
            except TypeError:
                print("Data product list(s) are not Tables, download cannot proceed.\nReturning product list(s)...")
                return productLists
            
            # apply filters 
            if "mrp_only" not in filters.keys():
                filters["mrp_only"] = True
            
        _filter_products(products,filters) # TODO: still not sure of filtering behavior.... 
            
        
        if not len(products):
            print("No products to download.")
            return
        
        # set up the download directory and paths
        if not download_dir:
            download_dir = '.'
                  
        if curl_flag: # don' want to download the files now, just the curl script
            manifest = self._download_curl_script(products, download_dir)
            
        else:
            baseDir = download_dir.rstrip('/') + "/mastDownload_" + time.strftime("%Y%m%d%H%M%S")
            manifest = self._download_files(products, baseDir)                     
            
        return manifest
        

Mast = MastClass()


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

    for col,atype in [(x['name'],x['type']) for x in jsonObj['fields']]:
        if atype=="string":
            atype="str"
        if atype=="boolean":
            atype="bool"
        dataTable[col] = np.array([x.get(col,None) for x in jsonObj['data']],dtype=atype)
        
    return dataTable


def _filter_products(products,filters):
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
                    
    products.remove_rows(np.where(filterMask == False))  
