# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
IRSA
====

API from

 https://irsa.ipac.caltech.edu/applications/Gator/GatorAid/irsa/catsearch.html

The URL of the IRSA catalog query service, CatQuery, is

 https://irsa.ipac.caltech.edu/cgi-bin/Gator/nph-query

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

catalog     Required    Catalog name in the IRSA database management system.

selcols     Optional    Target column list with value separated by a comma(,)

                        The input list always overwrites default selections
                        defined by a data dictionary. Full lists of columns
                        can be found at the IRSA catalogs website, e.g.
                        https://irsa.ipac.caltech.edu/cgi-bin/Gator/nph-dd?catalog=allsky_4band_p1bs_psd
                        To access the full list of columns, press
                        the "Long Form" button at the top of the Columns
                        table.

outfmt      Optional    Defines query's output format.
                        6 - returns a program interface in XML
                        3 - returns a VO Table (XML)
                        2 - returns SVC message
                        1 - returns an ASCII table
                        0 - returns Gator Status Page in HTML (default)

desc        Optional    Short description of a specific catalog, which will
                        appear in the result page.

order       Optional    Results ordered by this column.

constraint  Optional    User defined query constraint(s)
                        Note: The constraint should follow SQL syntax.

onlist      Optional    1 - catalog is visible through Gator web interface
                        (default)

                        0 - catalog has been ingested into IRSA but not yet
                        visible through web interface.

                        This parameter will generally only be set to 0 when
                        users are supporting testing and evaluation of new
                        catalogs at IRSA's request.

If onlist=0, the following parameters are required:

    server              Symbolic DataBase Management Server (DBMS) name

    database            Name of Database.

    ddfile              The data dictionary file is used to get column
                        information for a specific catalog.

    selcols             Target column list with value separated by a comma(,)

                        The input list always overwrites default selections
                        defined by a data dictionary.

    outrows             Number of rows retrieved from database.

                        The retrieved row number outrows is always less than or
                        equal to available to be retrieved rows under the same
                        constraints.
"""


import warnings
import xml.etree.ElementTree as tree

import six
import astropy.units as u
import astropy.coordinates as coord
import astropy.io.votable as votable

from ..query import BaseQuery
from ..utils import commons
from . import conf
from ..exceptions import TableParseError, NoResultsWarning, InvalidQueryError


__all__ = ['Irsa', 'IrsaClass']


class IrsaClass(BaseQuery):
    IRSA_URL = conf.server
    GATOR_LIST_URL = conf.gator_list_catalogs
    TIMEOUT = conf.timeout
    ROW_LIMIT = conf.row_limit

    def query_region(self, coordinates=None, catalog=None, spatial='Cone',
                     radius=10 * u.arcsec, width=None, polygon=None,
                     get_query_payload=False, verbose=False, selcols=None):
        """
        This function can be used to perform either cone, box, polygon or
        all-sky search in the catalogs hosted by the NASA/IPAC Infrared
        Science Archive (IRSA).

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
            :meth:`~astroquery.irsa.IrsaClass.print_catalogs`.
        spatial : str
            Type of spatial query: ``'Cone'``, ``'Box'``, ``'Polygon'``, and
            ``'All-Sky'``. If missing then defaults to ``'Cone'``.
        radius : str or `~astropy.units.Quantity` object, [optional for spatial is ``'Cone'``]
            The string must be parsable by `~astropy.coordinates.Angle`. The
            appropriate `~astropy.units.Quantity` object from
            `astropy.units` may also be used. Defaults to 10 arcsec.
        width : str, `~astropy.units.Quantity` object [Required for spatial is ``'Polygon'``.]

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
        verbose : bool, optional.
            If `True` then displays warnings when the returned VOTable does not
            conform to the standard. Defaults to `False`.
        selcols : str, optional
            Target column list with value separated by a comma(,)


        Returns
        -------
        table : `~astropy.table.Table`
            A table containing the results of the query
        """
        response = self.query_region_async(coordinates, catalog=catalog,
                                           spatial=spatial, radius=radius,
                                           width=width, polygon=polygon,
                                           get_query_payload=get_query_payload,
                                           selcols=selcols)
        if get_query_payload:
            return response
        return self._parse_result(response, verbose=verbose)

    def query_region_async(self, coordinates=None, catalog=None,
                           spatial='Cone', radius=10 * u.arcsec, width=None,
                           polygon=None, get_query_payload=False,
                           selcols=None):
        """
        This function serves the same purpose as
        :meth:`~astroquery.irsa.IrsaClass.query_region`, but returns the raw
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
            :meth:`~astroquery.irsa.IrsaClass.print_catalogs`.
        spatial : str
            Type of spatial query: ``'Cone'``, ``'Box'``, ``'Polygon'``, and
            ``'All-Sky'``. If missing then defaults to ``'Cone'``.
        radius : str or `~astropy.units.Quantity` object, [optional for spatial is ``'Cone'``]
            The string must be parsable by `~astropy.coordinates.Angle`. The
            appropriate `~astropy.units.Quantity` object from
            `astropy.units` may also be used. Defaults to 10 arcsec.
        width : str, `~astropy.units.Quantity` object [Required for spatial is ``'Polygon'``.]
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

        Returns
        -------
        response : `requests.Response`
            The HTTP response returned from the service
        """
        if catalog is None:
            raise InvalidQueryError("Catalog name is required!")

        request_payload = self._args_to_payload(catalog, selcols=selcols)
        request_payload.update(self._parse_spatial(spatial=spatial,
                                                   coordinates=coordinates,
                                                   radius=radius, width=width,
                                                   polygon=polygon))

        if get_query_payload:
            return request_payload
        response = self._request("GET", url=Irsa.IRSA_URL,
                                 params=request_payload, timeout=Irsa.TIMEOUT)
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
            <https://irsa.ipac.caltech.edu/search_help.html>`_ for more
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
                if commons._is_coordinate(coordinates):
                    request_payload['objstr'] = _parse_coordinates(coordinates)
                else:
                    request_payload['objstr'] = coordinates
            try:
                coordinates_list = [_parse_coordinates(c) for c in polygon]
            except (ValueError, TypeError):
                coordinates_list = [_format_decimal_coords(*_pair_to_deg(pair))
                                    for pair in polygon]
            request_payload['polygon'] = ','.join(coordinates_list)
        else:
            raise ValueError("Unrecognized spatial query type. Must be one of "
                             "'Cone', 'Box', 'Polygon', or 'All-Sky'.")

        request_payload['spatial'] = spatial

        return request_payload

    def _args_to_payload(self, catalog, selcols=None):
        """
        Sets the common parameters for all cgi -queries

        Parameters
        ----------
        catalog : str
            The name of the catalog to query.
        selcols : str, optional
            Target column list with value separated by a comma(,)

        Returns
        -------
        request_payload : dict
        """
        if selcols is None:
            selcols = ''
        request_payload = dict(catalog=catalog,
                               outfmt=3,
                               outrows=Irsa.ROW_LIMIT,
                               selcols=selcols)
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

        # Check if results were returned
        if 'The catalog is not on the list' in content:
            raise ValueError("Invalid Catalog specified")

        # Check that object name was not malformed
        if 'Either wrong or missing coordinate/object name' in content:
            raise ValueError("Malformed coordinate/object name")

        # Check to see that output table size limit hasn't been exceeded
        if 'Exceeding output table size limit' in content:
            raise TableParseError("Exceeded output table size - reduce number "
                                  "of output columns and/or limit search area")

        # Check to see that the query engine is working
        if 'SQLConnect failed' in content:
            raise TimeoutError("The IRSA server is currently down")

        # Check that the results are not of length zero
        if len(content) == 0:
            warnings.warn("The IRSA server sent back an empty reply",
                          NoResultsWarning)

        # Read it in using the astropy VO table reader
        try:
            first_table = votable.parse(six.BytesIO(response.content),
                                        pedantic=False).get_first_table()
        except Exception as ex:
            self.response = response
            self.table_parse_error = ex
            raise TableParseError("Failed to parse IRSA votable! The raw "
                                  "response can be found in self.response, "
                                  "and the error in self.table_parse_error.")

        # Convert to astropy.table.Table instance
        table = first_table.to_table()

        # Check if table is empty
        if len(table) == 0:
            warnings.warn("Query returned no results, so the table will "
                          "be empty", NoResultsWarning)

        return table

    def list_catalogs(self):
        """
        Return a dictionary of the catalogs in the IRSA Gator tool.

        Returns
        -------
        catalogs : dict
            A dictionary of catalogs where the key indicates the catalog
            name to be used in query functions, and the value is the verbose
            description of the catalog.
        """
        response = self._request("GET", url=Irsa.GATOR_LIST_URL,
                                 params=dict(mode='xml'), timeout=Irsa.TIMEOUT)

        root = tree.fromstring(response.content)
        catalogs = {}
        for catalog in root.findall('catalog'):
            catname = catalog.find('catname').text
            desc = catalog.find('desc').text
            catalogs[catname] = desc
        return catalogs

    def print_catalogs(self):
        """
        Display a table of the catalogs in the IRSA Gator tool.
        """
        catalogs = self.list_catalogs()
        for catname in catalogs:
            print("{:30s}  {:s}".format(catname, catalogs[catname]))


Irsa = IrsaClass()


def _parse_coordinates(coordinates):
    # borrowed from commons.parse_coordinates as from_name wasn't required in
    # this case
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
    Turn a pair of floats, Angles, or Quantities into pairs of float
    degrees
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
        warnings.warn("Polygon endpoints are being interpreted as "
                      "RA/Dec pairs specified in decimal degree units.")
    return tuple(pair)


def _format_decimal_coords(ra, dec):
    """
    Print *decimal degree* RA/Dec values in an IPAC-parseable form
    """
    return '{0} {1:+}'.format(ra, dec)


def _parse_dimension(dim):
    if (isinstance(dim, u.Quantity) and dim.unit in u.deg.find_equivalent_units()):
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
