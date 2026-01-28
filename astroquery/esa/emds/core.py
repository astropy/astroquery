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
from html import unescape
import os
import astroquery.esa.utils.utils as esautils
from astroquery.esa.utils import EsaTap, download_file

__all__ = ['Emds', 'EmdsClass']


class EmdsClass(EsaTap):

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

    def get_tables(self, *, only_names: bool = False):
        """
        Return the tables available for this mission.

        By default, only tables belonging to the mission-specific schema(s) are returned.
        Set ``only_names=True`` to return table names instead of table objects.

        Parameters
        ----------
        only_names : bool, optional
            If True, return table names as strings. If False, return table objects.

        Returns
        -------
        list
            Table names (str) if ``only_names=True``, otherwise table objects.

        """

        tables = super().get_tables(only_names=only_names)

        schemas = getattr(self.conf, "DEFAULT_SCHEMAS", "")
        if not isinstance(schemas, str) or not schemas.strip():
            # No schema filtering configured: return all tables
            return tables

        # Split and normalize schema names
        schemas_list = [s.strip() for s in schemas.split(",") if s.strip()]

        # Build lowercase schema prefixes
        schema_prefixes = tuple(s.lower() + "." for s in schemas_list)

        # Check whether a table belongs to one of the schemas
        def belongs(name: str) -> bool:
            n = (name or "").lower()
            return n.startswith(schema_prefixes)

        if only_names:
            # Filter table names (strings)
            return [t for t in tables if belongs(t)]
        else:
            # Filter table objects using their 'name' attribute
            return [
                t for t in tables
                if belongs(getattr(t, "name", ""))
            ]

    def get_missions(self):
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

    def get_products(self, *, target_name=None, coordinates=None, radius=1.0, get_metadata=False, **filters):

        """
        Retrieve data products given a Taget Name, coordinates and/or some filters

        This method queries the mission product catalogue and returns product-level
        information. It ensures that the ``obs_publisher_did`` and ``access_url`` columns required
        for downloading products are included in the results.

        Parameters
        ----------
        target_name: str, optional
            Name of the target to be resolved against SIMBAD/NED/VIZIER
        coordinates: str or SkyCoord, optional
            coordinates of the center in the cone search
        radius: float or quantity, optional, default value 1 degree
            radius in degrees (int, float) or quantity of the cone_search
        get_metadata : bool, optional, default False
            Get the table metadata to verify the columns that can be filtered
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
        astropy.table.Table
        """
        return self.get_observations(target_name=target_name, coordinates=coordinates, radius=radius,
                                     columns=['obs_id', 'obs_publisher_did', 'access_url'],
                                     get_metadata=get_metadata, **filters)

    def download_products(self, products, *, path="", cache=False, cache_folder=None,
                          verbose=False, params=None):
        """
        Download all products from a table returned by `get_products()`.


        Parameters
        ----------
        products : `~astropy.table.Table`
            Table returned by `get_products()`. The table must contain the
            ``access_url`` and ``obs_publisher_did`` columns.
        path : str, optional
            Local directory where the downloaded files will be stored.
            If not provided, files are downloaded to the current working directory.
            Ignored if ``cache=True``.
        cache : bool, optional
            If True, store the downloaded files in the Astroquery cache.
            Default is False.
        cache_folder : str, optional
            Subdirectory within the Astroquery cache where files will be stored.
            Only used if ``cache=True``.
        verbose : bool, optional
            If True, print progress messages during download.
            Default is False.
        params : dict, optional
            Additional parameters passed to the HTTP request.

        Returns
        -------
        list of str
            List of local file paths for the downloaded products.
        """
        if products is None or len(products) == 0:
            return []

        if "access_url" not in products.colnames:
            raise ValueError("Products table must contain an 'access_url' column.")

        if "obs_publisher_did" not in products.colnames:
            raise ValueError("Products table must contain an 'obs_publisher_did' column.")

        if path and not cache:
            os.makedirs(path, exist_ok=True)

        downloaded = []

        for row in products:
            url = unescape(row["access_url"])
            session = self.tap._session

            file_path = download_file(
                url,
                session,
                params=params,
                path=path,
                cache=cache,
                cache_folder=cache_folder,
                verbose=verbose,
            )
            downloaded.append(file_path)

        return downloaded


Emds = EmdsClass()
