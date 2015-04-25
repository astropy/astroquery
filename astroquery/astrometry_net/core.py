"""
==============
Astrometry.net
==============
Given an astropy `astropy.table.Table` as a source list, calculate the astrometric solution.
Before querying astrometry.net you will have to register and obtain an api key from 
[http://nova.astrometry.net/].

Sample Use
=========
::

    from astropy.table import Table
    from astroquery.astrometry_net import AstrometryNet

    AstrometryNet.api_key = 'XXXXXXXXXXXXXXXX'

    sources = Table.read('catalog.fits')

    settings = {
        'scale_units': 'arcsecperpix',
        'scale_type': 'ul', 
        'scale_lower': 0.20,
        'scale_upper': 0.30,
        'center_ra': 8.711675,
        'center_dec': -78.9810555556,
        'radius': 15,
        'parity': 0
    }

    AstrometryNet.solve(sources, settings, 'X_IMAGE', 'Y_IMAGE', 'FWHM_IMAGE', 'FLAGS', 'FLUX_APER')


Settings
========
In order to speed up the astrometric solution it is possible to pass a dictionary of settings
to `astroquery.AstrometryNet.build_pacakge` or `astroquery.AstrometryNet.build_pacakge`.
If no settings are passed to the build function then a set of default parameters will be
used, although this will increase the time it takes astrometry.net to generate a solution.
It is recommended to at least set the bounds of the pixel scale to a reasonable value.

Most of the following descriptions are taken directly from 
[astrometry.net](http://nova.astrometry.net/upload).

Scale
-----
It is important to set the pixel scale of the image as accurate as possible to increase the
speed of astrometry.net. From astrometry.net: "Most digital-camera images are at least 10 
degrees wide; most professional-grade telescopes are narrower than 2 degrees."

Several parameters are available to set the pixel scale.

    ``scale_units``
        - Units used by pixel scale variables
        - Possible values:
            * ``arcsecperpix``: arcseconds per pixel
            * ``arcminwidth``: width of the field (in arcminutes)
            * ``degwidth``:width of the field (in degrees)
            * ``focalmm``: focal length of the lens (for 35mm film equivalent sensor)
    ``scale_type``
        - Type of scale used
        - Possible values:
            * ``ul``: Set upper and lower bounds. If ``scale_type='ul'`` the parameters
              ``scale_upper`` and ``scale_lower`` must be set to the upper and lower bounds
              of the pixel scale respectively
            * ``ev``: Set the estimated value with a given error. If ``scale_type='ev'`` the
              parameters ``scale_est`` and ``scale_err`` must be set to the estiimated value 
              (in pix) and error (percentage) of the pixel scale.

Parity
------
Flipping an image reverses its "parity". If you point a digital camera at the sky and 
submit the JPEG, it probably has negative parity. If you have a FITS image, it probably 
has positive parity. Selecting the right parity will make the solving process run faster, 
but if in doubt just try both. ``parity`` can be set to the following values:
    - ``0``: positive parity
    - ``1``: negative parity
    - ``2``: try both

Star Positional Error
---------------------
When we find a matching "landmark", we check to see how many of the stars in your field 
match up with stars we know about. To do this, we need to know how much a star in your 
field could have moved from where it should be.

The unit for positional error is in pixels and is set by the key ``positional_error``.

Limits
------
In order to narrow down our search, you can supply a field center along with a radius. 
We will only search in indexes which fall within this area.

To set limits use all of the following parameters:
    ``center_ra``: center RA of the field (in degrees)
    ``center_dec``: center DEC of the field (in degrees)
    ``radius``: how far the actual RA and DEC might be from the estimated values (in degrees)

Tweak
-----
By default we try to compute a SIP polynomial distortion correction with order 2. 
You can disable this by changing the order to 0, or change the polynomial order by setting
``tweak_order``.

CRPIX Center
------------
By default the reference point (CRPIX) of the WCS we compute can be anywhere in your image, 
but often it's convenient to force it to be the center of the image. This can be set by choosing
``crpix_center=True``.

License and Sharing
-------------------
The Astrometry.net [website](http://nova.astrometry.net/) allows users to upload images
as well as catalogs to be used in generating an astrometric solution, so the site gives
users the choice of licenses for their publically available images. Since the astroquery
astrometry.net api is only uploading a source catalog the choice of ``public_visibility``,
``allow_commercial_use``, and ``allow_modifications`` are not really relevant and can be left
to their defaults, although their settings are described below

Visibility
^^^^^^^^^^
By default all catalogs uploaded are publically available. To change this use the setting
``publicly_visible='n'``.

License
^^^^^^^
There are two parameters that describe setting a license:
    ``allow_commercial_use``: 
        Chooses whether or not an image uploaded to astrometry.net is licensed
        for commercial use. This can either be set to ``y``, ``n``, or ``d``, which 
        uses the default license associated with the api key.
    ``allow_modifications``:
        Whether or not images uploaded to astrometry.net are allowed to be modified by
        other users. This can either be set to ``y``, ``n``, or ``d``, which 
        uses the default license associated with the api key.
"""

# Licensed under a 3-clause BSD style license - see LICENSE.rst
#from __future__ import print_function

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
import time

# export all the public classes and methods
__all__ = ['AstrometryNet', 'AstrometryNetClass']

# declare global variables and constants if any

# Now begin your main class
# should be decorated with the async_to_sync imported previously

astrometry_net_url = 'http://nova.astrometry.net/'
apiurl = 'http://nova.astrometry.net/api/'

@async_to_sync
class AstrometryNetClass(BaseQuery):

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
        from urllib import urlencode
        from urllib2 import urlopen, Request
        from email.mime.multipart import MIMEMultipart
        from email.mime.base import MIMEBase
        from email.mime.application  import MIMEApplication
        from email.encoders import encode_noop
        import simplejson
        
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
            raise Exception("Login error, exiting")
        session_string = result["session"]
        
        # Upload the text file to request a WCS solution
        upload_url = apiurl + "upload"
        upload_args = { 
                        'publicly_visible': 'y', 
                        'allow_commercial_use': 'd', 
                        'allow_modifications': 'd', 
                        'scale_units': 'deg',
                        'scale_type': 'ul', 
                        'scale_lower': 0.1,
                        'scale_upper': 180,
                        'parity': 2,
                        'session': session_string
                        }
        upload_args.update(settings)
        upload_json = simplejson.dumps(upload_args)
        
        # Format the list in the appropriate format
        # Currently this is just using the code from astrometry.net's client.py
        # Ideally this could probably be re-written and improved
        #src_list = '\n'.join(['{0:.3f}\t{1:.3f}'.format(row[x_colname], row[y_colname]) 
        #    for row in catalog])
        
        temp_file = 'temp.cat'
        f = open(temp_file, 'w')
        #f.write(src_list)
        for source in catalog:
            f.write('{0:.3f}\t{1:.3f}\n'.format(source[x_colname], source[y_colname]))
        f.close()
        
        f = open(temp_file, 'rb')
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
        from urllib2 import urlopen, Request
        import simplejson
        
        request = Request(url=url, headers=headers, data=data)
        f = urlopen(request)
        txt = f.read()
        result = simplejson.loads(txt)
        stat = result.get('status')
        if stat == 'error':
            raise Exception("Upload error, exiting.")
        subid = result["subid"]
        
        return subid
    
    def get_submit_status(self, subid, timeout=30):
        """
        Get the status of a submitted source list. This polls astrometry.net every 5
        seconds until it either receives a job status or timeout is reached.
        
        Parameters
        ----------
        subid: str
            - subid returned by ``submit`` function
        timeout: int (optional):
            - Maximum time to wait for a submission status
        
        Result
        ------
        jobs: str
            jobid's astrometry.net has assigned to the submitted list
        """
        import math
        from urllib2 import urlopen, Request
        import simplejson
        
        # Check submission status
        subcheck_url = apiurl + "submissions/" + str(subid)

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
                    raise Exception()
                still_processing = False
            except:
                log.info("Submission doesn't exist yet, sleeping for 5s.")
                time.sleep(5)
                n_failed_attempts += 1
        if n_failed_attempts > max_attempts:
            raise Exception(
                "The submitted job {0} has apparently timed out, exiting.".format(subid))
        
        return result['jobs']
    
    def get_wcs_file(self, subid, jobs, timeout=90, timeout_error=True):
        """
        Get a wcs file from astrometry.net given a jobid
        
        Parameters
        ----------
        subid: str
            - subid returned by ``submit`` function
        jobs: list
            List of jobs returned by `get_submit_status`
        timeout: int (optional):
            Maximum time to wait for an anstrometric solution before timing out
        timeout_error: bool (optional)
            Whether or not to raise an Exception if the request times out (default is False)
        Returns
        -------
        header: `astropy.io.fits.Header`
            Header returned by astrometry.net
        """
        import math
        from urllib2 import urlopen, Request
        import simplejson
        
        # Attempt to load wcs from astrometry.net
        n_jobs = len(jobs)
        still_processing = True
        n_failed_attempts = 0
        n_failed_jobs = 0
        max_attempts = math.ceil(timeout/5)
        while still_processing and n_failed_attempts < max_attempts and n_failed_jobs < n_jobs:
            time.sleep(5)
            for job_id in jobs:
                jobcheck_url = apiurl + "jobs/" + str(job_id)
                request = Request(url=jobcheck_url)
                f = urlopen(request)
                txt = f.read()
                result = simplejson.loads(txt)
                log.info("Checking astrometry.net for job ID {0}".format(job_id))
                if result["status"] == "failure":
                    status_url = astrometry_net_url+"status/"+str(subid)
                    log.error('job {0} failed. See {1} for details'.format(job_id, status_url))
                    n_failed_jobs += 1
                    jobs.remove(job_id)
                if result["status"] == "success":
                    log.info('Job {0} executed successfully'.format(job_id))
                    solved_job_id = job_id
                    still_processing = False
            n_failed_attempts += 1

        if still_processing == True:
            log.error("Astrometry.net took too long to process job {0}, so we're exiting. " +
                "Try checking astrometry.net again later".format(jobs))
            if timeout_error:
                raise Exception("Astrometry.net took too long to process")

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
        wcs_hdu = fits.open(wcs_image)
        wcs_header = wcs_hdu[0].header.copy()
        wcs_hdu.close()
        
        return wcs_header        

    def solve(self, sources, settings, x_colname="x", y_colname="y", fwhm_colname=None, 
            flag_colname=None, flux_colname=None, fwhm_std_cut=2, timeout=30):
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
        import astropy.io.fits as pyfits
        import simplejson
        from numpy import median, std
        from urllib2 import urlopen, Request
        
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
        catalog.sort(flux_colname)
        catalog.reverse()
        # Only choose the top 50 sources
        if len(catalog)>50:
            catalog = catalog[:50]
        
        # Create a list of coordinates in a format that astrometry.net recognizes
        upload_kwargs = self.build_request(catalog, settings, x_colname, y_colname)
        # Submit the job
        log.info('Submitting source list to astrometry.net')
        subid = self.submit(**upload_kwargs)
        log.info('Submission ID={0}'.format(subid))
        time.sleep(15)
        # Check that submission was successful
        jobs = self.get_submit_status(subid, 30)
        log.info('jobs generated by submission: {0}'.format(jobs))
        # Get the header
        wcs_fits = self.get_wcs_file(subid, jobs, timeout, True)
        
        return result

# the default tool for users to interact with is an instance of the Class
AstrometryNet = AstrometryNetClass()

# once your class is done, tests should be written
# See ./tests for examples on this

# Next you should write the docs in astroquery/docs/module_name
# using Sphinx.
