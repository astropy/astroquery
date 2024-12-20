# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
Access Sloan Digital Sky Survey database online.
"""
import re
import warnings
import numpy as np
import sys

from astropy import units as u
from astropy.coordinates import Angle
from astropy.table import Table, Column
from astropy.utils.exceptions import AstropyWarning

from astroquery.query import BaseQuery
from astroquery.sdss import conf
from astroquery.utils import commons, async_to_sync, prepend_docstr_nosections
from astroquery.exceptions import RemoteServiceError, NoResultsWarning
from astroquery.sdss.field_names import (photoobj_defs, specobj_defs,
                                         crossid_defs, get_field_info)

__all__ = ['SDSS', 'SDSSClass']
__doctest_skip__ = ['SDSSClass.*']

# Imaging pixelscale 0.396 arcsec
sdss_arcsec_per_pixel = 0.396 * u.arcsec / u.pixel


@async_to_sync
class SDSSClass(BaseQuery):
    TIMEOUT = conf.timeout
    PARSE_BOSS_RUN2D = re.compile(r'v(?P<major>[0-9]+)_(?P<minor>[0-9]+)_(?P<bugfix>[0-9]+)')
    MAX_CROSSID_RADIUS = 3.0 * u.arcmin
    QUERY_URL_SUFFIX_DR_OLD = '/dr{dr}/en/tools/search/x_sql.asp'
    QUERY_URL_SUFFIX_DR_10 = '/dr{dr}/en/tools/search/x_sql.aspx'
    QUERY_URL_SUFFIX_DR_NEW = '/dr{dr}/en/tools/search/x_results.aspx'
    XID_URL_SUFFIX_OLD = '/dr{dr}/en/tools/crossid/x_crossid.asp'
    XID_URL_SUFFIX_DR_10 = '/dr{dr}/en/tools/crossid/x_crossid.aspx'
    XID_URL_SUFFIX_NEW = '/dr{dr}/en/tools/search/X_Results.aspx'
    IMAGING_URL_SUFFIX = ('{base}/dr{dr}/{instrument}/photoObj/frames/'
                          '{rerun}/{run}/{camcol}/'
                          'frame-{band}-{run:06d}-{camcol}-'
                          '{field:04d}.fits.bz2')
    # Note: {plate:0>4d} does allow 5-digit plates, while still zero-padding 3-digit plates.
    SPECTRA_URL_SUFFIX = ('{base}/dr{dr}/{redux_path}/'
                          '{run2d}/{spectra_path}/{plate:0>4d}/'
                          'spec-{plate:0>4d}-{mjd}-{fiber:04d}.fits')

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

    def query_crossid_async(self, coordinates, *, radius=5. * u.arcsec, timeout=TIMEOUT,
                            fields=None, photoobj_fields=None, specobj_fields=None, obj_names=None,
                            spectro=False, region=False, field_help=False, get_query_payload=False,
                            data_release=conf.default_release, cache=True):
        """
        Query using the cross-identification web interface.

        This query returns the nearest `primary object`_.

        Note that there is a server-side limit of 3 arcmin on ``radius``.

        .. _`primary object`: https://www.sdss4.org/dr17/help/glossary/#surveyprimary

        Parameters
        ----------
        coordinates : str or `astropy.coordinates` object or (list or `~astropy.table.Column`) of coordinates
            The target(s) around which to search. It may be specified as a
            string in which case it is resolved using online services or as
            the appropriate `astropy.coordinates` object. ICRS coordinates
            may also be entered as strings as specified in the
            `astropy.coordinates` module.

            Example:
            ra = np.array([220.064728084,220.064728467,220.06473483])
            dec = np.array([0.870131920218,0.87013210119,0.870138329659])
            coordinates = SkyCoord(ra, dec, frame='icrs', unit='deg')
        radius : str or `~astropy.units.Quantity` object or `~astropy.coordinates.Angle` object, optional
            The string must be parsable by `~astropy.coordinates.Angle`. The
            appropriate `~astropy.units.Quantity` object from
            `astropy.units` or `~astropy.coordinates.Angle` object from
            `astropy.coordinates` may also be used. Defaults to 5 arcsec.
            The maximum allowed value is 3 arcmin.
        timeout : float, optional
            Time limit (in seconds) for establishing successful connection with
            remote server.  Defaults to `SDSSClass.TIMEOUT`.
        fields : list, optional
            SDSS PhotoObj or SpecObj quantities to return. If None, defaults
            to quantities required to find corresponding spectra and images
            of matched objects (e.g. plate, fiberID, mjd, etc.).
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
        spectro : bool, optional
            Look for spectroscopic match in addition to photometric match? If
            True, objects will only count as a match if photometry *and*
            spectroscopy exist. If False, will look for photometric matches
            only.
        region : bool, optional
            Normally cross-id only returns the closest primary object.
            Setting this to ``True`` will return all objects.
        field_help: str or bool, optional
            Field name to check whether a valid PhotoObjAll or SpecObjAll
            field name. If `True` or it is an invalid field name all the valid
            field names are returned as a dict.
        get_query_payload : bool, optional
            If True, this will return the data the query would have sent out,
            but does not actually do the query.
        data_release : int, optional
            The data release of the SDSS to use.
        cache : bool
            Defaults to True. If set overrides global caching behavior.
            See :ref:`caching documentation <astroquery_cache>`.

        Raises
        ------
        TypeError
            If the ``radius`` keyword could not be parsed as an angle.
        ValueError
            If the ``radius`` exceeds 3 arcmin, or if the sizes of
            ``coordinates`` and ``obj_names`` do not match.

        Returns
        -------
        result : `~astropy.table.Table`
            The result of the query as a `~astropy.table.Table` object.

        """

        if isinstance(radius, Angle):
            radius = radius.to_value(u.arcmin)
        else:
            try:
                radius = Angle(radius).to_value(u.arcmin)
            except ValueError:
                raise TypeError("radius should be either Quantity or "
                                "convertible to float.")
        if radius > self.MAX_CROSSID_RADIUS.value:
            raise ValueError(f"radius must be less than {self.MAX_CROSSID_RADIUS}.")

        if (not isinstance(coordinates, list) and not isinstance(coordinates, Column)
                and not (isinstance(coordinates, commons.CoordClasses) and not coordinates.isscalar)):
            coordinates = [coordinates]
        if obj_names is None:
            obj_names = [f'obj_{i:d}' for i in range(len(coordinates))]
        elif len(obj_names) != len(coordinates):
            raise ValueError("Number of coordinates and obj_names should "
                             "be equal")
        if region:
            data = "ra dec \n"
            data_format = '{ra} {dec}'
        else:
            # SDSS's own examples default to 'name'.  'obj_id' is too easy to confuse with 'objID'
            data = "name ra dec \n"
            data_format = '{obj} {ra} {dec}'
        data += " \n ".join([data_format.format(obj=obj_names[i],
                                                ra=coordinates[i].ra.deg,
                                                dec=coordinates[i].dec.deg)
                             for i in range(len(coordinates))])

        # firstcol is hardwired, as obj_names is always passed
        files = {'upload': ('astroquery', data)}

        request_payload = self._args_to_payload(coordinates=coordinates,
                                                fields=fields,
                                                spectro=spectro, region=region,
                                                photoobj_fields=photoobj_fields,
                                                specobj_fields=specobj_fields, field_help=field_help,
                                                data_release=data_release)
        if field_help:
            return request_payload, files

        request_payload['radius'] = radius
        if region:
            request_payload['firstcol'] = 0  # First column is RA.
            request_payload['photoScope'] = 'allObj'  # All nearby objects, i.e. PhotoObjAll
        else:
            request_payload['firstcol'] = 1  # Skip one column, which contains the object name.
            request_payload['photoScope'] = 'nearPrim'  # Nearest primary object
        request_payload['photoUpType'] = 'ra-dec'  # Input data payload has RA, Dec coordinates
        request_payload['searchType'] = 'photo'

        if get_query_payload:
            return request_payload, files

        url = self._get_crossid_url(data_release)
        response = self._request("POST", url, data=request_payload,
                                 files=files,
                                 timeout=timeout, cache=cache)
        return response

    def query_region_async(self, coordinates, *, radius=None,
                           width=None, height=None, timeout=TIMEOUT,
                           fields=None, photoobj_fields=None, specobj_fields=None, obj_names=None,
                           spectro=False, field_help=False, get_query_payload=False,
                           data_release=conf.default_release, cache=True):
        r"""
        Used to query a region around given coordinates. Either ``radius`` or
        ``width`` must be specified.

        When called with keyword ``radius``, a radial or "cone" search is
        performed, centered on each of the given coordinates. In this mode, internally,
        this function is equivalent to the object cross-ID (`query_crossid`),
        with slightly different parameters.  Note that in this mode there is a server-side
        limit of 3 arcmin on ``radius``.

        When called with keyword ``width``, and optionally a different ``height``,
        a rectangular search is performed, centered on each of the given
        coordinates. In this mode, internally, this function is equivalent to
        a general SQL query (`query_sql`). The shape of the rectangle is
        not corrected for declination (*i.e.* no :math:`\cos \delta` correction);
        conceptually, this means that the rectangle will become increasingly
        trapezoidal-shaped at high declination.

        In both radial and rectangular modes, this function returns all objects
        within the search area; this could potentially include duplicate observations
        of the same object.

        Parameters
        ----------
        coordinates : str or `astropy.coordinates` object or (list or `~astropy.table.Column`) of coordinates
            The target(s) around which to search. It may be specified as a
            string in which case it is resolved using online services or as
            the appropriate `astropy.coordinates` object. ICRS coordinates
            may also be entered as strings as specified in the
            `astropy.coordinates` module.

            Example:
            ra = np.array([220.064728084,220.064728467,220.06473483])
            dec = np.array([0.870131920218,0.87013210119,0.870138329659])
            coordinates = SkyCoord(ra, dec, frame='icrs', unit='deg')
        radius : str or `~astropy.units.Quantity` object, optional
            The string must be parsable by `~astropy.coordinates.Angle`. The
            appropriate `~astropy.units.Quantity` object from
            `astropy.units` may also be used.
            The maximum allowed value is 3 arcmin.
        width : str or `~astropy.units.Quantity` object, optional
            The string must be parsable by `~astropy.coordinates.Angle`. The
            appropriate `~astropy.units.Quantity` object from
            `astropy.units` may also be used.
        height : str or `~astropy.units.Quantity` object, optional
            The string must be parsable by `~astropy.coordinates.Angle`. The
            appropriate `~astropy.units.Quantity` object from
            `astropy.units` may also be used. If not specified, it will be
            set to the same value as ``width``.
        timeout : float, optional
            Time limit (in seconds) for establishing successful connection with
            remote server.  Defaults to `SDSSClass.TIMEOUT`.
        fields : list, optional
            SDSS PhotoObj or SpecObj quantities to return. If None, defaults
            to quantities required to find corresponding spectra and images
            of matched objects (e.g. plate, fiberID, mjd, etc.).
        photoobj_fields : list, optional
            PhotoObj quantities to return. If photoobj_fields is None and
            specobj_fields is None then the value of fields is used
        specobj_fields : list, optional
            SpecObj quantities to return. If photoobj_fields is None and
            specobj_fields is None then the value of fields is used
        obj_names : str, or list or `~astropy.table.Column`, optional
            Target names. If given, every coordinate should have a
            corresponding name, and it gets repeated in the query result.
        spectro : bool, optional
            Look for spectroscopic match in addition to photometric match? If
            True, objects will only count as a match if photometry *and*
            spectroscopy exist. If False, will look for photometric matches
            only.
        field_help: str or bool, optional
            Field name to check whether a valid PhotoObjAll or SpecObjAll
            field name. If `True` or it is an invalid field name all the valid
            field names are returned as a dict.
        get_query_payload : bool, optional
            If True, this will return the data the query would have sent out,
            but does not actually do the query.
        data_release : int, optional
            The data release of the SDSS to use.
        cache : bool
            Defaults to True. If set overrides global caching behavior.
            See :ref:`caching documentation <astroquery_cache>`.

        Raises
        ------
        TypeError
            If the ``radius``, ``width`` or ``height`` keywords could not be parsed as an angle.
        ValueError
            If both ``radius`` and ``width`` are set (or neither),
            or if the ``radius`` exceeds 3 arcmin,
            or if the sizes of ``coordinates`` and ``obj_names`` do not match,
            or if the units of ``width`` or ``height`` could not be parsed.

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
        # Allow field_help requests to pass without requiring a radius or width.
        if field_help and radius is None and width is None:
            radius = 2.0 * u.arcsec

        if radius is None and width is None:
            raise ValueError("Either radius or width must be specified!")
        if radius is not None and width is not None:
            raise ValueError("Either radius or width must be specified, not both!")

        if radius is not None:
            request_payload, files = self.query_crossid_async(coordinates=coordinates,
                                                              radius=radius, fields=fields,
                                                              photoobj_fields=photoobj_fields,
                                                              specobj_fields=specobj_fields,
                                                              obj_names=obj_names,
                                                              spectro=spectro,
                                                              region=True,
                                                              field_help=field_help,
                                                              get_query_payload=True,
                                                              data_release=data_release,
                                                              cache=cache)

        if width is not None:
            width = u.Quantity(width, u.degree).value
            if height is None:
                height = width
            else:
                height = u.Quantity(height, u.degree).value

            dummy_payload = self._args_to_payload(coordinates=coordinates,
                                                  fields=fields,
                                                  spectro=spectro, region=True,
                                                  photoobj_fields=photoobj_fields,
                                                  specobj_fields=specobj_fields, field_help=field_help,
                                                  data_release=data_release)

            sql_query = dummy_payload['uquery'].replace('#upload u JOIN #x x ON x.up_id = u.up_id JOIN ', '')

            if 'SpecObjAll' in dummy_payload['uquery']:
                sql_query = sql_query.replace('ON p.objID = x.objID ', '').replace(' ORDER BY x.up_id', '')
            else:
                sql_query = sql_query.replace(' ON p.objID = x.objID ORDER BY x.up_id', '')

            if (not isinstance(coordinates, list) and not isinstance(coordinates, Column)
                    and not (isinstance(coordinates, commons.CoordClasses) and not coordinates.isscalar)):
                coordinates = [coordinates]

            rectangles = list()
            for target in coordinates:
                # Query for a rectangle
                target = commons.parse_coordinates(target).transform_to('fk5')
                rectangles.append(self._rectangle_sql(target.ra.degree, target.dec.degree, width, height=height))

            rect = ' OR '.join(rectangles)

            # self._args_to_payload only returns a WHERE if e.g. plate, mjd, fiber
            # are set, which will not happen in this function.
            sql_query += f' WHERE ({rect})'

            return self.query_sql_async(sql_query, timeout=timeout,
                                        data_release=data_release,
                                        cache=cache,
                                        field_help=field_help,
                                        get_query_payload=get_query_payload)

        if get_query_payload or field_help:
            return request_payload

        url = self._get_crossid_url(data_release)
        response = self._request("POST", url, data=request_payload,
                                 files=files,
                                 timeout=timeout, cache=cache)
        return response

    def query_specobj_async(self, *, plate=None, mjd=None, fiberID=None,
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
        get_query_payload : bool, optional
            If True, this will return the data the query would have sent out,
            but does not actually do the query.
        data_release : int, optional
            The data release of the SDSS to use.
        cache : bool
            Defaults to True. If set overrides global caching behavior.
            See :ref:`caching documentation <astroquery_cache>`.

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

    def query_photoobj_async(self, *, run=None, rerun=301, camcol=None,
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
        get_query_payload : bool, optional
            If True, this will return the data the query would have sent out,
            but does not actually do the query.
        data_release : int, optional
            The data release of the SDSS to use.
        cache : bool
            Defaults to True. If set overrides global caching behavior.
            See :ref:`caching documentation <astroquery_cache>`.

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

    def query_sql_async(self, sql_query, *, timeout=TIMEOUT,
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
        data_release : int, optional
            The data release of the SDSS to use.
        cache : bool
            Defaults to True. If set overrides global caching behavior.
            See :ref:`caching documentation <astroquery_cache>`.

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

        if kwargs.get('get_query_payload') or kwargs.get('field_help'):
            return request_payload

        url = self._get_query_url(data_release)
        response = self._request("GET", url, params=request_payload,
                                 timeout=timeout, cache=cache)
        return response

    def get_spectra_async(self, *, coordinates=None, radius=2. * u.arcsec,
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
        fiberID : integer, optional
            Fiber number.
        mjd : integer, optional
            Modified Julian Date indicating the date a given piece of SDSS data
            was taken.
        timeout : float, optional
            Time limit (in seconds) for establishing successful connection with
            remote server.  Defaults to `SDSSClass.TIMEOUT`.
        get_query_payload : bool, optional
            If True, this will return the data the query would have sent out,
            but does not actually do the query.
        data_release : int, optional
            The data release of the SDSS to use. With the default server, this
            only supports DR8 or later.
        cache : bool
            Defaults to True. If set overrides global caching behavior.
            See :ref:`caching documentation <astroquery_cache>`.
        show_progress : bool, optional
            If False, do not display download progress.

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
            if coordinates is None:
                matches = self.query_specobj(plate=plate, mjd=mjd, fiberID=fiberID,
                                             fields=['run2d', 'plate', 'mjd', 'fiberID'],
                                             timeout=timeout, get_query_payload=get_query_payload,
                                             data_release=data_release, cache=cache)
            else:
                matches = self.query_crossid(coordinates, radius=radius, timeout=timeout,
                                             specobj_fields=['run2d', 'plate', 'mjd', 'fiberID'],
                                             spectro=True, get_query_payload=get_query_payload,
                                             data_release=data_release, cache=cache)
            if get_query_payload:
                if coordinates is None:
                    return matches
                else:
                    return matches[0]

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
            elif isinstance(row['run2d'], (np.integer, int)):
                run2d = str(row['run2d'])
            else:
                run2d = row['run2d']
            format_args = dict()
            format_args['base'] = conf.sas_baseurl
            format_args['dr'] = data_release
            format_args['redux_path'] = 'sdss/spectro/redux'
            format_args['run2d'] = run2d
            format_args['spectra_path'] = 'spectra'
            format_args['mjd'] = row['mjd']
            try:
                format_args['plate'] = row['plate']
                format_args['fiber'] = row['fiberID']
            except KeyError:
                format_args['fieldid'] = row['fieldID']
                format_args['catalogid'] = row['catalogID']
            if data_release > 15 and run2d not in ('26', '103', '104'):
                #
                # Still want this applied to data_release > 17.
                #
                format_args['spectra_path'] = 'spectra/full'
            if data_release > 17:
                #
                # This change will fix everything except run2d==v6_0_4 in DR18,
                # which is handled by the if major > 5 block below.
                #
                format_args['redux_path'] = 'spectro/sdss/redux'
                match_run2d = self.PARSE_BOSS_RUN2D.match(run2d)
                if match_run2d is not None:
                    major = int(match_run2d.group('major'))
                    if major > 5:
                        linkstr = linkstr.replace('/{plate:0>4d}/', '/{fieldid:0>4d}p/{mjd:5d}/')
                        linkstr = linkstr.replace('spec-{plate:0>4d}-{mjd}-{fiber:04d}.fits',
                                                  'spec-{fieldid:0>4d}-{mjd:5d}-{catalogid:0>11d}.fits')

            link = linkstr.format(**format_args)
            results.append(commons.FileContainer(link,
                                                 cache=cache,
                                                 encoding='binary',
                                                 remote_timeout=timeout,
                                                 show_progress=show_progress))

        return results

    @prepend_docstr_nosections(get_spectra_async.__doc__)
    def get_spectra(self, *, coordinates=None, radius=2. * u.arcsec,
                    matches=None, plate=None, fiberID=None, mjd=None,
                    timeout=TIMEOUT, get_query_payload=False,
                    data_release=conf.default_release, cache=True,
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
                                               get_query_payload=get_query_payload,
                                               data_release=data_release,
                                               cache=cache,
                                               show_progress=show_progress)

        if get_query_payload:
            return readable_objs

        if readable_objs is not None:
            if isinstance(readable_objs, dict):
                return readable_objs
            else:
                return [obj.get_fits() for obj in readable_objs]

    def get_images_async(self, coordinates=None, radius=2. * u.arcsec,
                         matches=None, run=None, rerun=301, camcol=None,
                         field=None, band='g', timeout=TIMEOUT,
                         cache=True, get_query_payload=False,
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
        band : str or list
            Could be individual band, or list of bands.
            Options: ``'u'``, ``'g'``, ``'r'``, ``'i'``, or ``'z'``.
        timeout : float, optional
            Time limit (in seconds) for establishing successful connection with
            remote server.  Defaults to `SDSSClass.TIMEOUT`.
        get_query_payload : bool, optional
            If True, this will return the data the query would have sent out,
            but does not actually do the query.
        cache : bool
            Defaults to True. If set overrides global caching behavior.
            See :ref:`caching documentation <astroquery_cache>`.
        data_release : int, optional
            The data release of the SDSS to use.
        show_progress : bool, optional
            If False, do not display download progress.

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
            if coordinates is None:
                matches = self.query_photoobj(run=run, rerun=rerun,
                                              camcol=camcol, field=field,
                                              fields=['run', 'rerun', 'camcol', 'field'],
                                              timeout=timeout, get_query_payload=get_query_payload,
                                              data_release=data_release, cache=cache)
            else:
                matches = self.query_crossid(coordinates, radius=radius, timeout=timeout,
                                             fields=['run', 'rerun', 'camcol', 'field'],
                                             get_query_payload=get_query_payload,
                                             data_release=data_release, cache=cache)
            if get_query_payload:
                if coordinates is None:
                    return matches
                else:
                    return matches[0]

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
                if data_release > 17:
                    instrument = 'prior-surveys/sdss4-dr17-eboss'
                link = linkstr.format(base=conf.sas_baseurl, run=row['run'],
                                      dr=data_release, instrument=instrument,
                                      rerun=row['rerun'], camcol=row['camcol'],
                                      field=row['field'], band=b)

                results.append(commons.FileContainer(
                    link, encoding='binary', remote_timeout=timeout,
                    cache=cache, show_progress=show_progress))

        return results

    @prepend_docstr_nosections(get_images_async.__doc__)
    def get_images(self, *, coordinates=None, radius=2. * u.arcsec,
                   matches=None, run=None, rerun=301, camcol=None, field=None,
                   band='g', timeout=TIMEOUT, cache=True,
                   get_query_payload=False, data_release=conf.default_release,
                   show_progress=True):
        """
        Returns
        -------
        list : List of `~astropy.io.fits.HDUList` objects.

        """

        readable_objs = self.get_images_async(coordinates=coordinates,
                                              radius=radius,
                                              matches=matches,
                                              run=run,
                                              rerun=rerun,
                                              camcol=camcol,
                                              field=field,
                                              band=band,
                                              timeout=timeout,
                                              cache=cache,
                                              get_query_payload=get_query_payload,
                                              data_release=data_release,
                                              show_progress=show_progress)

        if get_query_payload:
            return readable_objs

        if readable_objs is not None:
            if isinstance(readable_objs, dict):
                return readable_objs
            else:
                return [obj.get_fits() for obj in readable_objs]

    def get_spectral_template_async(self, kind='qso', *, timeout=TIMEOUT,
                                    show_progress=True):
        """
        Download spectral templates from SDSS DR-2.

        Location: http://classic.sdss.org/dr7/algorithms/spectemplates/

        There 32 spectral templates available from DR-2, from stellar spectra,
        to galaxies, to quasars. To see the available templates, do:

            from astroquery.sdss import SDSS
            print SDSS.AVAILABLE_TEMPLATES

        Parameters
        ----------
        kind : str or list
            Which spectral template to download? Options are stored in the
            dictionary astroquery.sdss.SDSS.AVAILABLE_TEMPLATES
        timeout : float, optional
            Time limit (in seconds) for establishing successful connection with
            remote server.  Defaults to `SDSSClass.TIMEOUT`.
        show_progress : bool, optional
            If False, do not display download progress.

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
            if not isinstance(indices, list):
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
    def get_spectral_template(self, kind='qso', *, timeout=TIMEOUT,
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
        verbose : bool, optional
            Not currently used.

        Returns
        -------
        table : `~astropy.table.Table`

        """
        if 'error_message' in response.text:
            raise RemoteServiceError(response.text)

        with warnings.catch_warnings():
            # Capturing the warning and converting the objid column to int64 is necessary for consistency as
            # it was convereted to string on systems with defaul integer int32 due to an overflow.
            if sys.platform.startswith('win'):
                warnings.filterwarnings("ignore", category=AstropyWarning,
                                        message=r'OverflowError converting to IntType in column.*')
            arr = Table.read(response.text, format='ascii.csv', comment="#")
            for id_column in ('objid', 'specobjid', 'objID', 'specobjID', 'specObjID'):
                if id_column in arr.columns:
                    arr[id_column] = arr[id_column].astype(np.uint64)

        if len(arr) == 0:
            return None
        else:
            return arr

    def _args_to_payload(self, *, coordinates=None,
                         fields=None, spectro=False, region=False,
                         plate=None, mjd=None, fiberID=None, run=None,
                         rerun=301, camcol=None, field=None,
                         photoobj_fields=None, specobj_fields=None,
                         field_help=None,
                         data_release=conf.default_release):
        """
        Construct the SQL query from the arguments.

        Parameters
        ----------
        coordinates : str or `astropy.coordinates` object or (list or `~astropy.table.Column`) or coordinates
            The target around which to search. It may be specified as a string
            in which case it is resolved using online services or as the
            appropriate `astropy.coordinates` object. ICRS coordinates may also
            be entered as strings as specified in the `astropy.coordinates`
            module.
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
        region : bool, optional
            Used internally to distinguish certain types of queries.
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
        data_release : int, optional
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
                    print(f"{field_help} is a valid 'photoobj_field'")
                    ret += 1
                if field_help in specobj_all:
                    print(f"{field_help} is a valid 'specobj_field'")
                    ret += 1
            if ret > 0:
                return
            else:
                if field_help is not True:
                    warnings.warn(f"{field_help} isn't a valid 'photobj_field' or "
                                  "'specobj_field' field, valid fields are "
                                  "returned.")
                return {'photoobj_all': photoobj_all,
                        'specobj_all': specobj_all}

        # Construct SQL query
        q_select = 'SELECT DISTINCT '
        crossid = coordinates is not None and not region  # crossid queries have different default fields
        if coordinates is not None:
            q_select = 'SELECT\r\n'  # Older versions expect the CRLF to be there.
        q_select_field = []
        fields_spectro = False
        if photoobj_fields is None and specobj_fields is None:
            # Fields to return
            if fields is None:
                if crossid:
                    photoobj_fields = crossid_defs
                else:
                    photoobj_fields = photoobj_defs
                if spectro:
                    specobj_fields = specobj_defs
            else:
                for sql_field in fields:
                    if (sql_field in photoobj_all
                            or sql_field.lower() in photoobj_all):
                        q_select_field.append(f'p.{sql_field}')
                    elif (sql_field in specobj_all
                          or sql_field.lower() in specobj_all):
                        fields_spectro = True
                        q_select_field.append(f's.{sql_field}')

        if photoobj_fields is not None:
            for sql_field in photoobj_fields:
                q_select_field.append(f'p.{sql_field}')
        if specobj_fields is not None:
            for sql_field in specobj_fields:
                q_select_field.append(f's.{sql_field}')
            if crossid and fields is None:
                q_select_field.append('s.SpecObjID AS obj_id')
        if crossid:
            q_select_field.append('dbo.fPhotoTypeN(p.type) AS type')
        q_select += ', '.join(q_select_field)

        q_from = 'FROM PhotoObjAll AS p'
        if coordinates is not None:
            q_from = 'FROM #upload u JOIN #x x ON x.up_id = u.up_id JOIN PhotoObjAll AS p ON p.objID = x.objID'
        if spectro or specobj_fields or fields_spectro:
            q_from += ' JOIN SpecObjAll AS s ON p.objID = s.bestObjID'

        q_where = None
        if coordinates is not None:
            q_where = 'ORDER BY x.up_id'
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

        sql = f"{q_select} {q_from} {q_where}"

        # In DR 8 & DR9 the format parameter is case-sensitive, but in later
        # releases that does not appear to be the case.  In principle 'csv'
        # should work for all.
        request_payload = dict(format='csv')
        if coordinates is not None:
            request_payload['uquery'] = sql
            if data_release > 11:
                request_payload['searchtool'] = 'CrossID'
        else:
            request_payload['cmd'] = sql
            if data_release > 11:
                request_payload['searchtool'] = 'SQL'

        return request_payload

    def _get_query_url(self, data_release):
        """Generate URL for generic SQL queries.
        """
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
        """Generate URL for CrossID queries.
        """
        if data_release < 10:
            suffix = self.XID_URL_SUFFIX_OLD
        elif data_release == 10:
            suffix = self.XID_URL_SUFFIX_DR_10
        else:
            suffix = self.XID_URL_SUFFIX_NEW

        url = conf.skyserver_baseurl + suffix.format(dr=data_release)
        self._last_url = url
        return url

    def _rectangle_sql(self, ra, dec, width, height=None):
        """
        Generate SQL for a rectangular query centered on ``ra``, ``dec``.

        This assumes that RA is defined on the range ``[0, 360)``, and Dec on
        ``[-90, 90]``.

        Parameters
        ----------
        ra : float
            Right Ascension in degrees.
        dec : float
            Declination in degrees.
        width : float
            Width of rectangle in degrees.
        height : float, optional
            Height of rectangle in degrees. If not specified, ``width`` is used.

        Returns
        -------
        :class:`str`
            A string defining the rectangle in SQL notation.
        """
        if height is None:
            height = width
        dr = width/2.0
        dd = height/2.0
        d0 = dec - dd
        if d0 < -90:
            d0 = -90.0
        d1 = dec + dd
        if d1 > 90.0:
            d1 = 90.0
        ra_wrap = False
        r0 = ra - dr
        if r0 < 0:
            ra_wrap = True
            r0 += 360.0
        r1 = ra + dr
        if r1 > 360.0:
            ra_wrap = True
            r1 -= 360.0
        # BETWEEN is inclusive, so it is equivalent to the <=, >= operators.
        if ra_wrap:
            sql = f"(((p.ra >= {r0:g}) OR (p.ra <= {r1:g}))"
        else:
            sql = f"((p.ra BETWEEN {r0:g} AND {r1:g})"
        return sql + f" AND (p.dec BETWEEN {d0:g} AND {d1:g}))"


SDSS = SDSSClass()
