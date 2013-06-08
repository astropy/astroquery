# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""

core.py

Author: Jordan Mirocha
Affiliation: University of Colorado at Boulder
Created on: Sun Apr 14 19:18:43 2013

Description: Access Sloan Digital Sky Survey database online. Higher level wrappers provided to download
spectra and images using wget.

"""

import numpy as np
import astropy.wcs as wcs
import math
from astropy.io import fits
from astropy import coordinates as coord
import requests
import io

__all__ = ['crossID','get_image','get_spectral_template','get_spectrum']

# Default photometric and spectroscopic quantities to retrieve.
photoobj_defs = ['ra', 'dec', 'objid', 'run', 'rerun', 'camcol', 'field']
specobj_defs = ['z', 'plate', 'mjd', 'fiberID', 'specobjid', 'specClass']

# Cross-correlation templates from DR-5
spec_templates = \
    {'star_O': 0, 'star_OB': 1, 'star_B': 2, 'star_A': [3,4],
     'star_FA': 5, 'star_F': [6,7], 'star_G': [8,9],
     'star_K': 10, 'star_M1': 11, 'star_M3': 12, 'star_M5': 13,
     'star_M8': 14, 'star_L1': 15, 'star_wd': [16,20,21],
     'star_carbon': [17,18,19], 'star_Ksubdwarf': 22,
     'galaxy_early': 23, 'galaxy': [24,25,26], 'galaxy_late': 27,
     'galaxy_lrg': 28, 'qso': 29, 'qso_bal': [30,31], 
     'qso_bright': 32 
     }

# Some website prefixes we need
spectro1d_prefix = 'http://das.sdss.org/spectro/1d_26'
images_prefix = 'http://das.sdss.org/www/cgi-bin/drC'
template_prefix = 'http://www.sdss.org/dr5/algorithms/spectemplates/spDR2'

sdss_arcsec_per_pixel = 0.396

def crossID(ra, dec, unit=None, dr=2., fields=None):
    """
    Perform object cross-ID in SDSS using SQL.
    
    Search for objects near position (ra, dec) within some radius.
    
    Parameters
    ----------
    ra : float, int, str, tuple
        An object that represents a right ascension angle.
    dec : float, int, str, tuple
        An object that represents a declination angle.
    unit : `~astropy.units.UnitBase`, str
        The unit of the value specified for the angle
    dr : int, float
        Radius of region to perform object cross-ID (arcseconds).
    fields : list, optional
        SDSS PhotoObj or SpecObj quantities to return. If None, defaults
        to quantities required to find corresponding spectra and images
        of matched objects (e.g. plate, fiberID, mjd, etc.).
             
    See documentation for astropy.coordinates.angles for more information 
    about ('ra', 'dec', 'unit') parameters.
    
    Examples
    --------
    >>> xid = sdss.crossID(ra='0h8m05.63s', dec='14d50m23.3s')
    >>> for match in xid:
    >>>     print match['ra'], match['dec'], match['objid']

    Returns
    -------
    List of all objects found within search radius. Each element of list is 
    a dictionary containing information about each matched object.
    
    """
    
    if not isinstance(ra, coord.angles.RA):
        ra = coord.RA(ra, unit=unit)
    if not isinstance(ra, coord.angles.Dec):    
        dec = coord.Dec(dec, unit=unit)
    
    if fields is None:
        fields = photoobj_defs + specobj_defs
        
    # Convert arcseconds to degrees
    dr /= 3600.    
            
    Nfields = len(fields)    
        
    q_select = 'SELECT '
    for field in fields:
        if field in photoobj_defs:
            q_select += 'p.%s,' % field
        if field in specobj_defs:
            q_select += 's.%s,' % field
    q_select = q_select.rstrip(',')
    q_select += ' '
    
    q_from = 'FROM PhotoObjAll AS p '
    q_join = 'JOIN SpecObjAll s ON p.objID = s.bestObjID '
    q_where = 'WHERE (p.ra between %g and %g) and (p.dec between %g and %g)' \
        % (ra.degrees-dr, ra.degrees+dr, dec.degrees-dr, dec.degrees+dr)
    
    sql = "%s%s%s%s" % (q_select, q_from, q_join, q_where)
    r = requests.get('http://cas.sdss.org/public/en/tools/search/x_sql.asp', params={'cmd': sql, 'format': 'csv'})
    
    return np.atleast_1d(np.genfromtxt(io.BytesIO(r.content), names=True, dtype=None, delimiter=','))
    
def get_spectrum(crossID=None, plate=None, fiberID=None, mjd=None):  
    """
    Download spectrum from SDSS. 
    
    Parameters
    ----------
    crossID : dict
        Dictionary that must contain the plate, fiberID, and mjd of desired
        spectrum. These parameters can be passed separately as well. All are 
        required. Most convenient to pass the result of function
        astroquery.sdss.crossID.
    
    Examples
    --------
    xid = sdss.crossID(ra='0h8m05.63s', dec='14d50m23.3s')
    sp = sdss.get_spectrum(crossID=xid[0])
    
    import pylab as pl
    pl.plot(sp.xarr, sp.data)   # plot the spectrum
    
    Returns
    -------
    Instance of Spectrum class, whose main attribute is a PyFITS HDUList.
    Also contains properties to return x-axis, data, and error arrays, as 
    well as the FITS header in dictionary form.
    """
    
    if crossID is not None:
        plate = crossID['plate']
        fiberID = crossID['fiberID']
        mjd = crossID['mjd']
                    
    plate = str(plate).zfill(4)
    fiber = str(fiberID).zfill(3)
    mjd = str(mjd)        
    link = '%s/%s/1d/spSpec-%s-%s-%s.fit' % (spectro1d_prefix, plate, mjd, 
        plate, fiber)
              
    hdulist = fits.open(link, ignore_missing_end=True)

    return Spectrum(hdulist)
            
def get_image(crossID=None, run=None, rerun=None, camcol=None, 
    field=None, band='g'):
    """
    Download an image from SDSS. 
    
    Querying SDSS for images will return the entire plate. For subsequent 
    analyses of individual objects
    
    Parameters
    ----------
    crossID : dict 
        Dictionary that must contain the run, rerun, camcol, and field for
        desired image. These parameters can be passed separately as well. All 
        are required. Most convenient to pass the result of function
        astroquery.sdss.crossID.
    band : str, list 
        Could be individual band, or list of bands. Options: u, g, r, i, or z          
    
    Examples
    --------
    xid = sdss.crossID(ra='0h8m05.63s', dec='14d50m23.3s')
    img = sdss.get_image(crossID=xid[0], band='g')
    
    plate = img.data # data for entire plate
    
    # 60x60 arcsecond cutout around (ra, dec)
    cutout = img.cutout(ra=xid[0]['ra'], dec=xid[0]['dec'], dr=60.)
    
    Returns
    -------
    Instance of Image class, whose main attribute is a PyFITS HDUList. Also 
    contains properties to return data and error arrays, as well as the FITS 
    header in dictionary form.
    """   
    
    if crossID is not None:
        run = crossID['run']
        rerun = crossID['rerun']
        camcol = crossID['camcol']
        field = crossID['field']

    # Read in and format some information we need
    field = str(field).zfill(4)
    run_zfill = str(run).zfill(6)
                                
    # Download and read in image data
    link = '%s?RUN=%i&RERUN=%i&CAMCOL=%i&FIELD=%s&FILTER=%s' % (images_prefix, 
        run, rerun, camcol, field, band)            

    hdulist = fits.open(link, ignore_missing_end=True)
     
    return Image(hdulist)
    
def get_spectral_template(kind='qso'):
    """
    Download spectral templates from SDSS DR-2, which are located here: 
    
        http://www.sdss.org/dr5/algorithms/spectemplates/
    
    There 32 spectral templates available from DR-2, from stellar spectra,
    to galaxies, to quasars. To see the available templates, do:
    
        from astroquery import sdss
        print sdss.spec_templates.keys()
    
    Parameters
    ----------
    kind : str, list
        Which spectral template to download? Options are stored in the 
        dictionary astroquery.sdss.spec_templates.
    
    Examples
    --------
    qso = sdss.get_spectral_template(kind='qso')
    Astar = sdss.get_spectral_template(kind='star_A')
    Fstar = sdss.get_spectral_template(kind='star_F')

    Returns
    -------
    List of Spectrum class instances, whose main attribute is a PyFITS HDUList.
    The reason for returning a list is that there are multiple templates 
    available for some spectral types.
    """   
    
    if kind == 'all':
        indices = list(np.arange(33))
    else:    
        indices = spec_templates[kind]
        if type(indices) is not list:
            indices = [indices]
        
    spectra = []
    for index in indices:
        name = str(index).zfill(3)
        link = '%s-%s.fit' % (template_prefix, name)        
        hdulist = fits.open(link, ignore_missing_end=True)
        spectra.append(Spectrum(hdulist)) 
        del hdulist
                
    return spectra
    
class Spectrum(object):
    """ TODO: document """
    def __init__(self, hdulist):
        self.hdulist = hdulist
        
    @property
    def hdr(self):
        if not hasattr(self, '_hdr'):
            self._hdr = {}  
            for key in self.header.keys(): 
                self._hdr[key] = self.header.get(key)
        return self._hdr
    
    @property
    def header(self):
        return self.hdulist[0].header    
        
    @property
    def xarr(self):
        if not hasattr(self, '_xarr'):
            i = np.arange(len(self.hdulist[0].data[0]))
            self._xarr = 10**(self.header['COEFF0']+i*self.header['COEFF1'])
        return self._xarr
        
    @property
    def data(self):
        if not hasattr(self, '_data'):
            self._data = self.hdulist[0].data[0]
        return self._data
        
    @property
    def err(self):
        if not hasattr(self, '_err'):
            self._err = self.hdulist[0].data[2]
        return self._err     
    
class Image(object):
    """ TODO: document """
    def __init__(self, hdulist):
        self.hdulist = hdulist
        self.w = wcs.WCS(self.header)
        
    @property
    def hdr(self):
        if not hasattr(self, '_hdr'):
            self._hdr = {}  
            for key in self.hdulist[0].header.keys(): 
                self._hdr[key] = self.hdulist[0].header[key]
        return self._hdr
    
    @property
    def header(self):
        return self.hdulist[0].header    
        
    @property
    def data(self):
        if not hasattr(self, '_data'):
            self._data = self.hdulist[0].data
        return self._data
        
    def cutout(self, ra, dec, dr):
        """ Return cutout of width dr (arcseconds) around point (ra, dec)."""
        x, y = self.w.wcs_world2pix(np.array([[ra,dec]]), 1)[0]
                        
        left = max(math.floor(x - dr / sdss_arcsec_per_pixel / 2.), 0)
        right = min(math.ceil(x + dr / sdss_arcsec_per_pixel / 2.), 
            self.hdr['NAXIS1'])
        bottom = max(math.floor(y - dr / sdss_arcsec_per_pixel / 2.), 0)
        top = min(math.ceil(y + dr / sdss_arcsec_per_pixel / 2.), 
            self.hdr['NAXIS2'])
            
        return self.data[bottom:top,left:right]    
    
        
