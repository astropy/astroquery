# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""

Author: Jordan Mirocha
Affiliation: University of Colorado at Boulder
Created on: Sun Apr 14 19:18:43 2013

Description: Access Sloan Digital Sky Survey database online.

"""

import numpy as np
from astropy import units as u
from astropy.table import Table
import requests
import io
from ..query import BaseQuery
from . import SDSS_SERVER, SDSS_MAXQUERY
from ..utils import commons, async_to_sync
from ..utils.docstr_chompers import prepend_docstr_noreturns

__all__ = ['SDSS','SDSSClass']

__doctest_skip__ = ['SDSSClass.*']

# Default photometric and spectroscopic quantities to retrieve.
photoobj_defs = ['ra', 'dec', 'objid', 'run', 'rerun', 'camcol', 'field']
specobj_defs = ['z', 'plate', 'mjd', 'fiberID', 'specobjid', 'run2d',
                'instrument']

# Cross-correlation templates from DR-7
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
class SDSSClass(BaseQuery):

    BASE_URL = SDSS_SERVER()
    SPECTRO_OPTICAL = BASE_URL
    IMAGING = BASE_URL + '/boss/photoObj/frames'
    TEMPLATES = 'http://www.sdss.org/dr7/algorithms/spectemplates/spDR2'
    MAXQUERIES = SDSS_MAXQUERY()
    AVAILABLE_TEMPLATES = spec_templates

    QUERY_URL = 'http://skyserver.sdss3.org/public/en/tools/search/x_sql.aspx'

    def query_region_async(self, coordinates, radius=u.degree / 1800.,
                           fields=None, spectro=False,
                           get_query_payload=False):
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
        >>> co = coords.ICRS('0h8m05.63s +14d50m23.3s')
        >>> result = SDSS.query_region(co)
        >>> print(result)
            ra         dec           objid        run  rerun camcol field
        ---------- ----------- ------------------ ---- ----- ------ -----
        2.02344483 14.83982059 587727221951234166 1739    40      3   315
        2.02344483 14.83982059 587727221951234165 1739    40      3   315
        2.02345465 14.83983064 587727221951234164 1739    40      3   315

        Returns
        -------
        result : `astropy.table.Table`
            The result of the query as an `astropy.table.Table` object.
        """

        request_payload = self._args_to_payload(coordinates=coordinates,
                                                radius=radius, fields=fields,
                                                spectro=spectro)
        if get_query_payload:
            return request_payload
        r = requests.get(SDSS.QUERY_URL, params=request_payload)

        return r

    def get_spectra_async(self, coordinates=None, radius=u.degree / 1800.,
                          matches=None, plate=None, fiberID=None, mjd=None,
                          get_query_payload=False):
        """
        Download spectrum from SDSS.

        Parameters
        ----------
        At least one of `coordinates`, `matches`, `plate`, `mjd` or `fiberID`
        must be specified.

        coordinates : str or `astropy.coordinates` object
            The target around which to search. It may be specified as a string
            in which case it is resolved using online services or as the
            appropriate `astropy.coordinates` object. ICRS coordinates may also
            be entered as strings as specified in the `astropy.coordinates`
            module.
        radius : str or `astropy.units.Quantity` object, optional
            The string must be parsable by `astropy.coordinates.Angle`. The
            appropriate `Quantity` object from `astropy.units` may also be
            used. Defaults to 2 arcsec.
        matches : astropy.table.Table instance
            Result of `query_region`.
        plate : integer, optional
            Plate number.
        mjd : integer, optional
            Modified Julian Date indicating the date a given piece of SDSS data
            was taken.
        fiberID : integer, optional
            Fiber number.

        Returns
        -------
        A list of context-managers that yield readable file-like objects. The
        function returns the spectra for only one of `matches`, or
        `coordinates` and `radius`, or `plate`, `mjd` and `fiberID`.

        """

        if not matches:
            request_payload = self._args_to_payload(
                                    fields=['instrument', 'run2d', 'plate',
                                            'mjd', 'fiberID'],
                                    coordinates=coordinates, radius=radius,
                                    spectro=True, plate=plate, mjd=mjd,
                                    fiberID=fiberID)
            if get_query_payload:
                return request_payload
            r = requests.get(SDSS.QUERY_URL, params=request_payload)
            matches = self._parse_result(r)

        if not isinstance(matches, Table):
            raise ValueError

        results = []
        for row in matches:
            link = ('{base}/{instrument}/spectro/redux/{run2d}/spectra'
                    '/{plate:04d}/spec-{plate:04d}-{mjd}-{fiber:04d}.fits')
            link = link.format(base=SDSS.SPECTRO_OPTICAL,
                               instrument=row['instrument'].lower(),
                               run2d=row['run2d'], plate=row['plate'],
                               fiber=row['fiberID'], mjd=row['mjd'])

            results.append(commons.FileContainer(link))


        return results

    @prepend_docstr_noreturns(get_spectra_async.__doc__)
    def get_spectra(self, coordinates=None, radius=u.degree / 1800.,
                    matches=None, plate=None, fiberID=None, mjd=None):
        """
        Returns
        -------
        List of PyFITS HDUList objects.
        """

        readable_objs = self.get_spectra_async(coordinates=coordinates,
                                               radius=radius, matches=matches,
                                               plate=plate, fiberID=fiberID,
                                               mjd=mjd )

        return [obj.get_fits() for obj in readable_objs]

    def get_images_async(self, coordinates=None, radius=u.degree / 1800.,
                         matches=None, run=None, rerun=301, camcol=None,
                         field=None, band='g', get_query_payload=False):
        """
        Download an image from SDSS.

        Querying SDSS for images will return the entire plate. For subsequent
        analyses of individual objects

        Parameters
        ----------
        At least one of `coordinates`, `matches`, `plate`, `mjd` or `fiberID`
        must be specified.

        coordinates : str or `astropy.coordinates` object
            The target around which to search. It may be specified as a string
            in which case it is resolved using online services or as the
            appropriate `astropy.coordinates` object. ICRS coordinates may also
            be entered as strings as specified in the `astropy.coordinates`
            module.
        radius : str or `astropy.units.Quantity` object, optional
            The string must be parsable by `astropy.coordinates.Angle`. The
            appropriate `Quantity` object from `astropy.units` may also be
            used. Defaults to 2 arcsec.
        matches : astropy.table.Table instance
            Result of `query_region`.
        run : integer, optional
            Length of a strip observed in a single continuous image observing
            scan.
        rerun : integer, optional
            Reprocessing of an imaging run. Defaults to 301 which is the most
            recent rerun.
        camcol : integer, optional
            Output of one camera column of CCDs.
        field : integer, optional
            Part of a camcol of size 2048 by 1489 pixels.
        band : str, list
            Could be individual band, or list of bands. Options: u, g, r, i, or z

        Returns
        -------
        List of PyFITS HDUList objects. The function returns the images for
        only one of `matches`, or `coordinates` and `radius`, or `run`,
        `camcol` and `field`.

        """
        if not matches:
            request_payload = self._args_to_payload(
                                    fields=['run', 'rerun', 'camcol', 'field'],
                                    coordinates=coordinates, radius=radius,
                                    spectro=False, run=run, rerun=rerun,
                                    camcol=camcol, field=field)
            if get_query_payload:
                return request_payload
            r = requests.get(SDSS.QUERY_URL, params=request_payload)
            matches = self._parse_result(r)

        if not isinstance(matches, Table):
            raise ValueError

        results = []
        for row in matches:
            for b in band:
                # Download and read in image data
                linkstr = ('{base}/{rerun}/{run}/{camcol}/'
                           'frame-{band}-{run:06d}-{camcol}-'
                           '{field:04d}.fits.bz2')
                link = linkstr.format(base=SDSS.IMAGING, run=row['run'],
                                      rerun=row['rerun'], camcol=row['camcol'],
                                      field=row['field'], band=b)

                results.append(commons.FileContainer(link))

        return results


    @prepend_docstr_noreturns(get_images_async.__doc__)
    def get_images(self, coordinates=None, radius=u.degree / 1800.,
                   matches=None, run=None, rerun=301, camcol=None,
                   field=None, band='g'):
        """
        Returns
        -------
        List of PyFITS HDUList objects.
        """

        readable_objs = self.get_images_async(coordinates=coordinates,
                                              radius=radius, matches=matches,
                                              run=run, rerun=rerun,
                                              camcol=camcol, field=field,
                                              band=band,
                                              get_query_payload=False)

        return [obj.get_fits() for obj in readable_objs]

    def get_spectral_template_async(self, kind='qso'):
        """
        Download spectral templates from SDSS DR-2, which are located here:

            http://www.sdss.org/dr7/algorithms/spectemplates/

        There 32 spectral templates available from DR-2, from stellar spectra,
        to galaxies, to quasars. To see the available templates, do:

            from astroquery.sdss import SDSS
            print SDSS.AVAILABLE_TEMPLATES

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
            results.append(commons.FileContainer(link))

        return results


    @prepend_docstr_noreturns(get_spectral_template_async.__doc__)
    def get_spectral_template(self, kind='qso'):
        """
        Returns
        -------
        List of PyFITS HDUList objects.
        """

        readable_objs = self.get_spectral_template_async(kind=kind)

        return [obj.get_fits() for obj in readable_objs]

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
                            names=True, dtype=None, delimiter=',',
                            skip_header=1))

        if len(arr) == 0:
            return None
        else:
            return Table(arr)

    def _args_to_payload(self, coordinates=None, radius=u.degree / 1800.,
                         fields=None, spectro=False,
                         plate=None, mjd=None, fiberID=None, run=None,
                         rerun=301, camcol=None, field=None):
        """
        Construct the SQL query from the arguments.

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
            Look for spectroscopic match in addition to photometric match? If
            True, objects will only count as a match if photometry *and*
            spectroscopy exist. If False, will look for photometric matches
            only. If `spectro` is True, it is possible to let coordinates
            undefined and set at least one of `plate`, `mjd` or `fiberID` to
            search using these fields.
        plate : integer, optional
            Plate number.
        mjd : integer, optional
            Modified Julian Date indicating the date a given piece of SDSS data
            was taken.
        fiberID : integer, optional
            Fiber number.
        run : integer, optional
            Length of a strip observed in a single continuous image observing
            scan.
        rerun : integer, optional
            Reprocessing of an imaging run. Defaults to 301 which is the most
            recent rerun.
        camcol : integer, optional
            Output of one camera column of CCDs.
        field : integer, optional
            Part of a camcol of size 2048 by 1489 pixels.

        Returns
        -------
        request_payload : dict
        """
        # Fields to return
        if fields is None:
            fields = list(photoobj_defs)
        if spectro:
            fields += specobj_defs

        # Construct SQL query
        q_select = 'SELECT DISTINCT '
        for sql_field in fields:
            if sql_field in photoobj_defs:
                q_select += 'p.%s,' % sql_field
            if sql_field in specobj_defs:
                q_select += 's.%s,' % sql_field
        q_select = q_select.rstrip(',')
        q_select += ' '

        q_from = 'FROM PhotoObjAll AS p '
        if spectro:
            q_join = 'JOIN SpecObjAll s ON p.objID = s.bestObjID '
        else:
            q_join = ''

        q_where = ''
        if coordinates:
            # Query for a region
            coordinates = commons.parse_coordinates(coordinates)

            ra = coordinates.ra.degree
            dec = coordinates.dec.degree
            dr = commons.radius_to_unit(radius,'degree')

            q_where = ('WHERE (p.ra between %g and %g) and '
                       '(p.dec between %g and %g)'
                       % (ra-dr, ra+dr, dec-dr, dec+dr))
        elif spectro:
            # Spectra: query for specified plate, mjd, fiberid
            s_fields = ['s.%s=%d' % (key, val) for (key, val) in
                        [('plate', plate), ('mjd', mjd), ('fiberid', fiberID)]
                        if val is not None]
            if s_fields:
                q_where = 'WHERE (' + ' AND '.join(s_fields) + ')'
        elif run or camcol or field:
            # Imaging: query for specified run, rerun, camcol, field
            p_fields = ['p.%s=%d' % (key, val) for (key, val) in
                        [('run', run), ('camcol', camcol), ('field', field)]
                        if val is not None]
            if p_fields:
                p_fields.append('p.rerun=%d' % rerun)
                q_where = 'WHERE (' + ' AND '.join(p_fields) + ')'

        if not q_where:
            if spectro:
                raise ValueError('must specify at least one of `coordinates`, '
                                 '`plate`, `mjd` or `fiberID`')
            else:
                raise ValueError('must specify at least one of `coordinates`, '
                                 '`run`, `camcol` or `field`')

        sql = "%s%s%s%s" % (q_select, q_from, q_join, q_where)
        request_payload = dict(cmd=sql, format='csv')

        return request_payload

SDSS = SDSSClass()
