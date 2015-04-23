# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import print_function

# put all imports organized as shown below
# 1. standard library imports

# 2. third party imports
import astropy.units as u
import astropy.coordinates as coord
import astropy.io.votable as votable
from astropy.table import Table
from astropy.io import fits
from astropy import log

# 3. local imports - use relative imports
# commonly required local imports shown below as example
from ..query import BaseQuery # all Query classes should inherit from this.
from ..utils import commons # has common functions required by most modules
from ..utils import prepend_docstr_noreturns # automatically generate docs for similar functions
from ..utils import async_to_sync # all class methods must be callable as static as well as instance methods.
from . import SERVER, TIMEOUT # import configurable items declared in __init__.py


# export all the public classes and methods
__all__ = ['Astrometry', 'AstrometryClass']

# declare global variables and constants if any

# Now begin your main class
# should be decorated with the async_to_sync imported previously

@async_to_sync
class AstrometryClass(BaseQuery):

    """
    Not all the methods below are necessary but these cover most of the common cases, new methods may be added if necessary, follow the guidelines at <http://astroquery.readthedocs.org/en/latest/api.html>
    """
    # use the Configuration Items imported from __init__.py to set the URL, TIMEOUT, etc.
    URL = SERVER()
    TIMEOUT = TIMEOUT()

    def _store_API_key(self, value):
        """ Cache the Astrometry.net API key on disk. """
        pass

    def _get_stored_API_key(self):
        """ Return the API key, raise KeyError if not cached on disk. """
        raise KeyError

    @property
    def key(self):
        """ Getter for the Astrometry.net API key. """

        if self._key is None:
            log.error("Astrometry.net API key not found")
        return self._key

    @key.setter
    def key(self, value):
        """ Setter for the API key, cache it on disk. """

        self._store_API_key(value)
        self._key = value

    def __init__(self):
        """ Load the cached API key, show a warning message if can't be found. """

        try:
            self._key = self._get_stored_API_key()
        except KeyError:
            log.warn("Astrometry.net API key not found")
            log.warn("You need to register it with Astrometry.key = 'XXXXXXXX'")
            self._key = None

    def build_request(self, catalog, settings={}, x_colname='x', y_colname='y'):
        """
        Convert the settings and sources into an object that can be used
        to query astrometry.net.
        
        Parameters
        ----------
        catalog: `astropy.table.Table`
            Sources used to generate astrometric solution
        settings: dict (optional)
            Settings sent to astrometry.net to help generate the astrometric solution
        x_colname: str
            Column name of the x coordinate in the table. Defaults to ``x``.
        y_colname: str
            Column name of the y coordinate in the table. Defaults to ``y``.
        Returns
        -------
        result: str
            String used to send request to astrometry.net
        """
        apiurl = 'http://nova.astrometry.net/api/'
        
        # Login to the service
        login_url = apiurl + "login"
        login_headers = {}
        login_data = {'request-json': simplejson.dumps({ 'apikey' : self._key})}
        login_data = urlencode(login_data)
        request = Request(url=login_url, headers=login_headers, data=login_data)
        f = urlopen(request)
        txt = f.read()
        result = simplejson.loads(txt)
        stat = result.get('status')
        if stat == 'error':
            print("Login error, exiting.")
            os.system("rm " + anetcat_file)
            os.system("rm " + sexcat_file)
            sys.exit()
        session_string = result["session"]
        
        # Upload the text file to request a WCS solution
        upload_url = apiurl + "upload"
        upload_args = { 
                        'allow_commercial_use': 'd', 
                        'allow_modifications': 'd', 
                        'publicly_visible': 'y', 
                        'scale_units': 'arcsecperpix',
                        'scale_type': 'ul', 
                        'scale_lower': 0.20,       # arcsec/pix
                        'scale_upper': 0.30,       # arcsec/pix
                        'parity': 0,
                        'session': session_string
                        }
        upload_args = upload_args.update(settings)
        upload_json = simplejson.dumps(upload_args)
        
        # Format the list in the appropriate format
        # Currently this is just using the code from astrometry.net's client.py
        # Ideally this could probably be re-written and improved
        src_list = '\n'.join(['{0:.3f}\t{1:.3f}'.format(row[x_colname], row[y_colname]) 
            for row in catalog])
        temp_file = 'temp.cat'
        f = open(tempfile, 'w')
        f.write(src_list)
        f = open(upload_filename, 'rb')
        file_args=(temp_file, f.read())

        m1 = MIMEBase('text', 'plain')
        m1.add_header('Content-disposition', 'form-data; name="request-json"')
        m1.set_payload(upload_json)

        m2 = MIMEApplication(file_args[1],'octet-stream',encode_noop)
        m2.add_header('Content-disposition',
                      'form-data; name="file"; filename="%s"' % file_args[0])

        #msg.add_header('Content-Disposition', 'attachment',
        # filename='bud.gif')
        #msg.add_header('Content-Disposition', 'attachment',
        # filename=('iso-8859-1', '', 'FuSballer.ppt'))

        mp = MIMEMultipart('form-data', None, [m1, m2])

        # Makie a custom generator to format it the way we need.
        from cStringIO import StringIO
        from email.generator import Generator

        class MyGenerator(Generator):
            def __init__(self, fp, root=True):
                Generator.__init__(self, fp, mangle_from_=False,
                                   maxheaderlen=0)
                self.root = root
            def _write_headers(self, msg):
                # We don't want to write the top-level headers;
                # they go into Request(headers) instead.
                if self.root:
                    return                        
                # We need to use \r\n line-terminator, but Generator
                # doesn't provide the flexibility to override, so we
                # have to copy-n-paste-n-modify.
                for h, v in msg.items():
                    print >> self._fp, ('%s: %s\r\n' % (h,v)),
                # A blank line always separates headers from body
                print >> self._fp, '\r\n',

            # The _write_multipart method calls "clone" for the
            # subparts.  We hijack that, setting root=False
            def clone(self, fp):
                return MyGenerator(fp, root=False)

        fp = StringIO()
        g = MyGenerator(fp)
        g.flatten(mp)
        upload_data = fp.getvalue()
        upload_headers = {'Content-type': mp.get('Content-type')}

        upload_package = {
            'url': upload_url,
            'headers': upload_headers,
            'data': upload_data
        }
        
        return upload_package
    
    def submit(self, url, headers, data):
        """
        Submit a list of coordinates to astrometry.net built by Astrometry.build_request
        
        Parameters
        ----------
        url: str
            url of the request
        headers: str
            headers for the request
        data: str
            data packet to send in request
        """
        request = Request(url=url, header=headers, data=data)
    
    def get_submit_status(self, subid, timeout=30):
        """
        Get the status of a submitted source list. This polls astrometry.net every 5
        seconds until it either receives a job status or timeout is reached.
        
        Parameters
        ----------
        subid: str
            - subid returned by ``submit`` function
        timeout: int (optional):
            Maximum time to wait for a submission status
        
        Result
        ------
        jobid: str
            jobid astrometry.net has assigned to the submitted list
        """
        import math
        # Check submission status
        subcheck_url = apiurl + "submissions/" + str(subid)

        print('subcheckurl', subcheck_url)

        request = Request(url=subcheck_url)
        still_processing = True
        n_failed_attempts = 0
        max_attempts = math.ceil(timeout/5)
        while still_processing and n_failed_attempts < max_attempts:
            try:
                f = urlopen(request)
                txt = f.read()
                result = simplejson.loads(txt)
                if result['jobs'][0] is None:
                    print('result is none')
                    raise Exception()
                # print result
                still_processing = False
            except:
                print("Submission doesn't exist yet, sleeping for 5s.")
                time.sleep(5)
                n_failed_attempts += 1
        if n_failed_attempts > max_attempts:
            raise Exception("The submitted job has apparently timed out, exiting.")
        
        return result['jobs']
    
    def get_wcs_file(self, jobs, timeout=90):
        """
        Get a wcs file from astrometry.net given a jobid
        
        Parameters
        ----------
        jobs: list
            List of jobs returned by `get_submit_status`
        timeout: int (optional):
            Maximum time to wait for an anstrometric solution before timing out
            
        
        Returns
        -------
        header: `astropy.io.fits.Header`
            Header returned by astrometry.net
        """
        # Attempt to load wcs from astrometry.net
        n_jobs = len(jobs)
        still_processing = True
        n_failed_attempts = 0
        n_failed_jobs = 0
        max_attempts = math.ceil(timeout/5)
        while still_processing and n_failed_attempts < max_attempts and n_failed_jobs < n_jobs:
            time.sleep(5)
            for job_id in job_id_list:
                jobcheck_url = apiurl + "jobs/" + str(job_id)
                print(jobcheck_url)
                request = Request(url=jobcheck_url)
                f = urlopen(request)
                txt = f.read()
                result = simplejson.loads(txt)
                print("Checking astrometry.net job ID", job_id, result)
                if result["status"] == "failure":
                    print('failed')
                    n_failed_jobs += 1
                    job_id_list.remove(job_id)
                if result["status"] == "success":
                    print('success')
                    solved_job_id = job_id
                    still_processing = False
                    print(job_id, "SOLVED")
            n_failed_attempts += 1

        if still_processing == True:
            print("Astrometry.net took too long to process, so we're exiting. Try checking "+
                "astrometry.net again later")
            return

        if still_processing == False:
            import wget
            url = "http://nova.astrometry.net/wcs_file/" + str(solved_job_id)
            wcs_filename = wget.download(url)
        
        # Finally, strip out the WCS header info from this solved fits file and write it
        # into the original fits file.
        string_header_keys_to_copy = [
            "CTYPE1",
            "CTYPE2",
            "CUNIT1",
            "CUNIT2"
            ]

        float_header_keys_to_copy = [
            "EQUINOX",
            "LONPOLE",
            "LATPOLE",
            "CRVAL1",
            "CRVAL2",
            "CRPIX1",
            "CRPIX2",
            "CD1_1",
            "CD1_2",
            "CD2_1",
            "CD2_2",
            "IMAGEW",
            "IMAGEH",
            "A_ORDER",
            "A_0_2",
            "A_1_1",
            "A_2_0",
            "B_ORDER",
            "B_0_2",
            "B_1_1",
            "B_2_0",
            "AP_ORDER",
            "AP_0_1",
            "AP_0_2",
            "AP_1_0",
            "AP_1_1",
            "AP_2_0",
            "BP_ORDER",
            "BP_0_1",
            "BP_0_2",
            "BP_1_0",
            "BP_1_1",
            "BP_2_0"
            ]
    

        wcs_image = wcs_filename
        wcs_hdu = pyfits.open(wcs_image)
        wcs_header = wcs_hdu[0].header.copy()
        wcs_hdu.close()
        
        return wcs_header        

    def solve(self, sources, settings, x_colname="x", y_colname="y", fwhm_colname=None, 
            fwhm_std_cut=1, flags_colname=None, flux=None, timeout=30):
        """
        First draft of function to send a catalog or image to astrometry.net and
        return the astrometric solution. 

        Parameters
        ----------
        sources : `astropy.table.Table` (for now)
            Object catalog or image to use for the astrometric solution.
        settings: dict
            Settings sent to astrometry.net to help generate the astrometric solution
        x_colname: str
            Column name of the x coordinate in the table. Defaults to ``x``.
        y_colname: str
            Column name of the y coordinate in the table. Defaults to ``y``.
        fwhm_colname: str (optional):
            Column name of the FWHM. This is only needed to cut sources based on 
            FWHM (sources where fhwm within ``fwhm_std`` of the median)
        fwhm_std_cut: int (optional):
            Number of standard deviations to use when selecting sources
        flags_colname: str (optional):
            Column name of flags for the sources. This is only needed to cut flagged sources
            (objects where flags=0).
        timeout: int (optional):
            Maximum time to wait for an anstrometric solution before timing out

        Returns
        -------
        result : `astropy.io.fits.Header`
            The result is a header that has the new keys giving the astrometric solution.

        Examples
        --------
        While this section is optional you may put in some examples that
        show how to use the method. The examples are written similar to
        standard doctests in python.
        """
        # Temporarily import all of the modules used by astromery.net's client to get the
        # astrometric solution. In the future this can be cleaned up and done in a more
        # standard way
        import os
        import sys
        from numpy import median, std
        import astropy.io.fits as pyfits
        import simplejson
        from urllib import urlencode
        from urllib2 import urlopen, Request
        from email.mime.multipart import MIMEMultipart
        from email.mime.base import MIMEBase
        from email.mime.application  import MIMEApplication
        from email.encoders import encode_noop
        import time
        import subprocess
        
        # Remove flagged sources
        if flag_colname is not None:
            catalog = sources[sources[flag_colname]==0]
        else:
            catalog = sources
        
        # Remove sources outside the normal 
        if fwhm_colname is not None:
            fwhm_med = median(catalog[fwhm_colname])
            fwhm_std = std(catalog[fwhm_colname])
            fwhm_lower = fwhm_med-fwhm_std_cut * fwhm_std
            fwhm_upper = fwhm_med+fwhm_std_cut * fwhm_std
            catalog = catalog[(catalog[fwhm_colname]<fwhm_upper) & 
                (catalog[fwhm_colname]>fwhm_lower)]
        
        # Only choose the top 50 sources
        if len(catalog)>50:
            catalog = catalog[:50]
        catalog = catalog.group_by(flux_colname)
        
        # Create a list of coordinates in a format that astrometry.net recognizes
        upload_kwargs = self.build_request(settings, catalog, x_colname, y_colname)
        
        self.submit(**upload_kwargs)
        
        f = urlopen(request)
        txt = f.read()
        result = simplejson.loads(txt)
        stat = result.get('status')
        if stat == 'error':
            print("Upload error, exiting.")
            os.system("rm " + temp_file)
            sys.exit()
        subid = result["subid"]

        print('stat', stat)
        print('id', result['subid'])

        time.sleep(5)
        
        jobs = self.get_submit_status(subid, 30)
        
        time.sleep(5)
        
        wcs_fits = self.get_wcs_file(job_id, timeout)
        
        return result

    # all query methods usually have a corresponding async method
    # that handles making the actual HTTP request and returns the
    # raw HTTP response, which should be parsed by a separate
    # parse_result method. Since these async counterparts take in
    # the same parameters as the corresponding query methods, but
    # differ only in the return value, they should be decorated with
    # prepend_docstr_noreturns which will automatically generate
    # the common docs. See below for an example.


    @prepend_docstr_noreturns(query_object.__doc__)
    def query_object_async(self, object_name, get_query_payload=False) :
        """
        Returns
        -------
        response : `requests.Response`
            The HTTP response returned from the service.
            All async methods should return the raw HTTP response.
        """
        # the async method should typically have the following steps:
        # 1. First construct the dictionary of the HTTP request params.
        # 2. If get_query_payload is `True` then simply return this dict.
        # 3. Else make the actual HTTP request and return the corresponding
        #    HTTP response
        # All HTTP requests are made via the `commons.send_request` method.
        # This uses the Python Requests library internally, and also takes
        # care of error handling.
        # See below for an example:

        # first initialize the dictionary of HTTP request parameters
        request_payload = dict()

        # Now fill up the dictionary. Here the dictionary key should match
        # the exact parameter name as expected by the remote server. The
        # corresponding dict value should also be in the same format as
        # expected by the server. Additional parsing of the user passed
        # value may be required to get it in the right units or format.
        # All this parsing may be done in a separate private `_args_to_payload`
        # method for cleaner code.

        request_payload['object_name'] = object_name
        # similarly fill up the rest of the dict ...

        if get_query_payload:
            return request_payload
        # commons.send_request takes 4 parameters - the URL to query, the dict of
        # HTTP request parameters we constructed above, the TIMEOUT which we imported
        # from __init__.py and the type of HTTP request - either 'GET' or 'POST', which
        # defaults to 'GET'.
        response = commons.send_request(self.URL,
                                        request_payload,
                                        self.TIMEOUT,
                                        request_type='GET')
        return response


    # For services that can query coordinates, use the query_region method.
    # The pattern is similar to the query_object method. The query_region
    # method also has a 'radius' keyword for specifying the radius around
    # the coordinates in which to search. If the region is a box, then
    # the keywords 'width' and 'height' should be used instead. The coordinates
    # may be accepted as an `astropy.coordinates` object or as a
    # string, which may be further parsed.

    def query_region(self, coordinates, radius, width, height, get_query_payload=False, verbose=False):
        """
        Queries a region around the specified coordinates.

        Parameters
        ----------
        coordinates : str or `astropy.coordinates`.
            coordinates around which to query
        radius : str or `astropy.units.Quantity`.
            the radius of the cone search
        width : str or `astropy.units.Quantity`
            the width for a box region
        height : str or `astropy.units.Quantity`
            the height for a box region
        get_query_payload : bool, optional
            Just return the dict of HTTP request parameters.
        verbose : bool, optional
            Display VOTable warnings or not.

        Returns
        -------
        result : `~astropy.table.Table`
            The result of the query as a `~astropy.table.Table` object.
            All queries other than image queries should typically return
            results like this.
        """
        # the documentation and code are similar to the steps outlined in the
        # `query_object` method, but a rough sketch is provided below

        response = self.query_region_async(coordinates, radius, height, width,
                                           get_query_payload=get_query_payload)
        result = self._parse_result(response, verbose=verbose)
        return result

    # similarly we write a query_region_async method that makes the
    # actual HTTP request and returns the HTTP response

    @prepend_docstr_noreturns(query_region.__doc__)
    def query_region_async(self, coordinates, radius, height, width, get_query_payload=False):
        """
        Returns
        -------
        response : `requests.Response`
            The HTTP response returned from the service.
            All async methods should return the raw HTTP response.
        """
        request_payload = self._args_to_payload(coordinates, radius, height, width)
        if get_query_payload:
            return request_payload
        response = commons.send_request(self.URL,
                                        request_payload,
                                        self.TIMEOUT,
                                        request_type='GET')
        return response

    # as we mentioned earlier use various python regular expressions, etc
    # to create the dict of HTTP request parameters by parsing the user
    # entered values. For cleaner code keep this as a separate private method:

    def _args_to_payload(self, *args, **kwargs):
        request_payload = dict()
        # code to parse input and construct the dict
        # goes here. Then return the dict to the caller
        return request_payload

    # the methods above call the private _parse_result method.
    # This should parse the raw HTTP response and return it as
    # an `astropy.table.Table`. Below is the skeleton:

    def _parse_result(self, response, verbose=False):
        # if verbose is False then suppress any VOTable related warnings
        if not verbose:
            commons.suppress_vo_warnings()
        # try to parse the result into an astropy.Table, else
        # return the raw result with an informative error message.
        try:
            # do something with regex to get the result into
            # astropy.Table form. return the Table.
            pass
        except:
            # catch common errors here
            # return raw result/ handle in some way
            pass

    # for image queries, the results should be returned as a
    # list of `astropy.fits.HDUList` objects. Typically image queries
    # have the following method family:
    # 1. get_images - this is the high level method that interacts with
    #        the user. It reads in the user input and returns the final
    #        list of fits images to the user.
    # 2. get_images_async - This is a lazier form of the get_images function, in
    #        that it returns just the list of handles to the image files instead
    #        of actually downloading them.
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
        readable_objs = self.get_images_async(coordinates, radius,
                                              get_query_payload=get_query_payload)
        if get_query_payload:
            return readable_objs # simply return the dict of HTTP request params
        # otherwise return the images as a list of astropy.fits.HDUList
        return [obj.get_fits() for obj in readable_objs]

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
        # 4. Pass this raw response to the extract_image_urls
        #    which scrapes it to extract the image download links.
        # 5. Return the download links as a list.
        request_payload = self._args_to_payload(coordinates, radius)
        if get_query_payload:
            return request_payload
        response = commons.send_request(self.URL,
                                        request_payload,
                                        self.TIMEOUT,
                                        request_type='GET')
        return self.extract_image_urls(response.content)

    # the extract_image_urls method takes in the HTML page as a string
    # and uses regexps, etc to scrape the image urls:


    def extract_image_urls(self, html_str):
        """
        Helper function that uses regex to extract the image urls from the given HTML.
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
Astrometry = AstrometryClass()

# once your class is done, tests should be written
# See ./tests for examples on this

# Next you should write the docs in astroquery/docs/module_name
# using Sphinx.
