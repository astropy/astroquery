# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""SIMBAD query class for accessing the SIMBAD Service"""

import copy
from dataclasses import dataclass, field
from difflib import get_close_matches
from functools import lru_cache
import gc
import re
from typing import Any
import warnings

import astropy.coordinates as coord
from astropy.table import Table, Column, vstack
import astropy.units as u
from astropy.utils import isiterable, deprecated
from astropy.utils.decorators import deprecated_renamed_argument

from astroquery.query import BaseVOQuery
from astroquery.utils import commons
from astroquery.exceptions import NoResultsWarning
from astroquery.simbad.utils import (_catch_deprecated_fields_with_arguments,
                                     _wildcard_to_regexp, CriteriaTranslator,
                                     query_criteria_fields)

from pyvo.dal import TAPService, TAPQuery
from . import conf


__all__ = ['Simbad', 'SimbadClass']


def _adql_parameter(entry: str):
    """Replace single quotes by two single quotes.

    This should be applied to parameters used in ADQL queries.
    It is not a SQL injection protection: it just allows to search, for example,
    for authors with quotes in their names or titles/descriptions with apostrophes.

    Parameters
    ----------
    entry : str

    Returns
    -------
    str
    """
    return entry.replace("'", "''")


@lru_cache(256)
def _cached_query_tap(tap, query: str, *, maxrec=10000):
    """Cache version of query TAP.

    This private function is called when query_tap is executed without an
    ``uploads`` extra keyword argument. This is a work around because
    `~astropy.table.Table` objects are not hashable and thus cannot
    be used as arguments for a function decorated with lru_cache.

    Parameters
    ----------
    tap : `~pyvo.dal.TAPService`
        The TAP service to query SIMBAD.
    query : str
        A string containing the query written in the
        Astronomical Data Query Language (ADQL).
    maxrec : int, optional
        The number of records to be returned. Its maximum value is 2000000.

    Returns
    -------
    `~astropy.table.Table`
        The response returned by SIMBAD.
    """
    return tap.search(query, maxrec=maxrec).to_table()


@dataclass(frozen=True)
class _Column:
    """A class to define a column in a SIMBAD query."""
    table: str
    name: str
    alias: str = field(default=None)


@dataclass(frozen=True)
class _Join:
    """A class to define a join between two tables."""
    table: str
    column_left: Any
    column_right: Any
    join_type: str = field(default="JOIN")
    alias: str = field(default=None)


class SimbadClass(BaseVOQuery):
    """The class for querying the SIMBAD web service.

    Note that SIMBAD suggests submitting no more than 6 queries per second; if
    you submit more than that, your IP may be temporarily blacklisted
    (https://simbad.cds.unistra.fr/guide/sim-url.htx)
    """
    SIMBAD_URL = 'https://' + conf.server + '/simbad/sim-script'

    def __init__(self, ROW_LIMIT=None):
        super().__init__()
        # to create the TAPService
        self._server = conf.server
        self._tap = None
        self._hardlimit = None
        self._uploadlimit = None
        # attributes to construct ADQL queries
        self._columns_in_output = None  # a list of _Column
        self.joins = []  # a list of _Join
        self.criteria = []  # a list of strings
        self.ROW_LIMIT = ROW_LIMIT

    @property
    def ROW_LIMIT(self):
        return self._ROW_LIMIT

    @ROW_LIMIT.setter
    def ROW_LIMIT(self, ROW_LIMIT):
        if ROW_LIMIT is None:
            self._ROW_LIMIT = conf.row_limit
        elif isinstance(ROW_LIMIT, int) and ROW_LIMIT >= -1:
            self._ROW_LIMIT = ROW_LIMIT
        else:
            raise ValueError("ROW_LIMIT can be either -1 to set the limit to SIMBAD's "
                             "maximum capability, 0 to retrieve an empty table, "
                             "or a positive integer.")

    @property
    def server(self):
        """The SIMBAD mirror to use."""
        return self._server

    @server.setter
    def server(self, server: str):
        """Allows to switch server between SIMBAD mirrors.

        Parameters
        ----------
        server : str
            It should be one of `~astroquery.simbad.conf.servers_list`.
        """
        if server in conf.servers_list:
            self._server = server
        else:
            raise ValueError(f"'{server}' does not correspond to a SIMBAD server, "
                             f"the two existing ones are {conf.servers_list}.")

    @property
    def tap(self):
        """A `~pyvo.dal.TAPService` service for SIMBAD."""
        tap_url = f"https://{self.server}/simbad/sim-tap"
        # only creates a new tap instance if there are no existing one
        # or if the server property changed since the last getter call.
        if (not self._tap) or (self._tap.baseurl != tap_url):
            self._tap = TAPService(baseurl=tap_url, session=self._session)
        return self._tap

    @property
    def hardlimit(self):
        """The maximum number of lines for SIMBAD's output."""
        if self._hardlimit is None:
            self._hardlimit = self.tap.hardlimit
        return self._hardlimit

    @property
    def uploadlimit(self):
        if self._uploadlimit is None:
            self._uploadlimit = self.tap.get_tap_capability().uploadlimit.hard.content
        return self._uploadlimit

    @property
    def columns_in_output(self):
        """A list of _Column.

        They will be included in the output of the following methods:

        - `query_object`,
        - `query_objects`,
        - `query_region`,
        - `query_catalog`,
        - `query_hierarchy`,
        - `query_bibobj`,
        - `query_criteria`.

        """
        if self._columns_in_output is None:
            self._columns_in_output = [_Column("basic", item)
                                       for item in conf.default_columns]
        return self._columns_in_output

    @columns_in_output.setter
    def columns_in_output(self, list_columns):
        self._columns_in_output = list_columns

    @staticmethod
    def list_wildcards():
        """
        Displays the available wildcards that may be used in SIMBAD queries and
        their usage.

        Examples
        --------
        >>> from astroquery.simbad import Simbad
        >>> Simbad.list_wildcards()
        *: Any string of characters (including an empty one)
        ?: Any character (exactly one character)
        [abc]: Exactly one character taken in the list. Can also be defined by a range of characters: [A-Z]
        [^0-9]: Any (one) character not in the list.
        """
        WILDCARDS = {'*': 'Any string of characters (including an empty one)',
                     '?': 'Any character (exactly one character)',
                     '[abc]': ('Exactly one character taken in the list. '
                               'Can also be defined by a range of characters: [A-Z]'),
                     '[^0-9]': 'Any (one) character not in the list.'}
        print("\n".join(f"{k}: {v}" for k, v in WILDCARDS.items()))

    # ---------------------------------
    # Methods to define SIMBAD's output
    # ---------------------------------

    def list_votable_fields(self):
        """List all options to add columns to SIMBAD's output.

        They are of four types:

        - "column of basic": a column of the basic table. There fields can also be explored with
          `~astroquery.simbad.SimbadClass.list_columns`.
        - "table": a table other than basic that has a declared direct join
        - "bundle of basic columns": a pre-selected bundle of columns of basic. Ex: "parallax" will add all
          columns relevant to parallax
        - "filter name": an optical filter name

        Examples
        --------
        >>> from astroquery.simbad import Simbad
        >>> options = Simbad.list_votable_fields() # doctest: +REMOTE_DATA
        >>> # to print only the available bundles of columns
        >>> options[options["type"] == "bundle of basic columns"][["name", "description"]] # doctest: +REMOTE_DATA
        <Table length=9>
             name                           description
            object                             object
        ------------- -------------------------------------------------------
          coordinates                     all fields related with coordinates
                  dim             major and minor axis, angle and inclination
           dimensions                 all fields related to object dimensions
            morphtype            all fields related to the morphological type
             parallax                        all fields related to parallaxes
        propermotions              all fields related with the proper motions
                   sp               all fields related with the spectral type
             velocity    all fields related with radial velocity and redshift
        """
        # get the tables with a simple link to basic
        query_tables = """SELECT DISTINCT table_name AS name, tables.description
        FROM TAP_SCHEMA.keys JOIN  TAP_SCHEMA.key_columns USING (key_id)
        JOIN TAP_SCHEMA.tables ON TAP_SCHEMA.keys.from_table = TAP_SCHEMA.tables.table_name
        OR TAP_SCHEMA.keys.target_table = TAP_SCHEMA.tables.table_name
        WHERE TAP_SCHEMA.tables.schema_name = 'public'
        AND (from_table = 'basic' OR target_table = 'basic')
        AND from_table != 'h_link'
        """
        tables = self.query_tap(query_tables)
        tables["type"] = Column(["table"] * len(tables), dtype="object")
        # the columns of basic are also valid options
        basic_columns = self.list_columns("basic")[["column_name", "description"]]
        basic_columns["column_name"].info.name = "name"
        basic_columns["type"] = Column(["column of basic"] * len(basic_columns), dtype="object")
        # get the bundles of columns from file
        bundle_entries = {key: value for key, value in query_criteria_fields.items()
                          if value["type"] == "bundle"}
        bundles = Table({"name": list(bundle_entries.keys()),
                         "description": [value["description"] for _, value in bundle_entries.items()],
                         "type": ["bundle of basic columns"] * len(bundle_entries)},
                        dtype=["object", "object", "object"])
        # get the filter names
        filters = self.query_tap("SELECT filtername AS name, description FROM filter")
        filters["type"] = Column(["filter name"] * len(filters), dtype="object")
        # vstack the four types of options
        return vstack([tables, basic_columns, bundles, filters], metadata_conflicts="silent")

    def _get_bundle_columns(self, bundle_name):
        """Get the list of columns in the preselected bundles.

        Parameters
        ----------
        bundle_name : str
            The possible values can be listed with `~astroquery.simbad.SimbadClass.list_votable_fields`

        Returns
        -------
        list[simbad._Column]
            The list of columns corresponding to the selected bundle.
        """
        basic_columns = set(map(str.casefold, set(self.list_columns("basic")["column_name"])))

        bundle_entries = {key: value for key, value in query_criteria_fields.items()
                          if value["type"] == "bundle"}

        if bundle_name in bundle_entries:
            bundle = bundle_entries[bundle_name]
            columns = [_Column("basic", column) for column in basic_columns
                       if column.startswith(bundle["tap_startswith"])]
            if "tap_column" in bundle:
                columns = [_Column("basic", column) for column in bundle["tap_column"]] + columns
        return columns

    def _add_table_to_output(self, table):
        """Add all fields of a 'table' to the output of queries.

        This handles the join from the table and the naming of the columns.
        It only takes in account tables with an explicit link to basic. Other
        cases should be added manually in an ADQL query string.

        Parameters
        ----------
        table : str
            name of the table to add
        """
        table = table.casefold()

        if table == "basic":
            self.columns_in_output.append(_Column(table, "*"))
            return

        linked_to_basic = self.list_linked_tables("basic")
        # list of accepted tables
        linked_to_basic["from_table"] = [table.casefold() for table in linked_to_basic["from_table"]]
        # the actual link to construct the join
        link = linked_to_basic[linked_to_basic["from_table"] == table][0]

        if table not in linked_to_basic["from_table"] or table == "h_link":
            raise ValueError(f"'{table}' has no explicit link to 'basic'. These cases require a custom ADQL "
                             "query to be written and called with 'SimbadClass.query_tap'.")

        columns = list(self.list_columns(table)["column_name"])

        # allfluxes is the only case-dependent table
        if table == "allfluxes":
            columns = [column for column in columns if column not in {"oidref", "oidbibref"}]
            alias = [column.replace("_", "") if "_" in column else None
                     for column in columns]
        else:
            columns = [column.casefold() for column in columns if column not in {"oidref", "oidbibref"}]
            # the alias is mandatory to be able to distinguish between duplicates like
            # mesDistance.bibcode and mesDiameter.bibcode.
            alias = [f"{table}.{column}" if not column.startswith(table) else None for column in columns]

        # modify the attributes here
        self.columns_in_output += [_Column(table, column, alias)
                                   for column, alias in zip(columns, alias)]
        self.joins += [_Join(table, _Column("basic", link["target_column"]),
                             _Column(table, link["from_column"]), "LEFT JOIN")]

    def add_votable_fields(self, *args):
        """Add columns to the output of a SIMBAD query.

        The list of possible arguments and their description for this method
        can be printed with `~astroquery.simbad.SimbadClass.list_votable_fields`.

        The methods affected by this:

        - `query_object`,
        - `query_objects`,
        - `query_region`,
        - `query_catalog`,
        - `query_hierarchy`,
        - `query_bibobj`,
        - `query_criteria`.


        Parameters
        ----------
        args : str
            The arguments to be added.

        Examples
        --------
        >>> from astroquery.simbad import Simbad
        >>> simbad = Simbad()
        >>> simbad.add_votable_fields('sp_type', 'sp_qual', 'sp_bibcode') # doctest: +REMOTE_DATA
        >>> simbad.get_votable_fields() # doctest: +REMOTE_DATA
        ['basic.main_id', 'basic.ra', 'basic.dec', 'basic.coo_err_maj', 'basic.coo_err_min', ...
        """

        # the legacy way of adding fluxes
        args = set(args)
        fluxes_to_add = []
        args_copy = args.copy()
        for arg in args_copy:
            if arg.startswith("flux_"):
                raise ValueError("The votable fields 'flux_***(filtername)' are removed and replaced "
                                 "by 'flux' that will add all information for every filters. "
                                 "See section on filters in "
                                 "https://astroquery.readthedocs.io/en/latest/simbad/simbad_evolution.html"
                                 " to see the new ways to interact with SIMBAD's fluxes.")
            if re.match(r"^flux.*\(.+\)$", arg):
                filter_name = re.findall(r"\((\w+)\)", arg)[0]
                warnings.warn(f"The notation 'flux({filter_name})' is deprecated since 0.4.8 in favor of "
                              f"'{filter_name}'. You will see the column appearing with its new name "
                              "in the output. See section on filters in "
                              "https://astroquery.readthedocs.io/en/latest/simbad/simbad_evolution.html "
                              "to see the new ways to interact with SIMBAD's fluxes.", DeprecationWarning, stacklevel=2)
                fluxes_to_add.append(filter_name)
                args.remove(arg)

        # output options
        output_options = self.list_votable_fields()
        # fluxes are case-dependant
        fluxes = set(output_options[output_options["type"] == "filter name"]["name"])
        # add fluxes
        fluxes_from_names = set(flux for flux in args if flux in fluxes)
        fluxes_to_add += fluxes_from_names
        if fluxes_to_add:
            self.joins.append(_Join("allfluxes", _Column("basic", "oid"),
                              _Column("allfluxes", "oidref")))
            for flux in fluxes_to_add:
                if len(flux) == 1 and flux.islower():
                    # the name in the allfluxes view has a trailing underscore. This is not
                    # the case in the list of filter names, so we homogenize with an alias
                    self.columns_in_output.append(_Column("allfluxes", flux + "_", flux))
                else:
                    self.columns_in_output.append(_Column("allfluxes", flux))
        # remove the arguments already added
        args -= fluxes_from_names
        # remove filters from output options
        output_options = output_options[output_options["type"] != "filter name"]

        # casefold args because we allow case difference for every other argument (legacy behavior)
        args = set(map(str.casefold, args))
        output_options["name"] = list(map(str.casefold, list(output_options["name"])))
        basic_columns = output_options[output_options["type"] == "column of basic"]["name"]
        all_tables = output_options[output_options["type"] == "table"]["name"]
        bundles = output_options[output_options["type"] == "bundle of basic columns"]["name"]

        # Add columns from basic
        self.columns_in_output += [_Column("basic", column) for column in args if column in basic_columns]

        # Add tables
        tables_to_add = [table for table in args if table in all_tables]
        for table in tables_to_add:
            self._add_table_to_output(table)

        # Add bundles
        bundles_to_add = [bundle for bundle in args if bundle in bundles]
        for bundle in bundles_to_add:
            self.columns_in_output += self._get_bundle_columns(bundle)

        if args.issubset(set(output_options["name"])):
            return

        # The other possible values are from the deprecated votable fields
        remaining_arguments = args - set(output_options["name"])
        for votable_field in remaining_arguments:
            if votable_field in query_criteria_fields:
                field_data = query_criteria_fields[votable_field]
                field_type = field_data["type"]
                # some columns are still there but under a new name
                if field_type == "alias":
                    tap_column = field_data["tap_column"]
                    self.columns_in_output.append(_Column("basic", tap_column))
                    warning_message = (f"'{votable_field}' has been renamed '{tap_column}'. You'll see it "
                                       "appearing with its new name in the output table")
                    warnings.warn(warning_message, DeprecationWarning, stacklevel=2)
                # some tables are still there but under a new name
                elif field_type == "alias table":
                    # add all columns of the desired measurement table
                    tap_table = field_data["tap_table"]
                    self._add_table_to_output(tap_table)
                    warning_message = (f"'{votable_field}' has been renamed '{tap_table}'. You will see "
                                       "this new name in the result.")
                    warnings.warn(warning_message, DeprecationWarning, stacklevel=2)
                # some tables have been moved to VizieR. This is broken since years
                # but they were still appearing in list_votable_fields.
                elif field_type == "historical measurement":
                    raise ValueError(f"'{votable_field}' is no longer a part of SIMBAD. It was moved "
                                     "into a separate VizieR catalog. It is possible to query "
                                     "it with the `astroquery.vizier` module.")
            else:
                # raise a ValueError on fields with arguments
                _catch_deprecated_fields_with_arguments(votable_field)
                # or a typo
                close_match = get_close_matches(votable_field, set(output_options["name"]))
                error_message = (f"'{votable_field}' is not one of the accepted options "
                                 "which can be listed with 'list_votable_fields'.")
                if close_match != []:
                    close_matches = "' or '".join(close_match)
                    error_message += f" Did you mean '{close_matches}'?"
                raise ValueError(error_message)

    def get_votable_fields(self):
        """Display votable fields."""
        return [f"{column.table}.{column.name}" for column in self.columns_in_output]

    def reset_votable_fields(self):
        """Reset the output of the query_*** methods to default.

        They will be included in the output of the following methods:

        - `query_object`,
        - `query_objects`,
        - `query_region`,
        - `query_catalog`,
        - `query_hierarchy`,
        - `query_bibobj`,
        - `query_criteria`.

        """
        self.columns_in_output = [_Column("basic", item)
                                  for item in conf.default_columns]
        self.joins = []
        self.criteria = []

    def get_field_description(self, field_name):
        """Displays a description of the VOTable field.

        This can be replaced by the output of `~astroquery.simbad.SimbadClass.list_votable_fields`.

        Examples
        --------
        >>> from astroquery.simbad import Simbad
        >>> options = Simbad.list_votable_fields() # doctest: +REMOTE_DATA
        >>> description_dimensions = options[options["name"] == "dimensions"]["description"] # doctest: +REMOTE_DATA
        >>> description_dimensions.data.data[0] # doctest: +REMOTE_DATA
        'all fields related to object dimensions'

        """
        options = self.list_votable_fields()
        description = options[options["name"] == field_name]["description"]
        return description.data.data[0]

    # -------------
    # Query methods
    # -------------

    @deprecated_renamed_argument(["verbose"], new_name=[None],
                                 since=['0.4.8'], relax=True)
    def query_object(self, object_name, *, wildcard=False,
                     criteria=None, get_query_payload=False, verbose=False):
        """Query SIMBAD for the given object.

        Object names may also be specified with wildcards. See examples below.

        Parameters
        ----------
        object_name : str
            name of object to be queried.
        wildcard : boolean, optional
            When it is set to `True` it implies that the object is specified
            with wildcards. This parameter will render the query case-sensitive.
            Defaults to `False`.
        criteria : str
            Criteria to be applied to the query. These should be written in the ADQL
            syntax in a single string. See example.
        get_query_payload : bool, optional
            When set to `True` the method returns the HTTP request parameters without
            querying SIMBAD. The ADQL string is in the 'QUERY' key of the payload.
            Defaults to `False`.

        Returns
        -------
        table : `~astropy.table.Table`
            The result of the query to SIMBAD.

        Examples
        --------

        Get the dimensions of a specific galaxy

        >>> from astroquery.simbad import Simbad
        >>> simbad = Simbad()
        >>> simbad.add_votable_fields("dim") # doctest: +REMOTE_DATA
        >>> result = simbad.query_object("m101") # doctest: +REMOTE_DATA
        >>> result["main_id", "ra", "dec", "galdim_majaxis", "galdim_minaxis", "galdim_bibcode"] # doctest: +REMOTE_DATA
        <Table length=1>
        main_id         ra           dec    ... galdim_minaxis    galdim_bibcode
                       deg           deg    ...     arcmin
         object      float64       float64  ...    float32            object
        ------- ------------------ -------- ... -------------- -------------------
          M 101 210.80242916666668 54.34875 ...          20.89 2003A&A...412...45P

        Get 5 NGC objects that are clusters of stars

        >>> from astroquery.simbad import Simbad
        >>> simbad = Simbad()
        >>> simbad.ROW_LIMIT = 5
        >>> ngc_clusters = simbad.query_object("NGC*", wildcard=True, criteria="otype='Cl*..'") # doctest: +REMOTE_DATA
        >>> ngc_clusters  # doctest: +REMOTE_DATA +IGNORE_OUTPUT
        <Table length=5>
         main_id          ra        ...     coo_bibcode     matched_id
                         deg        ...
          object       float64      ...        object         object
        --------- ----------------- ... ------------------- ----------
        NGC  2024 85.42916666666667 ... 2003A&A...397..177B  NGC  2024
        NGC  1826 76.39174999999999 ... 2011AJ....142...48W  NGC  1826
        NGC  2121 87.05495833333332 ... 2011AJ....142...48W  NGC  2121
        NGC  2019 82.98533333333333 ... 1999AcA....49..521P  NGC  2019
        NGC  1777             73.95 ... 2008MNRAS.389..678B  NGC  1777
        """
        top, columns, joins, instance_criteria = self._get_query_parameters()

        columns.append(_Column("ident", "id", "matched_id"))

        joins.append(_Join("ident", _Column("basic", "oid"), _Column("ident", "oidref")))

        if wildcard:
            instance_criteria.append(rf" regexp(id, '{_wildcard_to_regexp(object_name)}') = 1")
        else:
            instance_criteria.append(rf"id = '{_adql_parameter(object_name)}'")

        if criteria:
            instance_criteria.append(f"({criteria})")

        return self._query(top, columns, joins, instance_criteria,
                           get_query_payload=get_query_payload)

    @deprecated_renamed_argument(["verbose", "cache"], new_name=[None, None],
                                 since=['0.4.8', '0.4.8'], relax=True)
    def query_objects(self, object_names, *, wildcard=False, criteria=None,
                      get_query_payload=False, verbose=False, cache=False):
        """Query SIMBAD for the specified list of objects.

        Object names may be specified with wildcards.
        If one of the ``object_names`` is not found in SIMBAD, the corresponding line is
        returned empty in the output (see ``Giga Cluster`` in the example).
        In the output, the column ``user_specified_id`` is the input object name.

        Parameters
        ----------
        object_names : sequence of strs
            names of objects to be queried
        wildcard : boolean, optional
            When `True`, the names may have wildcards in them. Defaults to
            `False`.
        criteria : str
            Criteria to be applied to the query. These should be written in the ADQL
            syntax in a single string. See example.
        get_query_payload : bool, optional
            When set to `True` the method returns the HTTP request parameters without
            querying SIMBAD. The ADQL string is in the 'QUERY' key of the payload.
            Defaults to `False`.
        cache : Deprecated since 0.4.8. The cache is now automatically emptied at the
            end of the python session. It can also be emptied manually with
            `~astroquery.simbad.SimbadClass.clear_cache` but cannot be deactivated.

        Returns
        -------
        table : `~astropy.table.Table`
            The result of the query to SIMBAD.

        Examples
        --------
        >>> from astroquery.simbad import Simbad
        >>> clusters = Simbad.query_objects(["Boss Great Wall", "Great Attractor",
        ...                                  "Giga Cluster", "Coma Supercluster"]) # doctest: +REMOTE_DATA
        >>> clusters[["main_id", "ra", "dec", "user_specified_id"]] # doctest: +REMOTE_DATA
        <Table length=4>
               main_id            ra     dec   user_specified_id
                                 deg     deg
                object         float64 float64       object
        ---------------------- ------- ------- -----------------
          NAME Boss Great Wall   163.0    52.0   Boss Great Wall
          NAME Great Attractor   158.0   -46.0   Great Attractor
                                    --      --      Giga Cluster
        NAME Coma Supercluster  170.75    23.9 Coma Supercluster
        """
        top, columns, joins, instance_criteria = self._get_query_parameters()

        if criteria:
            instance_criteria.append(f"({criteria})")

        if wildcard:
            columns.append(_Column("ident", "id", "matched_id"))
            joins += [_Join("ident", _Column("basic", "oid"), _Column("ident", "oidref"))]
            list_criteria = [f"regexp(id, '{_wildcard_to_regexp(object_name)}') = 1"
                             for object_name in object_names]
            instance_criteria += [f'({" OR ".join(list_criteria)})']

            return self._query(top, columns, joins, instance_criteria,
                               get_query_payload=get_query_payload)

        # There is a faster way to do the query if there is no wildcard: the first table
        # can be the uploaded one and we use a LEFT JOIN for the other ones.
        upload = Table({"user_specified_id": object_names,
                        "object_number_id": list(range(1, len(object_names) + 1))})
        upload_name = "TAP_UPLOAD.script_infos"
        columns.append(_Column(upload_name, "*"))

        # join on ident needs an alias in case the users want to add the votable field ident
        left_joins = [_Join("ident", _Column(upload_name, "user_specified_id"),
                            _Column("ident", "id"), "LEFT JOIN", "ident_upload"),
                      _Join("basic", _Column("basic", "oid"),
                            _Column("ident_upload", "oidref"), "LEFT JOIN")]
        for join in joins:
            left_joins.append(_Join(join.table, join.column_left,
                                    join.column_right, "LEFT JOIN"))
        return self._query(top, columns, left_joins, instance_criteria,
                           from_table=upload_name,
                           get_query_payload=get_query_payload,
                           script_infos=upload)

    @deprecated_renamed_argument(["equinox", "epoch", "cache"],
                                 new_name=[None]*3,
                                 since=['0.4.8']*3, relax=True)
    def query_region(self, coordinates, radius=2*u.arcmin, *,
                     criteria=None, get_query_payload=False,
                     equinox=None, epoch=None, cache=None):
        """Query SIMBAD in a cone around the specified coordinates.

        Parameters
        ----------
        coordinates : str or `astropy.coordinates` object
            The identifier or coordinates around which to query.
        radius : str or `~astropy.units.Quantity`
            the radius of the region.  Defaults to 2 arcmin.
        criteria : str
            Criteria to be applied to the query. These should be written in the ADQL
            syntax in a single string.
        get_query_payload : bool, optional
            When set to `True` the method returns the HTTP request parameters without
            querying SIMBAD. The ADQL string is in the 'QUERY' key of the payload.
            Defaults to `False`.
        cache : Deprecated since 0.4.8. The cache is now automatically emptied at the
            end of the python session. It can also be emptied manually with
            `~astroquery.simbad.SimbadClass.clear_cache` but cannot be deactivated.

        Returns
        -------
        table : `~astropy.table.Table`
            The result of the query to SIMBAD.

        Examples
        --------

        Look for largest galaxies in two cones

        >>> from astroquery.simbad import Simbad
        >>> from astropy.coordinates import SkyCoord
        >>> simbad = Simbad()
        >>> simbad.ROW_LIMIT = 5
        >>> simbad.add_votable_fields("otype", "dim") # doctest: +REMOTE_DATA
        >>> coordinates = SkyCoord([SkyCoord(186.6, 12.7, unit=("deg", "deg")),
        ...                         SkyCoord(170.75, 23.9, unit=("deg", "deg"))])
        >>> result = simbad.query_region(coordinates, radius="2d5m",
        ...                              criteria="otype = 'Galaxy..' AND galdim_majaxis>8.5") # doctest: +REMOTE_DATA
        >>> result.sort("galdim_majaxis", reverse=True) # doctest: +REMOTE_DATA
        >>> result["main_id", "otype", "galdim_majaxis"] # doctest: +REMOTE_DATA
        <Table length=5>
          main_id    otype  galdim_majaxis
                                arcmin
           object    object    float32
        ------------ ------ --------------
        LEDA   41362    GiC           11.0
               M  86    GiG          10.47
        LEDA   40917    AG?           10.3
               M  87    AGN           9.12
           NGC  4438    LIN           8.91

        Notes
        -----
        It is very inefficient to call this within a loop. Creating an `~astropy.coordinates.SkyCoord`
        object with a list of coordinates will be way faster.

        """
        if radius is None:
            # this message is specifically for deprecated use of 'None' to mean 'Default'
            raise TypeError("The cone radius must be specified as an angle-equivalent quantity")

        center = commons.parse_coordinates(coordinates)
        center = center.transform_to("icrs")

        top, columns, joins, instance_criteria = self._get_query_parameters()
        if criteria:
            instance_criteria.append(f"({criteria})")

        if center.isscalar:
            radius = coord.Angle(radius)
            instance_criteria.append(f"CONTAINS(POINT('ICRS', basic.ra, basic.dec), "
                                     f"CIRCLE('ICRS', {center.ra.deg}, {center.dec.deg}, "
                                     f"{radius.to(u.deg).value})) = 1")
            return self._query(top, columns, joins, instance_criteria,
                               get_query_payload=get_query_payload)

        # from uploadLimit in SIMBAD's capabilities
        # http://simbad.cds.unistra.fr/simbad/sim-tap/capabilities
        if len(center) > self.uploadlimit:
            raise ValueError(f"'query_region' can process up to {self.uploadlimit} "
                             "centers. For larger queries, split your centers list.")

        # `radius` as `str` is iterable, but contains only one value.
        if isiterable(radius) and not isinstance(radius, str):
            if len(radius) != len(center):
                raise ValueError(f"Mismatch between radii of length {len(radius)}"
                                 f" and center coordinates of length {len(center)}.")
            radius = [coord.Angle(item).to(u.deg).value for item in radius]
        else:
            radius = [coord.Angle(radius).to(u.deg).value] * len(center)

        # for small number of centers, not using the upload method is faster
        if len(center) <= 300:
            cone_criteria = [(f"CONTAINS(POINT('ICRS', basic.ra, basic.dec), CIRCLE('ICRS', "
                             f"{center.ra.deg}, {center.dec.deg}, {radius})) = 1 ")
                             for center, radius in zip(center, radius)]

            cone_criteria = f" ({'OR '.join(cone_criteria)})"
            instance_criteria.append(cone_criteria)

            return self._query(top, columns, joins, instance_criteria,
                               get_query_payload=get_query_payload)

        # for longer centers list, we use a TAP upload
        upload_centers = Table({"ra": center.ra.deg, "dec": center.dec.deg,
                                "radius": radius})
        sub_query = "(SELECT ra, dec, radius FROM TAP_UPLOAD.centers) AS centers"
        instance_criteria.append("CONTAINS(POINT('ICRS', basic.ra, basic.dec), CIRCLE"
                                 "('ICRS', centers.ra, centers.dec, centers.radius)) = 1 ")

        return self._query(top, columns, joins, instance_criteria,
                           from_table=f"{sub_query}, basic",
                           get_query_payload=get_query_payload, centers=upload_centers)

    @deprecated_renamed_argument(["verbose", "cache"], new_name=[None, None],
                                 since=['0.4.8', '0.4.8'], relax=True)
    def query_catalog(self, catalog, *, criteria=None, get_query_payload=False,
                      verbose=False, cache=True):
        """Query a whole catalog.

        Parameters
        ----------
        catalog : str
            The name of the catalog. This is case-dependant.
        criteria : str
            Criteria to be applied to the query. These should be written in the ADQL
            syntax in a single string. See example.
        get_query_payload : bool, optional
            When set to `True` the method returns the HTTP request parameters without
            querying SIMBAD. The ADQL string is in the 'QUERY' key of the payload.
            Defaults to `False`.
        cache : Deprecated since 0.4.8. The cache is now automatically emptied at the
            end of the python session. It can also be emptied manually with
            `~astroquery.simbad.SimbadClass.clear_cache` but cannot be deactivated.

        Returns
        -------
        table : `~astropy.table.Table`
            The result of the query to SIMBAD.

        Examples
        --------
        >>> from astroquery.simbad import Simbad
        >>> simbad = Simbad()
        >>> simbad.ROW_LIMIT = 5
        >>> simbad.query_catalog("GSC", criteria="pmra > 50 and pmra < 100") # doctest: +REMOTE_DATA
        <Table length=5>
            main_id            ra       ...     coo_bibcode        catalog_id
                              deg       ...
             object         float64     ...        object            object
        --------------- --------------- ... ------------------- ---------------
              HD  26053  61.84326890626 ... 2020yCat.1350....0G GSC 04725-00973
        TYC 8454-1081-1 345.11163189562 ... 2020yCat.1350....0G GSC 08454-01081
              HD  10158  24.86286094434 ... 2020yCat.1350....0G GSC 00624-00340
            CD-22  1862  73.17988827324 ... 2020yCat.1350....0G GSC 05911-00222
            BD+02  4434 327.90220788982 ... 2020yCat.1350....0G GSC 00548-00194

        Notes
        -----
        Catalogs can be very large. Configuring ``SimbadClass.ROW_LIMIT`` allows to
        restrict the output.

        """
        top, columns, joins, instance_criteria = self._get_query_parameters()

        columns.append(_Column("ident", "id", "catalog_id"))

        joins += [_Join("ident", _Column("basic", "oid"), _Column("ident", "oidref"))]

        instance_criteria.append(fr"id LIKE '{catalog} %'")
        if criteria:
            instance_criteria.append(f"({criteria})")

        return self._query(top, columns, joins, instance_criteria,
                           get_query_payload=get_query_payload)

    def query_hierarchy(self, name, hierarchy, *,
                        detailed_hierarchy=True,
                        criteria=None, get_query_payload=False):
        """Query either the parents or the children of the object.

        Parameters
        ----------
        name : str
            name of the object
        hierarchy : str
            Can take the values "parents" to return the parents of the object (ex: a
            galaxy cluster is a parent of a galaxy), the value "children" to return
            the children of an object (ex: stars can be children of a globular cluster),
            or the value "siblings" to return the object that share a parent with the
            given one (ex: the stars of an open cluster are all siblings).
        detailed_hierarchy : bool
            Whether to add the two extra columns 'hierarchy_bibcode' that gives the
            article in which the hierarchy link is mentioned, and
            'membership_certainty'. membership_certainty is an integer that reflects the
            certainty of the hierarchy link according to the authors. Ranges between 0
            and 100 where 100 means that the authors were certain of the classification.
            Defaults to False.
        criteria : str
            Criteria to be applied to the query. These should be written in the ADQL
            syntax in a single string. See example.
        get_query_payload : bool, optional
            When set to `True` the method returns the HTTP request parameters without
            querying SIMBAD. The ADQL string is in the 'QUERY' key of the payload.
            Defaults to `False`.

        Returns
        -------
        table : `~astropy.table.Table`
            Query results table

        Examples
        --------
        >>> from astroquery.simbad import Simbad
        >>> parent = Simbad.query_hierarchy("2MASS J18511048-0615470",
        ...                                 detailed_hierarchy=False,
        ...                                 hierarchy="parents")  # doctest: +REMOTE_DATA
        >>> parent[["main_id", "ra", "dec"]] # doctest: +REMOTE_DATA
        <Table length=1>
         main_id     ra     dec
                    deg     deg
          object  float64 float64
        --------- ------- -------
        NGC  6705 282.766  -6.272
        """
        top, columns, joins, instance_criteria = self._get_query_parameters()

        sub_query = ("(SELECT oidref FROM ident "
                     f"WHERE id = '{name}') AS name")

        if detailed_hierarchy:
            columns.append(_Column("h_link", "link_bibcode", "hierarchy_bibcode"))
            columns.append(_Column("h_link", "membership", "membership_certainty"))

        if hierarchy == "parents":
            joins += [_Join("h_link", _Column("basic", "oid"), _Column("h_link", "parent"))]
            instance_criteria.append("h_link.child = name.oidref")
        elif hierarchy == "children":
            joins += [_Join("h_link", _Column("basic", "oid"), _Column("h_link", "child"))]
            instance_criteria.append("h_link.parent = name.oidref")
        elif hierarchy == "siblings":
            sub_query = ("(SELECT DISTINCT basic.oid FROM "
                         f"{sub_query}, basic JOIN h_link ON basic.oid = h_link.parent "
                         "WHERE h_link.child = name.oidref) AS parents")
            joins += [_Join("h_link", _Column("basic", "oid"), _Column("h_link", "child"))]
            instance_criteria.append("h_link.parent = parents.oid")
        else:
            raise ValueError("'hierarchy' can only take the values 'parents', "
                             f"'siblings', or 'children'. Got '{hierarchy}'.")

        if criteria:
            instance_criteria.append(f"({criteria})")

        return self._query(top, columns, joins, instance_criteria,
                           from_table=f"{sub_query}, basic", distinct=True,
                           get_query_payload=get_query_payload)

    @deprecated_renamed_argument(["verbose"], new_name=[None],
                                 since=['0.4.8'], relax=True)
    def query_bibobj(self, bibcode, *, criteria=None,
                     get_query_payload=False,
                     verbose=False):
        """Query all the objects mentioned in an article.

        Parameters
        ----------
        bibcode : str
            the bibcode of the article
        get_query_payload : bool, optional
            When set to `True` the method returns the HTTP request parameters without
            querying SIMBAD. The ADQL string is in the 'QUERY' key of the payload.
            Defaults to `False`.

        Returns
        -------
        table : `~astropy.table.Table`
            Query results table
        """
        top, columns, joins, instance_criteria = self._get_query_parameters()

        joins += [_Join("has_ref", _Column("basic", "oid"), _Column("has_ref", "oidref")),
                  _Join("ref", _Column("has_ref", "oidbibref"), _Column("ref", "oidbib"))]

        columns += [_Column("ref", "bibcode"),
                    _Column("has_ref", "obj_freq")]

        instance_criteria.append(f"bibcode = '{_adql_parameter(bibcode)}'")
        if criteria:
            instance_criteria.append(f"({criteria})")

        return self._query(top, columns, joins, instance_criteria,
                           get_query_payload=get_query_payload)

    @deprecated_renamed_argument(["verbose", "cache"], new_name=[None, None],
                                 since=['0.4.8', '0.4.8'], relax=True)
    def query_bibcode(self, bibcode, *, wildcard=False,
                      abstract=False, get_query_payload=False, criteria=None,
                      verbose=None, cache=None, ):
        """Query the references corresponding to a given bibcode.

        Wildcards may be used to specify bibcodes.

        Parameters
        ----------
        bibcode : str
            The bibcode of the article to be queried
        wildcard : bool, defaults to False
            When it is set to `True` it implies that the object is specified
            with wildcards.
        abstract : bool, defaults to False
            When this is set to `True`, the abstract of the article is also included
            to the result.
        criteria : str
            Criteria to be applied to the query. These should be written in the ADQL
            syntax in a single string. See example.
        get_query_payload : bool, optional
            When set to `True` the method returns the HTTP request parameters without
            querying SIMBAD. The ADQL string is in the 'QUERY' key of the payload.
            Defaults to `False`.
        cache : Deprecated since 0.4.8. The cache is now automatically emptied at the
            end of the python session. It can also be emptied manually with
            `~astroquery.simbad.SimbadClass.clear_cache` but cannot be deactivated.

        Returns
        -------
        table : `~astropy.table.Table`
            Query results table

        Examples
        --------
        >>> from astroquery.simbad import Simbad
        >>> simbad = Simbad()
        >>> simbad.ROW_LIMIT = 5
        >>> simbad.query_bibcode("2016PhRvL.*", wildcard=True,
        ...                      criteria="title LIKE '%gravitational wave%coalescence.'") # doctest: +REMOTE_DATA
        <Table length=1>
              bibcode                    doi               journal ... volume  year
               object                   object              object ... int32  int16
        ------------------- ------------------------------ ------- ... ------ -----
        2016PhRvL.116x1103A 10.1103/PhysRevLett.116.241103   PhRvL ...    116  2016
        """
        ref_columns = ["bibcode", "doi", "journal", "nbobject", "page", "last_page",
                       "title", "volume", "year"]
        # abstract option
        if abstract:
            ref_columns.append("abstract")
        ref_columns = str(ref_columns).replace("'", '"')[1:-1]

        # take row limit
        if self.ROW_LIMIT != -1:
            query = f"SELECT TOP {self.ROW_LIMIT} {ref_columns} FROM ref WHERE "
        else:
            query = f"SELECT {ref_columns} FROM ref WHERE "

        if wildcard:
            query += f"regexp(lowercase(bibcode), '{_wildcard_to_regexp(bibcode.casefold())}') = 1"
        else:
            query += f"bibcode = '{_adql_parameter(bibcode)}'"

        if criteria:
            query += f" AND {criteria}"

        query += " ORDER BY bibcode"

        return self.query_tap(query, get_query_payload=get_query_payload)

    @deprecated_renamed_argument(["verbose", "cache"], new_name=[None, None],
                                 since=['0.4.8', '0.4.8'], relax=True)
    def query_objectids(self, object_name, *, verbose=None, cache=None,
                        get_query_payload=False, criteria=None):
        """Query SIMBAD with an object name.

        This returns a table of all names associated with that object.

        Parameters
        ----------
        object_name : str
            name of object to be queried
        criteria : str
            an additional criteria to constrain the result. As the output of this
            method has only one column, these criteria can only be imposed on
            the column ``ident.id``.
        get_query_payload : bool, optional
            When set to `True` the method returns the HTTP request parameters without
            querying SIMBAD. The ADQL string is in the 'QUERY' key of the payload.
            Defaults to `False`.
        cache : Deprecated since 0.4.8. The cache is now automatically emptied at the
            end of the python session. It can also be emptied manually with
            `~astroquery.simbad.SimbadClass.clear_cache` but cannot be deactivated.

        Returns
        -------
        table : `~astropy.table.Table`
            The result of the query to SIMBAD.

        Examples
        --------
        Get all the names of the Bubble Nebula

        >>> from astroquery.simbad import Simbad
        >>> Simbad.query_objectids("bubble nebula") # doctest: +REMOTE_DATA
        <Table length=8>
                      id
                    object
        ------------------------------
        [ABB2014] WISE G112.212+00.229
                             LBN   548
                             NGC  7635
                             SH  2-162
                  [KC97c] G112.2+00.2b
                 [L89b] 112.237+00.226
                    GRS G112.22 +00.22
                    NAME Bubble Nebula

        Get the NGC name of M101

        >>> from astroquery.simbad import Simbad
        >>> Simbad.query_objectids("m101", criteria="ident.id LIKE 'NGC%'") # doctest: +REMOTE_DATA
        <Table length=1>
            id
          object
        ---------
        NGC  5457
        """
        query = ("SELECT ident.id FROM ident AS id_typed JOIN ident USING(oidref)"
                 f"WHERE id_typed.id = '{_adql_parameter(object_name)}'")
        if criteria is not None:
            query += f" AND {criteria}"
        return self.query_tap(query, get_query_payload=get_query_payload)

    @deprecated(since="v0.4.8",
                message=("'query_criteria' is deprecated. It uses the former sim-script "
                         "(SIMBAD specific) syntax "
                         "(see https://simbad.cds.unistra.fr/simbad/sim-fsam). "
                         "Possible replacements are the 'criteria' argument in the other "
                         "query methods or custom 'query_tap' queries. "
                         "These two replacements use the standard ADQL syntax."))
    def query_criteria(self, *args, get_query_payload=False, **kwargs):
        """Query SIMBAD based on any criteria [deprecated].

        This method is deprecated as it uses the former SIMBAD-specific sim-script syntax.
        There are two possible replacements that have been added with astroquery v0.4.8
        and that use the standard ADQL syntax. See the examples section.

        Parameters
        ----------
        args:
            String arguments passed directly to SIMBAD's script
            (e.g., 'region(box, GAL, 10.5 -10.5, 0.5d 0.5d)')
        get_query_payload : bool, optional
            When set to `True` the method returns the HTTP request parameters without
            querying SIMBAD. The ADQL string is in the 'QUERY' key of the payload.
            Defaults to `False`.
        kwargs:
            Keyword / value pairs passed to SIMBAD's script engine
            (e.g., {'otype'='SNR'} will be rendered as otype=SNR)

        Returns
        -------
        table : `~astropy.table.Table`
            Query results table

        Examples
        --------

        Can be replaced by the ``criteria`` argument that was added in the
        other query_*** methods

        >>> from astroquery.simbad import Simbad
        >>> Simbad(ROW_LIMIT=5).query_region('M1', '2d', criteria="otype='G..'") # doctest: +REMOTE_DATA +IGNORE_OUTPUT
        <Table length=5>
          main_id            ra        ... coo_wavelength     coo_bibcode
                            deg        ...
           object         float64      ...      str1             object
        ------------ ----------------- ... -------------- -------------------
        LEDA  136099 85.48166666666667 ...                1996A&AS..117....1S
        LEDA  136047 83.66958333333332 ...                1996A&AS..117....1S
        LEDA  136057 84.64499999999998 ...                1996A&AS..117....1S
        LEDA 1630996 83.99208333333333 ...              O 2003A&A...412...45P
          2MFGC 4574 84.37534166666669 ...              I 2006AJ....131.1163S

        Or by custom-written ADQL queries

        >>> from astroquery.simbad import Simbad
        >>> Simbad.query_tap("SELECT TOP 5 main_id, sp_type"
        ...                  " FROM basic WHERE sp_type < 'F3'") # doctest: +REMOTE_DATA +IGNORE_OUTPUT
        <Table length=5>
          main_id   sp_type
           object    object
        ----------- -------
         HD  24033B     (A)
         HD  70218B     (A)
         HD 128284B   (A/F)
        CD-34  5319   (A/F)
          HD  80593   (A0)V
        """
        top, columns, joins, instance_criteria = self._get_query_parameters()
        list_kwargs = [f"{key}='{argument}'" for key, argument in kwargs.items()]
        added_criteria = f"({CriteriaTranslator.parse(' & '.join(list(list(args) + list_kwargs)))})"
        instance_criteria.append(added_criteria)
        if "otypes." in added_criteria:
            joins.append(_Join("otypes", _Column("basic", "oid"),
                               _Column("otypes", "oidref")))
        if "allfluxes." in added_criteria:
            joins.append(_Join("allfluxes", _Column("basic", "oid"),
                               _Column("allfluxes", "oidref")))
        return self._query(top, columns, joins, instance_criteria,
                           get_query_payload=get_query_payload)

    @deprecated_renamed_argument("get_adql", new_name="get_query_payload",
                                 since='0.4.8', relax=True)
    def list_tables(self, *, get_query_payload=False):
        """List the names and descriptions of the tables in SIMBAD.

        Parameters
        ----------
        get_query_payload : bool, optional
            When set to `True` the method returns the HTTP request parameters without
            querying SIMBAD. The ADQL string is in the 'QUERY' key of the payload.
            Defaults to `False`.
        get_adql : bool, optional
            Deprecated since '0.4.8'. This is replaced by get_query_payload that contain
            more information than just the ADQL string

        Returns
        -------
        `~astropy.table.Table`
        """
        query = ("SELECT table_name, description"
                 " FROM TAP_SCHEMA.tables"
                 " WHERE schema_name = 'public'")
        return self.query_tap(query, get_query_payload=get_query_payload)

    @deprecated_renamed_argument("get_adql", new_name="get_query_payload",
                                 since='0.4.8', relax=True)
    def list_columns(self, *tables: str, keyword=None, get_query_payload=False):
        """Get the list of SIMBAD columns.

        Add tables names to restrict to some tables. Call the function without
        any parameter to get all columns names from all tables. The keyword argument
        looks for columns in the selected SIMBAD tables that contain the
        given keyword. The keyword search is not case-sensitive.

        Parameters
        ----------
        *tables : str, optional
            Add tables names as strings to restrict to these tables columns.
            This is not case-sensitive.
        keyword : str, optional
            A keyword to look for in column names, table names, or descriptions.
        get_query_payload : bool, optional
            When set to `True` the method returns the HTTP request parameters without
            querying SIMBAD. The ADQL string is in the 'QUERY' key of the payload.
            Defaults to `False`.
        get_adql : bool, optional
            Deprecated since '0.4.8'. This is replaced by get_query_payload that contain
            more information than just the ADQL string

        Returns
        -------
        `~astropy.table.Table`

        Examples
        --------
        >>> from astroquery.simbad import Simbad
        >>> Simbad.list_columns("ids", "ident") # doctest: +REMOTE_DATA
        <Table length=4>
        table_name column_name datatype ...  unit    ucd
          object      object    object  ... object  object
        ---------- ----------- -------- ... ------ -------
             ident          id  VARCHAR ...        meta.id
             ident      oidref   BIGINT ...
               ids         ids  VARCHAR ...        meta.id
               ids      oidref   BIGINT ...


        >>> from astroquery.simbad import Simbad
        >>> Simbad.list_columns(keyword="filter") # doctest: +REMOTE_DATA
        <Table length=5>
         table_name column_name   datatype  ...  unit           ucd
           object      object      object   ... object         object
        ----------- ----------- ----------- ... ------ ----------------------
             filter description UNICODECHAR ...        meta.note;instr.filter
             filter  filtername     VARCHAR ...                  instr.filter
             filter        unit     VARCHAR ...                     meta.unit
               flux      filter     VARCHAR ...                  instr.filter
        mesDiameter      filter        CHAR ...                  instr.filter

        >>> from astroquery.simbad import Simbad
        >>> Simbad.list_columns("basic", keyword="object") # doctest: +REMOTE_DATA
        <Table length=4>
        table_name column_name datatype ...  unit          ucd
          object      object    object  ... object        object
        ---------- ----------- -------- ... ------ -------------------
             basic     main_id  VARCHAR ...          meta.id;meta.main
             basic   otype_txt  VARCHAR ...                  src.class
             basic         oid   BIGINT ...        meta.record;meta.id
             basic       otype  VARCHAR ...                  src.class
        """
        query = ("SELECT table_name, column_name, datatype, description, unit, ucd"
                 " FROM TAP_SCHEMA.columns"
                 " WHERE table_name NOT LIKE 'TAP_SCHEMA.%'")
        # select the tables
        tables = tuple(map(str.casefold, tables))
        if len(tables) == 1:
            query += f" AND LOWERCASE(table_name) = '{tables[0]}'"
        elif len(tables) > 1:
            query += f" AND LOWERCASE(table_name) IN {tables}"
        # add the keyword condition
        if keyword is not None:
            condition = f"LIKE LOWERCASE('%{_adql_parameter(keyword)}%')"
            query += (f" AND ( (LOWERCASE(column_name) {condition})"
                      f" OR (LOWERCASE(description) {condition})"
                      f" OR (LOWERCASE(table_name) {condition}))")
        query += " ORDER BY table_name, principal DESC, column_name"
        return self.query_tap(query, get_query_payload=get_query_payload)

    def list_linked_tables(self, table: str, *, get_query_payload=False):
        """Expose the tables that can be non-obviously linked with the given table.

        This list contains only the links where the column names are not the same in the
        two tables. For example every ``oidref`` column of any table can be joined with
        any other ``oidref``. The same goes for every ``otype`` column even if this is not
        returned by this method.

        Parameters
        ----------
        table : str
            One of SIMBAD's tables name
        get_query_payload : bool, optional
            When set to `True` the method returns the HTTP request parameters without
            querying SIMBAD. The ADQL string is in the 'QUERY' key of the payload.
            Defaults to `False`.

        Returns
        -------
        `~astropy.table.Table`
            The information necessary to join the given table to an other.

        Examples
        --------
        >>> from astroquery.simbad import Simbad
        >>> Simbad.list_linked_tables("otypes") # doctest: +REMOTE_DATA
        <Table length=2>
        from_table from_column target_table target_column
          object      object      object        object
        ---------- ----------- ------------ -------------
          otypedef       otype       otypes         otype
            otypes      oidref        basic           oid
        """
        query = ("SELECT from_table, from_column, target_table, target_column"
                 " FROM TAP_SCHEMA.key_columns JOIN TAP_SCHEMA.keys USING (key_id)"
                 f" WHERE (from_table = '{_adql_parameter(table)}')"
                 f" OR (target_table = '{_adql_parameter(table)}')")
        return self.query_tap(query, get_query_payload=get_query_payload)

    def query_tap(self, query: str, *, maxrec=10000, get_query_payload=False, **uploads):
        """Query SIMBAD TAP service.

        Parameters
        ----------
        query : str
            A string containing the query written in the
            Astronomical Data Query Language (ADQL).
        maxrec : int, default: 10000
            The number of records to be returned. Its maximum value is given by
            `~astroquery.simbad.SimbadClass.hardlimit`.
        uploads : `~astropy.table.Table` | `~astropy.io.votable.tree.VOTableFile` | `~pyvo.dal.DALResults`
            Any number of local tables to be used in the *query*. In the *query*, these tables
            are referred as *TAP_UPLOAD.table_alias* where *TAP_UPLOAD* is imposed and *table_alias*
            is the keyword name you chose. The maximum number of lines for the uploaded tables is 200000.
        get_query_payload : bool, optional
            When set to `True` the method returns the HTTP request parameters without
            querying SIMBAD. The ADQL string is in the 'QUERY' key of the payload.
            Defaults to `False`.

        Returns
        -------
        `~astropy.table.Table`
            The response returned by Simbad.

        Notes
        -----
        A TAP (Table Access Protocol) service allows to query data tables with
        queries written in ADQL (Astronomical Data Query Language), a flavor
        of the more general SQL (Structured Query Language).
        For more documentation about writing ADQL queries, you can read its official
        documentation (`ADQL documentation <https://ivoa.net/documents/ADQL/index.html>`__)
        or the `Simbad ADQL cheat sheet <http://simbad.cds.unistra.fr/simbad/tap/help/adqlHelp.html>`__.
        See also: a `graphic representation of Simbad's tables and their relations
        <http://simbad.cds.unistra.fr/simbad/tap/tapsearch.html>`__.

        See Also
        --------
        list_tables : The list of SIMBAD's tables.
        list_columns : SIMBAD's columns list, can be restricted to some tables and some keyword.
        list_linked_tables : Given a table, expose non-obvious possible joins with other tables.

        Examples
        --------

        To see the five oldest papers referenced in SIMBAD

        >>> from astroquery.simbad import Simbad
        >>> Simbad.query_tap("SELECT top 5 bibcode, title "
        ...                  "FROM ref ORDER BY bibcode") # doctest: +REMOTE_DATA
        <Table length=5>
              bibcode       ...
               object       ...
        ------------------- ...
        1850CDT..1784..227M ...
        1857AN.....45...89S ...
        1861MNRAS..21...68B ...
        1874MNRAS..34...75S ...
        1877AN.....89...13W ...

        Get the type for a list of objects

        >>> from astroquery.simbad import Simbad
        >>> Simbad.query_tap("SELECT main_id, otype"
        ...                  " FROM basic WHERE main_id IN ('m10', 'm13')") # doctest: +REMOTE_DATA
        <Table length=2>
        main_id otype
         object object
        ------- ------
          M  10    GlC
          M  13    GlC

        Upload a table to use in a query

        >>> from astroquery.simbad import Simbad
        >>> from astropy.table import Table
        >>> letters_table = Table([["a", "b", "c"]], names=["alphabet"])
        >>> Simbad.query_tap("SELECT TAP_UPLOAD.my_table_name.* from TAP_UPLOAD.my_table_name",
        ...                  my_table_name=letters_table) # doctest: +REMOTE_DATA
        <Table length=3>
        alphabet
          str1
        --------
               a
               b
               c
        """
        if maxrec > self.hardlimit:
            raise ValueError(f"The maximum number of records cannot exceed {self.hardlimit}.")
        if query.count("'") % 2:
            raise ValueError("Query string contains an odd number of single quotes."
                             " Escape the unpaired single quote by doubling it.\n"
                             "ex: 'Barnard's galaxy' -> 'Barnard''s galaxy'.")
        if get_query_payload:
            return dict(TAPQuery(self.SIMBAD_URL, query, maxrec=maxrec, uploads=uploads))
        # without uploads we call the version with cache
        if uploads == {}:
            return _cached_query_tap(self.tap, query, maxrec=maxrec)
        # with uploads it has to be without cache
        return self.tap.run_async(query, maxrec=maxrec, uploads=uploads).to_table()

    @staticmethod
    def clear_cache():
        """Clear the cache of SIMBAD."""
        _cached_query_tap.cache_clear()
        gc.collect()

    # -----------------------------
    # Utility methods for query TAP
    # -----------------------------

    def _get_query_parameters(self):
        """Get the current building blocks of an ADQL query."""
        return tuple(map(copy.deepcopy, (self.ROW_LIMIT, self.columns_in_output, self.joins, self.criteria)))

    def _query(self, top, columns, joins, criteria, from_table="basic", distinct=False,
               get_query_payload=False, **uploads):
        """Generate an ADQL string from the given query parameters and executes the query.

        Parameters
        ----------
        top : int
            number of lines to be returned
        columns : List[SimbadClass.Column]
            The list of columns to be included in the output.
        joins : List[SimbadClass.Join]
            The list of joins to be made with basic.
        criteria : List[str]
            A list of strings. These criteria will be joined
            with an AND clause.
        from_table : str, optional
            The table after 'FROM' in the ADQL string. Defaults to "basic".
        distinct : bool, optional
            Whether to add the DISTINCT instruction to the query.
        get_query_payload : bool, optional
            When set to `True` the method returns the HTTP request parameters without
            querying SIMBAD. The ADQL string is in the 'QUERY' key of the payload.
            Defaults to `False`.
        uploads : `~astropy.table.Table`
            Any number of local tables to be used in the *query*. In the *query*, these tables
            are referred as *TAP_UPLOAD.table_alias* where *TAP_UPLOAD* is imposed and *table_alias*
            is the keyword name you chose. The maximum number of lines for the uploaded tables is 200000.

        Returns
        -------
        `~astropy.table.Table`
            The result of the query to SIMBAD.
        """
        distinct_results = " DISTINCT" if distinct else ""
        top_part = f" TOP {top}" if top != -1 else ""

        # columns
        input_columns = [f'{column.table}."{column.name}" AS "{column.alias}"' if column.alias is not None
                         else f'{column.table}."{column.name}"' for column in columns]
        # remove possible duplicates
        unique_columns = []
        [unique_columns.append(column) for column in input_columns if column not in unique_columns]
        columns = " " + ", ".join(unique_columns)
        # selecting all columns is the only case where this should not be a string
        columns = columns.replace('"*"', "*")

        # joins
        if joins == []:
            join = ""
        else:
            unique_joins = []
            [unique_joins.append(join) for join in joins if join not in unique_joins]
            # the joined tables can have an alias. We handle the two cases here
            join = " " + " ".join([(f'{join.join_type} {join.table} AS {join.alias} '
                                    f'ON {join.column_left.table}."{join.column_left.name}" = '
                                    f'{join.alias}."{join.column_right.name}"')
                                   if join.alias is not None else
                                   (f'{join.join_type} {join.table} ON {join.column_left.table}."'
                                    f'{join.column_left.name}" = {join.column_right.table}."'
                                    f'{join.column_right.name}"') for join in unique_joins])

        # criteria
        if criteria != []:
            criteria = f" WHERE {' AND '.join(criteria)}"
        else:
            criteria = ""

        query = f"SELECT{distinct_results}{top_part}{columns} FROM {from_table}{join}{criteria}"

        response = self.query_tap(query, get_query_payload=get_query_payload,
                                  maxrec=self.hardlimit,
                                  **uploads)

        if len(response) == 0 and top != 0:
            warnings.warn("The request executed correctly, but there was no data corresponding"
                          " to these criteria in SIMBAD", NoResultsWarning)
        return response


Simbad = SimbadClass()
