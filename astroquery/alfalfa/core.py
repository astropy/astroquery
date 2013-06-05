# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""

core.py

Author: Jordan Mirocha
Affiliation: University of Colorado at Boulder
Created on: Fri May  3 09:45:13 2013

Description: 

"""

from __future__ import print_function
import requests
import numpy as np
import numpy.ma as ma
from astropy.io import fits
from astropy import coordinates as coord

ascii_prefix = "http://arecibo.tc.cornell.edu/hiarchive/alfalfa/spectraASCII"
fits_prefix = "http://arecibo.tc.cornell.edu/hiarchive/alfalfa/spectraFITS"
propert_path = "http://egg.astro.cornell.edu/alfalfa/data/a40files/a40.datafile1.csv"

placeholder = -999999
ALFALFACAT = None

__all__ = ['get_catalog','crossID','get_spectrum','Spectrum']

def get_catalog():
    """
    Download catalog of ALFALFA source properties.
    
    Notes
    -----
    This catalog has ~15,000 entries, so after it's downloaded, it is made
    global to save some time later.
    
    Returns
    -------
    Dictionary of results, each element is a masked array.
    
    """
    
    if ALFALFACAT is not None:
        return ALFALFACAT
    else:
        pass
    
    result = requests.get(propert_path)
    iterable_lines = result.iter_lines()

    # Read header
    cols = [col.decode() for col in next(iterable_lines).rstrip(b'\n').split(b',')]

    catalog = {}
    for col in cols:
        catalog[col] = []

    # Parse result
    for line in iterable_lines:
        line = line.decode()
        l = line.rstrip('\n').split(',')
        for i, col in enumerate(cols):
            item = l[i].strip()
            if item == '\"\"':
                catalog[col].append(placeholder)
            elif item.isdigit():
                catalog[col].append(int(item))
            elif item.replace('.', '').isdigit():
                catalog[col].append(float(item))
            else:
                catalog[col].append(item)

    result.close()
        
    # Mask out blank elements    
    for col in cols:
        mask = np.zeros(len(catalog[col]))
        mask[np.array(catalog[col]) == placeholder] = 1
        catalog[col] = ma.array(catalog[col], mask=mask)    
        
    # Make this globally available so we don't have to re-download it 
    # again in this session 
    _make_cat_global(catalog)
    
    return catalog
    
def _make_cat_global(catalog):
    global ALFALFACAT
    ALFALFACAT = catalog    
    
def crossID(ra, dec, unit=None, dr=60., optical_counterpart=False):
    """
    Perform object cross-ID in ALFALFA.
    
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
    optical_counterpart : bool
        Search for position match using radio positions or position of
        any optical counterpart identified by ALFALFA team? Keep in mind that
        the ALFA beam size is about 3x3 arcminutes.
             
    See documentation for astropy.coordinates.angles for more information 
    about ('ra', 'dec', 'unit') parameters.
    
    Examples
    --------
    >>> agc = alfalfa.crossID(ra='0h8m05.63s', dec='14d50m23.3s', dr)
    >>> for match in xid:
    >>>     print match['ra'], match['dec'], match['objid']

    Returns
    -------
    AGC number for object nearest supplied position.
    
    """
    
    if not isinstance(ra, coord.angles.RA):
        ra = coord.RA(ra, unit=unit)
    if not isinstance(ra, coord.angles.Dec):    
        dec = coord.Dec(dec, unit=unit)    
    
    cat = get_catalog()
    
    # Use RA and DEC to find appropriate AGC
    if optical_counterpart:
        ra_ref = cat['RAdeg_OC']
        dec_ref = cat['DECdeg_OC']
    else:
        ra_ref = cat['RAdeg_HI']
        dec_ref = cat['Decdeg_HI']
    
    dra = np.abs(ra_ref - ra.degrees) \
        * np.cos(dec.degrees * np.pi / 180.)
    ddec = np.abs(dec_ref - dec.degrees)
    sep = np.sqrt(dra**2 + ddec**2)
    
    i_minsep = np.argmin(sep)
    minsep = sep[i_minsep]
    
    # Matched object within our search radius?
    if (minsep * 3600.) < dr:
        return cat['AGCNr'][i_minsep]
    else:
        return None
   
def get_spectrum(agc, ascii=False):
    """
    Download spectrum from ALFALFA catalogue.
    
    Parameters
    ----------
    agc : int
        Identification number for object in ALFALFA catalog.
    ascii : bool
        Download spectrum from remote server in ASCII or FITS format?
        
    Returns
    -------
    If ascii == False, returns Spectrum instance, which contains FITS hdulist
    and properties for x and y axes. If ascii == True, returns a tuple of 4
    arrays: velocity [km/s], frequency [MHz], flux density [mJy], and baseline 
    fit [mJy], respectively.
    
    See Also
    --------
    get_catalog : method that downloads ALFALFA catalog
    crossID : find object in catalog closest to supplied position (use this
        to determine AGC number first)
    
    """
        
    agc = str(agc).zfill(6)      
            
    if ascii:
        link = "%s/A%s.txt" % (ascii_prefix, agc)
        result = requests.get(link)
    
        vel = []
        freq = []
        flux = []
        baseline = [] 
        for i, line in enumerate(result.iter_line()):
            if i <= 30: 
                continue
            
            data = line.split()
            
            vel.append(float(data[0]))
            freq.append(float(data[1]))
            flux.append(float(data[2]))
            baseline.append(float(data[3]))
        
        result.close()
            
        return np.array(vel), np.array(freq), np.array(flux), np.array(baseline)
      
    link = "%s/A%s.fits" % (fits_prefix, agc)    
    hdulist = fits.open(link, ignore_missing_end=True)
    return Spectrum(hdulist)    
    
class Spectrum:
    def __init__(self, hdulist):
        self.hdulist = hdulist
        
    @property
    def hdr(self):
        if not hasattr(self, '_hdr'):
            for item in self.hdulist:
                if item.name == 'PRIMARY':
                    continue
                break    
            
            self._hdr = {}  
            for key in item.header.keys(): 
                self._hdr[key] = self.header.get(key)
                            
        return self._hdr
    
    @property
    def header(self):
        return self.hdulist[0].header    
        
    @property
    def freq(self):
        """ Return xarr in units of MHz. """
        if not hasattr(self, '_freq'):
            for item in self.hdulist:
                if item.name == 'PRIMARY':
                    continue
                break    
                    
            for i, col in enumerate(item.columns):
                if col.name == 'FREQ':
                    self._freq = item.data[0][i]
                    break
            
        return self._freq
    
    @property
    def varr(self):
        """ Return xarr in units of helio-centric velocity (km/s). """
        if not hasattr(self, '_varr'):
            for item in self.hdulist:
                if item.name == 'PRIMARY':
                    continue
                break    
                    
            for i, col in enumerate(item.columns):
                if col.name == 'VHELIO':
                    self._varr = item.data[0][i]
                    break
            
        return self._varr
        
    @property
    def data(self):
        if not hasattr(self, '_data'):
            for item in self.hdulist:
                if item.name == 'PRIMARY':
                    continue
                break    
                    
            for i, col in enumerate(item.columns):
                if col.name == 'FLUXDENS':
                    self._data = item.data[0][i]
                    break
                    
        return self._data
        
  
