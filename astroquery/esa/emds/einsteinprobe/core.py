# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
==========================================
EinsteinProbe Space Archive (EPSA)
==========================================

European Space Astronomy Centre (ESAC)
European Space Agency (ESA)

"""
import os
import astroquery.esa.utils.utils as esautils

from . import conf
from ..core import EmdsClass


__all__ = ['EinsteinProbe', 'EinsteinProbeClass']


class EinsteinProbeClass(EmdsClass):

    """
    Einstein Probe TAP client.

    This module provides access to Einstein Probe data through the EMDS multi-mission
    TAP and data services. It builds on the generic EMDS client and configures
    mission-specific defaults, such as the observation catalogue and table schema.
    """

    ESA_ARCHIVE_NAME = "EinsteinProbe Space Archive (EPSA)"

    def __init__(self, auth_session=None, tap_url=None):
        super().__init__(auth_session=auth_session, tap_url=tap_url)
        self.conf = conf

    def get_products(self, obs_id=None, *, columns=None, custom_filters=None,
                     get_metadata=False, output_file=None, **filters):
        """
        Retrieve data products associated with Einstein Probe observations.

        This method queries the mission product catalogue and returns product-level
        information. It ensures that the ``filename`` and ``filepath`` columns required
        for downloading products are included in the results.

        Parameters
        ----------
        obs_id : str, optional
            Observation identifier to restrict the query (e.g. a specific observation).
        columns : str or list of str, optional
            Columns to retrieve. If provided as a list, `filename` and `filepath`
            will be appended if missing. If not provided, a minimal useful set is used.
        custom_filters : str, optional
            Additional ADQL conditions appended to the WHERE clause.
        get_metadata : bool, optional
            If True, return metadata (columns) instead of results.
        output_file : str, optional
            If provided, save results to this file.
        **filters
            Column-based filters passed through to `query_table`.

        Returns
        -------
        astropy.table.Table
        """

        table = getattr(self.conf, "OBSCORE_TABLE", None)
        if not table:
            raise ValueError("OBSCORE_TABLE is not configured for EinsteinProbe.")

        # Ensure required columns for downloading are present
        required = ["filename", "filepath"]

        if columns is None:
            # Minimal set + obs_id for context
            columns = ["obs_id"] + required
        elif isinstance(columns, list):
            for r in required:
                if r not in columns:
                    columns.append(r)

        # If columns is a string (e.g. "*"), we leave it as-is.
        # Build an obs_id filter if provided
        obs_filter = None
        if obs_id:
            obs_filter = "obs_id = '{0}'".format(obs_id)

        # Combine obs_id filter with any custom_filters
        if obs_filter:
            if custom_filters:
                custom_filters = "({0}) AND ({1})".format(custom_filters, obs_filter)
            else:
                custom_filters = obs_filter

        return self.query_table(
            table_name=table,
            columns=columns,
            custom_filters=custom_filters,
            get_metadata=get_metadata,
            async_job=True,
            output_file=output_file,
            **filters
        )

    def download_product(self, filename, *, table=None, output_filename=None, path="", cache=False, verbose=False):
        """
        Download a single data product file.

        The product is retrieved from the EMDS data service using its filename and
        saved locally.

        Parameters
        ----------
        filename : str
            Product filename stored in the mission tables (unique identifier).
        table : str, optional
            Table to query for (filepath, filename). If not provided, defaults to
            `self.conf.OBSCORE_TABLE`.
        output_filename : str, optional
            Local filename for the downloaded file. Defaults to `filename`.
        path : str, optional
            Local directory where the file will be saved. Default is current working directory.
        cache : bool, optional
            Use astroquery cache (if supported by your downloader).
        verbose : bool, optional
            Verbose download output.

        Returns
        -------
        str
            Local file path returned by `esautils.download_file`.
        """

        data_url = getattr(self.conf, "EMDS_DATA_SERVER", None)
        if not data_url:
            raise ValueError("Data server URL is not configured (EMDS_DATA_SERVER).")

        if table is None:
            table = getattr(self.conf, "OBSCORE_TABLE", None)
        if not table:
            raise ValueError("OBSCORE_TABLE is not configured for EinsteinProbe.")

        if output_filename is None:
            output_filename = filename

        if path:
            os.makedirs(path, exist_ok=True)

        query = self._build_retrieval_query(table=table, filename=filename)
        params = self._build_data_params(retrieval_type="PRODUCT", query=query)

        session = self.tap._session
        return esautils.download_file(
            url=data_url,
            session=session,
            params=params,
            path=path,
            filename=output_filename,
            cache=cache,
            verbose=verbose
        )

    def _escape_adql_string(self, value: str) -> str:
        """
        Escape single quotes for ADQL/SQL string literals.

        Parameters
        ----------
        value : str
            Input string to be escaped for safe use in ADQL/SQL queries.

        Returns
        -------
        str
            Escaped string with single quotes doubled.
        """

        return value.replace("'", "''")

    def _build_retrieval_query(self, *, table: str, filename: str) -> str:
        """
        Build the retrieval QUERY used by the EMDS /data service to locate a product.

        The service expects a query that returns at least (filepath, filename).

        Parameters
        ----------
        table : str
            Name of the table to query.
        filename : str
            Name of the file to be retrieved.

        Returns
        -------
        str
            ADQL query string used to retrieve the product location.
        """

        safe = self._escape_adql_string(filename)
        return "SELECT filepath, filename FROM {0} WHERE filename = '{1}'".format(table, safe)

    def _build_data_params(self, *, retrieval_type: str, query: str, size: str = None) -> dict:
        """
        Build query parameters for the EMDS /data endpoint.

        Parameters
        ----------
        retrieval_type : str
            Type of retrieval to be performed by the EMDS service.
        query : str
            ADQL query string used to locate the requested product(s).
        size : str, optional
            Maximum size of the response, if supported by the service.

        Returns
        -------
        dict
            Dictionary of query parameters to be sent to the EMDS /data endpoint.
        """

        params = {
            "retrieval_type": retrieval_type,
            "QUERY": query,
        }
        if size is not None:
            params["SIZE"] = size
        return params


EinsteinProbe = EinsteinProbeClass()
