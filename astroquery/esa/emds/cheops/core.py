# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
========================
CHEOPS Astroquery Module
========================

European Space Astronomy Centre (ESAC)
European Space Agency (ESA)

"""
import astropy.table.row
from astropy.table import vstack

from . import conf
from astroquery.utils import commons

import astroquery.esa.utils.utils as esautils
from astroquery.esa.utils import download_file
from astropy import log
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
        Query the observations for this mission and download the results.

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

        return self.query_table(table_name=conf.CHEOPS_OBSERVATION_TABLE, columns=columns,
                                custom_filters=cone_search_filter, get_metadata=get_metadata,
                                async_job=async_job, output_file=output_file,
                                output_format=output_format, **filters)

    def get_program(self, *, program_key=None, title=None, pi_name=None):
        """
        Retrieve the CHEOPS program, given its program key, title or PI name

        Parameters
        ----------
        program_key: str, optional
            Key of the program provided
        title: str, optional
            Title of the program, it may be incomplete
        pi_name: str, optional
            Responsible for the program

        Returns
        -------
        An astropy.table with the programs associated to the key, title or pi_name

        """

        if sum(x is not None for x in (program_key, title, pi_name)) != 1:
            raise TypeError("One parameter (program_key, title, or pi_name) must be provided")

        programs = None

        # To retrieve the search in program table, we need the pi_oid or the type + id
        # PI Name table retrieves the pi_oid
        if pi_name is not None:
            programs = (self._get_program_from_pi(pi_name))

        # The title provides a program key, from where we can extract the type + id
        if title is not None:
            programs = (self._get_program_from_key_or_title(title=f"%{title}%"))

        if program_key is not None:
            programs = (self._get_program_from_key_or_title(program_key=program_key))
        return programs

    def _get_program_from_pi(self, pi_name):
        """
        Retrieve the programs associated to a specific PI

        Parameters
        ----------
        pi_name: str, mandatory
            Responsible for the program

        Returns
        -------
        An astropy.table containing the programs associated to that PI Name

        """
        programs = []
        result_pi = self.query_table(table_name=conf.CHEOPS_PI_TABLE,
                                     columns=['pi_oid'],
                                     name=f"%{pi_name}%",
                                     verbose=False)
        pi_oids = result_pi['pi_oid']
        if len(pi_oids) > 0:
            programs_by_pi = self.query_table(conf.CHEOPS_PROGRAMME_TABLE, pi_oid=pi_oids[0], verbose=False)
            program_keys_from_id = list(map(lambda x:
                                            self._get_program_key_from_type_and_id(x['type'], x['id']), programs_by_pi))
            programs = self.query_table(conf.CHEOPS_PROGRAMME_INFO_TABLE,
                                        columns=['program_key', 'title', 'abstract'],
                                        program_key=program_keys_from_id,
                                        verbose=False)
            programs['pi_name'] = pi_name
            programs['program_oid'] = programs_by_pi['program_oid']

        return programs

    def _get_program_from_key_or_title(self, program_key=None, title=None):
        """
        Retrieve the full program, including pi_name, associated to a specific program_key or title

        Parameters
        ----------
        program_key: str, optional
            Key of the program provided
        title: str, optional
            Title of the program

        Returns
        -------
        An astropy.table containing the programs associated to that PI Name

        """
        programs = None
        if program_key is not None and title is not None:
            raise TypeError("Please use only program_key or title as "
                            "parameter.")
        elif program_key is not None:
            programs = self.query_table(table_name=conf.CHEOPS_PROGRAMME_INFO_TABLE,
                                        columns=['program_key', 'title', 'abstract'],
                                        program_key=program_key,
                                        verbose=False)
        elif title is not None:
            programs = self.query_table(table_name=conf.CHEOPS_PROGRAMME_INFO_TABLE,
                                        columns=['program_key', 'title', 'abstract'],
                                        title=title,
                                        verbose=False)
        # It is necessary to retrieve the PI names using the type and id
        program_key_author = {}
        program_key_program_oid = {}
        for program_key in programs['program_key']:
            type, id = self._get_type_and_id_from_program_key(program_key)
            pi_oid = self.query_table(conf.CHEOPS_PROGRAMME_TABLE,
                                      columns=['pi_oid', 'program_oid'],
                                      type=type, id=id, verbose=False)
            if len(pi_oid) > 0:
                # In some cases we don't have enough information
                pi_name = self.query_table(conf.CHEOPS_PI_TABLE,
                                           columns=['name'],
                                           pi_oid=pi_oid['pi_oid'][0],
                                           verbose=False)
                program_key_author[program_key] = pi_name['name'][0]
                program_key_program_oid[program_key] = pi_oid['program_oid'][0]
            else:
                program_key_author[program_key] = None
                program_key_program_oid[program_key] = None

        programs['pi_name'] = [program_key_author[program_key] for program_key in programs['program_key']]
        programs['program_oid'] = [program_key_program_oid[program_key] for program_key in programs['program_key']]

        return programs

    def _get_type_and_id_from_program_key(self, program_key):
        """
        Extracts the type and id from a program_key

        Parameters
        ----------
        program_key: str, mandatory
            Key of the program provided

        Returns
        -------
        The type and id for the program, as two integers
        """
        return int(program_key[2:4]), int(program_key[4:8])

    def _get_program_key_from_type_and_id(self, program_type, program_id):
        """
        Extracts the program key from a type and an id

        Parameters
        ----------
        program_type: int, mandatory
            Type of the program

        program_id: int, mandatory
            Id of the program

        Returns
        -------
        The type and id for the program, as two integers
        """
        return f"PR{program_type:02d}{program_id:04d}"

    def get_observations_from_program(self, *, program_key=None, title=None, pi_name=None):
        """
        Retrieve the observations executed for a specific program given its program key, title or PI name

        Parameters
        ----------
        program_key: str, optional
            Key of the program provided
        title: str, optional
            Title of the program
        pi_name: str, optional
            Responsible for the program

        Returns
        -------
        An astropy.table with the observations included in the program, associated to the key, title or pi_name

        """
        programs = self.get_program(program_key, title, pi_name)
        return self.get_observations(program_oid=programs['program_oid'][0])

    def get_visit_from_observation(self, observation):
        """
        Retrieve the visit associated to an observation

        Parameters
        ----------
        observation: astropy.table.row.Row or int, mandatory
            Row of the observation obtained using get_observations method or value for
            the column observation_request_oid

        Returns
        -------
        An astropy.table containing the visit associated to the observation

        """
        observation_request_oid = None
        if isinstance(observation, astropy.table.row.Row):
            observation_request_oid = observation['observation_request_oid']
        elif isinstance(observation, int):
            observation_request_oid = observation
        else:
            raise TypeError("Please use either the value of the row or the observation_request_oid column")

        return self.query_table(conf.CHEOPS_VISIT_TABLE,
                                observation_request_oid=observation_request_oid,
                                verbose=False)

    def get_products_from_targets_or_coordinates(self, *, target_name=None, coordinates=None, radius=1.0, level=None):
        """
        Get the list of files available for a cone search centered in a target or coordinates
        and a default radius. The level of the products can also be specified

        Parameters
        ----------
        target_name: str, optional
            Name of the target to be resolved against SIMBAD/NED/VIZIER
        coordinates: str or SkyCoord, optional
            coordinates of the center in the cone search
        radius: float or quantity, optional, default value 1 degree
            radius in degrees (int, float) or quantity of the cone_search
        level: str, optional
            calibration level of the products.
            Available values: EXT, L0.5, L1 and L2

        """

        observations = self.get_observations(target_name=target_name, coordinates=coordinates, radius=radius)
        product_lists = []
        checked_visits = []
        for observation in observations:
            visits = self.query_table(table_name=conf.CHEOPS_VISIT_TABLE,
                                      observation_request_oid=observation['observation_request_oid'],
                                      verbose=False)
            for visit in visits:
                if visit['visit_id'] in checked_visits:
                    continue
                checked_visits.append(visit['visit_id'])
                products = self.query_table(table_name=conf.CHEOPS_DATA_PRODUCT_TABLE,
                                            visit_id=visit['visit_id'],
                                            verbose=False,
                                            **self._get_kwargs_for_level(level))
                if len(products) > 0:
                    product_lists.append(products)
        return vstack(product_lists)

    def get_products_from_observation(self, observation, *, level=None):
        """
        Retrieve the products associated to an observation

        Parameters
        ----------
        observation: astropy.table.row.Row or str, mandatory
            Row of the observation obtained using get_observations method or value
            for the column observation_request_oid
        level: str, optional
            calibration level of the products.
            Available values: EXT, L0.5, L1 and L2

        Returns
        -------
        An astropy.table containing the visit associated to the observation

        """
        visits = self.get_visit_from_observation(observation)
        product_list = []
        checked_visits = []
        for visit in visits:
            if visit['visit_id'] in checked_visits:
                continue
            checked_visits.append(visit['visit_id'])
            products = self.query_table(conf.CHEOPS_DATA_PRODUCT_TABLE,
                                        visit_id=visit['visit_id'],
                                        verbose=False,
                                        **self._get_kwargs_for_level(level))
            if len(products) > 0:
                product_list.append(products)
        return vstack(product_list)

    def get_products_from_visit(self, visit, *, level=None):
        """
        Retrieve the products associated to a visit

        Parameters
        ----------
        visit: astropy.table.row.Row or int, mandatory
            Row of the observation obtained using get_observations method or value
            for the column observation_request_oid
        level: str, optional
            calibration level of the products.
            Available values: EXT, L0.5, L1 and L2

        Returns
        -------
        An astropy.table containing the visit associated to the observation

        """
        visit_id = visit if isinstance(visit, int) else visit['visit_id']
        return self.query_table(conf.CHEOPS_DATA_PRODUCT_TABLE, visit_id=visit_id,
                                verbose=False, **self._get_kwargs_for_level(level))

    def get_products_from_program(self, *, program_key=None, title=None, pi_name=None, level=None):
        """
        Retrieve the files associated to a specific program given its program key, title or PI name

        Parameters
        ----------
        program_key: str, optional
            Key of the program provided
        title: str, optional
            Title of the program
        pi_name: str, optional
            Responsible for the program
        level: str, optional
            calibration level of the products.
            Available values: EXT, L0.5, L1 and L2

        Returns
        -------
        An astropy.table with the observations included in the program, associated to the key, title or pi_name

        """

        observations = self.get_observations_from_program(program_key=program_key, title=title, pi_name=pi_name)
        product_lists = []
        for observation in observations:
            products = self.get_products_from_observation(observation, **self._get_kwargs_for_level(level))
            if len(products) > 0:
                product_lists.append(products)

        return vstack(product_lists)

    def _get_kwargs_for_level(self, level):
        """
        Retrieve the kwargs to include or not the level

        Parameters
        ----------
        level: str, mandatory
            calibration level of the products.
            Available values: EXT, L0.5, L1 and L2

        Returns
        -------
        A kwargs object with level included or not

        """
        kwargs = {}
        if level is not None:
            kwargs["level"] = level
        return kwargs

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

    def download_products_from_targets_or_coordinates(self, *, target_name=None, coordinates=None, radius=1.0,
                                                      level=None, path=''):
        """
        Download the list of files available for a cone search centered in a target or coordinates
        and a default radius. The level of the products can also be specified

        Parameters
        ----------
        target_name: str, optional
            Name of the target to be resolved against SIMBAD/NED/VIZIER
        coordinates: str or SkyCoord, optional
            coordinates of the center in the cone search
        radius: float or quantity, optional, default value 1 degree
            radius in degrees (int, float) or quantity of the cone_search
        level: str, optional
            calibration level of the products.
            Available values: EXT, L0.5, L1 and L2
        path: str, optional, default current directory
            Path where the file will be stored

        """

        if path is not None and path != '' and not os.path.exists(path):
            os.makedirs(path)
        products = self.get_products_from_targets_or_coordinates(target_name=target_name,
                                                                 coordinates=coordinates,
                                                                 radius=radius,
                                                                 level=level)
        for product in products:
            log.info(f"Downloading {product['filename']}")
            self.download_product(filename=product['filename'], path=path)

    def download_products_from_observation(self, observation, *, level=None, path=''):
        """
        Download the list of files available for a specific observation.
        The level of the products can also be specified.

        Parameters
        ----------
        observation: astropy.table.row.Row or str, mandatory
            Row of the observation obtained using get_observations method or value
            for the column observation_request_oid
        level: str, optional
            calibration level of the products.
            Available values: EXT, L0.5, L1 and L2
        path: str, optional, default current directory
            Path where the file will be stored

        """

        if path is not None and path != '' and not os.path.exists(path):
            os.makedirs(path)
        products = self.get_products_from_observation(observation=observation, level=level)
        for product in products:
            log.info(f"Downloading {product['filename']}")
            self.download_product(filename=product['filename'], path=path)

    def download_products_from_visit(self, visit, *, level=None, path=''):
        """
        Download the list of files available for a specific observation.
        The level of the products can also be specified

        Parameters
        ----------
        visit: astropy.table.row.Row or str, mandatory
            Row of the observation obtained using get_observations method or value for
            the column observation_request_oid
        level: str, optional
            calibration level of the products.
            Available values: EXT, L0.5, L1 and L2
        path: str, optional, default current directory
            Path where the file will be stored

        """

        if path is not None and path != '' and not os.path.exists(path):
            os.makedirs(path)
        products = self.get_products_from_visit(visit=visit, level=level)
        for product in products:
            log.info(f"Downloading {product['filename']}")
            self.download_product(filename=product['filename'], path=path)

    def download_products_from_program(self, *, program_key=None, title=None, pi_name=None, level=None, path=''):
        """
        Retrieve the files associated to a specific program given its program key, title or PI name

        Parameters
        ----------
        program_key: str, optional
            Key of the program provided
        title: str, optional
            Title of the program
        pi_name: str, optional
            Responsible for the program
        level: str, optional
            calibration level of the products.
            Available values: EXT, L0.5, L1 and L2
        path: str, optional, default current directory
            Path where the file will be stored

        """
        if path is not None and path != '' and not os.path.exists(path):
            os.makedirs(path)
        products = self.get_products_from_program(program_key=program_key, title=title,
                                                  pi_name=pi_name, level=level)
        for product in products:
            log.info(f"Downloading {product['filename']}")
            self.download_product(filename=product['filename'], path=path)


Cheops = CheopsClass()
