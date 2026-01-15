import difflib
from dataclasses import dataclass
from typing import Dict, Optional

from pyvo.dal import TAPService, DALQueryError
from astropy.table import Table

from astroquery import log
from astroquery.exceptions import InvalidQueryError

__all__ = ['CatalogCollection']

DEFAULT_CATALOGS = {
    'caom': 'dbo.obspointing',
    'gaiadr3': 'dbo.gaia_source',
    'hsc': 'dbo.SumMagAper2CatView',
    'hscv2': 'dbo.SumMagAper2CatView',
    'missionmast': 'dbo.hst_science_missionmast',
    'ps1dr1': 'dbo.MeanObjectView',
    'ps1dr2': 'dbo.MeanObjectView',
    'ps1_dr2': 'ps1_dr2.forced_mean_object',
    'skymapperdr4': 'dr4.master',
    'tic': 'dbo.CatalogRecord',
    'classy': 'dbo.targets',
    'ullyses': 'dbo.sciencemetadata',
    'goods': 'dbo.goods_master_view',
    '3dhst': 'dbo.HLSP_3DHST_summary',
    'candels': 'dbo.candels_master_view',
    'deepspace': 'dbo.DeepSpace_Summary'
}


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

    TAP_BASE_URL = 'https://masttest.stsci.edu/vo-tap/api/v0.1/'

    def __init__(self, collection):
        """
        Initialize a CatalogCollection object for interacting with a MAST catalog collection.

        Parameters
        ----------
        collection : str
            The name of the MAST catalog collection to interact with.
        """
        self.name = collection.strip().lower()
        # Initialize TAP service for the specified collection
        self.tap_service = TAPService(self.TAP_BASE_URL + self.name)

        # Get catalogs within this collection
        self._catalogs = None  # Lazy-loaded property

        # ADQL functions supported by this collection's TAP service
        self._supported_adql_functions = None  # Lazy-loaded property

        # Determine the default catalog for this collection
        self.default_catalog = self.get_default_catalog()

        # Cache for catalog metadata to avoid redundant queries
        self._catalog_metadata_cache: Dict[str, CatalogMetadata] = dict()

    @property
    def catalogs(self):
        if self._catalogs is None:
            self._catalogs = self._fetch_catalogs()
        return self._catalogs

    @property
    def catalog_names(self):
        return self.catalogs['catalog_name'].tolist()

    @property
    def supported_adql_functions(self):
        if self._supported_adql_functions is None:
            self._supported_adql_functions = self._fetch_adql_supported_functions()
        return self._supported_adql_functions

    def get_catalog_metadata(self, catalog):
        """
        For a given catalog, cache and return metadata about its columns and capabilties.

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
        supports_adql_geometry = all(
            func in self.supported_adql_functions
            for func in ('POINT', 'CIRCLE', 'CONTAINS')
        )

        # Try an inexpensive spatial query if RA/Dec columns are known
        supports_spatial_queries = (supports_adql_geometry and ra_col is not None and dec_col is not None)
        if supports_spatial_queries:
            # If an ra and dec column exist, test spatial query support
            spatial_query = (f'SELECT TOP 0 * FROM {catalog} WHERE CONTAINS(POINT(\'ICRS\', {ra_col}, {dec_col}), '
                             'CIRCLE(\'ICRS\', 0, 0, 0.001)) = 1')
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
        list of str
            List of catalog names.
        """
        log.debug(f"Fetching available tables for collection '{self.name}' from MAST TAP service.")
        query = 'SELECT table_name, description FROM tap_schema.tables'
        result = self.tap_service.run_sync(query)

        # Rename table_name to catalog_name for clarity
        result_table = result.to_table()
        result_table.rename_column('table_name', 'catalog_name')
        return result_table

    def _fetch_adql_supported_functions(self):
        """
        Retrieve the ADQL supported functions of the TAP service.

        Returns
        -------
        list
            A list of supported ADQL functions.
        """
        adql_functions = ['CIRCLE', 'POLYGON', 'POINT', 'CONTAINS', 'INTERSECTS']
        supported = []
        feature_id = 'ivo://ivoa.net/std/TAPRegExt#features-adqlgeo'
        for capability in self.tap_service.capabilities:
            if capability.standardid != 'ivo://ivoa.net/std/TAP':
                continue

            for lang in capability.languages:
                if lang.name != 'ADQL':
                    continue

                for func in adql_functions:
                    if lang.get_feature(feature_id, func):
                        supported.append(func)

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
        catalog = catalog.lower()

        # Build a mapping for case-insensitive and no-prefix lookup
        lookup = {}
        no_prefix_map = {}
        for cat in self.catalog_names:
            cat_lower = cat.lower()
            lookup[cat_lower] = cat  # case-insensitive match
            no_prefix = cat_lower.split('.')[-1]
            if no_prefix not in no_prefix_map:
                no_prefix_map[no_prefix] = [cat]  # no-prefix match (first occurrence)
            else:
                no_prefix_map[no_prefix].append(cat)

        # Add unambiguous no-prefix matches to lookup
        for no_prefix, cats in no_prefix_map.items():
            if len(cats) == 1:
                lookup[no_prefix] = cats[0]

        # Direct or unambiguous no-prefix match
        if catalog in lookup:
            return lookup[catalog]

        # Check for ambiguous no-prefix matches
        if catalog in no_prefix_map and len(no_prefix_map[catalog]) > 1:
            matches = ', '.join(no_prefix_map[catalog])
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
            SELECT
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

        column_metadata = result.to_table()
        return column_metadata

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
        for name, ucd in zip(column_metadata['column_name'], column_metadata['ucd']):
            if ucd and 'pos.eq.ra;meta.main' in ucd:
                # TODO: ps1_dr2.mean_object and ps1_dr2.stacked_object has a column that can be used,
                # but is not labeled with "meta.main"
                ra_col = name
            elif ucd and 'pos.eq.dec;meta.main' in ucd:
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
        col_names = list(self.get_catalog_metadata(catalog).column_metadata['column_name'])

        # Check each criteria argument for validity
        for kwd in criteria.keys():
            if kwd not in col_names:
                # Suggest closest match for invalid keyword
                closest = difflib.get_close_matches(kwd, col_names, n=1)
                suggestion = f" Did you mean '{closest[0]}'?" if closest else ""
                raise InvalidQueryError(
                    f"Filter '{kwd}' is not recognized for collection '{self.name}' and "
                    f"catalog '{catalog}'.{suggestion}"
                )
