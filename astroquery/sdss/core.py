# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
Access Sloan Digital Sky Survey database online.
"""
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import io
import warnings
import numpy as np

from astropy import units as u
import astropy.coordinates as coord
from astropy.table import Table, Column

from ..query import BaseQuery
from . import conf
from ..utils import commons, async_to_sync, prepend_docstr_nosections
from ..exceptions import RemoteServiceError, NoResultsWarning
from .field_names import (photoobj_defs, specobj_defs,
                          crossid_defs, get_field_info)

__all__ = ['SDSS', 'SDSSClass']
__doctest_skip__ = ['SDSSClass.*']


sdss_arcsec_per_pixel = 0.396 * u.arcsec / u.pixel


@async_to_sync
class SDSSClass(BaseQuery):
    TIMEOUT = conf.timeout
    QUERY_URL_SUFFIX_DR_OLD = '/dr{dr}/en/tools/search/x_sql.asp'
    QUERY_URL_SUFFIX_DR_10 = '/dr{dr}/en/tools/search/x_sql.aspx'
    QUERY_URL_SUFFIX_DR_NEW = '/dr{dr}/en/tools/search/x_results.aspx'
    XID_URL_SUFFIX_OLD = '/dr{dr}/en/tools/crossid/x_crossid.aspx'
    XID_URL_SUFFIX_NEW = '/dr{dr}/en/tools/search/X_Results.aspx'
    IMAGING_URL_SUFFIX = ('{base}/dr{dr}/{instrument}/photoObj/frames/'
                          '{rerun}/{run}/{camcol}/'
                          'frame-{band}-{run:06d}-{camcol}-'
                          '{field:04d}.fits.bz2')
    SPECTRA_URL_SUFFIX = ('{base}/dr{dr}/{instrument}/spectro/redux/'
                          '{run2d}/spectra/{plate:04d}/'
                          'spec-{plate:04d}-{mjd}-{fiber:04d}.fits')

    TEMPLATES_URL = 'http://classic.sdss.org/dr7/algorithms/spectemplates/spDR2'
    # Cross-correlation templates from DR-7 - no clear way to look this up via
    # queries so we just name them explicitly here
    AVAILABLE_TEMPLATES = {'star_O': 0, 'star_OB': 1, 'star_B': 2,
                           'star_A': [3, 4], 'star_FA': 5, 'star_F': [6, 7],
                           'star_G': [8, 9], 'star_K': 10, 'star_M1': 11,
                           'star_M3': 12, 'star_M5': 13, 'star_M8': 14,
                           'star_L1': 15, 'star_wd': [16, 20, 21],
                           'star_carbon': [17, 18, 19], 'star_Ksubdwarf': 22,
                           'galaxy_early': 23, 'galaxy': [24, 25, 26],
                           'galaxy_late': 27, 'galaxy_lrg': 28, 'qso': 29,
                           'qso_bal': [30, 31], 'qso_bright': 32
                           }

    def query_crossid_async(self, coordinates, obj_names=None,
                            photoobj_fields=None, specobj_fields=None,
                            get_query_payload=False, timeout=TIMEOUT,
                            radius=5. * u.arcsec,
                            data_release=conf.default_release, cache=True):
        """
        Query using the cross-identification web interface.

        Parameters
        ----------
        coordinates : str or `astropy.coordinates` object or list of
            coordinates or `~astropy.table.Column` of coordinates The
            target(s) around which to search. It may be specified as a
            string in which case it is resolved using online services or as
            the appropriate `astropy.coordinates` object. ICRS coordinates
            may also be entered as strings as specified in the
            `astropy.coordinates` module.

            Example:
            ra = np.array([220.064728084,220.064728467,220.06473483])
            dec = np.array([0.870131920218,0.87013210119,0.870138329659])
            coordinates = SkyCoord(ra, dec, frame='icrs', unit='deg')
        radius : str or `~astropy.units.Quantity` object, optional The
            string must be parsable by `~astropy.coordinates.Angle`. The
            appropriate `~astropy.units.Quantity` object from
            `astropy.units` may also be used. Defaults to 2 arcsec.
        timeout : float, optional
            Time limit (in seconds) for establishing successful connection with
            remote server.  Defaults to `SDSSClass.TIMEOUT`.
        photoobj_fields : list, optional
            PhotoObj quantities to return. If photoobj_fields is None and
            specobj_fields is None then the value of fields is used
        specobj_fields : list, optional
            SpecObj quantities to return. If photoobj_fields is None and
            specobj_fields is None then the value of fields is used
        obj_names : str, or list or `~astropy.table.Column`, optional
            Target names. If given, every coordinate should have a
            corresponding name, and it gets repeated in the query result.
            It generates unique object names by default.
        get_query_payload : bool
            If True, this will return the data the query would have sent out,
            but does not actually do the query.
        data_release : int
            The data release of the SDSS to use.
        """

        if (not isinstance(coordinates, list) and
                not isinstance(coordinates, Column) and
                not (isinstance(coordinates, commons.CoordClasses) and
                     not coordinates.isscalar)):
            coordinates = [coordinates]

        if obj_names is None:
            obj_names = ['obj_{0}'.format(i) for i in range(len(coordinates))]
        elif len(obj_names) != len(coordinates):
            raise ValueError("Number of coordinates and obj_names should "
                             "be equal")

        if isinstance(radius, u.Quantity):
            radius = radius.to(u.arcmin).value
        else:
            try:
                float(radius)
            except TypeError:
                raise TypeError("radius should be either Quantity or "
                                "convertible to float.")

        sql_query = 'SELECT '

        if specobj_fields is None:
            if photoobj_fields is None:
                photoobj_fields = crossid_defs
            photobj_fields = ['p.{0}'.format(i) for i in photoobj_fields]
            photobj_fields.append('p.objID as obj_id')
            specobj_fields = []
        else:
            specobj_fields = ['s.{0}'.format(i) for i in specobj_fields]
            if photoobj_fields is not None:
                photobj_fields = ['p.{0}'.format(i) for i in photoobj_fields]
                photobj_fields.append('p.objID as obj_id')
            else:
                photobj_fields = []
                specobj_fields.append('s.objID as obj_id')

        sql_query += ', '.join(photobj_fields + specobj_fields)

        sql_query += ',dbo.fPhotoTypeN(p.type) as type \
                      FROM #upload u JOIN #x x ON x.up_id = u.up_id \
                      JOIN PhotoObjAll p ON p.objID = x.objID ORDER BY x.up_id'

        data = "obj_id ra dec \n"
        data += " \n ".join(['{0} {1} {2}'.format(obj_names[i],
                                                  coordinates[i].ra.deg,
                                                  coordinates[i].dec.deg)
                             for i in range(len(coordinates))])

        # firstcol is hardwired, as obj_names is always passed
        request_payload = dict(uquery=sql_query, paste=data,
                               firstcol=1,
                               format='csv', photoScope='nearPrim',
                               radius=radius,
                               photoUpType='ra-dec', searchType='photo')

        if data_release > 11:
            request_payload['searchtool'] = 'CrossID'

        if get_query_payload:
            return request_payload
        url = self._get_crossid_url(data_release)
        response = self._request("POST", url, params=request_payload,
                                 timeout=timeout, cache=cache)
        return response

    def query_region_async(self, coordinates, radius=2. * u.arcsec,
                           fields=None, spectro=False, timeout=TIMEOUT,
                           get_query_payload=False, photoobj_fields=None,
                           specobj_fields=None, field_help=False,
                           obj_names=None, data_release=conf.default_release,
                           cache=True):
        """
        Used to query a region around given coordinates. Equivalent to
        the object cross-ID from the web interface.

        Parameters
        ----------
        coordinates : str or `astropy.coordinates` object or list of
            coordinates or `~astropy.table.Column` of coordinates The
            target(s) around which to search. It may be specified as a
            string in which case it is resolved using online services or as
            the appropriate `astropy.coordinates` object. ICRS coordinates
            may also be entered as strings as specified in the
            `astropy.coordinates` module.

            Example:
            ra = np.array([220.064728084,220.064728467,220.06473483])
            dec = np.array([0.870131920218,0.87013210119,0.870138329659])
            coordinates = SkyCoord(ra, dec, frame='icrs', unit='deg')
        radius : str or `~astropy.units.Quantity` object, optional The
            string must be parsable by `~astropy.coordinates.Angle`. The
            appropriate `~astropy.units.Quantity` object from
            `astropy.units` may also be used. Defaults to 2 arcsec.
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
        photoobj_fields : list, optional
            PhotoObj quantities to return. If photoobj_fields is None and
            specobj_fields is None then the value of fields is used
        specobj_fields : list, optional
            SpecObj quantities to return. If photoobj_fields is None and
            specobj_fields is None then the value of fields is used
        field_help: str or bool, optional
            Field name to check whether a valid PhotoObjAll or SpecObjAll
            field name. If `True` or it is an invalid field name all the valid
            field names are returned as a dict.
        obj_names : str, or list or `~astropy.table.Column`, optional
            Target names. If given, every coordinate should have a
            corresponding name, and it gets repeated in the query result.
        get_query_payload : bool
            If True, this will return the data the query would have sent out,
            but does not actually do the query.
        data_release : int
            The data release of the SDSS to use.

        Examples
        --------
        >>> from astroquery.sdss import SDSS
        >>> from astropy import coordinates as coords
        >>> co = coords.SkyCoord('0h8m05.63s +14d50m23.3s')
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
        request_payload = self._args_to_payload(
            coordinates=coordinates, radius=radius, fields=fields,
            spectro=spectro, photoobj_fields=photoobj_fields,
            specobj_fields=specobj_fields, field_help=field_help,
            obj_names=obj_names, data_release=data_release)
        if get_query_payload or field_help:
            return request_payload

        url = self._get_query_url(data_release)
        response = self._request("GET", url, params=request_payload,
                                 timeout=timeout, cache=cache)
        return response

    def query_specobj_async(self, plate=None, mjd=None, fiberID=None,
                            fields=None, timeout=TIMEOUT,
                            get_query_payload=False, field_help=False,
                            data_release=conf.default_release, cache=True):
        """
        Used to query the SpecObjAll table with plate, mjd and fiberID values.

        At least one of ``plate``, ``mjd`` or ``fiberID`` parameters must be
        specified.

        Parameters
        ----------
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
        field_help: str or bool, optional
            Field name to check whether a valid PhotoObjAll or SpecObjAll
            field name. If `True` or it is an invalid field name all the valid
            field names are returned as a dict.
        get_query_payload : bool
            If True, this will return the data the query would have sent out,
            but does not actually do the query.
        data_release : int
            The data release of the SDSS to use.

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
                                                fiberID=fiberID,
                                                specobj_fields=fields,
                                                spectro=True,
                                                field_help=field_help,
                                                data_release=data_release)
        if get_query_payload or field_help:
            return request_payload

        url = self._get_query_url(data_release)
        response = self._request("GET", url, params=request_payload,
                                 timeout=timeout, cache=cache)
        return response

    def query_photoobj_async(self, run=None, rerun=301, camcol=None,
                             field=None, fields=None, timeout=TIMEOUT,
                             get_query_payload=False, field_help=False,
                             data_release=conf.default_release, cache=True):
        """
        Used to query the PhotoObjAll table with run, rerun, camcol and field
        values.

        At least one of ``run``, ``camcol`` or ``field`` parameters must be
        specified.

        Parameters
        ----------
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
        field_help: str or bool, optional
            Field name to check whether a valid PhotoObjAll or SpecObjAll
            field name. If `True` or it is an invalid field name all the valid
            field names are returned as a dict.
        get_query_payload : bool
            If True, this will return the data the query would have sent out,
            but does not actually do the query.
        data_release : int
            The data release of the SDSS to use.

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
                                                photoobj_fields=fields,
                                                spectro=False,
                                                field_help=field_help,
                                                data_release=data_release)
        if get_query_payload or field_help:
            return request_payload

        url = self._get_query_url(data_release)
        response = self._request("GET", url, params=request_payload,
                                 timeout=timeout, cache=cache)
        return response

    def __sanitize_query(self, stmt):
        """Remove comments and newlines from SQL statement."""
        fsql = ''
        for line in stmt.split('\n'):
            fsql += ' ' + line.split('--')[0]
        return fsql

    def query_sql_async(self, sql_query, timeout=TIMEOUT,
                        data_release=conf.default_release,
                        cache=True, **kwargs):
        """
        Query the SDSS database.

        Parameters
        ----------
        sql_query : str
            An SQL query
        timeout : float, optional
            Time limit (in seconds) for establishing successful connection with
            remote server.  Defaults to `SDSSClass.TIMEOUT`.
        data_release : int
            The data release of the SDSS to use.

        Examples
        --------
        >>> from astroquery.sdss import SDSS
        >>> query = "select top 10 \
                       z, ra, dec, bestObjID \
                     from \
                       specObj \
                     where \
                       class = 'galaxy' \
                       and z > 0.3 \
                       and zWarning = 0"
        >>> res = SDSS.query_sql(query)
        >>> print(res[:5])
            z         ra       dec         bestObjID
        --------- --------- --------- -------------------
        0.3000011 16.411075 4.1197892 1237678660894327022
        0.3000012 49.459411  0.847754 1237660241924063461
        0.3000027 156.25024 7.6586271 1237658425162858683
        0.3000027 256.99461 25.566255 1237661387086693265
         0.300003 175.65125  34.37548 1237665128003731630

        Returns
        -------
        result : `~astropy.table.Table`
            The result of the query as a `~astropy.table.Table` object.

        """

        request_payload = dict(cmd=self.__sanitize_query(sql_query),
                               format='csv')
        if data_release > 11:
            request_payload['searchtool'] = 'SQL'

        if kwargs.get('get_query_payload'):
            return request_payload

        url = self._get_query_url(data_release)
        response = self._request("GET", url, params=request_payload,
                                 timeout=timeout, cache=cache)
        return response

    def get_spectra_async(self, coordinates=None, radius=2. * u.arcsec,
                          matches=None, plate=None, fiberID=None, mjd=None,
                          timeout=TIMEOUT, get_query_payload=False,
                          data_release=conf.default_release, cache=True,
                          show_progress=True):
        """
        Download spectrum from SDSS.

        The query can be made with one the following groups of parameters
        (whichever comes first is used):

        - ``matches`` (result of a call to `query_region`);
        - ``coordinates``, ``radius``;
        - ``plate``, ``mjd``, ``fiberID``.

        See below for examples.

        Parameters
        ----------
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
        get_query_payload : bool
            If True, this will return the data the query would have sent out,
            but does not actually do the query.
        data_release : int
            The data release of the SDSS to use. With the default server, this
            only supports DR8 or later.

        Returns
        -------
        list : list
            A list of context-managers that yield readable file-like objects.
            The function returns the spectra for only one of ``matches``, or
            ``coordinates`` and ``radius``, or ``plate``, ``mjd`` and
            ``fiberID``.

        Examples
        --------
        Using results from a call to `query_region`:

        >>> from astropy import coordinates as coords
        >>> from astroquery.sdss import SDSS
        >>> co = coords.SkyCoord('0h8m05.63s +14d50m23.3s')
        >>> result = SDSS.query_region(co, spectro=True)
        >>> spec = SDSS.get_spectra(matches=result)

        Using coordinates directly:

        >>> spec = SDSS.get_spectra(co)

        Fetch the spectra from all fibers on plate 751 with mjd 52251:

        >>> specs = SDSS.get_spectra(plate=751, mjd=52251)

        """

        if not matches:
            request_payload = self._args_to_payload(
                specobj_fields=['instrument', 'run2d', 'plate',
                                'mjd', 'fiberID'],
                coordinates=coordinates, radius=radius, spectro=True,
                plate=plate, mjd=mjd, fiberID=fiberID,
                data_release=data_release)
            if get_query_payload:
                return request_payload

            url = self._get_query_url(data_release)
            r = self._request("GET", url, params=request_payload,
                              timeout=timeout, cache=cache)

            matches = self._parse_result(r)
            if matches is None:
                warnings.warn("Query returned no results.", NoResultsWarning)
                return

        if not isinstance(matches, Table):
            raise TypeError("'matches' must be an astropy Table.")

        results = []
        for row in matches:
            linkstr = self.SPECTRA_URL_SUFFIX
            # _parse_result returns bytes (requiring a decode) for
            # - instruments
            # - run2d sometimes (#739)
            if isinstance(row['run2d'], bytes):
                run2d = row['run2d'].decode()
            else:
                run2d = row['run2d']
            link = linkstr.format(
                base=conf.sas_baseurl, dr=data_release,
                instrument=row['instrument'].lower(),
                run2d=run2d, plate=row['plate'],
                fiber=row['fiberID'], mjd=row['mjd'])

            results.append(commons.FileContainer(link,
                                                 encoding='binary',
                                                 remote_timeout=timeout,
                                                 show_progress=show_progress))

        return results

    @prepend_docstr_nosections(get_spectra_async.__doc__)
    def get_spectra(self, coordinates=None, radius=2. * u.arcsec,
                    matches=None, plate=None, fiberID=None, mjd=None,
                    timeout=TIMEOUT, cache=True,
                    data_release=conf.default_release,
                    show_progress=True):
        """
        Returns
        -------
        list : List of `~astropy.io.fits.HDUList` objects.

        """

        readable_objs = self.get_spectra_async(coordinates=coordinates,
                                               radius=radius, matches=matches,
                                               plate=plate, fiberID=fiberID,
                                               mjd=mjd, timeout=timeout,
                                               data_release=data_release,
                                               show_progress=show_progress)

        if readable_objs is not None:
            if isinstance(readable_objs, dict):
                return readable_objs
            else:
                return [obj.get_fits() for obj in readable_objs]

    def get_images_async(self, coordinates=None, radius=2. * u.arcsec,
                         matches=None, run=None, rerun=301, camcol=None,
                         field=None, band='g', timeout=TIMEOUT,
                         get_query_payload=False, cache=True,
                         data_release=conf.default_release,
                         show_progress=True):
        """
        Download an image from SDSS.

        Querying SDSS for images will return the entire plate. For subsequent
        analyses of individual objects

        The query can be made with one the following groups of parameters
        (whichever comes first is used):

        - ``matches`` (result of a call to `query_region`);
        - ``coordinates``, ``radius``;
        - ``run``, ``rerun``, ``camcol``, ``field``.

        See below for examples.

        Parameters
        ----------
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
        get_query_payload : bool
            If True, this will return the data the query would have sent out,
            but does not actually do the query.
        data_release : int
            The data release of the SDSS to use.

        Returns
        -------
        list : List of `~astropy.io.fits.HDUList` objects.

        Examples
        --------
        Using results from a call to `query_region`:

        >>> from astropy import coordinates as coords
        >>> from astroquery.sdss import SDSS
        >>> co = coords.SkyCoord('0h8m05.63s +14d50m23.3s')
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
                rerun=rerun, camcol=camcol, field=field,
                data_release=data_release)
            if get_query_payload:
                return request_payload

            url = self._get_query_url(data_release)
            r = self._request("GET", url, params=request_payload,
                              timeout=timeout, cache=cache)
            matches = self._parse_result(r)
            if matches is None:
                warnings.warn("Query returned no results.", NoResultsWarning)
                return
        if not isinstance(matches, Table):
            raise ValueError("'matches' must be an astropy Table")

        results = []
        for row in matches:
            for b in band:
                # Download and read in image data
                linkstr = self.IMAGING_URL_SUFFIX
                instrument = 'boss'
                if data_release > 12:
                    instrument = 'eboss'
                link = linkstr.format(base=conf.sas_baseurl, run=row['run'],
                                      dr=data_release, instrument=instrument,
                                      rerun=row['rerun'], camcol=row['camcol'],
                                      field=row['field'], band=b)

                results.append(commons.FileContainer(
                    link, encoding='binary', remote_timeout=timeout,
                    cache=cache, show_progress=show_progress))

        return results

    @prepend_docstr_nosections(get_images_async.__doc__)
    def get_images(self, coordinates=None, radius=2. * u.arcsec,
                   matches=None, run=None, rerun=301, camcol=None, field=None,
                   band='g', timeout=TIMEOUT, cache=True,
                   get_query_payload=False, data_release=conf.default_release,
                   show_progress=True):
        """
        Returns
        -------
        list : List of `~astropy.io.fits.HDUList` objects.

        """

        readable_objs = self.get_images_async(
            coordinates=coordinates, radius=radius, matches=matches, run=run,
            rerun=rerun, data_release=data_release, camcol=camcol, field=field,
            band=band, timeout=timeout, get_query_payload=get_query_payload,
            show_progress=show_progress)

        if readable_objs is not None:
            if isinstance(readable_objs, dict):
                return readable_objs
            else:
                return [obj.get_fits() for obj in readable_objs]

    def get_spectral_template_async(self, kind='qso', timeout=TIMEOUT,
                                    show_progress=True):
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
            indices = self.AVAILABLE_TEMPLATES[kind]
            if type(indices) is not list:
                indices = [indices]

        results = []
        for index in indices:
            name = str(index).zfill(3)
            link = '%s-%s.fit' % (self.TEMPLATES_URL, name)
            results.append(commons.FileContainer(link,
                                                 remote_timeout=timeout,
                                                 encoding='binary',
                                                 show_progress=show_progress))

        return results

    @prepend_docstr_nosections(get_spectral_template_async.__doc__)
    def get_spectral_template(self, kind='qso', timeout=TIMEOUT,
                              show_progress=True):
        """
        Returns
        -------
        list : List of `~astropy.io.fits.HDUList` objects.

        """

        readable_objs = self.get_spectral_template_async(
            kind=kind, timeout=timeout, show_progress=show_progress)

        if readable_objs is not None:
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
                                          names=True, dtype=None,
                                          delimiter=',', skip_header=1,
                                          comments='#'))

        if len(arr) == 0:
            return None
        else:
            return Table(arr)

    def _args_to_payload(self, coordinates=None, radius=2. * u.arcsec,
                         fields=None, spectro=False,
                         plate=None, mjd=None, fiberID=None, run=None,
                         rerun=301, camcol=None, field=None,
                         photoobj_fields=None, specobj_fields=None,
                         field_help=None, obj_names=None,
                         data_release=conf.default_release):
        """
        Construct the SQL query from the arguments.

        Parameters
        ----------
        coordinates : str or `astropy.coordinates` object or list of
            coordinates or `~astropy.table.Column` or coordinates
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
        photoobj_fields: list, optional
            PhotoObj quantities to return. If photoobj_fields is None and
            specobj_fields is None then the value of fields is used
        specobj_fields: list, optional
            SpecObj quantities to return. If photoobj_fields is None and
            specobj_fields is None then the value of fields is used
        field_help: str or bool, optional
            Field name to check whether it is a valid PhotoObjAll or SpecObjAll
            field name. If `True` or it is an invalid field name all the valid
            field names are returned as a dict.
        obj_names : str, or list or `~astropy.table.Column`, optional
            Target names. If given, every coordinate should have a
            corresponding name, and it gets repeated in the query result
        data_release : int
            The data release of the SDSS to use.

        Returns
        -------
        request_payload : dict

        """
        url = self._get_query_url(data_release)
        # TODO: replace this with something cleaner below
        photoobj_all = get_field_info(self, 'PhotoObjAll', url,
                                      self.TIMEOUT)['name']

        specobj_all = get_field_info(self, 'SpecObjAll', url,
                                     self.TIMEOUT)['name']

        if field_help:
            if field_help is True:
                ret = 0
            elif field_help:
                ret = 0
                if field_help in photoobj_all:
                    print("{0} is a valid 'photoobj_field'".format(field_help))
                    ret += 1
                if field_help in specobj_all:
                    print("{0} is a valid 'specobj_field'".format(field_help))
                    ret += 1
            if ret > 0:
                return
            else:
                if field_help is not True:
                    warnings.warn("{0} isn't a valid 'photobj_field' or "
                                  "'specobj_field' field, valid fields are"
                                  "returned.".format(field_help))
                return {'photoobj_all': photoobj_all,
                        'specobj_all': specobj_all}

        # Construct SQL query
        q_select = 'SELECT DISTINCT '
        q_select_field = []
        if photoobj_fields is None and specobj_fields is None:
            # Fields to return
            if fields is None:
                photoobj_fields = photoobj_defs
                if spectro:
                    specobj_fields = specobj_defs
            else:
                for sql_field in fields:
                    if sql_field.lower() in photoobj_all:
                        q_select_field.append('p.{0}'.format(sql_field))
                    elif sql_field.lower() in specobj_all:
                        q_select_field.append('s.{0}'.format(sql_field))

        if photoobj_fields is not None:
            for sql_field in photoobj_fields:
                q_select_field.append('p.{0}'.format(sql_field))
        if specobj_fields is not None:
            for sql_field in specobj_fields:
                q_select_field.append('s.{0}'.format(sql_field))
        q_select += ', '.join(q_select_field)

        q_from = 'FROM PhotoObjAll AS p '
        if spectro:
            q_join = 'JOIN SpecObjAll s ON p.objID = s.bestObjID '
        else:
            q_join = ''

        q_where = 'WHERE '
        if coordinates is not None:
            if (not isinstance(coordinates, list) and
                not isinstance(coordinates, Column) and
                not (isinstance(coordinates, commons.CoordClasses) and
                     not coordinates.isscalar)):
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

        sql = "{0} {1} {2} {3}".format(q_select, q_from, q_join, q_where)

        request_payload = dict(cmd=sql, format='csv')

        if data_release > 11:
            request_payload['searchtool'] = 'SQL'

        return request_payload

    def _get_query_url(self, data_release):
        if data_release < 10:
            suffix = self.QUERY_URL_SUFFIX_DR_OLD
        elif data_release == 10:
            suffix = self.QUERY_URL_SUFFIX_DR_10
        else:
            suffix = self.QUERY_URL_SUFFIX_DR_NEW

        url = conf.skyserver_baseurl + suffix.format(dr=data_release)
        self._last_url = url
        return url

    def _get_crossid_url(self, data_release):
        if data_release < 11:
            suffix = self.XID_URL_SUFFIX_OLD
        else:
            suffix = self.XID_URL_SUFFIX_NEW

        url = conf.skyserver_baseurl + suffix.format(dr=data_release)
        self._last_url = url
        return url


SDSS = SDSSClass()
