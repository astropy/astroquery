# Licensed under a 3-clause BSD style license - see LICENSE.rst

import os
import re
import shutil
from email.message import Message
from pathlib import Path

from astropy import units as u
from astroquery.utils import commons
from astroquery import log
from astroquery.exceptions import LoginError
from astroquery.query import BaseQuery
from astroquery.utils.tap.core import Tap

from . import conf

__all__ = ['HSA', 'HSAClass']


class HSAClass(BaseQuery):

    data_url = conf.DATA_ACTION
    metadata_url = conf.METADATA_ACTION
    timeout = conf.TIMEOUT

    def __init__(self, tap_handler=None):
        super().__init__()
        if tap_handler is None:
            self._tap = Tap(url=self.metadata_url)
        else:
            self._tap = tap_handler

    def download_data(self, *, retrieval_type="OBSERVATION", observation_id=None,
                      instrument_name=None, filename=None, observation_oid=None,
                      instrument_oid=None, product_level=None, verbose=False,
                      download_dir="", cache=True, **kwargs):
        """
        Download data from Herschel

        Parameters
        ----------
        observation_id : string, optional
            id of the observation to be downloaded
            The identifies of the observation we want to retrieve, 10 digits
            example: 1342195355
        retrieval_type : string, optional, default 'OBSERVATION'
            The type of product that we want to retrieve
            values: OBSERVATION, PRODUCT, POSTCARD, POSTCARDFITS, REQUESTFILE_XML, STANDALONE, UPDP, HPDP
        instrument_name : string, optional, default 'PACS'
            values: PACS, SPIRE, HIFI
            The instrument name, by default 'PACS' if the retrieval_type is 'OBSERVATION'
        filename : string, optional, default None
            If the filename is not set it will use the observation_id as filename
            file name to be used to store the file
        verbose : bool, optional, default False
            flag to display information about the process
        observation_oid : string, optional
            Observation internal identifies. This is the database identifier
        instrument_oid : string, optional
            The database identifies of the instrument
            values: 1, 2, 3
        product_level : string, optional
            level to download
            values: ALL, AUXILIARY, CALIBRATION, LEVEL0, LEVEL0_5, LEVEL1, LEVEL2, LEVEL2_5, LEVEL3, ALL-LEVEL3
        download_dir : string, optional
            The directory in which the file will be downloaded
        cache : bool
            Defaults to True. If set overrides global caching behavior.
            See :ref:`caching documentation <astroquery_cache>`.

        Returns
        -------
        File name of downloaded data
        """
        if filename is not None:
            filename = os.path.splitext(filename)[0]

        params = {'retrieval_type': retrieval_type}
        if observation_id is not None:
            params['observation_id'] = observation_id

        if retrieval_type == "OBSERVATION" and instrument_name is None:
            instrument_name = "PACS"

        if instrument_name is not None:
            params['instrument_name'] = instrument_name

        if observation_oid is not None:
            params['observation_oid'] = observation_oid

        if instrument_oid is not None:
            params['instrument_oid'] = instrument_oid

        if product_level is not None:
            params['product_level'] = product_level

        link = self.data_url + "".join(f"&{key}={val}" for key, val in params.items())

        link += "".join(f"&{key}={val}" for key, val in kwargs.items())

        if verbose:
            log.info(link)

        response = self._request('HEAD', link, save=False, cache=cache)
        if response.status_code == 401:
            error = "Data protected by proprietary rights. Please check your credentials"
            raise LoginError(error)

        response.raise_for_status()

        if filename is None:
            if observation_id is not None:
                filename = observation_id
            else:
                error = "Please set either 'obervation_id' or 'filename' for the output"
                raise ValueError(error)

        message = Message()
        message["content-type"] = response.headers["Content-Disposition"]
        suffixes = Path(message.get_param("filename")).suffixes

        if len(suffixes) > 1 and suffixes[-1] == ".jpg":
            filename += suffixes[-1]
        else:
            filename += "".join(suffixes)

        filename = os.path.join(download_dir, filename)

        self._download_file(link, filename, head_safe=True, cache=cache)

        if verbose:
            log.info(f"Wrote {link} to {filename}")

        return filename

    def get_observation(self, observation_id, instrument_name, *, filename=None,
                        observation_oid=None, instrument_oid=None, product_level=None,
                        verbose=False, download_dir="", cache=True, **kwargs):
        """
        Download observation from Herschel.
        This consists of a .tar file containing:

        - The auxiliary directory: contains all Herschel non-science spacecraft data
        - The calibarion directory: contains the uplink and downlink calibration products
        - <obs_id> directory: contains the science data distributed in sub-directories called level0/0.5/1/2/2.5/3.

        More information can be found here:
            https://www.cosmos.esa.int/web/herschel/data-products-overview

        Parameters
        ----------
        observation_id : string
            id of the observation to be downloaded
            The identifies of the observation we want to retrieve, 10 digits
            example: 1342195355
        instrument_name : string
            The instrument name
            values: PACS, SPIRE, HIFI
        filename : string, optional, default None
            If the filename is not set it will use the observation_id as filename
            file name to be used to store the file
        verbose : bool, optional, default 'False'
            flag to display information about the process
        observation_oid : string, optional
            Observation internal identifies. This is the database identifier
        istrument_oid : string, optional
            The database identifies of the instrument
            values: 1, 2, 3
        product_level : string, optional
            level to download
            values: ALL, AUXILIARY, CALIBRATION, LEVEL0, LEVEL0_5, LEVEL1, LEVEL2, LEVEL2_5, LEVEL3, ALL-LEVEL3
        download_dir : string, optional
            The directory in which the file will be downloaded

        Returns
        -------
        File name of downloaded data
        """
        if filename is not None:
            filename = os.path.splitext(filename)[0]

        params = {'retrieval_type': "OBSERVATION",
                  'observation_id': observation_id,
                  'instrument_name': instrument_name}

        if observation_oid is not None:
            params['observation_oid'] = observation_oid

        if instrument_oid is not None:
            params['instrument_oid'] = instrument_oid

        if product_level is not None:
            params['product_level'] = product_level

        link = self.data_url + "".join(f"&{key}={val}" for key, val in params.items())

        link += "".join(f"&{key}={val}" for key, val in kwargs.items())

        if verbose:
            log.info(link)

        response = self._request('HEAD', link, save=False, cache=cache)
        if response.status_code == 401:
            error = "Data protected by proprietary rights. Please check your credentials"
            raise LoginError(error)

        response.raise_for_status()

        message = Message()
        message["content-type"] = response.headers["Content-Disposition"]
        suffixes = Path(message.get_param("filename")).suffixes

        if filename is None:
            filename = observation_id

        filename += "".join(suffixes)

        filename = os.path.join(download_dir, filename)

        self._download_file(link, filename, head_safe=True, cache=cache)

        if verbose:
            log.info(f"Wrote {link} to {filename}")

        return filename

    def get_postcard(self, observation_id, instrument_name, *, filename=None,
                     verbose=False, download_dir="", cache=True, **kwargs):
        """
        Download postcard from Herschel

        Parameters
        ----------
        observation_id : string
            id of the observation to be downloaded
            The identifies of the observation we want to retrieve, 10 digits
            example: 1342195355
        instrument_name : string
            The instrument name
            values: PACS, SPIRE, HIFI
        filename : string, optional, default None
            If the filename is not set it will use the observation_id as filename
            file name to be used to store the file
        verbose : bool, optional, default False
            flag to display information about the process
        observation_oid : string, optional
            Observation internal identifies. This is the database identifier
        istrument_oid : string, optional
            The database identifies of the instrument
            values: 1, 2, 3
        product_level : string, optional
            level to download
            values: ALL, AUXILIARY, CALIBRATION, LEVEL0, LEVEL0_5, LEVEL1, LEVEL2, LEVEL2_5, LEVEL3, ALL-LEVEL3
        postcard_single : string, optional
            'true' to retrieve one single postcard (main one)
            values: true, false
        download_dir : string, optional
            The directory in which the file will be downloaded

        Returns
        -------
        File name of downloaded data
        """
        if filename is not None:
            filename = os.path.splitext(filename)[0]

        params = {'retrieval_type': "POSTCARD",
                  'observation_id': observation_id,
                  'instrument_name': instrument_name}

        link = self.data_url + "".join(f"&{key}={val}" for key, val in params.items())

        link += "".join(f"&{key}={val}" for key, val in kwargs.items())

        if verbose:
            log.info(link)

        response = self._request('HEAD', link, save=False, cache=cache)
        response.raise_for_status()
        local_filepath = self._request('GET', link, cache=True, save=True)

        original_filename = re.findall('filename="(.+)"',
                                       response.headers["Content-Disposition"])[0]
        _, ext = os.path.splitext(original_filename)
        if filename is None:
            filename = observation_id

        filename += ext

        filename = os.path.join(download_dir, filename)

        shutil.move(local_filepath, filename)

        if verbose:
            log.info(f"Wrote {link} to {filename}")

        return filename

    def query_hsa_tap(self, query, *, output_file=None,
                      output_format="votable", verbose=False):
        """
        Launches a synchronous job to query HSA Tabular Access Protocol (TAP) Service

        Parameters
        ----------
        query : string
            query (adql) to be executed
        output_file : string, optional, default None
            file name where the results are saved if dumpToFile is True.
            If this parameter is not provided, the jobid is used instead
        output_format : string, optional, default 'votable'
            values 'votable' or 'csv'
        verbose : bool, optional, default 'False'
            flag to display information about the process

        Returns
        -------
        A table object
        """
        job = self._tap.launch_job(query=query, output_file=output_file,
                                   output_format=output_format,
                                   verbose=verbose,
                                   dump_to_file=output_file is not None)
        table = job.get_results()
        return table

    def get_tables(self, *, only_names=True, verbose=False):
        """
        Get the available table in HSA TAP service

        Parameters
        ----------
        only_names : bool, optional, default True
            True to load table names only
        verbose : bool, optional, default False
            flag to display information about the process

        Returns
        -------
        A list of tables
        """
        tables = self._tap.load_tables(verbose=verbose)
        if only_names:
            return [t.name for t in tables]
        else:
            return tables

    def get_columns(self, table_name, *, only_names=True, verbose=False):
        """
        Get the available columns for a table in HSA TAP service

        Parameters
        ----------
        table_name : string
            table name of which, columns will be returned
        only_names : bool, optional, default True
            True to load column names only
        verbose : bool, optional, default False
            flag to display information about the process

        Returns
        -------
        A list of columns
        """
        tables = self._tap.load_tables(verbose=verbose)

        columns = None
        for t in tables:
            if str(t.name) == str(table_name):
                columns = t.columns
                break

        if columns is None:
            raise ValueError("table name specified was not found in "
                             "HSA TAP service")

        if only_names:
            return [c.name for c in columns]
        else:
            return columns

    def query_observations(self, coordinate, radius, *, n_obs=10, **kwargs):
        """
        Get the observation IDs from a given region

        Parameters
        ----------
        coordinate : string / `astropy.coordinates`
            the identifier or coordinates around which to query
        radius : int / `~astropy.units.Quantity`
            the radius of the region
        n_obs : int, optional
            the number of observations
        kwargs : dict
            passed to `query_hsa_tap`

        Returns
        -------
        A table object with the list of observations in the region
        """
        return self.query_region(coordinate, radius, n_obs=n_obs, columns="observation_id", **kwargs)

    def query_region(self, coordinate, radius, *, n_obs=10, columns='*', **kwargs):
        """
        Get the observation metadata from a given region

        Parameters
        ----------
        coordinate : string / `astropy.coordinates`
            the identifier or coordinates around which to query
        radius : int / `~astropy.units.Quantity`
            the radius of the region
        n_obs : int, optional
            the number of observations
        columns : str, optional
            the columns to retrieve from the data table
        kwargs : dict
            passed to `query_hsa_tap`

        Returns
        -------
        A table object with the list of observations in the region
        """
        r = radius
        if not isinstance(radius, u.Quantity):
            r = radius*u.deg
        coord = commons.parse_coordinates(coordinate).icrs

        query = (f"select top {n_obs} {columns} from hsa.v_active_observation "
                 f"where contains("
                 f"point('ICRS', hsa.v_active_observation.ra, hsa.v_active_observation.dec), "
                 f"circle('ICRS', {coord.ra.degree},{coord.dec.degree},{r.to(u.deg).value}))=1")
        return self.query_hsa_tap(query, **kwargs)


HSA = HSAClass()
