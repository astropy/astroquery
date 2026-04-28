import difflib
from dataclasses import dataclass
from typing import Dict, Optional

from astropy.table import Table
from pyvo.dal import DALQueryError, TAPService

from .. import log
from ..exceptions import InvalidQueryError
from . import conf, utils

__all__ = ["CatalogCollection"]

DEFAULT_CATALOGS = {
    "caom": "dbo.obspointing",
    "gaiadr3": "dbo.gaia_source",
    "hsc": "dbo.SumMagAper2CatView",
    "hscv2": "dbo.SumMagAper2CatView",
    "missionmast": "dbo.hst_science_missionmast",
    "ps1dr1": "dbo.MeanObjectView",
    "ps1dr2": "dbo.MeanObjectView",
    "ps1_dr2": "ps1_dr2.forced_mean_object",
    "skymapperdr4": "dr4.master",
    "tic": "dbo.CatalogRecord",
    "classy": "dbo.targets",
    "ullyses": "dbo.sciencemetadata",
    "goods": "dbo.goods_master_view",
    "3dhst": "dbo.HLSP_3DHST_summary",
    "candels": "dbo.candels_master_view",
    "deepspace": "dbo.DeepSpace_Summary",
    "tic_v82": "tic_v82.source",
}

GROUPED_COLLECTION_ENDPOINTS = ["mast_catalogs", "roman_catalogs"]


@dataclass
class CatalogMetadata:
    """
    Data class to hold metadata about a catalog, including column metadata,
    RA/Dec column names, and spatial query support.
    """

    column_metadata: Table
    ra_column: Optional[str]
    dec_column: Optional[str]
    supports_spatial_queries: bool


class CatalogCollection:
    """
    This class provides an interface to interact with MAST catalog collections via TAP service.
    """

    TAP_BASE_URL = conf.server + "/vo-tap/api/v0.1/"
    _discovered_collections = None
    _collection_parent_map = None

    @classmethod
    def discover_collections(cls):
        """
        Discover collection names available through TAP and track parent collections.

        Returns
        -------
        `~astropy.table.Table`
            A table containing collection_name and parent_collection columns.
        """
        if cls._discovered_collections is not None:
            return cls._discovered_collections

        # Query TAP service for collection names
        url = cls.TAP_BASE_URL + "openapi.json"
        response = utils._simple_request(url)
        response.raise_for_status()
        data = response.json()

        try:
            collection_enum = data["components"]["schemas"]["CatalogName"]["enum"]
        except KeyError:
            raise RuntimeError("Failed to discover collections from TAP service: Unexpected response format")

        collection_parent_map = {}

        # Discover collections stored under grouped TAP collections
        for parent_collection in GROUPED_COLLECTION_ENDPOINTS:
            if parent_collection not in collection_enum:
                continue

            tap_service = TAPService(cls.TAP_BASE_URL + parent_collection)
            result = tap_service.run_sync("SELECT TOP 5000 table_name FROM tap_schema.tables")
            tables = result.to_table()

            for table_name in tables["table_name"]:
                table_name = str(table_name)
                if table_name.lower().startswith("tap_schema."):
                    continue

                collection_name = table_name.split(".", 1)[0].lower()
                collection_parent_map.setdefault(collection_name, parent_collection)

        # Include standalone collections in map
        for collection_name in collection_enum:
            normalized_name = collection_name.lower()
            if normalized_name in GROUPED_COLLECTION_ENDPOINTS:
                continue
            collection_parent_map.setdefault(normalized_name, normalized_name)

        collection_names = sorted(collection_parent_map.keys())
        parent_names = [collection_parent_map[name] for name in collection_names]
        cls._collection_parent_map = collection_parent_map
        cls._discovered_collections = Table(
            [collection_names, parent_names],
            names=("collection_name", "parent_collection"),
        )

        return cls._discovered_collections

    @classmethod
    def get_parent_collection(cls, collection_name):
        """
        Return the parent TAP collection for a user-facing collection name.

        Parameters
        ----------
        collection_name : str
            The user-facing collection name to get the parent collection for.
        """
        if not isinstance(collection_name, str):
            raise InvalidQueryError(f"Collection name must be a string, got {type(collection_name)}")

        if cls._collection_parent_map is None:
            cls.discover_collections()

        normalized_name = collection_name.lower().strip()
        parent_collection = cls._collection_parent_map.get(normalized_name)

        if parent_collection is None:
            raise InvalidQueryError(f"Collection '{collection_name}' not found")

        return parent_collection

    def __init__(self, collection):
        """
        Initialize a CatalogCollection object for interacting with a MAST catalog collection.

        Parameters
        ----------
        collection : str
            The name of the MAST catalog collection to interact with.
        """
        if not isinstance(collection, str):
            raise ValueError(f"Collection name must be a string, got {type(collection)}")

        self.name = collection.strip().lower()
        self._parent_collection = None
        self._tap_service = None

        # Get catalogs within this collection
        self._catalogs = None  # Lazy-loaded property

        # ADQL functions supported by this collection's TAP service
        self._supported_adql_functions = None  # Lazy-loaded property

        # Determine the default catalog lazily to avoid requests during initialization
        self._default_catalog = None

        # Cache for catalog metadata to avoid redundant queries
        self._catalog_metadata_cache: Dict[str, CatalogMetadata] = dict()

        # Cache the catalog lookup mapping for validating catalog names in queries
        self._catalog_lookup = None
        self._no_prefix_lookup = None

    @property
    def parent_collection(self):
        if self._parent_collection is None:
            self._parent_collection = self.get_parent_collection(self.name)
        return self._parent_collection

    @property
    def tap_service(self):
        if self._tap_service is None:
            self._tap_service = TAPService(self.TAP_BASE_URL + self.parent_collection)
        return self._tap_service

    @property
    def default_catalog(self):
        if self._default_catalog is None:
            self._default_catalog = self.get_default_catalog()
        return self._default_catalog

    @property
    def catalogs(self):
        if self._catalogs is None:
            self._catalogs = self._fetch_catalogs()
        return self._catalogs

    @property
    def catalog_names(self):
        return self.catalogs["catalog_name"].tolist()

    @property
    def supported_adql_functions(self):
        if self._supported_adql_functions is None:
            self._supported_adql_functions = self._fetch_adql_supported_functions()
        return self._supported_adql_functions

    def get_catalog_metadata(self, catalog):
        """
        For a given catalog, cache and return metadata about its columns and capabilities.

        Parameters
        ----------
        catalog : str
            The catalog within the collection to get metadata for.

        Returns
        -------
        CatalogMetadata
            A CatalogMetadata object containing metadata about the specified catalog, including column metadata,
            RA/Dec column names, and spatial query support.
        """
        # Verify catalog validity for this collection
        catalog = self._verify_catalog(catalog)

        # Check cache first
        if catalog in self._catalog_metadata_cache:
            return self._catalog_metadata_cache[catalog]

        # Get column metadata
        metadata = self._get_column_metadata(catalog)

        # Get RA/Dec column names
        ra_col, dec_col = self._get_ra_dec_column_names(metadata)

        # Determine if spatial queries are supported
        supports_adql_geometry = all(func in self.supported_adql_functions for func in ("POINT", "CIRCLE", "CONTAINS"))

        # Try an inexpensive spatial query if RA/Dec columns are known
        supports_spatial_queries = supports_adql_geometry and ra_col is not None and dec_col is not None
        if supports_spatial_queries:
            # If an ra and dec column exist, test spatial query support
            spatial_query = (
                f"SELECT TOP 0 * FROM {catalog} WHERE CONTAINS(POINT('ICRS', {ra_col}, {dec_col}), "
                "CIRCLE('ICRS', 0, 0, 0.001)) = 1"
            )
            try:
                self.tap_service.search(spatial_query)
            except DALQueryError:
                supports_spatial_queries = False

        meta = CatalogMetadata(
            column_metadata=metadata,
            ra_column=ra_col,
            dec_column=dec_col,
            supports_spatial_queries=supports_spatial_queries,
        )

        # Cache and return
        self._catalog_metadata_cache[catalog] = meta
        return meta

    def get_default_catalog(self):
        """
        Get the default catalog for this collection. This is the first catalog that does not start with "tap_schema.".

        Returns
        -------
        str
            The default catalog name.
        """
        # Check if collection has a known default catalog
        if self.name in DEFAULT_CATALOGS:
            return DEFAULT_CATALOGS[self.name]

        # Pick default catalog = first one that does NOT start with "tap_schema."
        default_catalog = next((c for c in self.catalog_names if not c.startswith("tap_schema.")), None)

        # If no valid catalog found, fallback to the first one
        if default_catalog is None:
            default_catalog = self.catalog_names[0] if self.catalog_names else None

        return default_catalog

    def run_tap_query(self, adql):
        """
        Run a TAP query against the specified catalog.

        Parameters
        ----------
        adql : str
            The ADQL query string.

        Returns
        -------
        response : `~astropy.table.Table`
            The result of the TAP query as an Astropy Table.
        """
        log.debug(f"Running TAP query on collection '{self.name}': {adql}")
        try:
            result = self.tap_service.run_sync(adql)
        except DALQueryError as e:
            raise InvalidQueryError(f"TAP query failed for collection '{self.name}': {e}")
        return result.to_table()

    def _fetch_catalogs(self):
        """
        Retrieve the list of catalogs in this collection.

        Returns
        -------
        `~astropy.table.Table`
            A table containing the catalog names and descriptions for this collection.
        """
        log.debug(f"Fetching available tables for collection '{self.name}' from MAST TAP service.")
        query = "SELECT TOP 5000 table_name, description FROM tap_schema.tables"

        # If this catalog is within a grouped collection, filter to only tables that belong to this collection
        if self.parent_collection in GROUPED_COLLECTION_ENDPOINTS:
            query += f" WHERE table_name LIKE '{self.name}.%'"

        result = self.tap_service.run_sync(query)

        # Rename table_name to catalog_name for clarity
        result_table = result.to_table()
        result_table.rename_column("table_name", "catalog_name")

        return result_table

    def _fetch_adql_supported_functions(self):
        """
        Retrieve the ADQL supported functions of the TAP service.

        Returns
        -------
        set
            A set of supported ADQL geometry functions (e.g. "POINT", "CIRCLE", "CONTAINS", etc.) for
            this collection's TAP service.
        """
        adql_functions = ["CIRCLE", "POLYGON", "POINT", "CONTAINS", "INTERSECTS"]
        supported = set()
        feature_id = "ivo://ivoa.net/std/TAPRegExt#features-adqlgeo"
        for capability in self.tap_service.capabilities:
            if capability.standardid != "ivo://ivoa.net/std/TAP":
                continue

            for lang in capability.languages:
                if lang.name != "ADQL":
                    continue

                for func in adql_functions:
                    if lang.get_feature(feature_id, func):
                        supported.add(func)

        return supported

    def _verify_catalog(self, catalog):
        """
        Verify that the specified catalog is valid for this collection and return the correct catalog name.
        Raises an error if the catalog is not valid.

        Parameters
        ----------
        catalog : str
            The catalog to be verified.

        Returns
        -------
        str
            The validated catalog name.

        Raises
        ------
        InvalidQueryError
            If the specified catalog is not valid for the given collection.
        """
        catalog = catalog.lower().strip()

        if self._catalog_lookup is not None and self._no_prefix_lookup is not None:
            lookup = self._catalog_lookup
            no_prefix_map = self._no_prefix_lookup
        else:
            # Build a mapping for case-insensitive and no-prefix lookup
            lookup = {}
            no_prefix_map = {}
            for cat in self.catalog_names:
                cat_lower = cat.lower()
                lookup[cat_lower] = cat  # case-insensitive match
                no_prefix = cat_lower.split(".")[-1]
                if no_prefix not in no_prefix_map:
                    no_prefix_map[no_prefix] = [cat]  # no-prefix match (first occurrence)
                else:
                    no_prefix_map[no_prefix].append(cat)

            # Add unambiguous no-prefix matches to lookup
            for no_prefix, cats in no_prefix_map.items():
                if len(cats) == 1:
                    lookup[no_prefix] = cats[0]

            # Cache the lookup maps for future calls
            self._catalog_lookup = lookup
            self._no_prefix_lookup = no_prefix_map

        # Direct or unambiguous no-prefix match
        if catalog in lookup:
            return lookup[catalog]

        # Check for ambiguous no-prefix matches
        if catalog in no_prefix_map and len(no_prefix_map[catalog]) > 1:
            matches = ", ".join(no_prefix_map[catalog])
            raise InvalidQueryError(
                f"Catalog '{catalog}' is ambiguous for collection '{self.name}'. "
                f"It matches multiple catalogs: {matches}. Please specify the full catalog name."
            )

        # Suggest closest match (based on full catalog names)
        closest = difflib.get_close_matches(catalog, self.catalog_names, n=1)
        suggestion = f" Did you mean '{closest[0]}'?" if closest else ""

        raise InvalidQueryError(
            f"Catalog '{catalog}' is not recognized for collection '{self.name}'."
            f"{suggestion} Available catalogs are: {', '.join(self.catalog_names)}"
        )

    def _get_column_metadata(self, catalog):
        """
        For a given catalog, return metadata about its columns.

        Parameters
        ----------
        catalog : str
            The catalog within the collection to get metadata for.

        Returns
        -------
        response : `~astropy.table.Table`
            A table containing metadata about the specified table, including column names, data types, and descriptions.
        """
        log.debug(f"Fetching column metadata for collection '{self.name}', catalog '{catalog}' from MAST TAP service.")

        query = f"""
            SELECT TOP 5000
                column_name,
                datatype,
                unit,
                ucd,
                description
            FROM tap_schema.columns
            WHERE table_name = '{catalog}'
        """
        result = self.tap_service.run_sync(query)

        if len(result) == 0:
            raise InvalidQueryError(f"Catalog '{catalog}' not found in collection '{self.name}'.")

        return result.to_table()

    def _get_ra_dec_column_names(self, column_metadata):
        """
        Return the RA and Dec column names for a given catalog and table.

        Parameters
        ----------
        column_metadata : `~astropy.table.Table`
            The column metadata table for a catalog.

        Returns
        -------
        tuple
            A tuple containing the (ra_column, dec_column) names.
        """
        # Look for a column with UCD 'pos.eq.ra;meta.main' and 'pos.eq.dec;meta.main'
        ra_col = None
        dec_col = None
        for name, ucd in zip(column_metadata["column_name"], column_metadata["ucd"]):
            if ucd and "pos.eq.ra;meta.main" in ucd.lower():
                # TODO: ps1_dr2.mean_object and ps1_dr2.stacked_object has a column that can be used,
                # but is not labeled with "meta.main"
                ra_col = name
            elif ucd and "pos.eq.dec;meta.main" in ucd.lower():
                dec_col = name
        return ra_col, dec_col

    def _verify_criteria(self, catalog, **criteria):
        """
        Check that criteria keyword arguments are valid column names for the specified collection and catalog.

        Parameters
        ----------
        catalog : str
            The catalog within the collection to query.
        **criteria
            Keyword arguments representing criteria filters to apply.

        Raises
        ------
        InvalidQueryError
            If a keyword does not match any valid column names, an error is raised that suggests the closest
            matching column name, if available.
        """
        if not criteria:
            return
        col_names = list(self.get_catalog_metadata(catalog).column_metadata["column_name"])
        col_name_lookup = {col.lower(): col for col in col_names}

        # Check each criteria argument for validity
        for kwd in criteria:
            if kwd.lower() not in col_name_lookup:
                # Suggest closest match for invalid keyword
                closest = difflib.get_close_matches(kwd.lower(), list(col_name_lookup.keys()), n=1)
                suggestion = f" Did you mean '{col_name_lookup[closest[0]]}'?" if closest else ""
                raise InvalidQueryError(
                    f"Filter '{kwd}' is not recognized for collection '{self.name}' and "
                    f"catalog '{catalog}'.{suggestion}"
                )
