# Licensed under a 3-clause BSD style license - see LICENSE.rst

import cgi
import os
import re
import shutil
from pathlib import Path

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
        super(HSAClass, self).__init__()
        if tap_handler is None:
            self._tap = Tap(url=self.metadata_url)
        else:
            self._tap = tap_handler

    def download_data(self, observation_id, *, retrieval_type=None,
                      instrument_name=None,
                      filename=None,
                      verbose=False,
                      cache=True,
                      **kwargs):
        """
        Download data from Herschel

        Parameters
        ----------
        observation_id : string, mandatory
            id of the observation to be downloaded
            The identifies of the observation we want to retrieve, 10 digits
            example: 1342195355
        retrieval_type : string, optional, default 'OBSERVATION'
            The type of product that we want to retrieve
            values: OBSERVATION, PRODUCT, POSTCARD, POSTCARDFITS, REQUESTFILE_XML, STANDALONE, UPDP, HPDP
        instrument_name : string, optinal, default 'PACS'
            values: PACS, SPIRE, HIFI
            The instrument name, by default 'PACS' if the retrieval_type is 'OBSERVATION'
        filename : string, optinal, default None
            If the filename is not set it will use the observation_id as filename
            file name to be used to store the file
        verbose : bool, optinal, default False
            flag to display information about the process
        observation_oid : string, optional
            Observation internal identifies. This is the database identifier
        istrument_oid : string, optional
            The database identifies of the instrument
            values: 1, 2, 3
        product_level : string, optional
            level to download
            values: ALL, AUXILIARY, CALIBRATION, LEVEL0, LEVEL0_5, LEVEL1, LEVEL2, LEVEL2_5, LEVEL3, ALL-LEVEL3

        Returns
        -------
        File name of downloaded data
        """
        if filename is not None:
            filename = os.path.splitext(filename)[0]

        if retrieval_type is None:
            retrieval_type = "OBSERVATION"

        params = {'retrieval_type': retrieval_type,
                  'observation_id': observation_id}

        if retrieval_type == "OBSERVATION" and instrument_name is None:
            instrument_name = "PACS"
            params['instrument_name'] = instrument_name

        link = self.data_url + "".join("&{0}={1}".format(key, val)
                                       for key, val in params.items())

        link += "".join("&{0}={1}".format(key, val)
                        for key, val in kwargs.items())

        if verbose:
            log.info(link)

        response = self._request('HEAD', link, save=False, cache=cache)
        response.raise_for_status()

        if 'Content-Type' in response.headers and 'text' not in response.headers['Content-Type']:
            _, params = cgi.parse_header(response.headers['Content-Disposition'])
        else:
            error = "Data protected by propietary rights. Please check your credentials"
            raise LoginError(error)

        r_filename = params["filename"]
        suffixes = Path(r_filename).suffixes

        if filename is None:
            filename = observation_id

        filename += "".join(suffixes)

        self._download_file(link, filename, head_safe=True, cache=cache)

        if verbose:
            log.info("Wrote {0} to {1}".format(link, filename))

        return filename

    def get_observation(self, observation_id, instrument_name, *, filename=None,
                        verbose=False,
                        cache=True, **kwargs):
        """
        Download observation from Herschel

        Parameters
        ----------
        observation_id : string, mandatory
            id of the observation to be downloaded
            The identifies of the observation we want to retrieve, 10 digits
            example: 1342195355
        instrument_name : string, mandatory
            The instrument name
            values: PACS, SPIRE, HIFI
        filename : string, optinal, default None
            If the filename is not set it will use the observation_id as filename
            file name to be used to store the file
        verbose : bool, optinal, default 'False'
            flag to display information about the process
        observation_oid : string, optional
            Observation internal identifies. This is the database identifier
        istrument_oid : string, optional
            The database identifies of the instrument
            values: 1, 2, 3
        product_level : string, optional
            level to download
            values: ALL, AUXILIARY, CALIBRATION, LEVEL0, LEVEL0_5, LEVEL1, LEVEL2, LEVEL2_5, LEVEL3, ALL-LEVEL3

        Returns
        -------
        File name of downloaded data
        """
        if filename is not None:
            filename = os.path.splitext(filename)[0]

        params = {'retrieval_type': "OBSERVATION",
                  'observation_id': observation_id,
                  'instrument_name': instrument_name}

        link = self.data_url + "".join("&{0}={1}".format(key, val)
                                       for key, val in params.items())

        link += "".join("&{0}={1}".format(key, val)
                        for key, val in kwargs.items())

        if verbose:
            log.info(link)

        response = self._request('HEAD', link, save=False, cache=cache)
        response.raise_for_status()

        if 'Content-Type' in response.headers and 'text' not in response.headers['Content-Type']:
            _, params = cgi.parse_header(response.headers['Content-Disposition'])
        else:
            error = "Data protected by propietary rights. Please check your credentials"
            raise LoginError(error)

        r_filename = params["filename"]
        suffixes = Path(r_filename).suffixes

        if filename is None:
            filename = observation_id

        filename += "".join(suffixes)

        self._download_file(link, filename, head_safe=True, cache=cache)

        if verbose:
            log.info("Wrote {0} to {1}".format(link, filename))

        return filename

    def get_postcard(self, observation_id, instrument_name, *, filename=None,
                     verbose=False,
                     cache=True, **kwargs):
        """
        Download postcard from Herschel

        Parameters
        ----------
        observation_id : string, mandatory
            id of the observation to be downloaded
            The identifies of the observation we want to retrieve, 10 digits
            example: 1342195355
        instrument_name : string, mandatory
            The instrument name
            values: PACS, SPIRE, HIFI
        filename : string, optinal, default None
            If the filename is not set it will use the observation_id as filename
            file name to be used to store the file
        verbose : bool, optinal, default False
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

        Returns
        -------
        File name of downloaded data
        """
        if filename is not None:
            filename = os.path.splitext(filename)[0]

        params = {'retrieval_type': "POSTCARD",
                  'observation_id': observation_id,
                  'instrument_name': instrument_name}

        link = self.data_url + "".join("&{0}={1}".format(key, val)
                                       for key, val in params.items())

        link += "".join("&{0}={1}".format(key, val)
                        for key, val in kwargs.items())

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

        shutil.move(local_filepath, filename)

        if verbose:
            log.info("Wrote {0} to {1}".format(link, filename))

        return filename

    def query_hsa_tap(self, query, *, output_file=None,
                      output_format="votable", verbose=False):
        """
        Launches a synchronous job to query HSA Tabular Access Protocol (TAP) Service

        Parameters
        ----------
        query : string, mandatory
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
        table_name : string, mandatory
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
HSA = HSAClass()
