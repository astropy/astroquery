# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

# put all imports organized as shown below
# 1. standard library imports
import urllib.request
import gzip
import json
import os
import tempfile
import tarfile
import sys

# 2. third party imports
import astropy.units as u
from astropy.extern import six
import astropy.io.votable as votable
from astropy.utils.data import download_file
from astropy.table import Table
from astropy.io import fits

# 3. local imports - use relative imports

# commonly required local imports shown below as example
# all Query classes should inherit from BaseQuery.
from ..query import BaseQuery
# has common functions required by most modules
from ..utils import commons
# prepend_docstr is a way to copy docstrings between methods
from ..utils import prepend_docstr_noreturns
# async_to_sync generates the relevant query tools from _async methods
from ..utils import async_to_sync
# import configurable items declared in __init__.py
from . import conf
from ..exceptions import TableParseError

# declare global variables and constants if any


# Now begin your main class
# should be decorated with the async_to_sync imported previously
@async_to_sync
class ESASkyClass(BaseQuery):

    """
    Not all the methods below are necessary but these cover most of the common
    cases, new methods may be added if necessary, follow the guidelines at
    <http://astroquery.readthedocs.io/en/latest/api.html>
    """
    # use the Configuration Items imported from __init__.py to set the URL,
    # TIMEOUT, etc.
    URLbase = conf.urlBase
    TIMEOUT = conf.timeout
    
    __FITS_STRING = ".fits"
    __FTZ_STRING = ".FTZ"
    __TAR_STRING = ".tar"

    def get_catalogs(self):
        """
        Get the available TAP catalogs in ESASky
        """
        return self._fetch_and_parse_json("catalogs")
    
    def get_catalog_mission_list(self):
        """
        Get the available mission catalogs in ESASky
        """
        return self._json_object_to_list(self.get_catalogs(), "mission")    
    
    def get_catalog_tap_list(self):
        """
        Get the list available TAP catalogs in ESASky
        """
        return self._json_object_to_list(self.get_catalogs(), "tapTable")
    
    def get_observations(self):
        return self._fetch_and_parse_json("observations")
    
    def get_observation_mission_list(self):
        """
        Get the available TAP observations in ESASky
        """
        return self._json_object_to_list(self.get_observations(), "mission")

    def query_region_maps(self, position, radius, mission_name = "all"):
        coordinates = commons.parse_coordinates(position)
        dictionary = {}
        if(mission_name.lower() == 'all'):
            mission_name_list = self.get_observation_mission_list()
            for mission_name in mission_name_list:
                dictionary[mission_name] = self._query_region_observation(coordinates, radius, mission_name)
        else:
            dictionary[mission_name.upper()] = self._query_region_observation(coordinates, radius, mission_name)
            
        return dictionary        
    
    def query_object_obs(self, object_name, observation=None, get_query_payload=False,
                           cache=True, verbose=True):
        """
        This method is for services that can parse object names. Otherwise
        use :meth:`astroquery.template_module.TemplateClass.query_region`.

        Parameters
        ----------
        object_name : str
            name of the identifier to query.
        get_query_payload : bool, optional
            This defaults to False. When set to `True` the method
            should return the HTTP request parameters as a dict.
        observation : string, mandatory 
            The observations in ESASKy to search for the name
        verbose : bool, optional
           This should default to `False`, when set to `True` it displays
           VOTable warnings.
        any_other_param : <param_type>
            similarly list other parameters the method takes

        Returns
        -------
        response : `requests.Response`
            The HTTP response returned from the service.
            All async methods should return the raw HTTP response.

        Examples
        --------
        While this section is optional you may put in some examples that
        show how to use the method. The examples are written similar to
        standard doctests in python.

        """
        
        # check if the catalog is available
        esaskyobs = self.get_esasky_obs_list()
        if (not observation in esaskyobs): 
            raise ValueError("Input observation %s not available." %observation)
            return None
        
        # Initialize the dictionary of HTTP request parameters
        # request_payload = dict()
        query = "SELECT * FROM %s WHERE name='%s';"%(observation, object_name)
        request_payload = self._create_request_payload(query)

        if get_query_payload:
            return request_payload

        return self._fetch_and_parse_from_tap(request_payload, cache, verbose)
     
    def query_region_catalogs(self, position, radius, catalog_name = "all"):
        coordinates = commons.parse_coordinates(position)
        dictionary = {}
        if(catalog_name == 'all'):
            catalogs = self.get_catalog_mission_list()
            for catalog in catalogs:
                dictionary[catalog] = self._query_region_catalog(coordinates, radius, catalog)
        else:
            dictionary[catalog_name] = self._query_region_catalog(coordinates, radius, catalog_name)
            
        return dictionary
    
    def get_maps(self, mission_table, verbose = True):
        maps = dict()
        for mission in mission_table:
            maps[mission] = self._get_maps_mission(mission_table[mission], mission)
        
        print("Observations available at %s" %os.path.abspath("Observations"))
        return maps
  
    def _get_maps_mission(self, maps_table, mission):
        maps = dict()
        
        #HST dev server down
        if(mission == "HST"):
            return maps
        #INTEGRAL does not have a product url yet.
        if(mission == "INTEGRAL"):
            return maps
        
        if(len(maps_table["product_url"]) > 0):
            mission_directory = self._create_directory(mission)    
            print("Starting download of %s data." %mission)
            for product_url_in_bytes in maps_table["product_url"]:
                directory_path = mission_directory + "/"
                product_url = product_url_in_bytes.decode('utf-8')
                print("Downloading from " + product_url, end=" ")
                sys.stdout.flush()
                if(mission == "HERSCHEL"):
                    herschel_data = self._get_herschel_map(product_url, directory_path)
                    
                else:
                    with urllib.request.urlopen(product_url) as response:
                        file_name = ""
                        if(product_url.endswith(self.__FITS_STRING)):
                            file_name = directory_path + self._get_file_name_from_url(product_url)
                        else:
                            file_name = directory_path + self._get_file_name_from_response(response)
                        
                        fits_data = response.read()
                        with open(file_name, 'wb') as fits_file:
                            fits_file.write(fits_data)
                            fits_file.close()
                            maps[file_name] = fits.open(file_name)
                
                print("[Done]")
            print("Downloading of %s data complete." %mission)
        
        return maps
    
    def _get_herschel_map(self, product_url, directory_path, instrument = "both", verbose = True):
        fitsOut = dict()            
        tar_file = tempfile.NamedTemporaryFile()
        with urllib.request.urlopen(product_url) as response:
            tar_file.write(response.read())    
        with tarfile.open(tar_file.name,'r') as tar:
            for member in tar.getmembers():
                member_name = member.name.lower()
                if ('hspire' in member_name or 'hpacs' in member_name):
                    tar.extract(member, path = directory_path)
                    if ('hspireplw' in member_name):
                        array = '500'
                    elif ('hspirepmw' in member_name):
                        array = '350'
                    elif ('hspirepsw' in member_name):
                        array = '250'
                    elif ('hppjsmapb' in member_name):
                        array = 'blue'
                    elif ('hppjsmapr' in member_name):
                        array = 'red'
                    else:
                        array = 'unknown'
                    fitsOut[array] = fits.open(directory_path + member.name)
        return fitsOut
    
    def _create_directory(self, mission):
        maps_directory = "Maps"
        mission_directory = maps_directory + "/" + mission
        if not os.path.exists(mission_directory):
            os.makedirs(mission_directory)
        return mission_directory
        
    def _decompress_map_data(self, file, telescope_name):
        telescope_name = telescope_name.lower()
        if(telescope_name == "hst"):
            file = gzip.decompress(file)
        return file
    
    def _get_file_name_from_response(self, response):
        content_disposition = response.headers.get('Content-Disposition')
        filename_string = "filename="
        start_index = content_disposition.index(filename_string) + len(filename_string)
        if (content_disposition[start_index] == "\""):
            start_index += 1
       
        if (self.__FITS_STRING in content_disposition[start_index : ]):
            end_index = content_disposition.index(self.__FITS_STRING, start_index + 1) + len(self.__FITS_STRING)
            return content_disposition[start_index : end_index]
        elif (self.__FTZ_STRING in content_disposition[start_index : ]):
            end_index = content_disposition.index(self.__FTZ_STRING, start_index + 1) + len(self.__FTZ_STRING)
            return content_disposition[start_index : end_index]
        elif (self.__TAR_STRING in content_disposition[start_index : ]):
            end_index = content_disposition.index(self.__TAR_STRING, start_index + 1) + len(self.__TAR_STRING)
            return content_disposition[start_index : end_index]
        else:
            raise ValueError("Could not find file name in header. Content disposition: %s." %content_disposition)
            return None
    
    def _get_file_name_from_url(self, product_url):
        start_index = product_url.rindex("/") + 1
        return product_url[start_index:]
    
    def _query_region_catalog(self, coordinates, radius, catalog_name):
        catalog_tap_name = self._get_catalog_tap_name(catalog_name)
        query = self._build_catalog_query(coordinates, radius, self._find_catalog_parameters(catalog_tap_name))
        request_payload = self._create_request_payload(query)
        return self._fetch_and_parse_from_tap(request_payload)
    
    def _query_region_observation(self, coordinates, radius, observation_name):
        observation_tap_name = self._get_observation_tap_name(observation_name)
        query = self._build_observation_query(coordinates, radius, self._find_observation_parameters(observation_tap_name))
        request_payload = self._create_request_payload(query)
        return self._fetch_and_parse_from_tap(request_payload)
    
    def _build_observation_query(self, coordinates, radius, json):

        raHours, dec = commons.coord_to_radec(coordinates) # note, RA is in hours 
        ra = raHours * 15.0 # it's need it in degrees
        radiusDeg = commons.radius_to_unit(radius,unit='deg')
        
        query_part1 = "SELECT DISTINCT postcard_url,  product_url,  observation_id, ra_deg, dec_deg, "
        if (json["isSurveyMission"]):
            query_part2 = "tstart_iso, telapse "
            query_part4 = "WHERE 1=CONTAINS(pos, "
        else:
            query_part2 = "stc_s "
            query_part4 = "WHERE 1=CONTAINS(fov, "
            
        query_part3 = "FROM %s " %json["tapTable"]
        
        if (radiusDeg == 0):
            query_part5 = "POINT('ICRS', %f, %f));" %(ra, dec) 
        else:
            query_part5 = "CIRCLE('ICRS', %f, %F, %f));" %(ra, dec, radiusDeg) 
        
        query = query_part1 + query_part2 + query_part3 + query_part4 + query_part5
        return query  
               
    def _build_catalog_query(self, coordinates, radius, json):

        raHours, dec = commons.coord_to_radec(coordinates) # note, RA is in hours 
        ra = raHours * 15.0 # it's need it in degrees
        radiusDeg = commons.radius_to_unit(radius,unit='deg')
        
        query = ("SELECT TOP %s %s as name, " %(json["sourceLimit"], json["polygonNameTapColumn"])
            + "%s as ra, %s as dec " %(json["polygonRaTapColumn"], json["polygonDecTapColumn"])
            + "FROM %s " %json["tapTable"])
        if (radiusDeg == 0):
            query += "WHERE 1=CONTAINS(%s, POINT('ICRS',%f,%f)) "%(json["posTapColumn"], ra, dec)
        else:
            query += "WHERE 1=CONTAINS(%s, CIRCLE('ICRS', %f, %f, %f)) "%(json["posTapColumn"], ra, dec, radiusDeg)  
            
        query += "ORDER BY %s;" %json["orderBy"]
        return query            
            
    def _find_catalog_parameters(self, catalog_name):
        return self._find_mission_parameters(catalog_name, self.get_catalogs())
    
    def _find_observation_parameters(self, mission_name):
        return self._find_mission_parameters(mission_name, self.get_observations())
    
    def _find_mission_parameters(self, tap_name, json):
        for mission in json:
            if (mission["tapTable"] == tap_name):
                return mission
        raise ValueError("Input tap name %s not available." %tap_name)
        return None
    
    def query_herschel_observations(self, obsid, get_query_payload=False, cache=True, verbose=True):
        """
        TODO
        """
        query = ("SELECT DISTINCT postcard_url, product_url,  observation_id,  instrument,  "
        + "filter,  ra_deg as ra,  dec_deg as dec, start_time,  duration FROM mv_hsa_esasky_photo_table_fdw "
        + "WHERE observation_id='%i'"%obsid)

        request_payload = self._create_request_payload(query)
        if get_query_payload:
            return request_payload
        
        return self._fetch_and_parse_from_tap(request_payload, cache, verbose)
    
    def get_herschel_default_maps(self, resultTable, instrument='both', verbose=True):
        """
        From the results table, download the standalone browse product tar file and extract the maps in a 
        dictionary with FITS files per band:
        for SPIRE with keywords '250', '350' and '500'
        for PACS with keywords 'blue', 'red'
        """
        
        if (not 'product_url' in resultTable.colnames):
            raise TableParseError("The input table has no column 'product_url'"
                                  ". Cannot continue")
            return None

        tar_file = tempfile.NamedTemporaryFile()
        if (verbose):
            print ("Will search for maps from %s instrument(s)"%instrument)
        nrows = len(resultTable)
        fitsOut = dict()            
        with tempfile.TemporaryDirectory() as tmp_dir:
            for i in range(nrows):
                product_url = resultTable["product_url"][i].decode('utf-8')
                if (not (instrument in product_url) and (instrument != 'both')):
                    continue
                with urllib.request.urlopen(product_url) as response:
                    tar_file.write(response.read())    
                with tarfile.open(tar_file.name,'r') as tar:
                    for member in tar.getmembers():
                        if (verbose): print (member.name)
                        if ('hspire' in member.name or 'hpacs' in member.name):
                            tar.extract(member,path=tmp_dir)
                            if ('hspireplw' in member.name):
                                array = '500'
                            elif ('hspirepmw' in member.name):
                                array = '350'
                            elif ('hspirepsw' in member.name):
                                array = '250'
                            elif ('hpppmapb' in member.name):
                                array = 'blue'
                            elif ('hpppmapr' in member.name):
                                array = 'red'
                            else:
                                array = 'unknown'
                            fitsFile = os.path.join(tmp_dir, member.name)
                            fitsOut[array] = fits.open(fitsFile)
        return fitsOut

    # For services that can query coordinates, use the query_region method.
    # The pattern is similar to the query_object method. The query_region
    # method also has a 'radius' keyword for specifying the radius around
    # the coordinates in which to search. If the region is a box, then
    # the keywords 'width' and 'height' should be used instead. The coordinates
    # may be accepted as an `astropy.coordinates` object or as a string, which
    # may be further parsed.

    # similarly we write a query_region_async method that makes the
    # actual HTTP request and returns the HTTP response

    def query_region_obs(self, coordinates, radius = 0 *u.arcmin,
                           get_query_payload=False, cache=True, verbose=True):
        """
        Queries a region around the specified coordinates.

        Parameters
        ----------
        coordinates : str or `astropy.coordinates`.
            coordinates around which to query
        radius : str or `astropy.units.Quantity`.
            the radius of the cone search
        get_query_payload : bool, optional
            Just return the dict of HTTP request parameters.
        verbose : bool, optional
            Display VOTable warnings or not.

        Returns
        -------
        response : `requests.Response`
            The HTTP response returned from the service.
            All async methods should return the raw HTTP response.
        """

        request_payload = self._args_to_payload(position=coordinates, radius=radius, table_name='mv_hsa_esasky_photo_table_fdw')
        if get_query_payload:
            return request_payload
        
        return self._fetch_and_parse_from_tap(request_payload, cache, verbose)

    def _fetch_and_parse_json(self, object_name):
        url = self.URLbase + "/" + object_name
        with urllib.request.urlopen(url) as response:
            string_response = response.read().decode('utf-8')
        json_response = json.loads(string_response)
        return json_response[object_name]
    
    def _json_object_to_list(self, json, field_name):
        response_list = []
        for i in range(len(json)):
            response_list.append(json[i][field_name])
        return response_list
    
    def _fetch_and_parse_from_tap(self, request_payload, cache = True, verbose = True):
        response = self._fetch("/tap/sync", request_payload, cache, verbose)
        return self._parse_xml_table(response, verbose=verbose)
    
    def _fetch(self, url_extension, request_payload, cache, verbose):
        URL = self.URLbase + url_extension
     
        # BaseQuery classes come with a _request method that includes a
        # built-in caching system   
        return self._request('GET', URL, params=request_payload,
                                 timeout=self.TIMEOUT, cache=cache)
        
    def _create_request_payload(self, query):
        return {'REQUEST':'doQuery', 'LANG':'ADQL', 'FORMAT': 'VOTABLE', 'QUERY': query}
    
    # as we mentioned earlier use various python regular expressions, etc
    # to create the dict of HTTP request parameters by parsing the user
    # entered values. For cleaner code keep this as a separate private method:

    def _args_to_payload(self, position = None, radius = 0 *u.arcmin, table_name=None):
        coordinates = commons.parse_coordinates(position)
        raHours, dec = commons.coord_to_radec(coordinates) # note, RA is in hours 
        ra = raHours* 15.0 # it's need it in degrees
        #
        radiusDeg = commons.radius_to_unit(radius,unit='deg')
        #
        query = ("SELECT DISTINCT postcard_url, product_url,  observation_id,  instrument,  "
        + "filter,  ra_deg as ra,  dec_deg as dec, start_time,  duration FROM  %s "%table_name)
        if (radiusDeg == 0):
            query += "WHERE 1=CONTAINS(POINT('ICRS',%f,%f),%s.fov) ORDER BY observation_id;"%(ra,dec,table_name)
        else:
            query += "WHERE 1=INTERSECTS(%s.fov,CIRCLE('ICRS',%f,%f,%f)) ORDER BY observation_id;"%(table_name,ra,dec,radiusDeg)        
                
        # code to parse input and construct the dict
        # goes here. Then return the dict to the caller
        
        return self._create_request_payload(query)

    # the methods above call the private _parse_xml_table method.
    # This should parse the raw HTTP response and return it as
    # an `astropy.table.Table`. Below is the skeleton:

    def _parse_xml_table(self, response, verbose=False):
        # if verbose is False then suppress any VOTable related warnings
        if not verbose:
            commons.suppress_vo_warnings()
        # try to parse the result into an astropy.Table, else
        # return the raw result with an informative error message.
        try:
            tf = six.BytesIO(response.content)
            vo_table = votable.parse(tf, pedantic=False)
            first_table = vo_table.get_first_table()
            table = first_table.to_table(use_names_over_ids=True)
            return table
        except Exception as ex:
            self.response = response
            self.table_parse_error = ex
            raise TableParseError(
                "Failed to parse ESASky VOTABLE result! The raw response can be "
                "found in self.response, and the error in "
                "self.table_parse_error.")
        return Table()
  
    def _get_observation_tap_name(self, mission_name):
        return self._get_tap_name(self._fetch_and_parse_json("observations"), mission_name)

    def _get_catalog_tap_name(self, mission_name):
        return self._get_tap_name(self._fetch_and_parse_json("catalogs"), mission_name)

    
    def _get_tap_name(self, json, mission_name):
        for i in range(len(json)):
            if (json[i]["mission"].lower() == mission_name.lower()):
                return json[i]["tapTable"]
        
        raise ValueError("Input %s not available." %mission_name)
        return None
    
    
    # Image queries do not use the async_to_sync approach: the "synchronous"
    # version must be defined explicitly.  The example below therefore presents
    # a complete example of how to write your own synchronous query tools if
    # you prefer to avoid the automatic approach.
    #
    # For image queries, the results should be returned as a
    # list of `astropy.fits.HDUList` objects. Typically image queries
    # have the following method family:
    # 1. get_images - this is the high level method that interacts with
    #        the user. It reads in the user input and returns the final
    #        list of fits images to the user.
    # 2. get_images_async - This is a lazier form of the get_images function,
    #        in that it returns just the list of handles to the image files
    #        instead of actually downloading them.
    # 3. extract_image_urls - This takes in the raw HTTP response and scrapes
    #        it to get the downloadable list of image URLs.
    # 4. get_image_list - this is similar to the get_images, but it simply
    #        takes in the list of URLs scrapped by extract_image_urls and
    #        returns this list rather than the actual FITS images
    # NOTE : in future support may be added to allow the user to save
    # the downloaded images to a preferred location. Here we look at the
    # skeleton code for image services

    def get_images(self, coordinates, radius, get_query_payload):
        """
        A query function that searches for image cut-outs around coordinates

        Parameters
        ----------
        coordinates : str or `astropy.coordinates`.
            coordinates around which to query
        radius : str or `astropy.units.Quantity`.
            the radius of the cone search
        get_query_payload : bool, optional
            If true than returns the dictionary of query parameters, posted to
            remote server. Defaults to `False`.

        Returns
        -------
        A list of `astropy.fits.HDUList` objects
        """
        readable_objects = self.get_images_async(coordinates, radius,
                                              get_query_payload=get_query_payload)
        if get_query_payload:
            return readable_objects  # simply return the dict of HTTP request params
        # otherwise return the images as a list of astropy.fits.HDUList
        return [obj.get_fits() for obj in readable_objects]

    @prepend_docstr_noreturns(get_images.__doc__)
    def get_images_async(self, coordinates, radius, get_query_payload=False):
        """
        Returns
        -------
        A list of context-managers that yield readable file-like objects
        """
        # As described earlier, this function should return just
        # the handles to the remote image files. Use the utilities
        # in commons.py for doing this:

        # first get the links to the remote image files
        image_urls = self.get_image_list(coordinates, radius,
                                         get_query_payload=get_query_payload)
        if get_query_payload:  # if true then return the HTTP request params dict
            return image_urls
        # otherwise return just the handles to the image files.
        return [commons.FileContainer(U) for U in image_urls]

    # the get_image_list method, simply returns the download
    # links for the images as a list

    @prepend_docstr_noreturns(get_images.__doc__)
    def get_image_list(self, coordinates, radius, get_query_payload=False):
        """
        Returns
        -------
        list of image urls
        """
        # This method should implement steps as outlined below:
        # 1. Construct the actual dict of HTTP request params.
        # 2. Check if the get_query_payload is True, in which
        #    case it should just return this dict.
        # 3. Otherwise make the HTTP request and receive the
        #    HTTP response.
        # 4. Pass this response to the extract_image_urls
        #    which scrapes it to extract the image download links.
        # 5. Return the download links as a list.
        request_payload = self._args_to_payload(coordinates, radius, table_name='mv_hsa_esasky_photo_table_fdw')
        if get_query_payload:
            return request_payload
        response = commons.send_request(self.URL,
                                        request_payload,
                                        self.TIMEOUT,
                                        request_type='GET')
        return self.extract_image_urls(response.text)

    # the extract_image_urls method takes in the HTML page as a string
    # and uses regexps, etc to scrape the image urls:

    def extract_image_urls(self, html_str):
        """
        Helper function that uses regex to extract the image urls from the
        given HTML.

        Parameters
        ----------
        html_str : str
            source from which the urls are to be extracted

        Returns
        -------
        list of image URLs
        """
        # do something with regex on the HTML
        # return the list of image URLs
        pass

# the default tool for users to interact with is an instance of the Class
ESASky = ESASkyClass()

# once your class is done, tests should be written
# See ./tests for examples on this

# Next you should write the docs in astroquery/docs/module_name
# using Sphinx.
