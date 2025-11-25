# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
MAST Collections
================

This module contains methods for discovering and querying MAST catalog collections.
"""
import difflib

import requests
from astropy.table import Table

from astroquery import log
from astroquery.utils import async_to_sync
from astroquery.utils.class_or_instance import class_or_instance
from astroquery.exceptions import InvalidQueryError

from .core import MastQueryWithLogin
from .catalog_collection import CatalogCollection


__all__ = ['Catalogs', 'CatalogsClass']


@async_to_sync
class CatalogsClass(MastQueryWithLogin):
    """
    MAST catalog query class.

    Class for querying MAST catalog data.
    """

    def __init__(self, collection="hsc", catalog=None):

        super().__init__()

        self.available_collections = self.get_collections()['collection_name'].tolist()
        self._no_longer_supported_collections = ['ctl', 'diskdetective', 'galex', 'plato']
        self._collections_cache = dict()

        self.collection = collection
        if catalog:
            self.catalog = catalog

    @property
    def collection(self):
        """
        The current MAST collection to be queried.
        """
        return self._collection

    @collection.setter
    def collection(self, collection):
        """
        Setter that creates a CatalogCollection object when the collection is changed and updates
        the catalog accordingly.
        """
        collection_obj = self._get_collection_obj(collection)
        self._collection = collection_obj

        # Only change catalog if not set yet or invalid for this collection
        if not hasattr(self, "_catalog") or self._catalog not in collection_obj.catalog_names:
            self._catalog = collection_obj.default_catalog

    @property
    def catalog(self):
        """
        The current catalog within the MAST collection.
        """
        return self._catalog

    @catalog.setter
    def catalog(self, catalog):
        """
        Setter that verifies that the catalog is valid for the current collection.
        """
        self.collection._verify_catalog(catalog)
        log.debug(f"Set catalog to: {catalog}")
        self._catalog = catalog

    @class_or_instance
    def get_collections(self):
        """
        Return a list of available collections from MAST.

        Returns
        -------
        response : list of str
            A list of available MAST collections.
        """
        # If already cached, use it directly
        if getattr(self, "available_collections", None):
            return Table([self.available_collections], names=('collection_name',))

        # Otherwise, fetch from the TAP service
        log.debug("Fetching available collections from MAST TAP service.")
        url = "https://masttest.stsci.edu/vo-tap/api/v0.1/openapi.json"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        # Extract collection enumeration
        collection_enum = data["components"]["schemas"]["CatalogName"]["enum"]

        # Cache the results
        self.available_collections = collection_enum

        # Build an Astropy Table to hold the results
        collection_table = Table([collection_enum], names=('collection_name',))
        return collection_table

    @class_or_instance
    def get_catalogs(self, collection=None):
        """
        For a given Catalogs.MAST collection, return a list of available catalogs.

        Parameters
        ----------
        collection : str
            The collection to be queried.

        Returns
        -------
        response : list of str
            A list of available catalogs for the specified collection.
        """
        # If no collection specified, use the class attribute
        collection_obj = self._get_collection_obj(collection) if collection else self.collection
        return collection_obj.catalogs

    @class_or_instance
    def get_catalog_metadata(self, collection=None, catalog=None):
        """
        For a given Catalogs.MAST collection and catalog, return metadata about the catalog.

        Parameters
        ----------
        collection : str
            The collection to be queried.
        catalog : str
            The catalog within the collection to get metadata for.

        Returns
        -------
        response : `~astropy.table.Table`
            A table containing metadata about the specified catalog, including column names, data types,
            and descriptions.
        """
        collection_obj, catalog = self._parse_inputs(collection, catalog)
        return collection_obj.get_catalog_metadata(catalog).column_metadata

    def _verify_collection(self, collection):
        """
        Verify that the specified collection is valid.

        Parameters
        ----------
        collection : str
            The collection to be verified.

        Raises
        ------
        InvalidQueryError
            If the specified collection is not valid.
        """
        if collection.lower() not in self.available_collections:
            if collection in self._no_longer_supported_collections:
                error_msg = (f"Collection '{collection}' is no longer supported. To query from this catalog, "
                             f"please use a version of Astroquery older than 0.4.12.")
            else:
                closest_match = difflib.get_close_matches(collection, self.available_collections, n=1)
                error_msg = (
                    f"Collection '{collection}' is not recognized. Did you mean '{closest_match[0]}'?"
                    if closest_match
                    else f"Collection '{collection}' is not recognized."
                )
            error_msg += " Available collections are: " + ", ".join(self.available_collections)
            raise InvalidQueryError(error_msg)

    def _get_collection_obj(self, collection_name):
        """
        Given a collection name, find or create the corresponding CatalogCollection object.
        """
        collection_name = collection_name.lower().strip()
        if collection_name in self._collections_cache:
            log.debug("Using cached CatalogCollection for collection: " + collection_name)
            return self._collections_cache[collection_name]

        self._verify_collection(collection_name)
        collection_obj = CatalogCollection(collection_name)
        log.debug("Cached CatalogCollection for collection: " + collection_name)
        self._collections_cache[collection_name] = collection_obj
        return collection_obj

    def _parse_inputs(self, collection=None, catalog=None):
        """
        Return (collection, catalog) applying default attributes, validation, and normalization.

        Parameters
        ----------
        collection : str, optional
            The collection to be queried. If None, uses the instance's default collection.
        catalog : str, optional
            The catalog within the collection to query. If None, uses the instance's default catalog.

        Returns
        -------
        tuple
            A tuple containing the (collection, catalog) to be queried.
        """

        collection_obj = self._get_collection_obj(collection) if collection else self.collection

        if not catalog:
            # If the class attribute catalog is valid for the collection, use it
            # Otherwise, use the default catalog for the collection
            if self.catalog in collection_obj.catalog_names:
                catalog = self.catalog
            else:
                catalog = collection_obj.default_catalog
        else:
            catalog = catalog.lower()
            collection_obj._verify_catalog(catalog)

        return collection_obj, catalog


Catalogs = CatalogsClass()
