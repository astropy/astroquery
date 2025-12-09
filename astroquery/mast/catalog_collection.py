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
    'gaia': 'dbo.gaia_source',
    'hscv3': 'dbo.SumMagAper2CatView',
    'hscv2': 'dbo.SumMagAper2CatView',
    'missionmast': 'dbo.hst_science_missionmast',
    'ps1dr1': 'dbo.MeanObjectView',
    'ps1dr2': 'dbo.MeanObjectView',
    'pd1_dr2': 'ps1_dr2.forced_mean_object',
    'skymapper': 'dr4.master',
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
        self.catalogs = self._get_catalogs()
        self.catalog_names = self.catalogs['catalog_name'].tolist()

        # ADQL functions supported by this collection's TAP service
        self.supported_adql_functions = self._get_adql_supported_functions()

        # Determine the default catalog for this collection
        self.default_catalog = self.get_default_catalog()

        # Cache for catalog metadata to avoid redundant queries
        self._catalog_metadata_cache: Dict[str, CatalogMetadata] = dict()

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
        # Check cache first
        if catalog in self._catalog_metadata_cache:
            return self._catalog_metadata_cache[catalog]

        # Verify catalog validity for this collection
        catalog = self._verify_catalog(catalog)

        # Get column metadata
        metadata = self._get_column_metadata(catalog)

        # Get RA/Dec column names
        ra_col, dec_col = self._get_ra_dec_column_names(metadata)

        # Determine if spatial queries are supported
        supports_spatial_queries = (ra_col is not None and dec_col is not None)
        if supports_spatial_queries:
            # If an ra and dec column exist, test spatial query support
            spatial_query = (f'SELECT TOP 0 * FROM {catalog} WHERE CONTAINS(POINT(\'ICRS\', {ra_col}, {dec_col}), '
                             'CIRCLE(\'ICRS\', 0, 0, 0.1)) = 1')
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
        result = self.tap_service.search(adql)
        return result.to_table()

    def _get_catalogs(self):
        """
        Retrieve the list of catalogs in this collection.

        Returns
        -------
        list of str
            List of catalog names.
        """
        log.debug(f"Fetching available tables for collection '{self.name}' from MAST TAP service.")
        tables = self.tap_service.tables
        names = [t.name for t in tables]
        descriptions = [t.description for t in tables]

        # Create an Astropy Table to hold the results
        result_table = Table([names, descriptions], names=('catalog_name', 'description'))
        return result_table

    def _get_adql_supported_functions(self):
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
        for cat in self.catalog_names:
            cat_lower = cat.lower()
            lookup[cat_lower] = cat  # case-insensitive match
            lookup[cat_lower.split('.')[-1]] = cat  # no-prefix match

        # Direct or no-prefix match
        if catalog in lookup:
            return lookup[catalog]

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

        # Case-insensitive match to find the table
        tap_table = next((t for name, t in self.tap_service.tables.items() if name == catalog), None)

        # Extract column metadata
        col_names = [col.name for col in tap_table.columns]
        col_datatypes = []
        for col in tap_table.columns:
            try:
                col_datatypes.append(col.datatype._content)
            except AttributeError:
                # Some pyvo versions store datatype differently; fall back gracefully
                # Fallback: str(col.datatype) or None
                col_datatypes.append(getattr(col.datatype, '_content', str(col.datatype)))
        col_units = [col.unit for col in tap_table.columns]
        col_ucds = [col.ucd for col in tap_table.columns]
        col_descriptions = [col.description for col in tap_table.columns]

        # Create an Astropy Table to hold the metadata
        column_metadata = Table([col_names, col_datatypes, col_units, col_ucds, col_descriptions],
                                names=('name', 'data_type', 'unit', 'ucd', 'description'))
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
        for name, ucd in zip(column_metadata['name'], column_metadata['ucd']):
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
        col_names = list(self.get_catalog_metadata(catalog).column_metadata['name'])

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
