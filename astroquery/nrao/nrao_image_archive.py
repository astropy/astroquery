"""
NRAO Image Archive Query Tool
-----------------------------------

:Author: Adam Ginsburg (adam.g.ginsburg@gmail.com)
"""
import urllib2
import urllib
import os
import gzip
import StringIO
from astropy.io import fits
from astroquery.utils import progressbar
from astropy import coordinates as coord
import re
import astropy.utils.data as aud

imfits_re = re.compile("http://[^\"]*\\.imfits")
uvfits_re = re.compile("http://[^\"]*\\.uvfits")
config_re = re.compile("([ABCD]/[ABCD])&nbsp;configuration")

request_URL = "https://webtest.aoc.nrao.edu/cgi-bin/lsjouwer/archive-pos.pl"

__all__ = ['get_nrao_image']


valid_bands = ["","L","C","X","U","K","Q"]

band_freqs = {
    "L":	(1,2),
    "S":	(2,4),
    "C":	(4,8),
    "X":	(8,12),
    "U":	(12,18),
    "K":	(18,26.5),
    "Ka":	(26.5,40),
    "Q":	(30,50),
    "V":	(50,75),
    "E":	(60,90),
    "W":	(75,110),
    "F":	(90,140),
    "D":	(110,170),
    }


def get_nrao_image(lon, lat, system='galactic', epoch='J2000', size=1.0,
        max_rms=1e4, band="", verbose=True, savename=None, save=True,
        overwrite=False, directory='./', get_uvfits=False):
    """
    Search for and download

    Parameters
    ----------
    lon : float
    lat : float
        Right ascension and declination or glon/glat
    system : ['celestial','galactic']
        System of lon/lat.  Can be any valid coordinate system supported by the
        astropy.coordinates package
    epoch : string
        Epoch of the coordinate system (e.g., B1950, J2000)
    savename : None or string
        filename to save fits file as.  If None, will become G###.###p###.###_(survey).fits
    size : float
        Size of search radius (arcminutes)
    max_rms : float
        Maximum allowable noise level in the image (mJy)
    verbose : bool
        Print out extra error messages?
    save : bool
        Save FITS file?
    overwrite : bool
        Overwrite if file already exists?
    directory : string
        Directory to store file in.  Defaults to './'.  
    get_uvfits : bool
        Get the UVfits files instead of the IMfits files?

    Examples
    --------
    >>> fitsfile = get_nrao_image(49.489,-0.37)
    """

    if band not in valid_bands:
        raise ValueError("Invalid band.  Valid bands are: %s" % valid_bands)

    if system == 'celestial':
        radec = coord.FK5Coordinates(lon, lat, unit=('deg', 'deg'))
        galactic = radec.galactic
    elif system == 'galactic':
        galactic = coord.GalacticCoordinates(lon, lat, unit=('deg', 'deg'))
        radec = galactic.fk5
    
    radecstr = radec.ra.format(sep=' ') + ' ' + radec.dec.format(sep=' ') 
    glon, glat = galactic.lonangle.degrees, galactic.latangle.degrees

    # Construct request
    request = {}
    request["nvas_pos"] = radecstr
    request["nvas_rad"] = size
    request["nvas_rms"] = max_rms
    request["nvas_scl"] = size
    request["submit"] = "Search"
    request["nvas_bnd"] = band

    # create the request header data
    request = urllib.urlencode(request)
    # load the URL as text
    U = urllib.urlopen(request_URL, request)
    # read results with progressbar
    results = progressbar.chunk_read(U, report_hook=progressbar.chunk_report)

    if get_uvfits:
        links = uvfits_re.findall(results)
    else:
        links = imfits_re.findall(results)
    configurations = config_re.findall(results)
            
    if len(links) == 0:
        if verbose:
            print "No matches found at ra,dec = %s." % (radecstr)
        return []

    if verbose > 1:
        print "Configurations: "
        print "\n".join(["%40s: %20s" % (L,C) for L,C in zip(links,configurations)])

    if save and not os.path.exists(directory):
        os.mkdir(directory)
    if save:
        opener = urllib2.build_opener()

    if verbose:
        print "Found %i imfits files" % len(links)

    images = []

    for link,config in zip(links,configurations):

        # Get the file
        U = opener.open(link)
        with aud.get_readable_fileobj(U) as f:
            results = f.read()
        S = StringIO.StringIO(results)
        try: 
            fitsfile = fits.open(S,ignore_missing_end=True)
        except IOError:
            S.seek(0)
            G = gzip.GzipFile(fileobj=S)
            fitsfile = fits.open(G,ignore_missing_end=True)

        # Get Multiframe ID from the header
        images.append(fitsfile)

        if save:
            h0 = fitsfile[0].header
            freq_ghz = h0['CRVAL3'] / 1e9
            for bn, bandlimits in band_freqs.iteritems():
                if freq_ghz < bandlimits[1] and freq_ghz > bandlimits[0]:
                    bandname = bn
            obj = str(h0['OBJECT']).strip()
            program = h0['OBSERVER'].strip()
            h0['CONFIG'] = config

            if savename is None:
                if get_uvfits:
                    filename = "VLA_%s_G%07.3f%+08.3f_%s_%s.uvfits" % (bandname,glon,glat,obj,program)
                else:
                    filename = "VLA_%s_G%07.3f%+08.3f_%s_%s.fits" % (bandname,glon,glat,obj,program)
            else:
                filename = savename

            # Set final directory and file names
            final_file = directory + '/' + filename

            if verbose:
                print "Saving file %s" % final_file

            fitsfile.writeto(final_file, clobber=overwrite)

    return images


