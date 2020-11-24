# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
Author: Jordan Mirocha
Affiliation: University of Colorado at Boulder
Created on: Fri May  3 09:45:13 2013
"""


import requests
import numpy as np
import numpy.ma as ma
from astropy import units as u
from astropy import coordinates as coord
from ..utils import commons, prepend_docstr_nosections
from ..query import BaseQuery

__all__ = ['Alfalfa', 'AlfalfaClass']

# have to skip because it tries to use the internet, which is not allowed
__doctest_skip__ = ['AlfalfaClass.query_region', 'Alfalfa.query_region']


class AlfalfaClass(BaseQuery):

    FITS_PREFIX = "http://arecibo.tc.cornell.edu/hiarchive/alfalfa/spectraFITS"
    CATALOG_PREFIX = "http://egg.astro.cornell.edu/alfalfa/data/a40files/a40.datafile1.csv"

    PLACEHOLDER = -999999

    def get_catalog(self):
        """
        Download catalog of ALFALFA source properties.

        Notes
        -----
        This catalog has ~15,000 entries, so after it's downloaded, it is made
        global to save some time later.

        Returns
        -------
        result : Dictionary of results, each element is a masked array.
        """

        if hasattr(self, 'ALFALFACAT'):
            return self.ALFALFACAT

        result = requests.get(self.CATALOG_PREFIX)
        iterable_lines = result.iter_lines()

        # Read header
        cols = [col for col in next(iterable_lines).rstrip('\n').split(',')]

        catalog = {}
        for col in cols:
            catalog[col] = []

        # Parse result
        for line in iterable_lines:
            # skip blank lines or trailing newlines
            if line == "":
                continue
            col_values = line.rstrip('\n').split(',')
            for i, col in enumerate(cols):
                item = col_values[i].strip()
                if item == '\"\"':
                    catalog[col].append(self.PLACEHOLDER)
                elif item.isdigit():
                    catalog[col].append(int(item))
                elif item.replace('.', '').isdigit():
                    catalog[col].append(float(item))
                else:
                    catalog[col].append(item)

        result.close()

        # Mask out blank elements
        for col in cols:
            mask = np.zeros(len(catalog[col]), dtype='bool')
            # need to turn list -> array for boolean comparison
            colArr = np.array(catalog[col])
            # placeholder must share Type with the array
            ph = np.array(self.PLACEHOLDER, dtype=colArr.dtype)
            mask[colArr == ph] = True
            catalog[col] = ma.array(catalog[col], mask=mask)

        # Make this globally available so we don't have to re-download it
        # again in this session
        self.ALFALFACAT = catalog

        return catalog

    def query_region(self, coordinates, radius=3. * u.arcmin,
                     optical_counterpart=False):
        """
        Perform object cross-ID in ALFALFA.

        Search for objects near position (ra, dec) within some radius.

        Parameters
        ----------
        coordinates : str or `astropy.coordinates` object
            The target around which to search. It may be specified as a
            string in which case it is resolved using online services or as
            the appropriate `astropy.coordinates` object. ICRS coordinates
            may also be entered as strings as specified in the
            `astropy.coordinates` module.
        radius : str or `~astropy.units.Quantity` object, optional
            The string must be parsable by `astropy.coordinates.Angle`. The
            appropriate `~astropy.units.Quantity` object from
            `astropy.units` may also be used. Defaults to 3 arcmin.
        optical_counterpart : bool
            Search for position match using radio positions or position of
            any optical counterpart identified by ALFALFA team? Keep in mind
            that the ALFA beam size is about 3x3 arcminutes.

        See documentation for astropy.coordinates.angles for more information
        about ('ra', 'dec', 'unit') parameters.

        Examples
        --------
        >>> from astroquery.alfalfa import Alfalfa
        >>> from astropy import coordinates as coords
        >>> C = coords.SkyCoord('0h8m05.63s +14d50m23.3s')
        >>> agc = Alfalfa.query_region(C,'3 arcmin')

        Returns
        -------
        result : AGC number for object nearest supplied position.

        """

        coordinates = commons.parse_coordinates(coordinates)

        ra = coordinates.ra.degree
        dec = coordinates.dec.degree
        dr = coord.Angle(radius).deg

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
        sep = np.sqrt(dra ** 2 + ddec ** 2)

        i_minsep = np.argmin(sep)
        minsep = sep[i_minsep]

        # Matched object within our search radius?
        if minsep < dr:
            return cat['AGCNr'][i_minsep]
        else:
            return None

    def get_spectrum_async(self, agc, show_progress=True):
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
        result : A file context manager

        See Also
        --------
        get_catalog : method that downloads ALFALFA catalog
        query_region : find object in catalog closest to supplied
            position (use this to determine AGC number first)

        """

        agc = str(agc).zfill(6)

        link = "%s/A%s.fits" % (self.FITS_PREFIX, agc)
        result = commons.FileContainer(link, show_progress=show_progress)
        return result

    @prepend_docstr_nosections(get_spectrum_async.__doc__)
    def get_spectrum(self, agc, show_progress=True):
        """
        Returns
        -------
        spectrum : `~astropy.io.fits.HDUList`
            Spectrum is in ``hdulist[0].data[0][2]``

        """

        result = self.get_spectrum_async(agc, show_progress=show_progress)
        hdulist = result.get_fits()
        return hdulist


Alfalfa = AlfalfaClass()
