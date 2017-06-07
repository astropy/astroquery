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

from ..query import BaseQuery
from ..utils import commons, async_to_sync
from ..utils.class_or_instance import class_or_instance
from ..exceptions import TimeoutError, InvalidQueryError
from . import conf


__all__ = ['Observations', 'ObservationsClass',
           'Mast',  'MastClass']


class ResolverError(Exception):
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

    for col,atype in [(x['name'],x['type']) for x in json_obj['fields']]:
        if atype=="string":
            atype="str"
        if atype=="boolean":
            atype="bool"
        dataTable[col] = np.array([x.get(col,None) for x in json_obj['data']],dtype=atype)

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
        
        self._SERVER = conf.server
        self.TIMEOUT = conf.timeout
        self.PAGESIZE = conf.pagesize

    
    def _request(self, method, url, params=None, data=None, headers=None,
                files=None, stream=False, auth=None, retrieve_all=True, verbose=False):        
        """
        Override of the parent method:
        A generic HTTP request method, similar to ``requests.Session.request``
        
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
            See ``requests.request``
        retrieve_all : bool
            Default True. Retrieve all pages of data or just the one indicated in the params value.
        verbose : bool
            Default False.  Setting to True provides more extensive output.
        
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
                response = super(MastClass, self)._request(method, url, params=params, data=data, headers=headers,
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
        Parse the results of a list of ``requests.Response`` objects and returns an `astropy.table.Table` of results.
        
        Parameters
        ----------
        responses : list of ``requests.Response``
            List of ``requests.Response`` objects.
        verbose : bool, optional
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
    def service_request_async(self, service, params, pagesize=None, page=None, verbose=False):
        """
        Given a Mashup service and parameters, builds and excecutes a Mashup query.
        See documentation `here <https://mast.stsci.edu/api/v0/class_mashup_1_1_mashup_request.html>`_ 
        for information about how to build a Mashup request.
        
        Parameters
        ----------
        service : str
            The Mashup service to query.
        params : dict
            JSON object containing service parameters.
        pagesize : int or None, optional
            Default None. 
            Can be used to override the default pagesize (set in configs) for this query only. 
            E.g. when using a slow internet connection.
        page : int or None, optional
            Default None. 
            Can be used to override the default behavior of all results being returned to obtain 
            a sepcific page of results.
        verbose : bool, optional
            Default False. Setting to True provides more extensive output.
        **kwargs: 
            See MashupRequest properties `here <https://mast.stsci.edu/api/v0/class_mashup_1_1_mashup_request.html>`_ for additional keyword arguments.
        
        
        Returns
        -------
            response: list of ``requests.Response``
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
    
        reqString = _prepare_service_request_string(mashupRequest)
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
        verbose : bool, optional
            Default False. Setting to True provides more extensive output.    
        """
        
        service = 'Mast.Name.Lookup'
        params ={'input':objectname,
                 'format':'json'}
        
        response = self.service_request_async(service,params)
        
        result = response[0].json() 
        
        if len(result['resolvedCoordinate']) == 0:
            raise ResolverError("Could not resolve %s to a sky position." % objectname)
            
        
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
    
        
    @class_or_instance
    def query_region_async(self, coordinates, radius=0.2*u.deg, pagesize=None, page=None, verbose=False):
        """
        Given a sky position and radius, returns a list of MAST observations.
        See column documentation `here <https://mast.stsci.edu/api/v0/_c_a_o_mfields.html>`_.
        
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
        pagesize : int or None, optional
            Default None. 
            Can be used to override the default pagesize for (set in configs) this query only. 
            E.g. when using a slow internet connection.
        page : int or None, optional
            Default None.
            Can be used to override the default behavior of all results being returned to 
            obtain a sepcific page of results.
        verbose : bool, optional
            Default False. Setting to True provides more extensive output. 
        
        
        Returns
        -------
            response: list of ``requests.Response``
        """       
        
        # Put coordinates and radius into consistant format
        coordinates = commons.parse_coordinates(coordinates)

        # if radius is just a number we assume degrees
        if isinstance(radius,(int,float)):
            radius = radius * u.deg
        radius = coord.Angle(radius)
        
        service = 'Mast.Caom.Cone'
        params = {'ra':coordinates.ra.deg,
                  'dec':coordinates.dec.deg,
                  'radius':radius.deg}
        
        return self.service_request_async(service, params, pagesize, page, verbose)
        

        
    @class_or_instance
    def query_object_async(self, objectname, radius=0.2*u.deg, pagesize=None, page=None, verbose=False):
        """
        Given an object name, returns a list of MAST observations.
        See column documentation `here <https://mast.stsci.edu/api/v0/_c_a_o_mfields.html>`_.
        
        Parameters
        ----------
        objectname : str 
            The name of the target around which to search. 
        radius : str or `~astropy.units.Quantity` object, optional
            Default 0.2 degrees.
            The string must be parsable by `astropy.coordinates.Angle`. The
            appropriate `~astropy.units.Quantity` object from
            `astropy.units` may also be used. Defaults to 0.2 deg.
        pagesize : int or None, optional
            Default None.
            Can be used to override the default pagesize for (set in configs) this query only. 
            E.g. when using a slow internet connection.
        page : int or None, optional
            Defaulte None.
            Can be used to override the default behavior of all results being returned 
            to obtain a sepcific page of results.
        verbose : bool, optional
            Default False. Setting to True provides more extensive output. 
        
        
        Returns
        -------
        response: list of ``requests.Response``
        """
        
        coordinates = self._resolve_object(objectname,verbose=verbose)
        
        return self.query_region_async(coordinates, radius, pagesize, page, verbose)
    


Observations = ObservationsClass()
Mast = MastClass()
