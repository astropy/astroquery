# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
IRSA
====


Module to query the IRSA archive.
"""

import warnings
from astropy.coordinates import SkyCoord, Angle
from astropy import units as u
from astropy.utils.decorators import deprecated, deprecated_renamed_argument

from pyvo.dal import TAPService, SIA2Service, SSAService
from pyvo.dal.sia2 import SIA2_PARAMETERS_DESC
from astroquery import log
from astroquery.query import BaseVOQuery
from astroquery.utils.commons import parse_coordinates
from astroquery.ipac.irsa import conf
from astroquery.exceptions import InvalidQueryError


__all__ = ['Irsa', 'IrsaClass']


class IrsaClass(BaseVOQuery):

    def __init__(self):
        super().__init__()
        self.sia_url = conf.sia_url
        self.ssa_url = conf.ssa_url
        self.tap_url = conf.tap_url
        self._sia = None
        self._ssa = None
        self._tap = None

    @property
    def sia(self):
        if not self._sia:
            self._sia = SIA2Service(baseurl=self.sia_url, session=self._session)
        return self._sia

    @property
    def ssa(self):
        if not self._ssa:
            self._ssa = SSAService(baseurl=self.ssa_url, session=self._session)
        return self._ssa

    @property
    def tap(self):
        if not self._tap:
            self._tap = TAPService(baseurl=self.tap_url, session=self._session)
        return self._tap

    def query_tap(self, query, *, async_job=False, maxrec=None):
        """
        Send query to IRSA TAP. Results in `~pyvo.dal.TAPResults` format.
        result.to_qtable in `~astropy.table.QTable` format

        Parameters
        ----------
        query : str
            ADQL query to be executed
        async_job : bool, optional
            if True query is run in asynchronous mode
        maxrec : int, optional
            maximum number of records to return

        Returns
        -------
        result : `~pyvo.dal.TAPResults`
            TAP query result.
        result.to_table : `~astropy.table.Table`
            TAP query result as `~astropy.table.Table`
        result.to_qtable : `~astropy.table.QTable`
            TAP query result as `~astropy.table.QTable`

        """
        log.debug(f'Query is run in async mode: {async_job}\n TAP query: {query}')

        if async_job:
            return self.tap.run_async(query, language='ADQL', maxrec=maxrec)
        else:
            return self.tap.run_sync(query, language='ADQL', maxrec=maxrec)

    def query_sia(self, *, pos=None, band=None, time=None, pol=None,
                  field_of_view=None, spatial_resolution=None,
                  spectral_resolving_power=None, exptime=None,
                  timeres=None, publisher_did=None,
                  facility=None, collection=None,
                  instrument=None, data_type=None,
                  calib_level=None, target_name=None,
                  res_format=None, maxrec=None,
                  **kwargs):
        """
        Use standard SIA2 attributes to query the IRSA SIA service.

        Parameters
        ----------
        _SIA2_PARAMETERS

        Returns
        -------
        Results in `~astropy.table.Table` format.

        """
        results = self.sia.search(
            pos=pos,
            band=band,
            time=time,
            pol=pol,
            field_of_view=field_of_view,
            spatial_resolution=spatial_resolution,
            spectral_resolving_power=spectral_resolving_power,
            exptime=exptime,
            timeres=timeres,
            publisher_did=publisher_did,
            facility=facility,
            collection=collection,
            instrument=instrument,
            data_type=data_type,
            calib_level=calib_level,
            target_name=target_name,
            res_format=res_format,
            maxrec=maxrec,
            **kwargs)

        return results.to_table()

    query_sia.__doc__ = query_sia.__doc__.replace('_SIA2_PARAMETERS', SIA2_PARAMETERS_DESC)

    def query_ssa(self, *, pos=None, radius=None, band=None, time=None, collection=None):
        """
        Use standard SSA attributes to query the IRSA SSA service.

        Parameters
        ----------
        pos : `~astropy.coordinates.SkyCoord` class or sequence of two floats
            the position of the center of the circular search region.
            assuming icrs decimal degrees if unit is not specified.
        raidus : `~astropy.units.Quantity` class or scalar float
            the radius of the circular region around pos in which to search.
            assuming icrs decimal degrees if unit is not specified.
        band : `~astropy.units.Quantity` class or sequence of two floats
            the bandwidth range the observations belong to.
            assuming meters if unit is not specified.
        time : `~astropy.time.Time` class or sequence of two strings
            the datetime range the observations were made in.
            assuming iso 8601 if format is not specified.
        collection : str
           Name of the collection that the data belongs to.

        Returns
        -------
        Results in `~astropy.table.Table` format.
        """

        if radius is None:
            diameter = None
        else:
            diameter = 2 * radius

        results = self.ssa.search(pos=pos, diameter=diameter, band=band, time=time,
                                  format='all', collection=collection)
        return results.to_table()

    def list_collections(self, *, servicetype=None, filter=None):
        """
        Return information of available IRSA SIAv2 collections to be used in ``query_sia`` queries.

        Parameters
        ----------
        servicetype : str or None
            Service type to list collections for. Returns all collections when not provided.
            Currently supported service types are: 'SIA', 'SSA'.
        filter : str or None
            If specified we only return collections then their collection_name
            contains the filter string.

        Returns
        -------
        collections : A `~astropy.table.Table` object.
            A table listing all the possible collections for IRSA SIA queries.
        """

        if not servicetype:
            query = "SELECT DISTINCT collection from caom.observation ORDER by collection"
        else:
            servicetype = servicetype.upper()
            if servicetype == 'SIA':
                query = ("SELECT DISTINCT o.collection FROM caom.observation o "
                         "JOIN caom.plane p ON o.obsid = p.obsid "
                         "WHERE (p.dataproducttype = 'image' OR p.dataproducttype = 'cube') "
                         "order by collection")
            elif servicetype == 'SSA':
                query = ("SELECT DISTINCT o.collection FROM caom.observation o "
                         "JOIN caom.plane p ON o.obsid = p.obsid "
                         "WHERE (p.dataproducttype = 'spectrum' OR p.dataproducttype = 'cube') "
                         "order by collection")
            else:
                raise ValueError("if specified, servicetype should be 'SIA' or 'SSA'")

        collections = self.query_tap(query=query).to_table()

        if filter:
            mask = [filter in collection for collection in collections['collection']]
            collections = collections[mask]
        return collections

    @deprecated_renamed_argument(("selcols", "cache", "verbose"), ("columns", None, None), since="0.4.7")
    def query_region(self, coordinates=None, *, catalog=None, spatial='Cone',
                     radius=10 * u.arcsec, width=None, polygon=None,
                     get_query_payload=False, columns='*', async_job=False,
                     verbose=False, cache=True):
        """
        Queries the IRSA TAP server around a coordinate and returns a `~astropy.table.Table` object.

        Parameters
        ----------
        coordinates : str, `astropy.coordinates` object
            Gives the position of the center of the cone or box if performing a cone or box search.
            Required if spatial is ``'Cone'`` or ``'Box'``. Ignored if spatial is ``'Polygon'`` or
            ``'All-Sky'``.
        catalog : str
            The catalog to be used. To list the available catalogs, use
            :meth:`~astroquery.ipac.irsa.IrsaClass.list_catalogs`.
        spatial : str
            Type of spatial query: ``'Cone'``, ``'Box'``, ``'Polygon'``, and
            ``'All-Sky'``. Defaults to ``'Cone'``.
        radius : str or `~astropy.units.Quantity` object, [optional for spatial is ``'Cone'``]
            The string must be parsable by `~astropy.coordinates.Angle`. The
            appropriate `~astropy.units.Quantity` object from
            `astropy.units` may also be used. Defaults to 10 arcsec.
        width : str, `~astropy.units.Quantity` object [Required for spatial is ``'Box'``.]
            The string must be parsable by `~astropy.coordinates.Angle`. The
            appropriate `~astropy.units.Quantity` object from `astropy.units`
            may also be used.
        polygon : list, [Required for spatial is ``'Polygon'``]
            A list of ``(ra, dec)`` pairs (as tuples), in decimal degrees,
            outlining the polygon to search in. It can also be a list of
            `astropy.coordinates` object or strings that can be parsed by
            `astropy.coordinates.ICRS`.
        get_query_payload : bool, optional
            If `True` then returns the dictionary sent as the HTTP request.
            Defaults to `False`.
        columns : str, optional
            Target column list with value separated by a comma(,)
        async_job : bool, optional
            if True query is run in asynchronous mode

        Returns
        -------
        table : A `~astropy.table.Table` object.
        """
        if catalog is None:
            raise InvalidQueryError("Catalog name is required!")

        adql = f'SELECT {columns} FROM {catalog}'

        spatial = spatial.lower()

        if spatial == 'all-sky' or spatial == 'allsky':
            where = ''
        elif spatial == 'polygon':
            try:
                coordinates_list = [parse_coordinates(coord).icrs for coord in polygon]
            except TypeError:
                # to handle the input cases that worked before
                try:
                    coordinates_list = [SkyCoord(*coord).icrs for coord in polygon]
                except u.UnitTypeError:
                    warnings.warn("Polygon endpoints are being interpreted as "
                                  "RA/Dec pairs specified in decimal degree units.")
                    coordinates_list = [SkyCoord(*coord, unit='deg').icrs for coord in polygon]

            coordinates_str = [f'{coord.ra.deg},{coord.dec.deg}' for coord in coordinates_list]
            where = (" WHERE CONTAINS(POINT('ICRS',ra,dec),"
                     f"POLYGON('ICRS',{','.join(coordinates_str)}))=1")
        else:
            coords_icrs = parse_coordinates(coordinates).icrs
            ra, dec = coords_icrs.ra.deg, coords_icrs.dec.deg

            if spatial == 'cone':
                if isinstance(radius, str):
                    radius = Angle(radius)
                where = (" WHERE CONTAINS(POINT('ICRS',ra,dec),"
                         f"CIRCLE('ICRS',{ra},{dec},{radius.to(u.deg).value}))=1")
            elif spatial == 'box':
                if isinstance(width, str):
                    width = Angle(width)
                where = (" WHERE CONTAINS(POINT('ICRS',ra,dec),"
                         f"BOX('ICRS',{ra},{dec},{width.to(u.deg).value},{width.to(u.deg).value}))=1")
            else:
                raise ValueError("Unrecognized spatial query type. Must be one of "
                                 "'Cone', 'Box', 'Polygon', or 'All-Sky'.")

        adql += where

        if get_query_payload:
            return adql
        response = self.query_tap(query=adql, async_job=async_job)

        return response.to_table()

    @deprecated_renamed_argument("cache", None, since="0.4.7")
    def list_catalogs(self, *, full=False, filter=None, cache=False):
        """
        Return information of available IRSA catalogs.

        Parameters
        ----------
        full : bool
            If True returns the full schema as a `~astropy.table.Table`.
            If False returns a dictionary of the table names and their description.
        filter : str or None
            If specified we only return catalogs when their catalog_name
            contains the filter string.
        """
        tap_tables = self.query_tap("SELECT * FROM TAP_SCHEMA.tables").to_table()

        if filter:
            mask = [filter in name for name in tap_tables['table_name']]
            tap_tables = tap_tables[mask]

        if full:
            return tap_tables
        else:
            return {tap_table['table_name']: tap_table['description'] for tap_table in tap_tables}

    @deprecated(since="0.4.10", alternative="list_catalogs")
    def print_catalogs(self):
        catalogs = self.list_catalogs()

        for catname in catalogs:
            print("{:30s}  {:s}".format(catname, catalogs[catname]))

    def list_columns(self, catalog, *, full=False):
        """
        Return list of columns of a given IRSA catalog.

        Parameters
        ----------
        catalog : str
            The name of the catalog.
        full : bool
            If True returns the full schema as a `~astropy.table.Table`.
            If False returns a dictionary of the column names and their description.
        """

        query = f"SELECT * from TAP_SCHEMA.columns where table_name='{catalog}'"

        column_table = self.query_tap(query).to_table()

        if full:
            return column_table
        else:
            return {column['column_name']: column['description'] for column in column_table}


Irsa = IrsaClass()
