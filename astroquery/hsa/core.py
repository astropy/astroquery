# Licensed under a 3-clause BSD style license - see LICENSE.rst

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
