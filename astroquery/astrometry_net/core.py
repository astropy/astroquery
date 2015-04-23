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

# the default tool for users to interact with is an instance of the Class
Astrometry = AstrometryClass()

# once your class is done, tests should be written
# See ./tests for examples on this

# Next you should write the docs in astroquery/docs/module_name
# using Sphinx.
