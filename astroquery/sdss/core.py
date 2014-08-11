# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""

Author: Jordan Mirocha
Affiliation: University of Colorado at Boulder
Created on: Sun Apr 14 19:18:43 2013

Description: Access Sloan Digital Sky Survey database online.

"""

from __future__ import print_function
import io
import numpy as np
from astropy import units as u
import astropy.coordinates as coord
from astropy.table import Table
from ..query import BaseQuery
from . import conf
from ..utils import commons, async_to_sync
from ..utils.docstr_chompers import prepend_docstr_noreturns
from ..exceptions import RemoteServiceError

__all__ = ['SDSS', 'SDSSClass']

__doctest_skip__ = ['SDSSClass.*']

# Default photometric and spectroscopic quantities to retrieve.
photoobj_defs = ['ra', 'dec', 'objid', 'run', 'rerun', 'camcol', 'field']
specobj_defs = ['z', 'plate', 'mjd', 'fiberID', 'specobjid', 'run2d',
                'instrument']

# Cross-correlation templates from DR-7
spec_templates = {'star_O': 0, 'star_OB': 1, 'star_B': 2, 'star_A': [3, 4],
                  'star_FA': 5, 'star_F': [6, 7], 'star_G': [8, 9],
                  'star_K': 10, 'star_M1': 11, 'star_M3': 12, 'star_M5': 13,
                  'star_M8': 14, 'star_L1': 15, 'star_wd': [16, 20, 21],
                  'star_carbon': [17, 18, 19], 'star_Ksubdwarf': 22,
                  'galaxy_early': 23, 'galaxy': [24, 25, 26],
                  'galaxy_late': 27, 'galaxy_lrg': 28, 'qso': 29,
                  'qso_bal': [30, 31], 'qso_bright': 32
                  }

sdss_arcsec_per_pixel = 0.396


@async_to_sync
class SDSSClass(BaseQuery):

    BASE_URL = conf.server
    SPECTRO_OPTICAL = BASE_URL
    IMAGING = BASE_URL + '/boss/photoObj/frames'
    TEMPLATES = 'http://www.sdss.org/dr7/algorithms/spectemplates/spDR2'
    MAXQUERIES = conf.maxqueries
    AVAILABLE_TEMPLATES = spec_templates
    TIMEOUT = conf.timeout

    QUERY_URL = 'http://skyserver.sdss3.org/public/en/tools/search/x_sql.aspx'

    def query_region_async(self, coordinates, radius=u.degree / 1800.,
                           fields=None, spectro=False, timeout=TIMEOUT,
                           get_query_payload=False, photoobj_fields=None, specobj_fields=None):
        """
        Used to query a region around given coordinates. Equivalent to
        the object cross-ID from the web interface.

        Parameters
        ----------
        coordinates : str or `astropy.coordinates` object or list of coordinates
            The target(s) around which to search. It may be specified as a string
            in which case it is resolved using online services or as the
            appropriate `astropy.coordinates` object. ICRS coordinates may also
            be entered as strings as specified in the `astropy.coordinates`
            module.

            Example:
            ra = np.array([220.064728084,220.064728467,220.06473483])
            dec = np.array([0.870131920218,0.87013210119,0.870138329659])
            coordinates = SkyCoord(ra, dec, frame='icrs', unit='deg')
        radius : str or `~astropy.units.Quantity` object, optional
            The string must be parsable by `~astropy.coordinates.Angle`. The
            appropriate `~astropy.units.Quantity` object from `astropy.units` may also be
            used. Defaults to 2 arcsec.
        fields : list, optional
            SDSS PhotoObj or SpecObj quantities to return. If None, defaults
            to quantities required to find corresponding spectra and images
            of matched objects (e.g. plate, fiberID, mjd, etc.).
        spectro : bool, optional
            Look for spectroscopic match in addition to photometric match? If
            True, objects will only count as a match if photometry *and*
            spectroscopy exist. If False, will look for photometric matches
            only.
        timeout : float, optional
            Time limit (in seconds) for establishing successful connection with
            remote server.  Defaults to `SDSSClass.TIMEOUT`.
        photoobj_fields: float, optional
            PhotoObj quantities to return. If photoobj_fields is None and
            specobj_fields is None then the value of fields is used
        specobj_fields: float, optional
            SpecObj quantities to return. If photoobj_fields is None and
            specobj_fields is None then the value of fields is used

        Examples
        --------
        >>> from astroquery.sdss import SDSS
        >>> from astropy import coordinates as coords
        >>> co = coords.ICRS('0h8m05.63s +14d50m23.3s')
        >>> result = SDSS.query_region(co)
        >>> print(result[:5])
              ra           dec             objid        run  rerun camcol field
        ------------- ------------- ------------------- ---- ----- ------ -----
        2.02344282607 14.8398204075 1237653651835781245 1904   301      3   163
        2.02344283666 14.8398204143 1237653651835781244 1904   301      3   163
        2.02344596595 14.8398237229 1237652943176138867 1739   301      3   315
        2.02344596303 14.8398237521 1237652943176138868 1739   301      3   315
        2.02344772021 14.8398201105 1237653651835781243 1904   301      3   163

        Returns
        -------
        result : `~astropy.table.Table`
            The result of the query as a `~astropy.table.Table` object.

        """
        request_payload = self._args_to_payload(coordinates=coordinates,
                                                radius=radius, fields=fields,
                                                spectro=spectro, photoobj_fields=photoobj_fields,
                                                specobj_fields=specobj_fields)
        if get_query_payload:
            return request_payload
        r = commons.send_request(SDSS.QUERY_URL, request_payload, timeout,
                                 request_type='GET')

        return r

    def query_specobj_async(self, plate=None, mjd=None, fiberID=None,
                            fields=None, timeout=TIMEOUT,
                            get_query_payload=False):
        """
        Used to query the SpecObjAll table with plate, mjd and fiberID values.

        Parameters
        ----------
        At least one of ``plate``, ``mjd`` or ``fiberID`` must be specified.

        plate : integer, optional
            Plate number.
        mjd : integer, optional
            Modified Julian Date indicating the date a given piece of SDSS data
            was taken.
        fiberID : integer, optional
            Fiber number.
        fields : list, optional
            SDSS PhotoObj or SpecObj quantities to return. If None, defaults
            to quantities required to find corresponding spectra and images
            of matched objects (e.g. plate, fiberID, mjd, etc.).
        timeout : float, optional
            Time limit (in seconds) for establishing successful connection with
            remote server.  Defaults to `SDSSClass.TIMEOUT`.

        Examples
        --------
        >>> from astroquery.sdss import SDSS
        >>> result = SDSS.query_specobj(plate=2340,
        ...     fields=['ra', 'dec','plate', 'mjd', 'fiberID', 'specobjid'])
        >>> print(result[:5])
              ra           dec      plate  mjd  fiberID      specobjid
        ------------- ------------- ----- ----- ------- -------------------
        49.2020613611 5.20883041368  2340 53733      60 2634622337315530752
        48.3745360119 5.26557511598  2340 53733     154 2634648175838783488
        47.1604269095 5.48241410994  2340 53733     332 2634697104106219520
        48.6634992214 6.69459110287  2340 53733     553 2634757852123654144
        48.0759195428 6.18757403485  2340 53733     506 2634744932862027776

        Returns
        -------
        result : `~astropy.table.Table`
            The result of the query as an `~astropy.table.Table` object.

        """

        if plate is None and mjd is None and fiberID is None:
            raise ValueError('must specify at least one of '
                             '`plate`, `mjd` or `fiberID`')
        request_payload = self._args_to_payload(plate=plate, mjd=mjd,
                                                fiberID=fiberID, fields=fields,
                                                spectro=True)
        if get_query_payload:
            return request_payload
        r = commons.send_request(SDSS.QUERY_URL, request_payload, timeout,
                                 request_type='GET')

        return r

    def query_photoobj_async(self, run=None, rerun=301, camcol=None,
                             field=None, fields=None, timeout=TIMEOUT,
                             get_query_payload=False):
        """
        Used to query the PhotoObjAll table with run, rerun, camcol and field
        values.

        Parameters
        ----------
        At least one of ``run``, ``camcol`` or ``field`` must be specified.

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
        fields : list, optional
            SDSS PhotoObj or SpecObj quantities to return. If None, defaults
            to quantities required to find corresponding spectra and images
            of matched objects (e.g. plate, fiberID, mjd, etc.).
        timeout : float, optional
            Time limit (in seconds) for establishing successful connection with
            remote server.  Defaults to `SDSSClass.TIMEOUT`.

        Examples
        --------
        >>> from astroquery.sdss import SDSS
        >>> result = SDSS.query_photoobj(run=5714, camcol=6)
        >>> print(result[:5])
              ra           dec             objid        run  rerun camcol field
        ------------- ------------- ------------------- ---- ----- ------ -----
        30.4644529079 7.86460794626 1237670017266024498 5714   301      6    75
        38.7635496073 7.47083098197 1237670017269628978 5714   301      6   130
        22.2574304026 8.43175488904 1237670017262485671 5714   301      6    21
        23.3724928784 8.32576993103 1237670017262944491 5714   301      6    28
        25.4801226435 8.27642390025 1237670017263927330 5714   301      6    43

        Returns
        -------
        result : `~astropy.table.Table`
            The result of the query as a `~astropy.table.Table` object.

        """

        if run is None and camcol is None and field is None:
            raise ValueError('must specify at least one of '
                             '`run`, `camcol` or `field`')
        request_payload = self._args_to_payload(run=run, rerun=rerun,
                                                camcol=camcol, field=field,
                                                fields=fields, spectro=False)
        if get_query_payload:
            return request_payload
        r = commons.send_request(SDSS.QUERY_URL, request_payload, timeout,
                                 request_type='GET')

        return r

    def get_spectra_async(self, coordinates=None, radius=u.degree / 1800.,
                          matches=None, plate=None, fiberID=None, mjd=None,
                          timeout=TIMEOUT, get_query_payload=False):
        """
        Download spectrum from SDSS.

        Parameters
        ----------
        The query can be made with one the following groups of parameters
        (whichever comes first is used):
          - ``matches`` (result of a call to `query_region`);
          - ``coordinates``, ``radius``;
          - ``plate``, ``mjd``, ``fiberID``.
        See below for examples.

        coordinates : str or `astropy.coordinates` object
            The target around which to search. It may be specified as a string
            in which case it is resolved using online services or as the
            appropriate `astropy.coordinates` object. ICRS coordinates may also
            be entered as strings as specified in the `astropy.coordinates`
            module.
        radius : str or `~astropy.units.Quantity` object, optional
            The string must be parsable by `~astropy.coordinates.Angle`. The
            appropriate `~astropy.units.Quantity` object from `astropy.units`
            may also be used. Defaults to 2 arcsec.
        matches : `~astropy.table.Table`
            Result of `query_region`.
        plate : integer, optional
            Plate number.
        mjd : integer, optional
            Modified Julian Date indicating the date a given piece of SDSS data
            was taken.
        fiberID : integer, optional
            Fiber number.
        timeout : float, optional
            Time limit (in seconds) for establishing successful connection with
            remote server.  Defaults to `SDSSClass.TIMEOUT`.

        Returns
        -------
        list : A list of context-managers that yield readable file-like objects.
            The function returns the spectra for only one of ``matches``, or
            ``coordinates`` and ``radius``, or ``plate``, ``mjd`` and
            ``fiberID``.

        Examples
        --------
        Using results from a call to `query_region`:

        >>> from astropy import coordinates as coords
        >>> from astroquery.sdss import SDSS
        >>> co = coords.ICRS('0h8m05.63s +14d50m23.3s')
        >>> result = SDSS.query_region(co, spectro=True)
        >>> spec = SDSS.get_spectra(matches=result)

        Using coordinates directly:

        >>> spec = SDSS.get_spectra(co)

        Fetch the spectra from all fibers on plate 751 with mjd 52251:

        >>> specs = SDSS.get_spectra(plate=751, mjd=52251)

        """

        if not matches:
            request_payload = self._args_to_payload(
                fields=['instrument', 'run2d', 'plate', 'mjd', 'fiberID'],
                coordinates=coordinates, radius=radius, spectro=True,
                plate=plate, mjd=mjd, fiberID=fiberID)
            if get_query_payload:
                return request_payload
            r = commons.send_request(SDSS.QUERY_URL, request_payload, timeout,
                                     request_type='GET')
            matches = self._parse_result(r)

        if not isinstance(matches, Table):
            raise TypeError("Matches must be an astropy Table.")

        results = []
        for row in matches:
            link = ('{base}/{instrument}/spectro/redux/{run2d}/spectra'
                    '/{plate:04d}/spec-{plate:04d}-{mjd}-{fiber:04d}.fits')
            # _parse_result returns bytes for instrunments, requiring a decode
            link = link.format(base=SDSS.SPECTRO_OPTICAL,
                               instrument=row['instrument'].decode().lower(),
                               run2d=row['run2d'], plate=row['plate'],
                               fiber=row['fiberID'], mjd=row['mjd'])

            results.append(commons.FileContainer(link,
                                                 encoding='binary',
                                                 remote_timeout=timeout))

        return results

    @prepend_docstr_noreturns(get_spectra_async.__doc__)
    def get_spectra(self, coordinates=None, radius=u.degree / 1800.,
                    matches=None, plate=None, fiberID=None, mjd=None,
                    timeout=TIMEOUT):
        """
        Returns
        -------
        list : List of `~astropy.io.fits.HDUList` objects.

        """

        readable_objs = self.get_spectra_async(coordinates=coordinates,
                                               radius=radius, matches=matches,
                                               plate=plate, fiberID=fiberID,
                                               mjd=mjd, timeout=timeout)

        return [obj.get_fits() for obj in readable_objs]

    def get_images_async(self, coordinates=None, radius=u.degree / 1800.,
                         matches=None, run=None, rerun=301, camcol=None,
                         field=None, band='g', timeout=TIMEOUT,
                         get_query_payload=False, cache=True):
        """
        Download an image from SDSS.

        Querying SDSS for images will return the entire plate. For subsequent
        analyses of individual objects

        Parameters
        ----------
        The query can be made with one the following groups of parameters
        (whichever comes first is used):
          - ``matches`` (result of a call to `query_region`);
          - ``coordinates``, ``radius``;
          - ``run``, ``rerun``, ``camcol``, ``field``.
        See below for examples.

        coordinates : str or `astropy.coordinates` object
            The target around which to search. It may be specified as a string
            in which case it is resolved using online services or as the
            appropriate `astropy.coordinates` object. ICRS coordinates may also
            be entered as strings as specified in the `astropy.coordinates`
            module.
        radius : str or `~astropy.units.Quantity` object, optional
            The string must be parsable by `~astropy.coordinates.Angle`. The
            appropriate `~astropy.units.Quantity` object from
            `astropy.units` may also be used. Defaults to 2 arcsec.
        matches : `~astropy.table.Table`
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
            Could be individual band, or list of bands.
            Options: ``'u'``, ``'g'``, ``'r'``, ``'i'``, or ``'z'``.
        timeout : float, optional
            Time limit (in seconds) for establishing successful connection with
            remote server.  Defaults to `SDSSClass.TIMEOUT`.
        cache : bool
            Cache the images using astropy's caching system

        Returns
        -------
        list : List of `~astropy.io.fits.HDUList` objects.

        Examples
        --------
        Using results from a call to `query_region`:

        >>> from astropy import coordinates as coords
        >>> from astroquery.sdss import SDSS
        >>> co = coords.ICRS('0h8m05.63s +14d50m23.3s')
        >>> result = SDSS.query_region(co)
        >>> imgs = SDSS.get_images(matches=result)

        Using coordinates directly:

        >>> imgs = SDSS.get_images(co)

        Fetch the images from all runs with camcol 3 and field 164:

        >>> imgs = SDSS.get_images(camcol=3, field=164)

        Fetch only images from run 1904, camcol 3 and field 164:

        >>> imgs = SDSS.get_images(run=1904, camcol=3, field=164)

        """
        if not matches:
            request_payload = self._args_to_payload(
                fields=['run', 'rerun', 'camcol', 'field'],
                coordinates=coordinates, radius=radius, spectro=False, run=run,
                rerun=rerun, camcol=camcol, field=field)
            if get_query_payload:
                return request_payload
            r = commons.send_request(SDSS.QUERY_URL, request_payload, timeout,
                                     request_type='GET')
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

                results.append(commons.FileContainer(link,
                                                     encoding='binary',
                                                     remote_timeout=timeout,
                                                     cache=cache))

        return results

    @prepend_docstr_noreturns(get_images_async.__doc__)
    def get_images(self, coordinates=None, radius=u.degree / 1800.,
                   matches=None, run=None, rerun=301, camcol=None, field=None,
                   band='g', timeout=TIMEOUT, cache=True):
        """
        Returns
        -------
        list : List of `~astropy.io.fits.HDUList` objects.

        """

        readable_objs = self.get_images_async(coordinates=coordinates,
                                              radius=radius, matches=matches,
                                              run=run, rerun=rerun,
                                              camcol=camcol, field=field,
                                              band=band, timeout=timeout,
                                              get_query_payload=False)

        return [obj.get_fits() for obj in readable_objs]

    def get_spectral_template_async(self, kind='qso', timeout=TIMEOUT):
        """
        Download spectral templates from SDSS DR-2.

        Location: http://www.sdss.org/dr7/algorithms/spectemplates/

        There 32 spectral templates available from DR-2, from stellar spectra,
        to galaxies, to quasars. To see the available templates, do:

            from astroquery.sdss import SDSS
            print SDSS.AVAILABLE_TEMPLATES

        Parameters
        ----------
        kind : str, list
            Which spectral template to download? Options are stored in the
            dictionary astroquery.sdss.SDSS.AVAILABLE_TEMPLATES
        timeout : float, optional
            Time limit (in seconds) for establishing successful connection with
            remote server.  Defaults to `SDSSClass.TIMEOUT`.

        Examples
        --------
        >>> qso = SDSS.get_spectral_template(kind='qso')
        >>> Astar = SDSS.get_spectral_template(kind='star_A')
        >>> Fstar = SDSS.get_spectral_template(kind='star_F')

        Returns
        -------
        list : List of `~astropy.io.fits.HDUList` objects.

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
            results.append(commons.FileContainer(link,
                                                 remote_timeout=timeout,
                                                 encoding='binary'))

        return results

    @prepend_docstr_noreturns(get_spectral_template_async.__doc__)
    def get_spectral_template(self, kind='qso', timeout=TIMEOUT):
        """
        Returns
        -------
        list : List of `~astropy.io.fits.HDUList` objects.

        """

        readable_objs = self.get_spectral_template_async(kind=kind,
                                                         timeout=timeout)

        return [obj.get_fits() for obj in readable_objs]

    def _parse_result(self, response, verbose=False):
        """
        Parses the result and return either a `~astropy.table.Table` or
        `None` if no matches were found.

        Parameters
        ----------
        response : `requests.Response`
            Result of requests -> np.atleast_1d.

        Returns
        -------
        table : `~astropy.table.Table`

        """

        if 'error_message' in io.BytesIO(response.content):
            raise RemoteServiceError(response.content)
        arr = np.atleast_1d(np.genfromtxt(io.BytesIO(response.content),
                            names=True, dtype=None, delimiter=',',
                            skip_header=1,  # this may be a hack; it is necessary for tests to pass
                            comments='#'))

        if len(arr) == 0:
            return None
        else:
            return Table(arr)

    def _args_to_payload(self, coordinates=None, radius=u.degree / 1800.,
                         fields=None, spectro=False,
                         plate=None, mjd=None, fiberID=None, run=None,
                         rerun=301, camcol=None, field=None, photoobj_fields=None, specobj_fields=None):
        """
        Construct the SQL query from the arguments.

        Parameters
        ----------
        coordinates : str or `astropy.coordinates` object or list of coordinates
            The target around which to search. It may be specified as a string
            in which case it is resolved using online services or as the
            appropriate `astropy.coordinates` object. ICRS coordinates may also
            be entered as strings as specified in the `astropy.coordinates`
            module.
        radius : str or `~astropy.units.Quantity` object, optional
            The string must be parsable by `~astropy.coordinates.Angle`. The
            appropriate `~astropy.units.Quantity` object from `astropy.units`
            may also be used. Defaults to 2 arcsec.
        fields : list, optional
            SDSS PhotoObj or SpecObj quantities to return. If None, defaults
            to quantities required to find corresponding spectra and images
            of matched objects (e.g. plate, fiberID, mjd, etc.).
        spectro : bool, optional
            Look for spectroscopic match in addition to photometric match? If
            True, objects will only count as a match if photometry *and*
            spectroscopy exist. If False, will look for photometric matches
            only. If ``spectro`` is True, it is possible to let coordinates
            undefined and set at least one of ``plate``, ``mjd`` or ``fiberID``
            to search using these fields.
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
        photoobj_fields: float, optional
            PhotoObj quantities to return. If photoobj_fields is None and
            specobj_fields is None then the value of fields is used
        specobj_fields: float, optional
            SpecObj quantities to return. If photoobj_fields is None and
            specobj_fields is None then the value of fields is used

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
        if photoobj_fields is None and specobj_fields is None:
            for sql_field in fields:
                if sql_field in photoobj_defs:
                    q_select += 'p.%s,' % sql_field
                if sql_field in specobj_defs:
                    q_select += 's.%s,' % sql_field
        else:
            if photoobj_fields is not None:
                for sql_field in photoobj_fields:
                    q_select += 'p.%s,' % sql_field
            if specobj_fields is not None:
                for sql_field in photoobj_fields:
                    q_select += 's.%s,' % sql_field
        q_select = q_select.rstrip(',')
        q_select += ' '

        q_from = 'FROM PhotoObjAll AS p '
        if spectro:
            q_join = 'JOIN SpecObjAll s ON p.objID = s.bestObjID '
        else:
            q_join = ''

        q_where = 'WHERE '
        if coordinates is not None:
            if (not isinstance(coordinates, list) and
                not (isinstance(coordinates, commons.CoordClasses) and
                not coordinates.isscalar)
            ):
                coordinates = [coordinates]
            for n, target in enumerate(coordinates):
                # Query for a region
                target = commons.parse_coordinates(target).transform_to('fk5')

                ra = target.ra.degree
                dec = target.dec.degree
                dr = coord.Angle(radius).to('degree').value
                if n > 0:
                    q_where += ' or '
                q_where += ('((p.ra between %g and %g) and '
                           '(p.dec between %g and %g))'
                           % (ra - dr, ra + dr, dec - dr, dec + dr))
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
