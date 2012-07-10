"""
MAGPIS Image and Catalog Query Tool
-----------------------------------

:Author: Adam Ginsburg (adam.g.ginsburg@gmail.com)
"""
import cookielib
import urllib2
import urllib
import htmllib
import formatter
import os
import sys
import astropy.io.fits as pyfits
from math import cos, radians
import multiprocessing as mp
import time
import tempfile
import StringIO
from astroquery.utils import progressbar

url_gpscutout  = "http://third.ucllnl.org/cgi-bin/gpscutout"

__all__ = ['get_magpis_image_gal']

surveys = ["gps6epoch3",
    "gps6epoch4",
    "gps20",
    "gps20new",
    "gps90",
    "gpsmsx",
    "gpsmsx2",
    "gpsglimpse36",
    "gpsglimpse45",
    "gpsglimpse58",
    "gpsglimpse80",
    "mipsgal",
    "bolocam"]


def get_magpis_image_gal(glon, glat, survey='bolocam', size=1.0, 
        verbose=False, savename=None, save=True,
        overwrite=False, directory='./'):
    """
    Get an image at a specified glon/glat.  Size can be specified
    WARNING: MAGPIS has a maxmimum image size of about 2048x2048

    Parameters
    ----------
    glon : float
    glat : float
        Galactic latitude and longitude at the center
    survey : string
        Which MAGPIS survey do you want to cut out?
    frametype : ['stack','normal','interleave','deep%stack','confidence','difference','all']
        The type of image
    savename : None or string
        filename to save fits file as.  If None, will become G###.###p###.###_(survey).fits
    size : float
        Size of cutout (symmetric) in arcminutes
    verbose : bool
        Print out extra error messages?
    save : bool
        Save FITS file?
    overwrite : bool
        Overwrite if file already exists?
    directory : string
        Directory to store file in.  Defaults to './'.  

    Examples
    --------
    >>> fitsfile = get_magpis_image_gal(10.5,0.0)
    """

    if survey not in surveys:
        raise ValueError("Invalide survey.  Valid surveys are: %s" % surveys)

    # Construct request
    request = {}
    request["Survey"] = survey 
    # NOTE: RA is passed as a 2-part string, DEC is not used.  Whoops!
    request["RA"] = "%s %s" % (glon,glat)
    # request["Dec"] = 
    request["Equinox"] = "Galactic"
    request["ImageSize"] = size
    request["ImageType"] = "FITS"

    # these options are not used
    # optional request["MaxInt"] = 10
    # optional request["Epochs"] = 
    # optional request["Fieldname"] = 

    # create the request header data
    request = urllib.urlencode(request)
    # load the URL as text
    U = urllib.urlopen(url_gpscutout, request)
    # read results with progressbar
    results = progressbar.chunk_read(U, report_hook=progressbar.chunk_report)
    # turn the text into a StringIO object for FITS reading
    S = StringIO.StringIO(results)
    fitsfile = pyfits.open(S)

    if save:
        if savename is None:
            savename = "G%08.4f%+09.4f_%s.fits" % (glon,glat,survey)
        if directory[-1] != '/':
            directory += '/'
        fitsfile.writeto(directory+savename, clobber=overwrite)

    return fitsfile

