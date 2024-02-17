# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
IRSA
====


Module to query the IRSA archive.
"""

import warnings
from astropy.coordinates import SkyCoord, Angle
from astropy import units as u
from astropy.utils.decorators import deprecated_renamed_argument

from pyvo.dal import TAPService

try:
    from pyvo.dal.sia2 import SIA2Service, SIA2_PARAMETERS_DESC
except ImportError:
    # Can be removed once min version of pyvo is 1.5
    from pyvo.dal.sia2 import SIA_PARAMETERS_DESC as SIA2_PARAMETERS_DESC
    from pyvo.dal.sia2 import SIAService as SIA2Service

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
        self.tap_url = conf.tap_url
        self._sia = None
        self._tap = None

    @property
    def sia(self):
        if not self._sia:
            self._sia = SIA2Service(baseurl=self.sia_url, session=self._session)
        return self._sia

    @property
    def tap(self):
        if not self._tap:
            self._tap = TAPService(baseurl=self.tap_url, session=self._session)
        return self._tap

    def query_tap(self, query, *, maxrec=None):
        """
        Send query to IRSA TAP. Results in `~pyvo.dal.TAPResults` format.
        result.to_qtable in `~astropy.table.QTable` format

        Parameters
        ----------
        query : str
            ADQL query to be executed
        maxrec : int
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
        log.debug(f'TAP query: {query}')
        return self.tap.search(query, language='ADQL', maxrec=maxrec)

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
        Results in `pyvo.dal.SIAResults` format.
        result.table in Astropy table format
        """
        return self.sia.search(
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

    # SIA2_PARAMETERS_DESC contains links that Sphinx can't resolve.
    # SIA2_PARAMETERS_DESC contains links that Sphinx can't resolve.
    for var in ('POLARIZATION_STATES', 'CALIBRATION_LEVELS'):
        SIA2_PARAMETERS_DESC = SIA2_PARAMETERS_DESC.replace(f'`pyvo.dam.obscore.{var}`',
                                                            f'pyvo.dam.obscore.{var}')
    query_sia.__doc__ = query_sia.__doc__.replace('_SIA2_PARAMETERS', SIA2_PARAMETERS_DESC)

    def list_collections(self):
        """
        Return information of available IRSA SIAv2 collections to be used in ``query_sia`` queries.

        Returns
        -------
        collections : A `~astropy.table.Table` object.
            A table listing all the possible collections for IRSA SIA queries.
        """
        query = "SELECT DISTINCT collection from caom.observation ORDER by collection"
        collections = self.query_tap(query=query)
        return collections.to_table()

    @deprecated_renamed_argument(("selcols", "cache", "verbose"), ("columns", None, None), since="0.4.7")
    def query_region(self, coordinates=None, *, catalog=None, spatial='Cone',
                     radius=10 * u.arcsec, width=None, polygon=None,
                     get_query_payload=False, columns='*',
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

        Returns
        -------
        table : A `~astropy.table.Table` object.
        """
        if catalog is None:
            raise InvalidQueryError("Catalog name is required!")

        adql = f'SELECT {columns} FROM {catalog}'

        if spatial == 'All-Sky':
            where = ''
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
            coords_icrs = parse_coordinates(coordinates).icrs
            ra, dec = coords_icrs.ra.deg, coords_icrs.dec.deg

            if spatial == 'Cone':
                if isinstance(radius, str):
                    radius = Angle(radius)
                where = (" WHERE CONTAINS(POINT('ICRS',ra,dec),"
                         f"CIRCLE('ICRS',{ra},{dec},{radius.to(u.deg).value}))=1")
            elif spatial == 'Box':
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
        response = self.query_tap(query=adql)

        return response.to_table()

    @deprecated_renamed_argument("cache", None, since="0.4.7")
    def list_catalogs(self, full=False, cache=False):
        """
        Return information of available IRSA catalogs.

        Parameters
        ----------
        full : bool
            If True returns the full schema VOTable. If False returns a dictionary of the table names and
            their description.
        """
        tap_tables = Irsa.query_tap("SELECT * FROM TAP_SCHEMA.tables")

        if full:
            return tap_tables
        else:
            return {tap_table['table_name']: tap_table['description'] for tap_table in tap_tables}

    # TODO, deprecate this as legacy
    def print_catalogs(self):
        catalogs = self.list_catalogs()

        for catname in catalogs:
            print("{:30s}  {:s}".format(catname, catalogs[catname]))


Irsa = IrsaClass()
