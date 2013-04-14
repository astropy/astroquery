"""
UKIDSS Image and Catalog Query Tool
-----------------------------------

:Author: Thomas Robitalle (thomas.robitaille@gmail.com)
:Author: Adam Ginsburg (adam.g.ginsburg@gmail.com)
"""
import cookielib
import urllib2
import urllib
try:
    import htmllib
except ImportError:
    # python 3 compatibility
    import HTMLParser as htmllib
import formatter
import gzip
import os
from astropy.io import fits
from math import cos, radians
import multiprocessing as mp
import time
import StringIO
from astroquery.utils import progressbar
import astropy.utils.data as aud

__all__ = ['UKIDSSQuery','clean_catalog','ukidss_programs_short','ukidss_programs_long']

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
url_getcatalog = "http://surveys.roe.ac.uk:8080/wsa/WSASQL"

frame_types = ['stack', 'normal', 'interleave', 'deep%stack', 'confidence',
    'difference', 'leavstack', 'all']

ukidss_programs_short = {'LAS': 101,
                         'GPS': 102,
                         'GCS': 103,
                         'DXS': 104,
                         'UDS': 105,}

ukidss_programs_long = {'Large Area Survey': 101,
                        'Galactic Plane Survey': 102,
                        'Galactic Clusters Survey': 103,
                        'Deep Extragalactic Survey': 104,
                        'Ultra Deep Survey': 105}

class UKIDSSQuery():
    """
    The UKIDSSQuery class.  Must instantiate this class in order to make any
    queries.  Allows registered users to login, but defaults to using the
    public UKIDSS data sets.
    """

    def __init__(self, database='UKIDSSDR7PLUS', programmeID='all',
            directory='./'):
        self.opener = urllib2.build_opener()
        self.database = database
        self.programmeID = programmeID # 102 = GPS
        self.filters = {'all': 'all', 'J': '3', 'H': '4', 'K': '5', 'Y': 2,
                'Z': 1, 'H2': 6, 'Br': 7}
        self.directory = directory
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
        self._login_page = self.opener.open(url_login, urllib.urlencode(credentials))

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
        filter : ['all','J','H','K','H2','Z','Y','Br']
            The color filter to download.
        frametype : ['stack','normal','interleave','deep%stack','confidence','difference','leavstack','all']
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
        >>> R = UKIDSSQuery()
        >>> fitsfile = R.get_image_gal(10.5,0.0)
        
        # get UWISH2 data (as per http://astro.kent.ac.uk/uwish2/main.html)
        >>> R.database='U09B8v20120403'
        >>> R.login(username='U09B8',password='uwish2',community='nonSurvey')
        >>> R.get_image_gal(49.489,-0.27,frametype='leavstack',size=20,filter='H2')
        """

        # Check for validity of requested frame_type
        if frametype not in frame_types:
            raise ValueError("Invalide frame type.  Valid frame types are: %s"
                    % frame_types)
        if filter not in self.filters:
            raise ValueError("Invalide filter.  Valid filters are: %s"
                    % self.filters.keys())

        # Construct request
        self.request = {}
        self.request['database']    = self.database
        self.request['programmeID'] = verify_programme_id(self.programmeID,querytype='image')
        self.request['ra']          = glon
        self.request['dec']         = glat
        self.request['sys']         = 'G'
        self.request['filterID']    = self.filters[filter]
        self.request['xsize']       = size
        self.request['ysize']       = size
        self.request['obsType']     = 'object'
        self.request['frameType']   = frametype
        self.request['mfid']        = ''
        self.query_str = url_getimage +"?"+ urllib.urlencode(self.request)

        if directory is None:
            directory = self.directory

        # Retrieve page
        page = self.opener.open(url_getimage, urllib.urlencode(self.request))
        with aud.get_readable_fileobj(page) as f:
            results = f.read()

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

            # Get the file
            U = self.opener.open(link.replace("getImage", "getFImage"))
            with aud.get_readable_fileobj(U, cache=True) as f:
                results = f.read()
            S = StringIO.StringIO(results)

            try: 
                # try to open as a fits file
                fitsfile = fits.open(S,ignore_missing_end=True)
            except IOError:
                # if that fails, try to open as a gzip'd fits file
                # have to rewind to the start
                S.seek(0)
                G = gzip.GzipFile(fileobj=S)
                fitsfile = fits.open(G,ignore_missing_end=True)

            # Get Multiframe ID from the header
            images.append(fitsfile)

            if save:
                h0 = fitsfile[0].header
                filt = str(h0['FILTER']).strip()
                obj = filt + "_" + str(h0['OBJECT']).strip().replace(":", ".")

                if savename is None:
                    filename = "UKIDSS_%s_G%07.3f%+08.3f_%s.fits" % (filt,glon,glat,obj)
                else:
                    filename = savename

                # Set final directory and file names
                final_file = directory + '/' + filename

                if verbose:
                    print "Saving file %s" % final_file

                fitsfile.writeto(final_file, clobber=overwrite)

        return images

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
        frametype : ['stack', 'normal', 'interleave', 'deep%stack',
            'confidence', 'difference', 'leavstack', 'all']
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
        >>> R = UKIDSSQuery()
        >>> fitsfile = R.get_image_gal(10.5,0.0)
        """

        # Check for validity of requested frame_type
        if frametype not in frame_types:
            raise ValueError("Invalide frame type.  Valid frame types are: %s"
                    % frame_types)
        if filter not in self.filters:
            raise ValueError("Invalide filter.  Valid filters are: %s"
                    % self.filters.keys())

        if directory is None:
            directory = self.directory

        # Construct self.request
        self.request = {}

        self.request['database']    = self.database
        self.request['programmeID'] = verify_programme_id(self.programmeID,querytype='image')
        self.request['userSelect'] = 'default'

        self.request['obsType']     = 'object'
        self.request['frameType']   = frametype
        self.request['filterID']    = self.filters[filter]

        self.request['minRA']       = str(round(ra - radius / cos(radians(dec)),2))
        self.request['maxRA']       = str(round(ra + radius / cos(radians(dec)),2))
        self.request['formatRA']    = 'degrees'

        self.request['minDec']       = str(dec - radius)
        self.request['maxDec']       = str(dec + radius)
        self.request['formatDec']    = 'degrees'

        self.request['startDay'] = 0
        self.request['startMonth'] = 0
        self.request['startYear'] = 0

        self.request['endDay'] = 0
        self.request['endMonth'] = 0
        self.request['endYear'] = 0

        self.request['dep'] = 0

        self.request['mfid'] = ''
        self.request['lmfid'] = ''
        self.request['fsid'] = ''

        self.request['rows'] = 1000
        self.query_str = url_getimages +"?"+ urllib.urlencode(self.request)

        # Retrieve page
        page = self.opener.open(url_getimages, urllib.urlencode(self.request))
        with aud.get_readable_fileobj(page) as f:
            results = f.read()

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
                        target=progressbar.retrieve, args=(link, temp_file, self.opener))
                else:
                    p = mp.Process(
                        target=urllib.urlretrieve, args=(link, temp_file))
                p.start()

                while True:
                    if len(mp.active_children()) < n_concurrent:
                        break
                    time.sleep(0.1)

    def get_region(self, lon, lat, directory=None, radius=1, save=False,
            verbose=True, savename=None, overwrite=False, sys='J'):
        """
        Get all sources in the catalog within some radius

        Parameters
        ----------
        lon : float
        lat : float
            latitude and longitude at the center
        sys : str
            System of lat/lon.  'J' for J2000, 'G' for Galactic
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
        List of fits.primaryHDU instances containing FITS tables

        Example
        -------
        >>> R = UKIDSSQuery(programmeID='GPS')
        >>> data = R.get_catalog_gal(10.625,-0.38,radius=0.1)
        >>> bintable = data[0][1]
        """
        #database:UKIDSSDR8PLUS
        #programmeID:103 # DR8


        # Construct request
        self.request = {}
        self.request['database'] = self.database
        self.request['programmeID'] = verify_programme_id(self.programmeID,querytype='catalog')
        self.request['from'] = 'source'
        self.request['formaction'] = 'region'
        self.request['ra'] = lon
        self.request['dec'] = lat
        self.request['sys'] = sys
        self.request['radius'] = radius
        self.request['xSize'] = ''
        self.request['ySize'] = ''
        self.request['boxAlignment'] = 'RADec'
        self.request['emailAddress'] = ''
        self.request['format'] = 'FITS'
        self.request['compress'] = 'GZIP'
        self.request['rows'] = 1
        self.request['select'] = '*'
        self.request['where'] = ''
        self.query_str = url_getcatalog +"?"+ urllib.urlencode(self.request)

        if directory is None:
            directory = self.directory

        # Retrieve page
        page = self.opener.open(url_getcatalog, urllib.urlencode(self.request))
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
                        savename = ("UKIDSS_catalog_G%07.3f%+08.3f_r%03i.fits.gz" %
                                    (lon, lat, radius))
                    filename = directory + "/" + savename
                
                U = self.opener.open(link)
                if verbose:
                    print "Downloading catalog %s" % link
                    results = progressbar.chunk_read(U, report_hook=progressbar.chunk_report)
                else:
                    results = U.read()
                S = StringIO.StringIO(results)
                try: 
                    fitsfile = fits.open(S,ignore_missing_end=True)
                except IOError:
                    S.seek(0)
                    G = gzip.GzipFile(fileobj=S)
                    fitsfile = fits.open(G,ignore_missing_end=True)


                data.append(fitsfile)
                if save: 
                    fitsfile.writeto(filename.rstrip(".gz"), clobber=overwrite)

        return data


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
        List of fits.primaryHDU instances containing FITS tables

        Example
        -------
        >>> R = UKIDSSQuery()
        >>> data = R.get_catalog_gal(10.625,-0.38,radius=0.1)
        >>> bintable = data[0][1]
        """

        # Construct request
        self.request = {}
        self.request['database'] = self.database
        self.request['programmeID'] = verify_programme_id(self.programmeID,querytype='catalog')
        self.request['from'] = 'source'
        self.request['formaction'] = 'region'
        self.request['ra'] = glon
        self.request['dec'] = glat
        self.request['sys'] = 'G'
        self.request['radius'] = radius
        self.request['xSize'] = ''
        self.request['ySize'] = ''
        self.request['boxAlignment'] = 'RADec'
        self.request['emailAddress'] = ''
        self.request['format'] = 'FITS'
        self.request['compress'] = 'GZIP'
        self.request['rows'] = 1
        self.request['select'] = '*'
        self.request['where'] = ''
        self.query_str = url_getcatalog +"?"+ urllib.urlencode(self.request)

        if directory is None:
            directory = self.directory

        # Retrieve page
        page = self.opener.open(url_getcatalog, urllib.urlencode(self.request))
        with aud.get_readable_fileobj(page) as f:
            results = f.read()

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
                with aud.get_readable_fileobj(U, cache=True) as f:
                    results = f.read()

                S = StringIO.StringIO(results)
                try: 
                    fitsfile = fits.open(S,ignore_missing_end=True)
                except IOError:
                    S.seek(0)
                    G = gzip.GzipFile(fileobj=S)
                    fitsfile = fits.open(G,ignore_missing_end=True)


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

def verify_programme_id(pid, querytype='catalog'):
    """
    Verify the programme ID is valid for the query being executed

    Parameters
    ----------
    pid : int or str
        The programme ID, either an integer (i.e., the # that will get passed
        to the URL) or a string using the three-letter acronym for the
        programme or its long name

    Returns
    -------
    pid : int
        Returns the integer version of the programme ID

    Raises
    ------
    ValueError if the pid is 'all' and the query type is a catalog.  You can query
    all surveys for images, but not all catalogs.
    """
    if pid == 'all' and querytype == 'catalog':
        raise ValueError("Cannot query all catalogs at once. Valid catalogs are: {0}.  Change programmeID to one of these.".format(
            ",".join(ukidss_programs_short.keys())))
    elif pid in ukidss_programs_long:
        return ukidss_programs_long[pid]
    elif pid in ukidss_programs_short:
        return ukidss_programs_short[pid]
    elif querytype != 'image':
        raise ValueError("ProgrammeID {0} not recognized".format(pid))
