# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
LCOGT
====

API from

http://lcogtarchive.ipac.caltech.edu/docs/catsearch.html

The URL of the LCOGT catalog query service, CatQuery, is

 http://lcogtarchive.ipac.caltech.edu/cgi-bin/Gator/nph-query

The service accepts the following keywords, which are analogous to the search
fields on the Gator search form:


spatial     Required    Type of spatial query: Cone, Box, Polygon, and NONE

polygon                 Convex polygon of ra dec pairs, separated by comma(,)
                        Required if spatial=polygon

radius                  Cone search radius
                        Optional if spatial=Cone, otherwise ignore it
                        (default 10 arcsec)

radunits                Units of a Cone search: arcsec, arcmin, deg.
                        Optional if spatial=Cone
                        (default='arcsec')

size                    Width of a box in arcsec
                        Required if spatial=Box.

objstr                  Target name or coordinate of the center of a spatial
                        search center. Target names must be resolved by
                        SIMBAD or NED.

                        Required only when spatial=Cone or spatial=Box.

                        Examples: 'M31'
                                  '00 42 44.3 -41 16 08'
                                  '00h42m44.3s -41d16m08s'

catalog     Required    Catalog name in the LCOGT Archive. The database of
                        photometry can be found using lco_cat and the
                        database of image metadata is found using lco_img.

outfmt      Optional    Defines query's output format.
                        6 - returns a program interface in XML
                        3 - returns a VO Table (XML)
                        2 - returns SVC message
                        1 - returns an ASCII table
                        0 - returns Gator Status Page in HTML (default)

desc        Optional    Short description of a specific catalog, which will
                        appear in the result page.

order       Optional    Results ordered by this column.

selcols     Optional    Select specific columns to be returned. The default
                        action is to return all columns in the queried
                        catalog. To find the names of the columns in the
                        LCOGT Archive databases, please read Photometry
                        Table column descriptions
                        [http://lcogtarchive.ipac.caltech.edu/docs/lco_cat_dd.html]
                        and Image Table column descriptions
                        [http://lcogtarchive.ipac.caltech.edu/docs/lco_img_dd.html].

constraint  Optional    User defined query constraint(s)
                        Note: The constraint should follow SQL syntax.

"""
from __future__ import print_function, division

import warnings
import logging

import six
import astropy.units as u
import astropy.coordinates as coord
import astropy.io.votable as votable

from ..query import BaseQuery
from ..utils import commons, async_to_sync
from . import conf
from ..exceptions import TableParseError, NoResultsWarning

__all__ = ['Lcogt', 'LcogtClass']


@async_to_sync
class LcogtClass(BaseQuery):
    LCOGT_URL = conf.server
    TIMEOUT = conf.timeout
    ROW_LIMIT = conf.row_limit

    @property
    def catalogs(self):
        """ immutable catalog listing """
        return {'lco_cat': 'Photometry archive from LCOGT',
                'lco_img': 'Image metadata archive from LCOGT'}

    def query_object_async(self, objstr, catalog=None, cache=True,
                           get_query_payload=False):
        """
        Serves the same function as `query_object`, but
        only collects the response from the LCOGT IPAC archive and returns.

        Parameters
        ----------
        objstr : str
            name of object to be queried
        catalog : str
            name of the catalog to use. 'lco_img' for image meta data;
            'lco_cat' for photometry.

        Returns
        -------
        response : `requests.Response`
            Response of the query from the server
        """
        if catalog is None:
            raise ValueError("Catalogue name is required!")
        if catalog not in self.catalogs:
            raise ValueError("Catalog name must be one of {0}"
                             .format(self.catalogs))

        request_payload = self._args_to_payload(catalog)
        request_payload['objstr'] = objstr
        if get_query_payload:
            return request_payload

        response = self._request(method='GET', url=self.LCOGT_URL,
                                 params=request_payload, timeout=self.TIMEOUT,
                                 cache=cache)
        return response

    def query_region_async(self, coordinates=None, catalog=None,
                           spatial='Cone', radius=10 * u.arcsec, width=None,
                           polygon=None, get_query_payload=False, cache=True,
                           ):
        """
        This function serves the same purpose as
        :meth:`~astroquery.irsa.LcogtClass.query_region`, but returns the raw
        HTTP response rather than the results in a `~astropy.table.Table`.

        Parameters
        ----------
        coordinates : str, `astropy.coordinates` object
            Gives the position of the center of the cone or box if
            performing a cone or box search. The string can give coordinates
            in various coordinate systems, or the name of a source that will
            be resolved on the server (see `here
            <http://irsa.ipac.caltech.edu/search_help.html>`_ for more
            details). Required if spatial is ``'Cone'`` or ``'Box'``. Optional
            if spatial is ``'Polygon'``.
        catalog : str
            The catalog to be used. Either ``'lco_img'`` for image metadata or
            ``'lco_cat'`` for photometry.
        spatial : str
            Type of spatial query: ``'Cone'``, ``'Box'``, ``'Polygon'``, and
            ``'All-Sky'``. If missing then defaults to ``'Cone'``.
        radius : str or `~astropy.units.Quantity` object, [optional for \\
                spatial is ``'Cone'``]
            The string must be parsable by `~astropy.coordinates.Angle`. The
            appropriate `~astropy.units.Quantity` object from
            `astropy.units` may also be used. Defaults to 10 arcsec.
        width : str, `~astropy.units.Quantity` object [Required for spatial \\
                is ``'Polygon'``.]
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

        Returns
        -------
        response : `requests.Response`
            The HTTP response returned from the service
        """
        if catalog is None:
            raise ValueError("Catalogue name is required!")
        if catalog not in self.catalogs:
            raise ValueError("Catalog name must be one of {0}"
                             .format(self.catalogs))

        request_payload = self._args_to_payload(catalog)
        request_payload.update(self._parse_spatial(spatial=spatial,
                                                   coordinates=coordinates,
                                                   radius=radius, width=width,
                                                   polygon=polygon))

        if get_query_payload:
            return request_payload
        response = self._request(method='GET', url=self.LCOGT_URL,
                                 params=request_payload, timeout=self.TIMEOUT,
                                 cache=cache)
        return response

    def _parse_spatial(self, spatial, coordinates, radius=None, width=None,
                       polygon=None):
        """
        Parse the spatial component of a query

        Parameters
        ----------
        spatial : str
            The type of spatial query. Must be one of: ``'Cone'``, ``'Box'``,
            ``'Polygon'``, and ``'All-Sky'``.
        coordinates : str, `astropy.coordinates` object
            Gives the position of the center of the cone or box if
            performing a cone or box search. The string can give coordinates
            in various coordinate systems, or the name of a source that will
            be resolved on the server (see `here
            <http://irsa.ipac.caltech.edu/search_help.html>`_ for more
            details). Required if spatial is ``'Cone'`` or ``'Box'``. Optional
            if spatial is ``'Polygon'``.
        radius : str or `~astropy.units.Quantity` object, [optional for spatial is ``'Cone'``]
            The string must be parsable by `~astropy.coordinates.Angle`. The
            appropriate `~astropy.units.Quantity` object from `astropy.units`
            may also be used. Defaults to 10 arcsec.
        width : str, `~astropy.units.Quantity` object [Required for spatial is ``'Polygon'``.]
            The string must be parsable by `~astropy.coordinates.Angle`. The
            appropriate `~astropy.units.Quantity` object from `astropy.units`
            may also be used.
        polygon : list, [Required for spatial is ``'Polygon'``]
            A list of ``(ra, dec)`` pairs as tuples of
            `astropy.coordinates.Angle`s outlining the polygon to search in.
            It can also be a list of `astropy.coordinates` object or strings
            that can be parsed by `astropy.coordinates.ICRS`.

        Returns
        -------
        payload_dict : dict
        """

        request_payload = {}

        if spatial == 'All-Sky':
            spatial = 'NONE'
        elif spatial in ['Cone', 'Box']:
            if not commons._is_coordinate(coordinates):
                request_payload['objstr'] = coordinates
            else:
                request_payload['objstr'] = _parse_coordinates(coordinates)
            if spatial == 'Cone':
                radius = _parse_dimension(radius)
                request_payload['radius'] = radius.value
                request_payload['radunits'] = radius.unit.to_string()
            else:
                width = _parse_dimension(width)
                request_payload['size'] = width.to(u.arcsec).value
        elif spatial == 'Polygon':
            if coordinates is not None:
                request_payload['objstr'] = (
                    coordinates if not commons._is_coordinate(coordinates)
                    else _parse_coordinates(coordinates))
            try:
                coordinates_list = [_parse_coordinates(c) for c in polygon]
            except (ValueError, TypeError):
                coordinates_list = [_format_decimal_coords(*_pair_to_deg(pair))
                                    for pair in polygon]
            request_payload['polygon'] = ','.join(coordinates_list)
        else:
            raise ValueError("Unrecognized spatial query type. "
                             "Must be one of `Cone`, `Box`, "
                             "`Polygon`, or `All-Sky`.")

        request_payload['spatial'] = spatial

        return request_payload

    def _args_to_payload(self, catalog):
        """
        Sets the common parameters for all cgi -queries

        Parameters
        ----------
        catalog : str
            The name of the catalog to query.

        Returns
        -------
        request_payload : dict
        """
        request_payload = dict(catalog=catalog,
                               outfmt=3,
                               spatial=None,
                               outrows=Lcogt.ROW_LIMIT)
        return request_payload

    def _parse_result(self, response, verbose=False):
        """
        Parses the results form the HTTP response to `~astropy.table.Table`.

        Parameters
        ----------
        response : `requests.Response`
            The HTTP response object
        verbose : bool, optional
            Defaults to `False`. When true it will display warnings whenever
            the VOtable returned from the Service doesn't conform to the
            standard.

        Returns
        -------
        table : `~astropy.table.Table`
        """
        if not verbose:
            commons.suppress_vo_warnings()

        content = response.text
        logging.debug(content)

        # Check if results were returned
        if 'The catalog is not in the list' in content:
            raise Exception("Catalogue not found")

        # Check that object name was not malformed
        if 'Either wrong or missing coordinate/object name' in content:
            raise Exception("Malformed coordinate/object name")

        # Check that the results are not of length zero
        if len(content) == 0:
            raise Exception("The LCOGT server sent back an empty reply")

        # Read it in using the astropy VO table reader
        try:
            first_table = votable.parse(six.BytesIO(response.content),
                                        pedantic=False).get_first_table()
        except Exception as ex:
            self.response = response
            self.table_parse_error = ex
            raise TableParseError("Failed to parse LCOGT votable! The raw "
                                  " response can be found in self.response,"
                                  " and the error in self.table_parse_error.")

        # Convert to astropy.table.Table instance
        table = first_table.to_table()

        # Check if table is empty
        if len(table) == 0:
            warnings.warn("Query returned no results, so the table will "
                          "be empty", NoResultsWarning)

        return table

    def list_catalogs(self):
        """
        Return a dictionary of the catalogs in the LCOGT Gator tool.

        Returns
        -------
        catalogs : dict
            A dictionary of catalogs where the key indicates the catalog
            name to be used in query functions, and the value is the verbose
            description of the catalog.
        """
        return self.catalogs

    def print_catalogs(self):
        """
        Display a table of the catalogs in the LCOGT Gator tool.
        """
        for catname in self.catalogs:
            print("{:30s}  {:s}".format(catname, self.catalogs[catname]))


Lcogt = LcogtClass()


def _parse_coordinates(coordinates):
    # borrowed from commons.parse_coordinates as from_name wasn't required
    # in this case
    if isinstance(coordinates, six.string_types):
        try:
            c = coord.SkyCoord(coordinates, frame='icrs')
            warnings.warn("Coordinate string is being interpreted as an "
                          "ICRS coordinate.")
        except u.UnitsError as ex:
            warnings.warn("Only ICRS coordinates can be entered as strings\n"
                          "For other systems please use the appropriate "
                          "astropy.coordinates object")
            raise ex
    elif isinstance(coordinates, commons.CoordClasses):
        c = coordinates
    else:
        raise TypeError("Argument cannot be parsed as a coordinate")
    c_icrs = c.transform_to(coord.ICRS)
    formatted_coords = _format_decimal_coords(c_icrs.ra.degree,
                                              c_icrs.dec.degree)
    return formatted_coords


def _pair_to_deg(pair):
    """
    Turn a pair of floats, Angles, or Quantities into pairs of float degrees.
    """

    # unpack
    lon, lat = pair

    if hasattr(lon, 'degree') and hasattr(lat, 'degree'):
        pair = (lon.degree, lat.degree)
    elif hasattr(lon, 'to') and hasattr(lat, 'to'):
        pair = [lon, lat]
        for ii, ang in enumerate((lon, lat)):
            if ang.unit.is_equivalent(u.degree):
                pair[ii] = ang.to(u.degree).value
    else:
        warnings.warn("Polygon endpoints are being interpreted as RA/Dec "
                      "pairs specified in decimal degree units.")
    return tuple(pair)


def _format_decimal_coords(ra, dec):
    """
    Print *decimal degree* RA/Dec values in an IPAC-parseable form
    """
    return '{0} {1:+}'.format(ra, dec)


def _parse_dimension(dim):
    if (isinstance(dim, u.Quantity) and
            dim.unit in u.deg.find_equivalent_units()):
        if dim.unit not in ['arcsec', 'arcmin', 'deg']:
            dim = dim.to(u.degree)
    # otherwise must be an Angle or be specified in hours...
    else:
        try:
            new_dim = coord.Angle(dim)
            dim = u.Quantity(new_dim.degree, u.Unit('degree'))
        except (u.UnitsError, coord.errors.UnitsError, AttributeError):
            raise u.UnitsError("Dimension not in proper units")
    return dim
