# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
==========================================
CHEOPS Astroquery Module
==========================================

European Space Astronomy Centre (ESAC)
European Space Agency (ESA)

"""

from . import conf
from astroquery.utils import commons

import astroquery.esa.utils.utils as esautils
from astroquery.esa.utils import download_file
import os


from astroquery.esa.emds import EmdsClass

__all__ = ['Cheops', 'CheopsClass']


class CheopsClass(EmdsClass):

    """
    Cheops TAP client.

    This module provides access to Cheops data through the EMDS multi-mission
    TAP and data services. It builds on the generic EMDS client and configures
    mission-specific defaults, such as the observation catalogue and table schema.
    """

    ESA_ARCHIVE_NAME = "CHEOPS Astroquery Module"

    def __init__(self, auth_session=None, tap_url=None):
        super().__init__(auth_session=auth_session, tap_url=tap_url)
        self.conf = conf

    def get_observations(self, *, target_name=None, coordinates=None, radius=0.01, columns=None, get_metadata=False,
                         output_file=None, async_job=False, output_format='votable', **filters):
        """
        Query the observations for this mission and download the xml with the results.

        Parameters
        ----------
        target_name: str, optional
            Name of the target to be resolved against SIMBAD/NED/VIZIER
        coordinates: str or SkyCoord, optional
            coordinates of the center in the cone search
        radius: float or quantity, optional, default value 0.01 degree
            radius in degrees (int, float) or quantity of the cone_search
        columns : str or list of str, optional, default None
            Columns from the table to be retrieved. They can be checked using
            get_metadata=True
        get_metadata : bool, optional, default False
            Get the table metadata to verify the columns that can be filtered
        output_file : str, optional, default None
            file name where the results are saved.
            If this parameter is not provided, the jobid is used instead
        async_job : bool, optional, default 'False'
            executes the query (job) in asynchronous/synchronous mode (default
            synchronous)
        output_format : string
            optional, default 'votable'
            output format of the query
        **filters : str, optional, default None
            Filters to be applied to the search. The column name is the keyword and the value is any
            value accepted by the column datatype. They will be
            used to generate the SQL filters for the query. Some examples are described below,
            where the left side is the parameter defined for this method and the right side the
            SQL filter generated:
            target_name="AT 2023%" -> target_name ILIKE 'AT 2023%'
            dataproduct_type=["img", "pha"] -> dataproduct_type = 'img' OR dataproduct_type = 'pha'
            dataproduct_type=["img", "pha"] -> dataproduct_type IN ('img', 'pha')
            t_min=(">", 60000) -> t_min > 60000
            ra=(80, 82) -> ra >= 80 AND ra <= 82

        Returns
        -------
        An astropy.table containing the query results, or the metadata table when ``get_metadata=True``

        """

        cone_search_filter = None
        if radius is not None:
            radius = esautils.get_degree_radius(radius)

        if target_name and coordinates:
            raise TypeError("Please use only target or coordinates as "
                            "parameter.")
        elif target_name:
            coordinates = esautils.resolve_target(conf.EMDS_TARGET_RESOLVER,
                                                  self.tap._session, target_name,
                                                  'ALL')
            cone_search_filter = self.create_cone_search_query(coordinates.ra.deg, coordinates.dec.deg,
                                                               "ra", "dec", radius)
        elif coordinates:
            coord = commons.parse_coordinates(coordinates=coordinates)
            ra = coord.ra.degree
            dec = coord.dec.degree
            cone_search_filter = self.create_cone_search_query(ra, dec, "ra", "dec", radius)

        return self.query_table(table_name=conf.CHEOPS_OBSERVATION_TABLE, columns=columns, custom_filters=cone_search_filter,
                                get_metadata=get_metadata, async_job=async_job, output_file=output_file, output_format=output_format, **filters)

    def get_products(self, *, observation_id=None, visit_id=None, output_file=None, **filters):
        """
        Retrieve data products associated with Cheops observations or visits.

        This method queries the data product table and returns product-level
        information. It ensures that the ``filename`` and ``filepath`` columns required
        for downloading products are included in the results.

        Parameters
        ----------
        observation_id : str, optional
            Observation identifier to restrict the query (e.g. a specific observation).
        visit_id : str, optional
            Visit identifier to restrict the query (e.g. a specific visit).
        output_file : str, optional
            If provided, save results to this file.
        **filters
            Column-based filters passed through to query_table method.

        Returns
        -------
        astropy.table.Table
        """

        if observation_id is None and visit_id is None:
            raise TypeError("Please use either observation_id or visit_id")

        custom_filters = None

        # Builds an obs_id filter if provided
        if observation_id:
            custom_filters = f"b.obsid = '{observation_id}'"

        # Builds a visit_id filter if provided
        if visit_id:
            visit_filter = f"b.visit_id = '{visit_id}'"
            if observation_id:
                custom_filters = f"({custom_filters}) AND ({visit_filter})"
            else:
                custom_filters = visit_filter

        query = conf.CHEOPS_DATA_PRODUCT_QUERY.format(custom_filters)

        result = self.query_tap(query=query, output_file=output_file)
        if len(result) > 0:
            return result

        raise ValueError(f"No data products can be found for CHEOPS with these parameters")

    def download_product(self, filename, *, output_filename=None, path="", cache=False, verbose=False):
        """
        Download a single data product file.

        The product is retrieved from the EMDS data service using its filename and
        saved locally.

        Parameters
        ----------
        filename : str, mandatory
            Product filename stored in the mission tables (unique identifier).
        output_filename : str, optional
            file name where the data product is saved,
            If this parameter is not provided, the original filename is used instead
        path : str, optional
            Local directory where the file will be saved. Default is current working directory.
        cache : bool, optional
            Use astroquery cache (if supported by your downloader).
        verbose : bool, optional
            Verbose download output.

        Returns
        -------
        str
            Local file path returned by esautils.download_file.
        """

        data_url = getattr(self.conf, "EMDS_DATA_SERVER", None)
        if not data_url:
            raise ValueError("Data server URL is not configured (EMDS_DATA_SERVER).")

        if filename is None:
            raise TypeError("Please specify a file name of the data product to download.")

        if output_filename is None:
            output_filename = filename

        if path:
            os.makedirs(path, exist_ok=True)

        query = self._build_retrieval_query(table=conf.CHEOPS_DATA_PRODUCT_TABLE, filename=filename)
        params = self._build_data_params(retrieval_type="PRODUCT", query=query)

        session = self.tap._session
        return download_file(
            url=data_url,
            session=session,
            params=params,
            path=path,
            filename=output_filename,
            cache=cache,
            verbose=verbose
        )

Cheops = CheopsClass()
