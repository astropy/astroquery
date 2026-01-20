# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
==========================================
Multi-Mission Data Services (EMDS)
==========================================

European Space Astronomy Centre (ESAC)
European Space Agency (ESA)

"""

from . import conf
from astroquery.utils import commons
import astroquery.esa.utils.utils as esautils

__all__ = ['Emds', 'EmdsClass']

class EmdsClass(esautils.EsaTap):

    """
    EMDS TAP client (multi-mission / multi-schema).

    EMDS provides access to multiple missions through a single TAP service. Mission data are
    organised under different TAP schemas. This client offers a small convenience layer to work
    with mission-specific tables while reusing the standard TAP utilities.
    """

    ESA_ARCHIVE_NAME = "ESA Multi-Mission Data Services (EMDS)"
    TAP_URL = conf.EMDS_TAP_SERVER
    LOGIN_URL = conf.EMDS_LOGIN_SERVER
    LOGOUT_URL = conf.EMDS_LOGOUT_SERVER

    def __init__(self, auth_session=None, tap_url=None):
        super().__init__(auth_session=auth_session, tap_url=tap_url)
        # IMPORTANT: ensure every instance has a config namespace.
        # Subclasses (missions) can overwrite this with their own module conf.
        self.conf = conf

    def _get_obscore_table(self) -> str:
        """
        Return the fully-qualified ObsCore table/view used by this client.
        Sub-clients override this by providing `conf.OBSCORE_TABLE`.
        """

        table = getattr(self.conf, "OBSCORE_TABLE", None)
        if not (isinstance(table, str) and table.strip()):
            raise ValueError(
                "OBSCORE_TABLE is not configured for this client. "
                "Please set conf.OBSCORE_TABLE to a fully-qualified name like 'schema.table'."
            )
        return table

    def _qualify_table_name(self, table_name: str) -> str:
        """
        Return a schema-qualified table name when needed.

        If the input table name does not include a schema, the default mission schema
        is applied when available. Fully-qualified table names are returned unchanged.

        Parameters
        ----------
        table_name : str
            Table name, either fully-qualified ('schema.table') or unqualified ('table').
        """

        if "." in table_name:
            return table_name

        default_schema = getattr(self.conf, "DEFAULT_SCHEMA", None)
        if isinstance(default_schema, str) and default_schema.strip():
            return f"{default_schema}.{table_name}"

        # Independent missions: do not modify.
        return table_name

    def get_tables(self, *, only_names=False):
        """
        Return the tables available for this mission.

        By default, only tables belonging to the mission-specific schema are returned.
        Set ``only_names=True`` to return table names instead of table objects.

        """

        tables = super().get_tables(only_names=only_names)

        schema = getattr(self.conf, "DEFAULT_SCHEMA", None)
        if not schema:
            return tables

        schema_prefix = schema.lower() + "."

        if only_names:
            return [t for t in tables if t.lower().startswith(schema_prefix)]
        else:
            return [
                t for t in tables
                if getattr(t, "name", "").lower().startswith(schema_prefix)
            ]

    def get_table(self, table):
        """
        Retrieve a table from the TAP service.

        Parameters
        ----------
        table : str
            Table name. It can be fully qualified (``schema.table``) or unqualified
            (``table``). Unqualified names are automatically prefixed with the default
            mission schema when available.

        """

        qualified = self._qualify_table_name(table)
        return super().get_table(qualified)

    def get_metadata(self, table):
        """
        Retrieve metadata for a table.

        The table name can be provided with or without a schema. If no schema is given,
        the default mission schema is applied when available.

        Parameters
        ----------
        table : str
            Table name. It can be fully qualified (``schema.table``) or unqualified
            (``table``). Unqualified names are automatically prefixed with the default
            mission schema when available.

        """

        qualified = self._qualify_table_name(table)
        return super().get_metadata(qualified)

    def query_table(self, table_name, *, columns=None, custom_filters=None, get_metadata=False,
                    async_job=False, output_file=None, output_format='votable', **filters):
        """
        Query a table in the TAP service.

        The table name can be provided with or without a schema. If no schema is given,
        the default mission schema is applied when available.

        Parameters
        ----------
        table_name : str
            Table name (either 'schema.table' or 'table').
        columns : str or list of str, optional
            Columns to retrieve.
        custom_filters : str, optional
            Additional ADQL conditions (e.g. cone search predicate).
        get_metadata : bool, optional
            If True, return column metadata for the table.
        async_job : bool, optional
            Run query asynchronously.
        output_file : str, optional
            Output filename.
        output_format : str, optional
            Output format (e.g. 'votable').
        **filters
            Column-based filters passed to the underlying implementation.

        """

        qualified = self._qualify_table_name(table_name)

        # Ensure the metadata path uses the qualified table name.
        if get_metadata:
            return self.get_metadata(qualified)

        return super().query_table(
            qualified,
            columns=columns,
            custom_filters=custom_filters,
            get_metadata=False,
            async_job=async_job,
            output_file=output_file,
            output_format=output_format,
            **filters
        )

    def get_emds_missions(self):
        """
        Retrieve the list of missions available in the EMDS ObsCore view.

        This method returns the distinct values of the ``obs_collection`` field
        from the ``ivoa.ObsCore`` view, where ``obs_collection`` typically
        identifies the mission or data collection associated with each observation.

        Returns
        -------
        astropy.table that contains the distinct mission identifiers present in ObsCore.
        """

        query = "SELECT DISTINCT obs_collection FROM ivoa.ObsCore WHERE obs_collection IS NOT NULL"
        return self.query_tap(query=query)

    def get_observations(self, *, target_name=None, coordinates=None, radius=1.0, columns=None, get_metadata=False,
                          output_file=None, **filters):
        """
        Query the observation catalogue for this mission.

        This method queries the mission-specific observation catalogue configured for
        this client and returns observation-level metadata as an Astropy table.
        Queries can be restricted using a cone search (by target name or coordinates)
        and additional column-based filters.

        Parameters
        ----------
        target_name: str, optional
            Name of the target to be resolved against SIMBAD/NED/VIZIER
        coordinates: str or SkyCoord, optional
            coordinates of the center in the cone search
        radius: float or quantity, optional, default value 1 degree
            radius in degrees (int, float) or quantity of the cone_search
        columns : str or list of str, optional, default None
            Columns from the table to be retrieved. They can be checked using
            get_metadata=True
        get_metadata : bool, optional, default False
            Get the table metadata to verify the columns that can be filtered
        output_file : str, optional, default None
            file name where the results are saved.
            If this parameter is not provided, the jobid is used instead
        **filters : str, optional, default None
            Filters to be applied to the search. The column name is the keyword and the value is any
            value accepted by the column datatype. They will be
            used to generate the SQL filters for the query. Some examples are described below,
            where the left side is the parameter defined for this method and the right side the
            SQL filter generated:
            obs_collection="EPSA" -> obs_collection = 'EPSA'
            target_name="AT 2023%" -> target_name ILIKE 'AT 2023%'
            dataproduct_type=["img", "pha"] -> dataproduct_type = 'img' OR dataproduct_type = 'pha'
            dataproduct_type=["img", "pha"] -> dataproduct_type IN ('img', 'pha')
            t_min=(">", 60000) -> t_min > 60000
            s_ra=(80, 82) -> s_ra >= 80 AND s_ra <= 82

        Returns
        -------
        An astropy.table containing the query results, or the metadata table when ``get_metadata=True``

        """

        cone_search_filter = None
        if radius:
            radius = esautils.get_degree_radius(radius)

        if target_name and coordinates:
            raise TypeError("Please use only target or coordinates as "
                            "parameter.")
        elif target_name:
            coordinates = esautils.resolve_target(conf.EMDS_TARGET_RESOLVER,
                                                  self.tap._session, target_name,
                                                  'ALL')
            cone_search_filter = self.create_cone_search_query(coordinates.ra.deg, coordinates.dec.deg,
                                                               "s_ra", "s_dec", radius)
        elif coordinates:
            coord = commons.parse_coordinates(coordinates=coordinates)
            ra = coord.ra.degree
            dec = coord.dec.degree
            cone_search_filter = self.create_cone_search_query(ra, dec, "s_ra", "s_dec", radius)

        obscore_table = self._get_obscore_table()
        return self.query_table(table_name=obscore_table, columns=columns, custom_filters=cone_search_filter,
                                get_metadata=get_metadata, async_job=True, output_file=output_file, **filters)

Emds = EmdsClass()
