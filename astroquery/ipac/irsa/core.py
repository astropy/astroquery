# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
IRSA
====


Module to query the IRSA archive.
"""

import warnings
from astropy.coordinates import SkyCoord
from astropy import units as u
from astropy.utils.decorators import deprecated_renamed_argument
from pyvo.dal.tap import TAPService
from astroquery import log
from astroquery.query import BaseQuery
from astroquery.utils.commons import parse_coordinates
from astroquery.ipac.irsa import conf
from astroquery.exceptions import InvalidQueryError


__all__ = ['Irsa', 'IrsaClass']


class IrsaClass(BaseQuery):

    def __init__(self):
        super().__init__()
        self.tap_url = conf.tap_url
        self._tap = None

    @property
    def tap(self):
        if not self._tap:
            self._tap = TAPService(baseurl=self.tap_url)
        return self._tap

    def query_tap(self, query, *, maxrec=None):
        """
        Send query to IRSA TAP. Results in `~pyvo.dal.TapResult` format.
        result.to_qtable in `~astropy.table.QTable` format

        Parameters
        ----------
        query : str
            ADQL query to be executed
        maxrec : int
            maximum number of records to return

        Return
        ------
        result : `~pyvo.dal.TapResult`
            TAP query result.
        result.to_table : `~astropy.table.Table`
            TAP query result as `~astropy.table.Table`
        result.to_qtable : `~astropy.table.QTable`
            TAP query result as `~astropy.table.QTable`

        """
        log.debug(f'TAP query: {query}')
        return self.tap.search(query, language='ADQL', maxrec=maxrec)
    def query_region(self, coordinates=None, *, catalog=None, spatial='Cone',
                     radius=10 * u.arcsec, width=None, polygon=None,
                     get_query_payload=False, selcols=None,
                     verbose=False, cache=True):
        """
        This function serves the same purpose as
        :meth:`~astroquery.ipac.irsa.IrsaClass.query_region`, but returns the raw
        HTTP response rather than the results in a `~astropy.table.Table`.

        Parameters
        ----------
        coordinates : str, `astropy.coordinates` object
            Gives the position of the center of the cone or box if
            performing a cone or box search. The string can give coordinates
            in various coordinate systems, or the name of a source that will
            be resolved on the server (see `here
            <https://irsa.ipac.caltech.edu/search_help.html>`_ for more
            details). Required if spatial is ``'Cone'`` or ``'Box'``. Optional
            if spatial is ``'Polygon'``.
        catalog : str
            The catalog to be used. To list the available catalogs, use
            :meth:`~astroquery.ipac.irsa.IrsaClass.print_catalogs`.
        spatial : str
            Type of spatial query: ``'Cone'``, ``'Box'``, ``'Polygon'``, and
            ``'All-Sky'``. If missing then defaults to ``'Cone'``.
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
        selcols : str, optional
            Target column list with value separated by a comma(,)
        verbose : bool, optional.
            If `True` then displays warnings when the returned VOTable does not
            conform to the standard. Defaults to `False`.
        cache : bool, optional
            Use local cache when set to `True`.

        Returns
        -------
        """
        if catalog is None:
            raise InvalidQueryError("Catalog name is required!")

        if selcols is None:
            columns = '*'
        else:
            columns = selcols

        adql = f'SELECT {columns} from {catalog}'

        coords_icrs = parse_coordinates(coordinates).icrs
        ra, dec = coords_icrs.ra.deg, coords_icrs.dec.deg

        if spatial == 'All-Sky':
            where = ''
        elif spatial == 'Cone':
            where = (" WHERE CONTAINS(POINT('ICRS',ra,dec),"
                     f"CIRCLE('ICRS',{ra},{dec},{radius.to(u.deg).value}))=1")
        elif spatial == 'Box':
            where = (" WHERE CONTAINS(POINT('ICRS',ra,dec),"
                     f"BOX('ICRS',{ra},{dec},{width.to(u.deg).value},{width.to(u.deg).value}))=1")
        elif spatial == 'Polygon':
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
            raise ValueError("Unrecognized spatial query type. Must be one of "
                             "'Cone', 'Box', 'Polygon', or 'All-Sky'.")

        adql += where

        if get_query_payload:
            return adql
        response = self.query_tap(query=adql)

        return response.to_table()

    def list_tap_tables(self):
        tap_tables = Irsa.query_tap("SELECT * FROM TAP_SCHEMA.tables")
        return tap_tables

    # TODO, deprecate this legacy in favour of full TAP table Table
    @deprecated_renamed_argument("cache", None, "0.4.7")
    def list_catalogs(self, cache=False):
        """
        Return a dictionary of IRSA catalogs.
        """
        tap_tables = Irsa.query_tap("SELECT * FROM TAP_SCHEMA.tables")
        return {tap_table['table_name']: tap_table['description'] for tap_table in tap_tables}

    # TODO, deprecate this as legacy
    def print_catalogs(self):
        catalogs = self.list_catalogs()
        for catname in catalogs:
            print("{:30s}  {:s}".format(catname, catalogs[catname]))


Irsa = IrsaClass()
