# Licensed under a 3-clause BSD style license - see LICENSE.rst


import os
import warnings
import json
import copy
import re

from io import BytesIO

import astropy.units as u
import astropy.coordinates as coord
import astropy.table as tbl
import astropy.utils.data as aud
from collections import OrderedDict
import astropy.io.votable as votable
from astropy.io import ascii, fits
from pyvo import registry

from ..query import BaseQuery
from ..utils import commons
from ..utils import async_to_sync
from ..utils import schema
from . import conf
from ..exceptions import TableParseError


__all__ = ['Vizier', 'VizierClass']


@async_to_sync
class VizierClass(BaseQuery):

    _str_schema = schema.Schema(str)
    _schema_columns = schema.Schema([_str_schema],
                                    error="columns must be a list of strings")
    _schema_ucd = schema.Schema(_str_schema, error="ucd must be string")
    _schema_column_filters = schema.Schema(
        {schema.Optional(_str_schema): _str_schema},
        error=("column_filters must be a dictionary where both keys "
               "and values are strings"))
    _schema_catalog = schema.Schema(
        schema.Or([_str_schema], _str_schema, None),
        error="catalog must be a list of strings or a single string")

    def __init__(self, *, columns=["*"], column_filters={}, catalog=None,
                 keywords=None, ucd="", timeout=conf.timeout,
                 vizier_server=conf.server, row_limit=conf.row_limit):
        """
        Parameters
        ----------
        columns : list
            List of strings
        column_filters : dict
        catalog : str or None
        keywords : str or None
        ucd : string
            "Unified Content Description" column descriptions.  Specifying
            these will select only catalogs that have columns matching the
            column descriptions defined on the Vizier web pages.
            See https://vizier.cds.unistra.fr/vizier/vizHelp/1.htx#ucd and
            https://vizier.cds.unistra.fr/vizier/doc/UCD/
        vizier_server : string
            Name of the VizieR mirror to use.
            (This parameter's default is set from a configuration object.)
        timeout : number
            timeout for connecting to server
            (This parameter's default is set from a configuration object.)
        row_limit : int
            Maximum number of rows that will be fetched from the result
            (set to -1 for unlimited).
            (This parameter's default is set from a configuration object.)
        """

        super().__init__()
        self.columns = columns
        self.column_filters = column_filters
        self.catalog = catalog
        self._keywords = None
        self.ucd = ucd
        if keywords:
            self.keywords = keywords
        self.TIMEOUT = timeout
        self.VIZIER_SERVER = vizier_server
        self.ROW_LIMIT = row_limit

    @property
    def columns(self):
        """ Columns to include.  The special keyword 'all' will return ALL
        columns from ALL retrieved tables. """
        # columns need to be immutable but still need to be a list
        return list(tuple(self._columns))

    @columns.setter
    def columns(self, values):
        self._columns = VizierClass._schema_columns.validate(values)

    @property
    def column_filters(self):
        """
        Filters to run on the individual columns. See the Vizier website
        for details.
        """
        return self._column_filters

    @column_filters.setter
    def column_filters(self, values):
        self._column_filters = (
            VizierClass._schema_column_filters.validate(values))

    @property
    def catalog(self):
        """
        The default catalog to search.  If left empty, will search all
        catalogs.
        """
        return self._catalog

    @catalog.setter
    def catalog(self, values):
        self._catalog = VizierClass._schema_catalog.validate(values)

    @property
    def ucd(self):
        """
        UCD criteria: see https://vizier.cds.unistra.fr/vizier/vizHelp/1.htx#ucd

        Examples
        --------
        >>> Vizier.ucd = '(spect.dopplerVeloc*|phys.veloc*)'
        """
        return self._ucd

    @ucd.setter
    def ucd(self, values):
        self._ucd = VizierClass._schema_ucd.validate(values)

    def _server_to_url(self, return_type='votable'):
        """
        Not generally meant to be modified, but there are different valid
        return types supported by Vizier, listed here:
        https://vizier.cds.unistra.fr/doc/asu-summary.htx

        HTML: VizieR
        votable: votable
        tab-separated-values: asu-tsv
        FITS ascii table: asu-fits
        FITS binary table: asu-binfits
        plain text: asu-txt
        """

        # Only votable is supported now, but in case we try to support
        # something in the future we should disallow invalid ones.
        assert return_type in ('votable', 'asu-tsv', 'asu-fits',
                               'asu-binfits', 'asu-txt')
        if return_type in ('asu-txt',):
            # I had a look at the format of these "tables" and... they just
            # aren't.  They're quasi-fixed-width without schema.  I think they
            # follow the general philosophy of "consistency is overrated"
            # The CDS reader chokes on it.
            raise TypeError("asu-txt is not and cannot be supported: the "
                            "returned tables are not and cannot be made "
                            "parseable.")
        return "https://" + self.VIZIER_SERVER + "/viz-bin/" + return_type

    @property
    def keywords(self):
        """The set of keywords to filter the Vizier search"""
        return self._keywords

    @keywords.setter
    def keywords(self, value):
        self._keywords = VizierKeyword(value)

    @keywords.deleter
    def keywords(self):
        self._keywords = None

    def find_catalogs(self, keywords, *, include_obsolete=False, verbose=False,
                      max_catalogs=None, return_type='votable'):
        """
        Search Vizier for catalogs based on a set of keywords, e.g. author name

        Parameters
        ----------
        keywords : list or string
            List of keywords, or space-separated set of keywords.
            From `Vizier <https://vizier.cds.unistra.fr/doc/asu-summary.htx>`_:
            "names or words of title of catalog. The words are and'ed, i.e.
            only the catalogues characterized by all the words are selected."
        include_obsolete : bool, optional
            If set to True, catalogs marked obsolete will also be returned.
        max_catalogs : int or None
            The maximum number of catalogs to return.  If ``None``, all
            catalogs will be returned.

        Returns
        -------
        resource_dict : dict
            Dictionary of the "Resource" name and the VOTable resource object.
            "Resources" are generally publications; one publication may contain
            many tables.

        Examples
        --------
        >>> from astroquery.vizier import Vizier
        >>> catalog_list = Vizier.find_catalogs('Kang W51') # doctest: +REMOTE_DATA +IGNORE_WARNINGS
        >>> catalog_list # doctest: +REMOTE_DATA +IGNORE_OUTPUT
        OrderedDict([('J/ApJ/684/1143', </>), ('J/ApJ/736/87', </>) ... ])
        >>> print({k:v.description for k,v in catalog_list.items()}) # doctest: +REMOTE_DATA +IGNORE_OUTPUT
        {'J/ApJ/684/1143': 'BHB candidates in the Milky Way (Xue+, 2008)',
         'J/ApJ/736/87': 'Abundances in G-type stars with exoplanets (Kang+, 2011)',
         'J/ApJ/738/79': "SDSS-DR8 BHB stars in the Milky Way's halo (Xue+, 2011)",
         'J/ApJ/760/12': 'LIGO/Virgo gravitational-wave (GW) bursts with GRBs (Abadie+, 2012)',
         ...}
        """

        if isinstance(keywords, list):
            keywords = " ".join(keywords)

        data_payload = {'-words': keywords, '-meta.all': 1}

        data_payload['-ucd'] = self.ucd

        if max_catalogs is not None:
            data_payload['-meta.max'] = max_catalogs
        response = self._request(
            method='POST', url=self._server_to_url(return_type=return_type),
            data=data_payload, timeout=self.TIMEOUT)

        if 'STOP, Max. number of RESOURCE reached' in response.text:
            raise ValueError("Maximum number of catalogs exceeded.  Try "
                             "setting max_catalogs to a large number and"
                             " try again")
        result = self._parse_result(response, verbose=verbose,
                                    get_catalog_names=True)

        # Filter out the obsolete catalogs, unless requested
        if include_obsolete is False:
            for key in list(result):
                for info in result[key].infos:
                    if (info.name == 'status') and (info.value == 'obsolete'):
                        del result[key]

        return result

    def get_catalogs_async(self, catalog, *, verbose=False, return_type='votable',
                           get_query_payload=False):
        """
        Query the Vizier service for a specific catalog

        Parameters
        ----------
        catalog : str, Resource, or list, optional
            The catalog(s) that will be retrieved

        Returns
        -------
        response : `~requests.Response`
            Returned if asynchronous method used
        """

        if not isinstance(catalog, (str, votable.tree.Resource)):
            catalog = list(catalog)
        data_payload = self._args_to_payload(catalog=catalog)
        if get_query_payload:
            return data_payload

        response = self._request(
            method='POST', url=self._server_to_url(return_type=return_type),
            data=data_payload, timeout=self.TIMEOUT)

        return response

    def get_catalog_metadata(self, *, catalog=None, get_query_payload=False):
        """Get a VizieR's catalog metadata.

        Parameters
        ----------
        catalog : str, optional
            The catalog identifier. It usually looks like 'III/55' for big surveys
            or 'J/ApJ/811/67' for catalogs linked to a published paper. When this
            parameter is not provided, the function looks for the metadata of the
            catalog property of the Vizier class instance
            (`~astroquery.vizier.VizierClass.catalog`).
        get_query_payload : bool, optional
            When True, returns the dict of HTTP request parameters. This does not
            execute the search for metadata.

        Returns
        -------
        `~astropy.table.Table`
            A table with the following columns:
            - title
            - authors
            - abstract (the abstract of the article, modified to explain the data
            more specifically)
            - origin_article (the bibcode of the associated article)
            - webpage (a link to VizieR, contains more information about the catalog)
            - created (date of creation of the catalog *in VizieR*)
            - updated (date of the last modification applied to the entry,
            this is often metadata, with no appearance in the history tap on the
            webpage but sometimes also data erratum, which will appear in the
            history tab)
            - waveband
            - doi (the catalog doi when it exists)

        Examples
        --------
        >>> from astroquery.vizier import Vizier
        >>> Vizier(catalog="I/324").get_catalog_metadata() # doctest: +REMOTE_DATA
        <Table length=1>
                       title                        authors         ... waveband  doi
                       object                        object         ...  object  object
        ----------------------------------- ----------------------- ... -------- ------
        The Initial Gaia Source List (IGSL) Smart R.L.; Nicastro L. ...              --

        >>> from astroquery.vizier import Vizier
        >>> Vizier.get_catalog_metadata(catalog="J/ApJS/173/185") # doctest: +REMOTE_DATA
        <Table length=1>
                          title                    ...              doi
                          object                   ...              object
        ------------------------------------------ ... --------------------------------
        GALEX ultraviolet atlas of nearby galaxies ... doi:10.26093/cds/vizier.21730185
        """
        # searches the instance catalog property if the keyword argument is not provided
        if not catalog:
            catalog = self.catalog
        if not catalog:
            raise ValueError("No catalog name was provided.")
        query = f"""SELECT TOP 1 res_title as title,
                creator_seq as authors,
                res_description as abstract,
                source_value as origin_article,
                reference_url as webpage,
                created, updated,
                waveband,
                alt_identifier as doi
                FROM rr.resource NATURAL LEFT OUTER JOIN rr.capability
                NATURAL LEFT OUTER JOIN rr.interface
                NATURAL LEFT OUTER JOIN rr.alt_identifier
                WHERE ivoid = 'ivo://cds.vizier/{catalog.lower()}'"""
        metadata = registry.regtap.RegistryQuery(registry.regtap.REGISTRY_BASEURL, query)
        if get_query_payload:
            return metadata
        result = metadata.execute().to_table()
        # apply mask if the `alt_identifier` value is not a doi
        result["doi"].mask = True if "doi:" not in result["doi"][0] else False
        return result

    def query_object_async(self, object_name, *, catalog=None, radius=None,
                           coordinate_frame=None, get_query_payload=False,
                           return_type='votable', cache=True):
        """
        Serves the same purpose as `query_object` but only
        returns the HTTP response rather than the parsed result.

        Parameters
        ----------
        object_name : str
            The name of the identifier.
        catalog : str or list, optional
            The catalog(s) which must be searched for this identifier.
            If not specified, all matching catalogs will be searched.
        radius : `~astropy.units.Quantity` or None
            A degree-equivalent radius (optional).
        coordinate_system : str or None
            If the object name is given as a coordinate, you *should* use
            `~astroquery.vizier.VizierClass.query_region`, but you can
            specify a coordinate frame here instead (today, J2000, B1975,
            B1950, B1900, B1875, B1855, Galactic, Supergal., Ecl.J2000, )
        cache : bool
            Defaults to True. If set overrides global caching behavior.
            See :ref:`caching documentation <astroquery_cache>`.

        Returns
        -------
        response : `~requests.Response`
            The response of the HTTP request.

        """
        catalog = VizierClass._schema_catalog.validate(catalog)
        if radius is None:
            center = {'-c': object_name}
        else:
            radius_arcmin = radius.to(u.arcmin).value
            cframe = (coordinate_frame if coordinate_frame in
                      ["today", "J2000", "B1975", "B1950", "B1900", "B1875",
                       "B1855", "Galactic", "Supergal.", "Ecl.J2000"]
                      else 'J2000')

            center = {'-c': object_name, '-c.u': 'arcmin', '-c.geom': 'r',
                      '-c.r': radius_arcmin, '-c.eq': cframe}

        data_payload = self._args_to_payload(
            center=center,
            catalog=catalog)
        if get_query_payload:
            return data_payload
        response = self._request(
            method='POST', url=self._server_to_url(return_type=return_type),
            data=data_payload, timeout=self.TIMEOUT, cache=cache)
        return response

    def query_region_async(self, coordinates, *, radius=None, inner_radius=None,
                           width=None, height=None, catalog=None,
                           get_query_payload=False, cache=True,
                           return_type='votable', column_filters={},
                           frame='fk5'):
        """
        Serves the same purpose as `query_region` but only
        returns the HTTP response rather than the parsed result.

        At least one of ``radius`` or ``width`` must be specified.

        Parameters
        ----------
        coordinates : str, `astropy.coordinates` object, or `~astropy.table.Table`
            The target around which to search. It may be specified as a
            string in which case it is resolved using online services or as
            the appropriate `astropy.coordinates` object. ICRS coordinates
            may also be entered as a string.  If a table is used, each of
            its rows will be queried, as long as it contains two columns
            named ``_RAJ2000`` and ``_DEJ2000`` with proper angular units.
        radius : convertible to `~astropy.coordinates.Angle`
            The radius of the circular region to query.
        inner_radius : convertible to `~astropy.coordinates.Angle`
            When set in addition to ``radius``, the queried region becomes
            annular, with outer radius ``radius`` and inner radius
            ``inner_radius``.
        width : convertible to `~astropy.coordinates.Angle`
            The width of the square region to query.
        height : convertible to `~astropy.coordinates.Angle`
            When set in addition to ``width``, the queried region becomes
            rectangular, with the specified ``width`` and ``height``.
        catalog : str or list, optional
            The catalog(s) which must be searched for this identifier.
            If not specified, all matching catalogs will be searched.
        column_filters: dict, optional
            Constraints on columns of the result. The dictionary contains
            the column name as keys, and the constraints as values.
        frame : str, optional
            The frame to use for the request. It should be 'fk5', 'icrs',
            or 'galactic'. This choice influences the the orientation of
            box requests.
        cache : bool
            Defaults to True. If set overrides global caching behavior.
            See :ref:`caching documentation <astroquery_cache>`.

        Returns
        -------
        response : `requests.Response`
            The response of the HTTP request.

        """
        if frame not in ('galactic', 'fk5', 'icrs'):
            raise ValueError("Only the 'galactic', 'icrs', and 'fk5' frames are supported by VizieR")
        catalog = VizierClass._schema_catalog.validate(catalog)
        center = {}
        columns = []

        # Process coordinates
        if isinstance(coordinates, (commons.CoordClasses, str)):
            target = commons.parse_coordinates(coordinates).transform_to(frame)

            if not target.isscalar:
                center["-c"] = []
                for pos in target:
                    if frame == 'galactic':
                        glon_deg = pos.l.to_string(unit="deg", decimal=True, precision=8)
                        glat_deg = pos.b.to_string(unit="deg", decimal=True, precision=8,
                                                   alwayssign=True)
                        center["-c"] += ["G{}{}".format(glon_deg, glat_deg)]
                    else:
                        ra_deg = pos.ra.to_string(unit="deg", decimal=True, precision=8)
                        dec_deg = pos.dec.to_string(unit="deg", decimal=True,
                                                    precision=8, alwayssign=True)
                        center["-c"] += ["{}{}".format(ra_deg, dec_deg)]
                columns += ["_q"]  # Always request reference to input table
            else:
                if frame == 'galactic':
                    glon = target.l.to_string(unit='deg', decimal=True, precision=8)
                    glat = target.b.to_string(unit="deg", decimal=True, precision=8,
                                              alwayssign=True)
                    center["-c"] = "G{glon}{glat}".format(glon=glon, glat=glat)
                else:
                    ra = target.ra.to_string(unit='deg', decimal=True, precision=8)
                    dec = target.dec.to_string(unit="deg", decimal=True, precision=8,
                                               alwayssign=True)
                    center["-c"] = "{ra}{dec}".format(ra=ra, dec=dec)
        elif isinstance(coordinates, tbl.Table):
            if (("_RAJ2000" in coordinates.keys()) and ("_DEJ2000" in
                                                        coordinates.keys())):
                center["-c"] = []
                sky_coord = coord.SkyCoord(coordinates["_RAJ2000"],
                                           coordinates["_DEJ2000"],
                                           unit=(coordinates["_RAJ2000"].unit,
                                                 coordinates["_DEJ2000"].unit))
                for (ra, dec) in zip(sky_coord.ra, sky_coord.dec):
                    ra_deg = ra.to_string(unit="deg", decimal=True,
                                          precision=8)
                    dec_deg = dec.to_string(unit="deg", decimal=True,
                                            precision=8, alwayssign=True)
                    center["-c"] += ["{}{}".format(ra_deg, dec_deg)]
                columns += ["_q"]  # Always request reference to input table
            else:
                raise ValueError("Table must contain '_RAJ2000' and "
                                 "'_DEJ2000' columns!")
        else:
            raise TypeError("Coordinates must be one of: string, astropy "
                            "coordinates, or table containing coordinates!")

        if radius is not None:
            if inner_radius is None:
                _, unit_str, o_radius = _parse_angle(radius)
                center["-c.r" + unit_str] = str(o_radius)
            else:
                unit, unit_str, i_radius = _parse_angle(inner_radius)
                o_radius = coord.Angle(radius).to_value(unit)
                center["-c.r" + unit_str] = f"{i_radius},{o_radius}"
        elif width is not None:
            unit, unit_str, w_box = _parse_angle(width)
            h_box = w_box if height is None else coord.Angle(height).to_value(unit)
            center["-c.b" + unit_str] = f"{w_box}x{h_box}"
        else:
            raise Exception(
                "At least one of radius, width/height must be specified")

        # Prepare payload
        data_payload = self._args_to_payload(center=center, columns=columns,
                                             catalog=catalog, column_filters=column_filters)

        if get_query_payload:
            return data_payload

        response = self._request(
            method='POST', url=self._server_to_url(return_type=return_type),
            data=data_payload, timeout=self.TIMEOUT, cache=cache)
        return response

    def query_constraints_async(self, *, catalog=None, return_type='votable',
                                cache=True, get_query_payload=False,
                                **kwargs):
        """
        Send a query to Vizier in which you specify constraints with
        keyword/value pairs.

        See `the vizier constraints page
        <https://vizier.cds.unistra.fr/vizier/vizHelp/syntax.htx>`_ for details.

        Parameters
        ----------
        catalog : str or list, optional
            The catalog(s) which must be searched for this identifier.
            If not specified, all matching catalogs will be searched.
        kwargs : dict
            Any key/value pairs besides "catalog" will be parsed
            as additional column filters.
        cache : bool
            Defaults to True. If set overrides global caching behavior.
            See :ref:`caching documentation <astroquery_cache>`.

        Returns
        -------
        response : `requests.Response`
            The response of the HTTP request.

        Examples
        --------
        >>> from astroquery.vizier import Vizier
        >>> # note that glon/glat constraints here *must* be floats
        >>> result = Vizier(row_limit=3).query_constraints(catalog='J/ApJ/723/492/table1',
        ...                                   GLON='>49.0 & <51.0', GLAT='<0.0') # doctest: +REMOTE_DATA
        >>> result[result.keys()[0]].pprint() # doctest: +REMOTE_DATA
            GRSMC      GLON   GLAT   VLSR   DelV  ... alpha  Note RD09 _RA.icrs _DE.icrs
                       deg    deg   km / s km / s ...                    deg      deg
        ------------- ------ ------ ------ ------ ... ------ ---- ---- -------- --------
        G049.49-00.41  49.49  -0.41  56.90   9.12 ...   0.73    i RD09 290.9536  14.4992
        G049.39-00.26  49.39  -0.26  50.94   3.51 ...   0.16    i RD09 290.7682  14.4819
        G049.44-00.06  49.44  -0.06  62.00   3.67 ...   0.17    i RD09 290.6104  14.6203
        """

        catalog = VizierClass._schema_catalog.validate(catalog)
        data_payload = self._args_to_payload(
            catalog=catalog,
            column_filters=kwargs,
            center={'-c.rd': 180})
        if get_query_payload:
            return data_payload
        response = self._request(
            method='POST', url=self._server_to_url(return_type=return_type),
            data=data_payload, timeout=self.TIMEOUT, cache=cache)
        return response

    def _args_to_payload(self, *args, **kwargs):
        """
        accepts the arguments for different query functions and
        builds a script suitable for the Vizier votable CGI.
        """
        body = OrderedDict()
        center = kwargs.get('center')
        # process: catalog
        catalog = kwargs.get('catalog') or self.catalog

        if catalog is not None:
            if isinstance(catalog, str):
                body['-source'] = catalog
            elif isinstance(catalog, list):
                catalog = [item.name if hasattr(item, 'name') else item
                           for item in catalog]
                body['-source'] = ",".join(catalog)
            elif hasattr(catalog, 'name'):
                # this is probably a votable Resource, but no harm in duck-typing on `name`
                body['-source'] = catalog.name
            else:
                raise TypeError("Catalog must be specified as list, string, or Resource")

        # take row_limit in account
        body['-out.max'] = self.ROW_LIMIT

        # process: columns
        columns = kwargs.get('columns', copy.copy(self.columns))

        if columns is not None:
            columns = self.columns + columns
            # filter columns to _unique_ columns, preserving order in python >3.6
            # note that "set" does not preserve order, but dict.keys does
            columns = list(dict.fromkeys(columns, ).keys())

        # special keywords need to be treated separately
        # keyword names that can mean 'all'
        alls = ['all', '**']
        if any(x in columns for x in alls):
            columns_all = True
            for x in alls:
                if x in columns:
                    columns.remove(x)
            body['-out.all'] = None
        else:
            columns_all = False

        # process: columns - identify sorting requests
        columns_out = []
        sorts_out = []
        for column in columns:
            if column[0] == '+':
                columns_out += [column[1:]]
                sorts_out += [column[1:]]
            elif column[0] == '-':
                columns_out += [column[1:]]
                sorts_out += [column]
            else:
                columns_out += [column]

        # calculated keyword names that start with an underscore
        columns_calc = []
        for column in columns_out:
            if column[0] == '_':
                columns_calc.append(column)
        for column in columns_calc:
            columns_out.remove(column)

        if columns_out and not columns_all:
            body['-out'] = ','.join(columns_out)

        if columns_calc:
            body['-out.add'] = ','.join(columns_calc)

        if len(sorts_out) > 0:
            body['-sort'] = ','.join(sorts_out)

        # process: maximum rows returned
        row_limit = kwargs.get('row_limit') or self.ROW_LIMIT
        if row_limit < 0:
            body["-out.max"] = 'unlimited'
        else:
            body["-out.max"] = row_limit
        # process: column filters
        column_filters = self.column_filters.copy()
        column_filters.update(kwargs.get('column_filters', {}))
        for (key, value) in column_filters.items():
            body[key] = value
        # process: center
        if center is not None:
            for (key, value) in center.items():
                body[key] = value
        # add column metadata: name, unit, UCD1+, and description
        body["-out.meta"] = "huUD"
        # merge tables when a list is queried against a single catalog
        body["-out.form"] = "mini"
        # computed position should always be in decimal degrees
        body["-oc.form"] = "d"

        ucd = kwargs.get('ucd', "") + self.ucd
        if ucd:
            body['-ucd'] = ucd

        # create final script starting with keywords
        script = []
        if (not isinstance(self.keywords, property)
                and self.keywords is not None):
            script += [str(self.keywords)]
        # add all items that are not lists
        for key, val in body.items():
            if type(val) is not list:
                if val:
                    script += ["{key}={val}".format(key=key, val=val)]
                else:
                    script += [key]
        # add list at the end
        for key, val in body.items():
            if type(val) is list:
                script += ["{key}=<<====AstroqueryList".format(key=key)]
                script += val
                script += ["====AstroqueryList"]
        # merge result
        return "\n".join(script)

    def _parse_result(self, response, *, get_catalog_names=False, verbose=False,
                      invalid='warn'):
        """
        Parses the HTTP response to create a `~astropy.table.Table`.

        Returns the raw result as a string in case of parse errors.

        Parameters
        ----------
        response : `requests.Response`
            The response of the HTTP POST request
        get_catalog_names : bool
            (only for VOTABLE queries)
            If specified, return only the table names (useful for table
            discovery).
        invalid : 'warn', 'mask' or 'exception'
            (only for VOTABLE queries)
            The behavior if a VOTABLE cannot be parsed. The default is
            'warn', which will try to parse the table, but if an
            exception is raised during parsing, the exception will be
            issued as a warning instead and a masked table will be
            returned. A value of 'exception' will not catch the
            exception, while a value of 'mask' will simply always mask
            invalid values.

        Returns
        -------
        table_list : `astroquery.utils.TableList` or str
            If there are errors in the parsing, then returns the raw results
            as a string.

        """
        if response.content[:5] == b'<?xml':
            try:
                return _parse_vizier_votable(
                    response.content, verbose=verbose, invalid=invalid,
                    get_catalog_names=get_catalog_names)
            except Exception as ex:
                self.response = response
                self.table_parse_error = ex
                raise TableParseError("Failed to parse VIZIER result! The "
                                      "raw response can be found in "
                                      "self.response, and the error in "
                                      "self.table_parse_error. The attempted "
                                      "parsed result is in "
                                      "self.parsed_result.\n Exception: "
                                      + str(self.table_parse_error))
        elif response.content[:5] == b'#\n#  ':
            return _parse_vizier_tsvfile(response.content, verbose=verbose)
        elif response.content[:6] == b'SIMPLE':
            return fits.open(BytesIO(response.content),
                             ignore_missing_end=True)

    @property
    def valid_keywords(self):
        if not hasattr(self, '_valid_keyword_dict'):
            file_name = aud.get_pkg_data_filename(
                os.path.join("data", "inverse_dict.json"))
            with open(file_name, 'r') as f:
                kwd = json.load(f)
                self._valid_keyword_types = sorted(kwd.values())
                self._valid_keyword_dict = OrderedDict([(k, kwd[k])
                                                        for k in sorted(kwd)])

        return self._valid_keyword_dict


def _parse_vizier_tsvfile(data, *, verbose=False):
    """
    Parse a Vizier-generated list of tsv data tables into a list of astropy
    Tables.

    Parameters
    ----------
    data : response content bytes
       Bytes containing the vizier-formatted list of tables
    """

    # http://stackoverflow.com/questions/4664850/find-all-occurrences-of-a-substring-in-python
    split_indices = [m.start() for m in re.finditer(b'\n\n#', data)]
    # we want to slice out chunks of the file each time
    split_limits = zip(split_indices[:-1], split_indices[1:])
    tables = [ascii.read(BytesIO(data[a:b]), format='fast_tab', delimiter='\t',
                         header_start=0, comment="#") for
              a, b in split_limits]
    return tables


def _parse_vizier_votable(data, *, verbose=False, invalid='warn',
                          get_catalog_names=False):
    """
    Given a votable as string, parse it into dict or tables
    """
    if not verbose:
        commons.suppress_vo_warnings()

    tf = BytesIO(data)

    if invalid == 'mask':
        vo_tree = votable.parse(tf, verify='warn', invalid='mask')
    elif invalid == 'warn':
        try:
            vo_tree = votable.parse(tf, verify='warn', invalid='exception')
        except Exception as ex:
            warnings.warn("VOTABLE parsing raised exception: {0}".format(ex))
            vo_tree = votable.parse(tf, verify='warn', invalid='mask')
    elif invalid == 'exception':
        vo_tree = votable.parse(tf, verify='warn', invalid='exception')
    else:
        raise ValueError("Invalid keyword for 'invalid'. "
                         "Must be exception, mask, or warn")

    if get_catalog_names:
        return OrderedDict([(R.name, R) for R in vo_tree.resources])
    else:
        table_dict = OrderedDict()
        for t in vo_tree.iter_tables():
            if len(t.array) > 0:
                if t.ref is not None:
                    name = vo_tree.get_table_by_id(t.ref).name
                else:
                    name = t.name
                if name not in table_dict.keys():
                    table_dict[name] = []
                table_dict[name] += [t.to_table()]
        for name in table_dict.keys():
            if len(table_dict[name]) > 1:
                table_dict[name] = tbl.vstack(table_dict[name])
            else:
                table_dict[name] = table_dict[name][0]
        return commons.TableList(table_dict)


def _parse_angle(angle):
    """
    Returns the Vizier-formatted units and values for box/radius
    dimensions in case of region queries.

    Parameters
    ----------
    angle : convertible to `astropy.coordinates.Angle`

    Returns
    -------
    (unit, unit_str, value) : tuple
    """
    angle = coord.Angle(angle)
    if angle.unit is u.arcsec:
        return u.arcsec, "s", angle.value
    elif angle.unit is u.arcmin:
        return u.arcmin, "m", angle.value
    else:
        return u.deg, "d", angle.to_value(u.deg)


class VizierKeyword(list):

    """Helper class for setting keywords for Vizier queries"""

    def __init__(self, keywords):
        file_name = aud.get_pkg_data_filename(
            os.path.join("data", "inverse_dict.json"))
        with open(file_name, 'r') as f:
            kwd = json.load(f)
            self.keyword_types = sorted(kwd.values())
            self.keyword_dict = OrderedDict([(k, kwd[k]) for k in sorted(kwd)])
        self._keywords = None
        self.keywords = keywords

    @property
    def keywords(self):
        """
        List or string for keyword(s) that must be set for the Vizier
        object.
        """
        return self._keywords

    @keywords.setter
    def keywords(self, values):
        if isinstance(values, str):
            values = list(values)
        keys = [key.lower() for key in self.keyword_dict]
        values = [val.lower() for val in values]
        # warn about unknown keywords
        for val in set(values) - set(keys):
            warnings.warn("{val} : No such keyword".format(val=val))
        valid_keys = [
            key for key in self.keyword_dict.keys()
            if key.lower() in list(map(str.lower, values))]
        # create a dict for each type of keyword
        set_keywords = OrderedDict()
        for key in self.keyword_dict:
            if key in valid_keys:
                if self.keyword_dict[key] in set_keywords:
                    set_keywords[self.keyword_dict[key]].append(key)
                else:
                    set_keywords[self.keyword_dict[key]] = [key]
        self._keywords = OrderedDict(
            [(k, sorted(set_keywords[k]))
             for k in set_keywords])

    @keywords.deleter
    def keywords(self):
        del self._keywords

    def __repr__(self):
        return "\n".join([x for key in self.keywords
                          for x in self.get_keyword_str(key)])

    def get_keyword_str(self, key):
        """
        Helper function that returns the keywords, grouped into appropriate
        categories and suitable for the Vizier votable CGI.

        Comma-separated is not valid!!!
        """
        keyword_name = "-kw." + key
        return [keyword_name + "=" + s for s in self.keywords[key]]


Vizier = VizierClass()
