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
        """
        if filename is not None:
            filename = os.path.splitext(filename)[0]

        if retrieval_type is None:
            retrieval_type = "OBSERVATION"

        if retrieval_type == "OBSERVATION" and instrument_name is None:
            instrument_name = "PACS"

        params = {'retrieval_type': retrieval_type,
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

    def get_observation(self, observation_id, instrument_name, *, filename=None,
                        verbose=False,
                        cache=True, **kwargs):
        """
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
        """
        job = self._tap.launch_job(query=query, output_file=output_file,
                                   output_format=output_format,
                                   verbose=verbose,
                                   dump_to_file=output_file is not None)
        table = job.get_results()
        return table

    def get_tables(self, *, only_names=True, verbose=False):
        """
        """
        tables = self._tap.load_tables(verbose=verbose)
        if only_names:
            return [t.name for t in tables]
        else:
            return tables

    def get_columns(self, table_name, *, only_names=True, verbose=False):
        """
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
