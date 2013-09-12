# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""

Author: Jordan Mirocha
Affiliation: University of Colorado at Boulder
Created on: Sun Apr 14 19:18:43 2013

Description: Access Sloan Digital Sky Survey database online.

"""

import numpy as np
import copy
from astropy.io import fits
from astropy import units as u
from astropy.table import Table
import requests
import io
from ..query import BaseQuery
from . import SDSS_SERVER, SDSS_MAXQUERY
from ..utils.class_or_instance import class_or_instance
from ..utils import commons, async_to_sync
from ..utils.docstr_chompers import prepend_docstr_noreturns
import astropy.utils.data as aud

__all__ = ['SDSS']

# Default photometric and spectroscopic quantities to retrieve.
photoobj_defs = ['ra', 'dec', 'objid', 'run', 'rerun', 'camcol', 'field']
specobj_defs = ['z', 'plate', 'mjd', 'fiberID', 'specobjid', 'specClass']

# Cross-correlation templates from DR-5
spec_templates = {'star_O': 0, 'star_OB': 1, 'star_B': 2, 'star_A': [3,4],
                  'star_FA': 5, 'star_F': [6,7], 'star_G': [8,9],
                  'star_K': 10, 'star_M1': 11, 'star_M3': 12, 'star_M5': 13,
                  'star_M8': 14, 'star_L1': 15, 'star_wd': [16,20,21],
                  'star_carbon': [17,18,19], 'star_Ksubdwarf': 22,
                  'galaxy_early': 23, 'galaxy': [24,25,26], 'galaxy_late': 27,
                  'galaxy_lrg': 28, 'qso': 29, 'qso_bal': [30,31],
                  'qso_bright': 32
                  }

sdss_arcsec_per_pixel = 0.396

@async_to_sync
class SDSS(BaseQuery):

    BASE_URL = SDSS_SERVER()
    SPECTRO_1D = BASE_URL + '/spectro/1d_26'
    IMAGING = BASE_URL + '/www/cgi-bin/drC'
    TEMPLATES = 'http://www.sdss.org/dr5/algorithms/spectemplates/spDR2'
    MAXQUERIES = SDSS_MAXQUERY()
    AVAILABLE_TEMPLATES = spec_templates

    QUERY_URL = 'http://cas.sdss.org/public/en/tools/search/x_sql.asp'

    @class_or_instance
    def query_region_async(self, coordinates, radius=u.degree / 1800., fields=None,
                           spectro=False):
        """
        Used to query a region around given coordinates. Equivalent to
        the object cross-ID from the web interface.

        Parameters
        ----------
        coordinates : str or `astropy.coordinates` object
            The target around which to search. It may be specified as a string
            in which case it is resolved using online services or as the appropriate
            `astropy.coordinates` object. ICRS coordinates may also be entered as strings
            as specified in the `astropy.coordinates` module.
        radius : str or `astropy.units.Quantity` object, optional
            The string must be parsable by `astropy.coordinates.Angle`. The appropriate
            `Quantity` object from `astropy.units` may also be used. Defaults to 2 arcsec.
        fields : list, optional
            SDSS PhotoObj or SpecObj quantities to return. If None, defaults
            to quantities required to find corresponding spectra and images
            of matched objects (e.g. plate, fiberID, mjd, etc.).
        spectro : bool, optional
            Look for spectroscopic match in addition to photometric match? If True,
            objects will only count as a match if photometry *and* spectroscopy
            exist. If False, will look for photometric matches only.

        Examples
        --------
        >>> from astroquery.sdss import SDSS
        >>> from astropy import coordinates as coords
        >>> result = SDSS.query_region(coords.ICRSCoordinates('0h8m05.63s +14d50m23.3s'))

        Returns
        -------
        result : `astropy.table.Table`
            The result of the query as an `astropy.table.Table` object.
        """

        coordinates = commons.parse_coordinates(coordinates)
        
        ra = coordinates.ra.degree
        dec = coordinates.dec.degree
        dr = commons.radius_to_unit(radius,'degree')

        # Fields to return (if cross-ID successful)
        if fields is None:
            fields = copy.deepcopy(photoobj_defs)
            if spectro:
                fields += specobj_defs

        # Construct SQL query
        q_select = 'SELECT '
        for field in fields:
            if field in photoobj_defs:
                q_select += 'p.%s,' % field
            if field in specobj_defs:
                q_select += 's.%s,' % field
        q_select = q_select.rstrip(',')
        q_select += ' '

        q_from = 'FROM PhotoObjAll AS p '
        if spectro:
            q_join = 'JOIN SpecObjAll s ON p.objID = s.bestObjID '
        else:
            q_join = ''
        q_where = 'WHERE (p.ra between %g and %g) and (p.dec between %g and %g)' \
            % (ra-dr, ra+dr, dec-dr, dec+dr)

        sql = "%s%s%s%s" % (q_select, q_from, q_join, q_where)
        r = requests.get(SDSS.QUERY_URL, params={'cmd': sql, 'format': 'csv'})

        return r

    @class_or_instance
    def get_spectra_async(self, matches, plate=None, fiberID=None, mjd=None):
        """
        Download spectrum from SDSS.

        Parameters
        ----------
        matches : astropy.table.Table instance (result of query_region).

        Returns
        -------
        A list of context-managers that yield readable file-like objects
        """

        if not isinstance(matches, Table):
            raise ValueError

        results = []
        for row in matches:
            plate = str(row['plate']).zfill(4)
            fiber = str(row['fiberID']).zfill(3)
            mjd = str(row['mjd'])
            link = '%s/%s/1d/spSpec-%s-%s-%s.fit' % (SDSS.SPECTRO_1D, plate,
                                                     mjd, plate, fiber)

            results.append(aud.get_readable_fileobj(link))

        return results

    @class_or_instance
    @prepend_docstr_noreturns(get_spectra_async.__doc__)
    def get_spectra(self, matches, plate=None, fiberID=None, mjd=None):
        """
        Returns
        -------
        List of PyFITS HDUList objects.
        """

        readable_objs = self.get_spectra_async(matches, plate=plate, fiberID=fiberID, mjd=mjd)

        return [fits.open(obj.__enter__(), ignore_missing_end=True) for obj in readable_objs]

    @class_or_instance
    def get_images_async(self, matches, run=None, rerun=None, camcol=None,
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

        Returns
        -------
        List of PyFITS HDUList objects.
        """

        results = []
        for row in matches:

            # Read in and format some information we need
            field = str(row['field']).zfill(4)

            # Download and read in image data
            linkstr = '%s?RUN=%i&RERUN=%i&CAMCOL=%i&FIELD=%s&FILTER=%s'
            link = linkstr % (SDSS.IMAGING, row['run'], row['rerun'],
                              row['camcol'], field, band)

            results.append(aud.get_readable_fileobj(link))

        return results


    @class_or_instance
    @prepend_docstr_noreturns(get_images_async.__doc__)
    def get_images(self, matches, run=None, rerun=None, camcol=None):
        """
        Returns
        -------
        List of PyFITS HDUList objects.
        """

        readable_objs = self.get_images_async(matches, run=run, rerun=rerun, camcol=camcol)

        return [fits.open(obj.__enter__(), ignore_missing_end=True) for obj in readable_objs]

    @class_or_instance
    def get_spectral_template_async(self, kind='qso'):
        """
        Download spectral templates from SDSS DR-2, which are located here:

            http://www.sdss.org/dr5/algorithms/spectemplates/

        There 32 spectral templates available from DR-2, from stellar spectra,
        to galaxies, to quasars. To see the available templates, do:

            from astroquery.sdss import SDSS
            print sdss.AVAILABLE_TEMPLATES

        Parameters
        ----------
        kind : str, list
            Which spectral template to download? Options are stored in the
            dictionary astroquery.sdss.SDSS.AVAILABLE_TEMPLATES

        Examples
        --------
        >>> qso = SDSS.get_spectral_template(kind='qso')
        >>> Astar = SDSS.get_spectral_template(kind='star_A')
        >>> Fstar = SDSS.get_spectral_template(kind='star_F')

        Returns
        -------
        List of PyFITS HDUList objects.
        """

        if kind == 'all':
            indices = list(np.arange(33))
        else:
            indices = spec_templates[kind]
            if type(indices) is not list:
                indices = [indices]

        results = []
        for index in indices:
            name = str(index).zfill(3)
            link = '%s-%s.fit' % (SDSS.TEMPLATES, name)
            results.append(aud.get_readable_fileobj(link))

        return results


    @class_or_instance
    @prepend_docstr_noreturns(get_spectral_template_async.__doc__)
    def get_spectral_template(self, kind='qso'):
        """
        Returns
        -------
        List of PyFITS HDUList objects.
        """

        readable_objs = self.get_spectral_template_async(kind=kind)

        return [fits.open(obj.__enter__(), ignore_missing_end=True) for obj in readable_objs]

    @class_or_instance
    def _parse_result(self, response, verbose=False):
        """
        Parses the result and return either an `astropy.table.Table` or
        None if no matches were found.

        Parameters
        ----------
        response : `requests.Response`
            Result of requests -> np.atleast1d.

        Returns
        -------
        table : `astropy.table.Table`
        """

        arr = np.atleast_1d(np.genfromtxt(io.BytesIO(response.content),
                            names=True, dtype=None, delimiter=','))

        if len(arr) == 0:
            return None
        else:
            return Table(arr)
