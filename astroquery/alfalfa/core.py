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

from astropy import units as u
from astropy.table import Table
from ..query import BaseQuery
from ..utils.class_or_instance import class_or_instance

__all__ = ['ALFALFA']

ALFALFACAT = None

class ALFALFA(BaseQuery):
    
    ASCII_PREFIX = "http://arecibo.tc.cornell.edu/hiarchive/alfalfa/spectraASCII"
    FITS_PREFIX = "http://arecibo.tc.cornell.edu/hiarchive/alfalfa/spectraFITS"
    CATALOG_PREFIX = "http://egg.astro.cornell.edu/alfalfa/data/a40files/a40.datafile1.csv"

    PLACEHOLDER = -999999
    
    def __init__(self, *args):
        pass
    
    @class_or_instance
    def get_catalog(self):
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
        
        result = requests.get(ALFALFA.CATALOG_PREFIX)
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
                    catalog[col].append(ALFALFA.PLACEHOLDER)
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
            mask[np.array(catalog[col]) == ALFALFA.PLACEHOLDER] = 1
            catalog[col] = ma.array(catalog[col], mask=mask)    
            
        # Make this globally available so we don't have to re-download it 
        # again in this session 
        self._make_cat_global(catalog)
        
        return catalog
    
    @class_or_instance    
    def _make_cat_global(self, catalog):
        global ALFALFACAT
        ALFALFACAT = catalog    
        
    @class_or_instance    
    def query_region(self, coordinates, radius=3. * u.arcmin,
        optical_counterpart=False):
        """
        Perform object cross-ID in ALFALFA.
        
        Search for objects near position (ra, dec) within some radius.
        
        Parameters
        ----------
        coordinates : str or `astropy.coordinates` object
            The target around which to search. It may be specified as a string
            in which case it is resolved using online services or as the appropriate
            `astropy.coordinates` object. ICRS coordinates may also be entered as strings
            as specified in the `astropy.coordinates` module.
        radius : str or `astropy.units.Quantity` object, optional
            The string must be parsable by `astropy.coordinates.Angle`. The appropriate
            `Quantity` object from `astropy.units` may also be used. Defaults to 3 arcmin.
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
        
        ra = coordinates.ra.degrees
        dec = coordinates.dec.degrees
        dr = radius.to('degree')
        
        cat = self.get_catalog()
        
        # Use RA and DEC to find appropriate AGC
        if optical_counterpart:
            ra_ref = cat['RAdeg_OC']
            dec_ref = cat['DECdeg_OC']
        else:
            ra_ref = cat['RAdeg_HI']
            dec_ref = cat['Decdeg_HI']
        
        dra = np.abs(ra_ref - ra) \
            * np.cos(dec * np.pi / 180.)
        ddec = np.abs(dec_ref - dec)
        sep = np.sqrt(dra**2 + ddec**2)
        
        i_minsep = np.argmin(sep)
        minsep = sep[i_minsep]
        
        # Matched object within our search radius?
        if minsep < dr:
            return cat['AGCNr'][i_minsep]
        else:
            return None
       
    @class_or_instance   
    def get_spectrum(self, agc):
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
        PyFITS HDUList. Spectrum is in hdulist[0].data[0][2]
        
        See Also
        --------
        get_catalog : method that downloads ALFALFA catalog
        crossID : find object in catalog closest to supplied position (use this
            to determine AGC number first)
        
        """
            
        agc = str(agc).zfill(6)      
                
        link = "%s/A%s.fits" % (ALFALFA.FITS_PREFIX, agc)    
        hdulist = fits.open(link, ignore_missing_end=True)
        return hdulist
    
