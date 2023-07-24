# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
=====================
ISO Astroquery Module
=====================

European Space Astronomy Centre (ESAC)
European Space Agency (ESA)

"""
import re
from astroquery.utils.tap.core import TapPlus
from astroquery.query import BaseQuery
import shutil
import os
from email.message import Message
from requests import HTTPError
from pathlib import Path

from . import conf
from astroquery import log


__all__ = ['ISO', 'ISOClass']


class ISOClass(BaseQuery):

    data_url = conf.DATA_ACTION
    metadata_url = conf.METADATA_ACTION
    TIMEOUT = conf.TIMEOUT

    def __init__(self, tap_handler=None):
        super().__init__()

        if tap_handler is None:
            self._tap = TapPlus(url=self.metadata_url)
        else:
            self._tap = tap_handler

    def get_download_link(self, tdt, retrieval_type, filename,
                          verbose, **kwargs):
        """
        Get download link for ISO

        Parameters
        ----------
        tdt : string
          id of the Target Dedicated Time (observation identifier) to be
          downloaded, mandatory
          The identifier of the observation we want to retrieve, 8 digits
          example: 40001501
        product_level : string
            level to download, optional, by default everything is selected
            values: DEFAULT_DATA_SET, FULLY_PROC, RAW_DATA, BASIC_SCIENCE,
            QUICK_LOOK, DEFAULT_DATA_SET, HPDP, ALL
        retrieval_type : string
            type of retrieval: OBSERVATION for full observation or STANDALONE
            for single files
        filename : string
            file name to be used to store the file
        verbose : bool
            optional, default 'False'
            flag to display information about the process

        Returns
        -------
        None if not verbose. It downloads the observation indicated
        If verbose returns the filename
        """

        link = self.data_url
        link = link + "retrieval_type=" + retrieval_type
        link = link + "&DATA_RETRIEVAL_ORIGIN=astroquery"
        link = link + "&tdt=" + tdt

        link = link + "".join("&{0}={1}".format(key, val)
                              for key, val in kwargs.items())

        if verbose:
            log.info(link)

        return link

    def download_data(self, tdt, *, retrieval_type=None, filename=None,
                      verbose=False, **kwargs):

        """
        Download data from ISO

        Parameters
        ----------
        tdt : string
          id of the Target Dedicated Time (observation identifier) to be
          downloaded, mandatory
          The identifier of the observation we want to retrieve, 8 digits
          example: 40001501
        product_level : string
            level to download, optional, by default everything is selected
            values: DEFAULT_DATA_SET, FULLY_PROC, RAW_DATA, BASIC_SCIENCE,
            QUICK_LOOK, DEFAULT_DATA_SET, HPDP, ALL
        retrieval_type : string
            type of retrieval: OBSERVATION for full observation or STANDALONE
            for single files
        filename : string
            file name to be used to store the file
        verbose : bool
            optional, default 'False'
            flag to display information about the process

        Returns
        -------
        File name of downloaded data
        """

        if retrieval_type is None:
            retrieval_type = "OBSERVATION"

        link = self.get_download_link(tdt, retrieval_type, filename,
                                      verbose, **kwargs)

        response = self._request('GET', link, save=False, cache=True)
        response.raise_for_status()

        # Get original extension
        message = Message()
        message["content-type"] = response.headers["Content-Disposition"]
        suffixes = Path(message.get_param("filename")).suffixes

        if filename is None:
            filename = tdt

        filename += "".join(suffixes)

        if verbose:
            log.info("Copying file to {0}...".format(filename))

        with open(filename, 'wb') as f:
            f.write(response.content)

        if verbose:
            log.info("Wrote {0} to {1}".format(link, filename))

        return filename

    def get_postcard_link(self, tdt, filename=None, verbose=False):
        """
        Get postcard link for ISO

        Parameters
        ----------
        tdt : string
          id of the Target Dedicated Time (observation identifier) to be
          downloaded, mandatory
          The identifier of the observation we want to retrieve, 8 digits
          example: 40001501
        product_level : string
            level to download, optional, by default everything is selected
            values: DEFAULT_DATA_SET, FULLY_PROC, RAW_DATA, BASIC_SCIENCE,
            QUICK_LOOK, DEFAULT_DATA_SET, HPDP, ALL
        retrieval_type : string
            type of retrieval: OBSERVATION for full observation or STANDALONE
            for single files
        filename : string
            file name to be used to store the file
        verbose : bool
            optional, default 'False'
            flag to display information about the process

        Returns
        -------
        The postcard filename
        """

        link = self.data_url
        link = link + "retrieval_type=POSTCARD"
        link = link + "&DATA_RETRIEVAL_ORIGIN=astroquery"
        link = link + "&tdt=" + tdt

        if verbose:
            log.info(link)

        return link

    def get_postcard(self, tdt, *, filename=None, verbose=False):
        """
        Download postcards from ISO Data Archive

        Parameters
        ----------
        tdt : string
            id of the observation for which download the postcard, mandatory
            The identifier of the observation we want to retrieve, regardless
            of whether it is simple or composite.
        filename : string
            file name to be used to store the postcard, optional, default None
        verbose : bool
            optional, default 'False'
            Flag to display information about the process

        Returns
        -------
        File name to be used to store the postcard
        """

        link = self.get_postcard_link(tdt, filename, verbose)

        local_filepath = self._request('GET', link, cache=True, save=True)

        if filename is None:

            response = self._request('HEAD', link)
            response.raise_for_status()

            filename = os.path.basename(re.findall('filename="(.+)"', response.headers[
                "Content-Disposition"])[0])
        else:

            filename = filename + ".png"

        if verbose:
            log.info("Copying file to {0}...".format(filename))

        shutil.move(local_filepath, filename)

        if verbose:
            log.info("Wrote {0} to {1}".format(link, filename))

        return filename

    def query_ida_tap(self, query, *, output_file=None,
                      output_format="votable", verbose=False):
        """
        Launches a synchronous job to query ISO Tabular Access Protocol Service

        Parameters
        ----------
        query : str, mandatory
            query (adql) to be executed
        output_file : str, optional, default None
            file name where the results are saved if dumpToFile is True.
            If this parameter is not provided, the jobid is used instead
        output_format : str, optional, default 'votable'
            possible values 'votable' or 'csv'
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
        try:
            table = job.get_results()
            return table
        except HTTPError as e:
            print(str(e))

    def get_tables(self, *, only_names=True, verbose=False):
        """
        Get the available table in XSA TAP service

        Parameters
        ----------
        only_names : bool, TAP+ only, optional, default 'True'
            True to load table names only
        verbose : bool, optional, default 'False'
            flag to display information about the process

        Returns
        -------
        A list of tables
        """

        tables = self._tap.load_tables(only_names=only_names,
                                       include_shared_tables=False,
                                       verbose=verbose)
        if only_names:
            return [t.name for t in tables]
        else:
            return tables

    def get_columns(self, table_name, *, only_names=True, verbose=False):
        """
        Get the available columns for a table in XSA TAP service

        Parameters
        ----------
        table_name : string, mandatory, default None
            table name of which, columns will be returned
        only_names : bool, TAP+ only, optional, default 'True'
            True to load table names only
        verbose : bool, optional, default 'False'
            flag to display information about the process

        Returns
        -------
        A list of columns
        """

        tables = self._tap.load_tables(only_names=False,
                                       include_shared_tables=False,
                                       verbose=verbose)
        columns = None
        for table in tables:
            if str(table.name) == str(table_name):
                columns = table.columns
                break

        if columns is None:
            raise ValueError("table name specified is not found in "
                             "IDA TAP service")

        if only_names:
            return [c.name for c in columns]
        else:
            return columns


ISO = ISOClass()
