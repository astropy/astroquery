"""

sdss.py

Author: Jordan Mirocha
Affiliation: University of Colorado at Boulder
Created on: Sun Apr 14 19:18:43 2013

Description: Access Sloan Digital Sky Survey database online via Tamas 
Budavari's SQL tool (included). Higher level wrappers provided to download
spectra and images using wget.

"""

import numpy as np
import astropy.wcs as wcs
import os, re, sqlcl, math
from astropy.io import fits
from astropy import coordinates as coord

# Default photometric and spectroscopic quantities to retrieve.
photoobj_defs = ['ra', 'dec', 'objid', 'run', 'rerun', 'camcol', 'field']
specobj_defs = ['z', 'plate', 'mjd', 'fiberID', 'specobjid', 'specClass']

spectro1d_prefix = 'http://das.sdss.org/spectro/1d_26'
images_prefix = 'http://das.sdss.org/www/cgi-bin/drC'

sdss_arcsec_per_pixel = 0.396

def crossID(ra, dec, unit=None, dr=2., fields=None):
    """
    Perform object cross-ID in SDSS using SQL.
    
    Search for objects near position (ra, dec) within some radius.
    
    Parameters
    ----------
    ra = An object that represents a right ascension angle.
    dec = An object that represents a declination angle.
    unit = The unit of the value specified for the angle
    dr = Radius of region to perform object cross-ID (arcseconds).
    fields = SDSS PhotoObj or SpecObj quantities to return. If None, defaults
             to quantities required to find corresponding spectra and images
             of matched objects (e.g. plate, fiberID, mjd, etc.).
             
    See documentation for astropy.coordinates.angles for more information 
    about ('ra', 'dec', 'unit') parameters.
    
    Examples
    --------
    xid = sdss.crossID(ra='0h8m05.63s', dec='14d50m23.3s')
    
    for match in xid:
        print match['ra'], match['dec'], match['objid']

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
    
    q = sqlcl.query("%s%s%s%s" % (q_select, q_from, q_join, q_where))
    
    results = []
    cols = q.readline()
    while True:
        line = q.readline().replace('\n', '').split(',')
        
        if len(line) == 1:
            break
        
        tmp = {}
        for i, val in enumerate(line):
            
            field = fields[i]
            
            if val.isdigit(): 
                tmp[field] = int(val)
            else:
                try: 
                    tmp[field] = float(val)
                except ValueError: 
                    tmp[field] = str(val)
                    
        results.append(tmp)            

    return results
    
def get_spectrum(crossID=None, plate=None, fiberID=None, mjd=None):  
    """
    Download spectrum from SDSS. 
    
    Parameters
    ----------
    crossID = dictionary that must contain the plate, fiberID, and mjd. These
              parameters can be passed separately as well. All are required.
    
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
    web = '%s/%s/1d/spSpec-%s-%s-%s.fit' % (spectro1d_prefix, plate, mjd, 
        plate, fiber)
    
    os.system('wget -x -nH -nv -q %s' % web)
    
    hdulist = fits.open('spectro/1d_26/%s/1d/spSpec-%s-%s-%s.fit' % (plate, 
        mjd, plate, fiber), ignore_missing_end=True)
            
    os.system('rm -rf spectro')
    
    return Spectrum(hdulist)
            
def get_image(crossID=None, run=None, rerun=None, camcol=None, 
    field=None, band='g'):
    """
    Download an image from SDSS. 
    
    Querying SDSS for images will return the entire plate. For subsequent 
    analyses of individual objects
    
    Parameters
    ----------
    crossID = dictionary that must contain the run, rerun, camcol, and field. 
              These parameters can be passed separately as well. All are 
              required.
    band = u, g, r, i, or z          
    
    Examples
    --------
    xid = sdss.crossID(ra='0h8m05.63s', dec='14d50m23.3s')
    img = sdss.get_image(crossID=xid[0], band='g')
    
    plate = img.data # data for entire plate
    
    # 60x60 arcsecond cutout around (ra, dec)
    cutout = img.cutout(ra=xid[0]['ra'], dec=xid[0]['dec'], dr=60.)
    
    Returns
    -------
    Instance of Image class, whose main attribute is a PyFITS HDUList.
    Also contains properties to return data and error arrays, as 
    well as the FITS header in dictionary form.
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
    path_to_img = 'www/cgi-bin/drC?RUN=%i&RERUN=%i&CAMCOL=%i&FIELD=%s&FILTER=%s' % (run, 
        rerun, camcol, field, band)
                
    os.system('wget -x -nH -nv -q \'%s\'' % link)
    
    hdulist = fits.open(path_to_img, ignore_missing_end=True) 
 
    # Erase download directory tree    
    os.system('rm -rf www')    
    os.system('rm -rf imaging')    
    
    return Image(hdulist)
    
class Spectrum:
    def __init__(self, hdulist):
        self.hdulist = hdulist
        
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
    
class Image:
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
    
        