"""
UKIDSS Image and Catalog Query Tool
-----------------------------------

:Author: Thomas Robitalle (thomas.robitaille@gmail.com)
:Author: Adam Ginsburg (adam.g.ginsburg@gmail.com)
"""
import cookielib
import urllib2
import urllib
import htmllib
import formatter
import gzip
import os
import sys
import astropy.io.fits as pyfits
from math import cos, radians
import multiprocessing as mp
import time
import tempfile
import numpy as np
import shutil
import StringIO
from astrodata.utils import progressbar

__all__ = ['UKIDSSQuery','clean_catalog']

class LinksExtractor(htmllib.HTMLParser):  # derive new HTML parser

    def __init__(self, formatter):        # class constructor
        htmllib.HTMLParser.__init__(self, formatter)  # base class constructor
        self.links = []        # create an empty list for storing hyperlinks

    def start_a(self, attrs):  # override handler of <A ...>...</A> tags
        # process the attributes
        if len(attrs) > 0:
            for attr in attrs:
                if attr[0] == "href":         # ignore all non HREF attributes
                    self.links.append(
                        attr[1])  # save the link info in the list

    def get_links(self):
        return self.links

url_login      = "http://surveys.roe.ac.uk:8080/wsa/DBLogin"
url_getimage   = "http://surveys.roe.ac.uk:8080/wsa/GetImage"
url_getimages  = "http://surveys.roe.ac.uk:8080/wsa/ImageList"
url_getcatalog = "http://surveys.roe.ac.uk:8080/wsa/WSASQL?"

frame_types = ['stack', 'normal', 'interleave', 'deep%stack', 'confidence',
    'difference', 'all']


class UKIDSSQuery():
    """
    The Query class.  Must instantiate this class in order to make any
    queries.  Allows registered users to login, but defaults to using the
    public UKIDSS data sets.
    """

    def __init__(self):
        self.opener = urllib2.build_opener()
        self.database = 'UKIDSSDR7PLUS'
        self.programmeID = 102  # GPS
        self.filters = {'all': 'all', 'J': '3', 'H': '4', 'K': '5'}
        self.directory = './'
        self.cj = None

    def login(self, username, password, community):
        """
        Login to non-public data as a known user

        Parameters
        ----------
        username : string
        password : string
        community : string
        """

        # Construct cookie holder, URL openenr, and retrieve login page
        self.cj = cookielib.CookieJar()
        self.opener = urllib2.build_opener(
            urllib2.HTTPCookieProcessor(self.cj))
        credentials = {'user': username, 'passwd': password,
            'community': ' ', 'community2': community}
        page = self.opener.open(url_login, urllib.urlencode(credentials))

    def logged_in(self):
        """
        Determine whether currently logged in
        """
        if self.cj is None:
            return False
        for c in self.cj:
            if c.is_expired():
                return False
        return True

    def get_image_gal(self, glon, glat, filter='all', frametype='stack',
            directory=None, size=1.0, verbose=True, save=True, savename=None,
            overwrite=False):
        """
        Get an image at a specified glon/glat.  Size can be specified

        Parameters
        ----------
        glon : float
        glat : float
            Galactic latitude and longitude at the center
        filter : ['all','J','H','K']
            The color filter to download.
        frametype : ['stack','normal','interleave','deep%stack','confidence','difference','all']
            The type of image
        directory : None or string
            Directory to download files into.  Defaults to self.directory
        size : float
            Size of cutout (symmetric) in arcminutes
        verbose : bool
            Print out extra error messages?
        save : bool
            Save FITS file?
        savename : string or None
            The file name to save the catalog to.  If unspecified, will save as
            UKIDSS_[band]_G###.###-###.###_[obj].fits.gz, where the #'s
            indicate galactic lon/lat and [band] and [obj] refer to the filter
            and the object name
        overwrite : bool
            Overwrite if file already exists?

        Examples
        --------
        >>> R = Query()
        >>> fitsfile = R.get_image_gal(10.5,0.0)
        """

        # Check for validity of requested frame_type
        if frametype not in frame_types:
            raise ValueError("Invalide frame type.  Valid frame types are: %s"
                    % frame_types)
        if filter not in self.filters:
            raise ValueError("Invalide filter.  Valid filters are: %s"
                    % self.filters.keys())

        # Construct request
        request = {}
        request['database']    = self.database
        request['programmeID'] = self.programmeID
        request['ra']          = glon
        request['dec']         = glat
        request['sys']         = 'G'
        request['filterID']    = self.filters[filter]
        request['xsize']       = size
        request['ysize']       = size
        request['obsType']     = 'object'
        request['frameType']   = frametype
        request['mfid']        = ''

        if directory is None:
            directory = self.directory

        # Retrieve page
        page = self.opener.open(url_getimage, urllib.urlencode(request))
        if verbose:
            print "Loading page..."
            results = progressbar.chunk_read(page, report_hook=progressbar.chunk_report)
        else:
            results = page.read()

        # Parse results for links
        format = formatter.NullFormatter()
        htmlparser = LinksExtractor(format)
        htmlparser.feed(results)
        htmlparser.close()
        links = htmlparser.get_links()

        if verbose:
            print "Found %i targets" % (len(links))

        # Loop through links and retrieve FITS images
        images = []
        for link in links:

            if not os.path.exists(directory):
                os.mkdir(directory)

            # Get image filename
            basename = os.path.basename(
                link.split("&")[0]).replace('.fit', '.fits.gz')
            temp_file = tempfile.NamedTemporaryFile()

            # Get the file
            U = self.opener.open(link.replace("getImage", "getFImage"))
            if verbose:
                print "Downloading image from %s" % link
                results = progressbar.chunk_read(U, report_hook=progressbar.chunk_report)
            else:
                results = U.read()
            S = StringIO.StringIO(results)
            fitsfile = pyfits.open(S,ignore_missing_end=True)

            # Get Multiframe ID from the header
            images.append(fitsfile)

            if save:
                h0 = fitsfile[0].header
                filt = str(h0['FILTER']).strip()
                obj = filt + "_" + str(h0['OBJECT']).strip().replace(":", ".")

                if savename is None:
                    savename = "UKIDSS_%s_G%07.3f%+08.3f_%s.fits" % (filt,glon,glat,obj)

                # Set final directory and file names
                final_file = directory + '/' + savename

                if not overwrite:
                    # Check that the final file doesn't already exist
                    if os.path.exists(final_file):
                        raise IOError("File exists : " + final_file)

                shutil.copy(temp_file.name, final_file)

        return fitsfile

    def get_images_radius(self, ra, dec, radius, filter='all',
            frametype='stack', directory=None, n_concurrent=1, save=True,
            verbose=True, overwrite=False):
        """
        Get all images within some radius of a specified RA/Dec

        Parameters
        ----------
        ra  : float
        dec : float
            ra/dec center to search around
        radius : float
            Radius of circle to search within
        filter : ['all','J','H','K']
            The color filter to download.
        frametype : ['stack','normal','interleave','deep%stack','confidence','difference','all']
            The type of image
        directory : None or string
            Directory to download files into.  Defaults to self.directory
        verbose : bool
            Print out extra error messages?
        save : bool
            Save FITS file?
        overwrite : bool
            Overwrite if file already exists?
        n_concurrent : int
            Number of concurrent download threads to start

        Examples
        --------
        >>> R = Query()
        >>> fitsfile = R.get_image_gal(10.5,0.0)
        """

        # Check for validity of requested frame_type
        if frametype not in frame_types:
            raise ValueError("Invalide frame type.  Valid frame types are: %s"
                    % frame_types)
        if filter not in self.filters:
            raise ValueError("Invalide filter.  Valid filters are: %s"
                    % self.filters.keys())

        # Construct request
        request = {}

        request['database']    = self.database
        request['programmeID'] = self.programmeID
        request['userSelect'] = 'default'

        request['obsType']     = 'object'
        request['frameType']   = frametype
        request['filterID']    = self.filters[filter]

        request['minRA']       = str(round(ra - radius / cos(radians(dec)),2))
        request['maxRA']       = str(round(ra + radius / cos(radians(dec)),2))
        request['formatRA']    = 'degrees'

        request['minDec']       = str(dec - radius)
        request['maxDec']       = str(dec + radius)
        request['formatDec']    = 'degrees'

        request['startDay'] = 0
        request['startMonth'] = 0
        request['startYear'] = 0

        request['endDay'] = 0
        request['endMonth'] = 0
        request['endYear'] = 0

        request['dep'] = 0

        request['mfid'] = ''
        request['lmfid'] = ''
        request['fsid'] = ''

        request['rows'] = 1000

        # Retrieve page
        page = self.opener.open(url_getimages, urllib.urlencode(request))
        if verbose:
            print "Loading page..."
            results = progressbar.chunk_read(page, report_hook=progressbar.chunk_report)
        else:
            results = page.read()

        # Parse results for links
        format = formatter.NullFormatter()
        htmlparser = LinksExtractor(format)
        htmlparser.feed(results)
        htmlparser.close()
        links = htmlparser.get_links()

        # Loop through links and retrieve FITS images
        for link in links:

            if not os.path.exists(directory):
                os.mkdir(directory)
            if not os.path.exists(directory + '/' + frametype):
                os.mkdir(directory + '/' + frametype)

            if 'fits_download' in link and '_cat.fits' not in link and '_two.fit' not in link:

                # Get image filename
                basename = os.path.basename(link.split("&")[0])
                temp_file = directory + '/' + frametype + '/' + basename

                if verbose:
                    print "Downloading %s..." % basename

                p = mp.Process(
                    target=urllib.urlretrieve, args=(link, temp_file))
                p.start()

                while True:
                    if len(mp.active_children()) < n_concurrent:
                        break
                    time.sleep(0.1)

    def get_catalog_gal(self, glon, glat, directory=None, radius=1, save=False,
            verbose=True, savename=None, overwrite=False):
        """
        Get all sources in the catalog within some radius

        Parameters
        ----------
        glon : float
        glat : float
            Galactic latitude and longitude at the center
        directory : None or string
            Directory to download files into.  Defaults to self.directory
        radius : float
            Radius in which to search for catalog entries in arcminutes
        savename : string or None
            The file name to save the catalog to.  If unspecified, will save as
            UKIDSS_catalog_G###.###-###.###_r###.fits.gz, where the #'s indicate
            galactic lon/lat and radius

        Returns
        -------
        List of pyfits.primaryHDU instances containing FITS tables

        Example
        -------
        >>> R = Query()
        >>> data = R.get_catalog_gal(10.625,-0.38,radius=0.1)
        >>> bintable = data[0][1]
        """

        # Construct request
        request = {}
        request['database'] = self.database
        request['programmeID'] = self.programmeID
        request['from'] = 'source'
        request['formaction'] = 'region'
        request['ra'] = glon
        request['dec'] = glat
        request['sys'] = 'G'
        request['radius'] = radius
        request['xSize'] = ''
        request['ySize'] = ''
        request['boxAlignment'] = 'RADec'
        request['emailAddress'] = ''
        request['format'] = 'FITS'
        request['compress'] = 'GZIP'
        request['rows'] = 1
        request['select'] = '*'
        request['where'] = ''

        if directory is None:
            directory = self.directory

        # Retrieve page
        page = self.opener.open(url_getcatalog + urllib.urlencode(request))
        if verbose:
            print "Loading page..."
            results = progressbar.chunk_read(page, report_hook=progressbar.chunk_report)
        else:
            results = page.read()

        # Parse results for links
        format = formatter.NullFormatter()           # create default formatter
        htmlparser = LinksExtractor(format)        # create new parser object
        htmlparser.feed(results)
        htmlparser.close()
        links = list(set(htmlparser.get_links()))

        # Loop through links and retrieve FITS tables
        c = 0
        data = []
        for link in links:
            if not "8080" in link:
                c = c + 1

                if not os.path.exists(directory):
                    os.mkdir(directory)

                if save:
                    if savename is None:
                        savename = "UKIDSS_catalog_G%07.3f%+08.3f_r%03i.fits.gz" % (glon,glat,radius)
                    filename = directory + "/" + savename
                
                U = self.opener.open(link)
                if verbose:
                    print "Downloading catalog %s" % link
                    results = progressbar.chunk_read(U, report_hook=progressbar.chunk_report)
                else:
                    results = U.read()
                S = StringIO.StringIO(results)
                try: 
                    fitsfile = pyfits.open(S,ignore_missing_end=True)
                except IOError:
                    S.seek(0)
                    G = gzip.GzipFile(fileobj=S)
                    fitsfile = pyfits.open(G,ignore_missing_end=True)


                data.append(fitsfile)
                if save: 
                    fitsfile.writeto(filename.rstrip(".gz"), clobber=overwrite)

        return data


def clean_catalog(ukidss_catalog, clean_band='K_1', badclass=-9999, maxerrbits=41, minerrbits=0,
        maxpperrbits=60):
    """
    Attempt to remove 'bad' entries in a catalog

    Parameters
    ----------
    ukidss_catalog : astropy.io.fits.hdu.table.BinTableHDU
        A FITS binary table instance from the UKIDSS survey
    clean_band : ['K_1','K_2','J','H']
        The band to use for bad photometry flagging
    badclass : int
        Class to exclude
    minerrbits : int
    maxerrbits : int
        Inside this range is the accepted # of error bits
    maxpperrbits : int
        Exclude this type of error bit

    Examples
    --------
    """

    band = clean_band
    mask = ((ukidss_catalog.data[band + 'CLASS'] != badclass)
            * (ukidss_catalog.data[band + 'ERRBITS'] <= maxerrbits)
            * (ukidss_catalog.data[band + 'ERRBITS'] >= minerrbits)
            * ((ukidss_catalog.data['PRIORSEC'] == ukidss_catalog.data['FRAMESETID'])
                + (ukidss_catalog.data['PRIORSEC'] == 0))
            * (ukidss_catalog.data[band + 'PPERRBITS'] < maxpperrbits)
        )

    return ukidss_catalog.data[mask]
