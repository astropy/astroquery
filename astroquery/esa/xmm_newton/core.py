# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""

@author: Elena Colomo
@contact: ecolomo@esa.int

European Space Astronomy Centre (ESAC)
European Space Agency (ESA)

Created on 3 Sept 2019


"""
import re
from ...utils.tap.core import TapPlus
from ...query import BaseQuery
import shutil
import cgi
from pathlib import Path

from . import conf
from astropy import log


__all__ = ['XMMNewton', 'XMMNewtonClass']


class XMMNewtonClass(BaseQuery):

    data_url = conf.DATA_ACTION
    data_aio_url = conf.DATA_ACTION_AIO
    metadata_url = conf.METADATA_ACTION
    TIMEOUT = conf.TIMEOUT

    def __init__(self, tap_handler=None):
        super(XMMNewtonClass, self).__init__()

        if tap_handler is None:
            self._tap = TapPlus(url="http://nxsa.esac.esa.int"
                                    "/tap-server/tap/")
        else:
            self._tap = tap_handler

    def download_data(self, observation_id, *, filename=None, verbose=False,
                      **kwargs):
        """
        Download data from XMM-Newton

        Parameters
        ----------
        observation_id : string
            id of the observation to be downloaded, mandatory
            The identifier of the observation we want to retrieve, 10 digits
            example: 0144090201
        filename : string
            file name to be used to store the file
        verbose : bool
            optional, default 'False'
            flag to display information about the process
        level : string
            level to download, optional, by default everything is downloaded
            values: ODF, PPS
        instname : string
            instrument name, optional, two characters, by default everything
            values: OM, R1, R2, M1, M2, PN
        instmode : string
            instrument mode, optional
            examples: Fast, FlatFieldLow, Image, PrimeFullWindow
        filter : string
            filter, optional
            examples: Closed, Open, Thick, UVM2, UVW1, UVW2, V
        expflag : string
            exposure flag, optional, by default everything
            values: S, U, X(not applicable)
        expno : integer
            exposure number with 3 digits, by default all exposures
            examples: 001, 003
        name : string
            product type, optional, 6 characters, by default all product types
            examples: 3COLIM, ATTTSR, EVENLI, SBSPEC, EXPMAP, SRCARF
        datasubsetno : character
            data subset number, optional, by default all
            examples: 0, 1
        sourceno : hex value
            source number, optional, by default all sources
            example: 00A, 021, 001
        extension : string
            file format, optional, by default all formats
            values: ASC, ASZ, FTZ, HTM, IND, PDF, PNG


        Returns
        -------
        None if not verbose. It downloads the observation indicated
        If verbose returns the filename
        """

        link = self.data_aio_url + "obsno=" + observation_id

        link = link + "".join("&{0}={1}".format(key, val)
                              for key, val in kwargs.items())

        if verbose:
            log.info(link)

        response = self._request('GET', link, save=False, cache=True)

        # Get original extension
        _, params = cgi.parse_header(response.headers['Content-Disposition'])
        r_filename = params["filename"]
        suffixes = Path(r_filename).suffixes

        if filename is None:
            filename = observation_id

        filename += "".join(suffixes)

        log.info("Copying file to {0}...".format(filename))
        with open(filename, 'wb') as f:
            f.write(response.content)

        if verbose:
            log.info("Wrote {0} to {1}".format(link, filename))

    def get_postcard(self, observation_id, *, image_type="OBS_EPIC",
                     filename=None, verbose=False):
        """
        Download postcards from XSA

        Parameters
        ----------
        observation_id : string
            id of the observation for which download the postcard, mandatory
            The identifier of the observation we want to retrieve, regardless
            of whether it is simple or composite.
        image_type : string
            image type, optional, default 'OBS_EPIC'
            The image_type to be returned. It can be: OBS_EPIC,
            OBS_RGS_FLUXED, OBS_RGS_FLUXED_2, OBS_RGS_FLUXED_3, OBS_EPIC_MT,
            OBS_RGS_FLUXED_MT, OBS_OM_V, OBS_OM_B, OBS_OM_U, OBS_OM_L,
            OBS_OM_M, OBS_OM_S, OBS_OM_W
        filename : string
            file name to be used to store the postcard, optional, default None
        verbose : bool
            optional, default 'False'
            Flag to display information about the process

        Returns
        -------
        None. It downloads the observation postcard indicated
        """

        params = {'RETRIEVAL_TYPE': 'POSTCARD',
                  'OBSERVATION_ID': observation_id,
                  'OBS_IMAGE_TYPE': image_type,
                  'PROTOCOL': 'HTTP'}

        link = self.data_url + "".join("&{0}={1}".format(key, val)
                                       for key, val in params.items())

        if verbose:
            log.info(link)

        local_filepath = self._request('GET', link, params, cache=True, save=True)

        if filename is None:
            response = self._request('HEAD', link)
            response.raise_for_status()
            filename = re.findall('filename="(.+)"', response.headers[
                "Content-Disposition"])[0]
        else:
            filename = observation_id + ".png"

        log.info("Copying file to {0}...".format(filename))

        shutil.move(local_filepath, filename)

        if verbose:
            log.info("Wrote {0} to {1}".format(link, filename))

        return filename

    def query_xsa_tap(self, query, *, output_file=None,
                      output_format="votable", verbose=False):
        """Launches a synchronous job to query the XSA tap

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
        table = job.get_results()
        return table

    def get_tables(self, *, only_names=True, verbose=False):
        """Get the available table in XSA TAP service

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
        """Get the available columns for a table in XSA TAP service

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
                             "XSA TAP service")

        if only_names:
            return [c.name for c in columns]
        else:
            return columns


XMMNewton = XMMNewtonClass()
