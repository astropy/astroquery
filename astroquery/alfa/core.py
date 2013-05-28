# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""

core.py

Author: Jordan Mirocha
Affiliation: University of Colorado at Boulder
Created on: Fri May  3 09:45:13 2013

Description: 

"""

import urllib
import numpy as np
import numpy.ma as ma
from astropy.io import fits
from astropy import coordinates as coord

ascii_prefix = "http://arecibo.tc.cornell.edu/hiarchive/alfalfa/spectraASCII"
fits_prefix = "http://arecibo.tc.cornell.edu/hiarchive/alfalfa/spectraFITS"
propert_path = "http://egg.astro.cornell.edu/alfalfa/data/a40files/a40.datafile1.csv"

placeholder = -999999

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
    
    if 'ALFALFACAT' in globals():
        return ALFALFACAT
    
    f = urllib.urlopen(propert_path)

    # Read header
    cols = f.readline().rstrip('\n').split(',')

    catalog = {}
    for col in cols:
        catalog[col] = []

    # Parse result
    for line in f:
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
        
    # Mask out blank elements    
    for col in cols:
        mask = np.zeros(len(catalog[col]))
        mask[np.array(catalog[col]) == placeholder] = 1
        catalog[col] = ma.array(catalog[col], mask=mask)    
        
    # Make this globally available so we don't have to re-download it 
    # again in this session 
    global ALFALFACAT
    ALFALFACAT = catalog
    
    return catalog
    
def get_spectrum(agc=None, ra=None, dec=None, unit=None, counterpart=False, 
    ascii=False):
    """
    Download spectrum from ALFALFA catalogue.
    
    Parameters
    ----------
    agc : int
        Identification number for object in ALFALFA catalog.
    ra : float
        Right ascension (degrees).
    dec : float
        Declination (degrees).
    ascii : bool
        Download spectrum from remote server in ASCII or FITS format?
    counterpart : bool
        Do supplied ra and dec refer to HI source or optical counterpart?
        
    Notes
    -----
    If AGC number is not supplied, will download entire ALFALFA catalog and
    do a cross-ID with supplied RA and DEC.     
        
    Returns
    -------
    If ascii == False, returns Spectrum instance, which contains FITS hdulist
    and properties for x and y axes. If ascii == True, returns a tuple of 4
    arrays: velocity [km/s], frequency [MHz], flux density [mJy], and baseline 
    fit [mJy], respectively.
    
    See Also
    --------
    get_catalog : method that downloads ALFALFA catalog
    
    """
        
    if agc is not None: 
        agc = str(agc).zfill(6)
    else:
        if ra is None and dec is None:
            raise ValueError('Must supply ra and dec if agc=None!')
        
        try:
            cat = ALFALFACAT
        except NameError:
            cat = get_catalog()    
            
        if not isinstance(ra, coord.angles.RA):
            ra = coord.RA(ra, unit=unit)
        if not isinstance(ra, coord.angles.Dec):    
            dec = coord.Dec(dec, unit=unit)    
        
        # Use RA and DEC to find appropriate AGC
        if counterpart:
            ra_ref = cat['RAdeg_OC']
            dec_ref = cat['DECdeg_OC']
        else:
            ra_ref = cat['RAdeg_HI']
            dec_ref = cat['Decdeg_HI']
        
        dra = np.abs(ra_ref - ra.degrees) \
            * np.cos(dec.degrees * np.pi / 180.)
        ddec = np.abs(dec_ref - dec.degrees)
        dr = np.sqrt(dra**2 + ddec**2)
        
        agc = cat['AGCNr'][np.argmin(dr)]
                
        print 'Found HI source AGC #%i %g arcseconds from supplied position.' \
            % (agc, dr.min() * 3600.)        
            
    if ascii:
        link = "%s/A%s.txt" % (ascii_prefix, agc)
        f = urllib.urlopen(link)
    
        vel = []
        freq = []
        flux = []
        baseline = [] 
        for i, line in enumerate(f):
            if i <= 30: continue
            
            data = line.split()
            
            vel.append(float(data[0]))
            freq.append(float(data[1]))
            flux.append(float(data[2]))
            baseline.append(float(data[3]))
        
        f.close()
            
        return np.array(vel), np.array(freq), np.array(flux), np.array(baseline)
      
    link = "%s/A%s.fits" % (fits_prefix, agc)    
    hdulist = fits.open(urllib.urlopen(link).url, ignore_missing_end=True)
    return Spectrum(hdulist)    
    
def match_object(ra, dec, ra_ref, dec_ref):
    """
    Assumes everything is in degrees.  Supply ra and dec of single object being considered, as well as reference
    arrays of RA and DEC for some sample.  Returns index of match in reference arrays.
    """    
            
    
    if min(dr) < maxsep: 
        return np.argmin(dr)                      
    else:
        return placeholder        
    

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
        
  