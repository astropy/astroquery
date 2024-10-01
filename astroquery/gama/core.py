# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""Download GAMA data"""
import re
import os
from astropy.table import Table
from ..query import BaseQuery
from ..utils import commons, async_to_sync

__all__ = ['GAMA', 'GAMAClass']


@async_to_sync
class GAMAClass(BaseQuery):
    """
    TODO: document
    """

    request_url = 'https://www.gama-survey.org/dr3/query/'
    timeout = 60

    def query_sql_async(self, *args, **kwargs):
        """
        Query the GAMA database

        Returns
        -------
        url : The URL of the FITS file containing the results.
        """

        payload = self._parse_args(*args, **kwargs)

        if kwargs.get('get_query_payload'):
            return payload

        result = self._request("POST", url=self.request_url,
                               data=payload, timeout=self.timeout)

        result_url_relative = find_data_url(result.text)
        result_url = os.path.join(self.request_url, result_url_relative)

        return result_url

    def _parse_args(self, sql_query):
        """
        Parameters
        ----------
        sql_query : str
            An SQL query

        Returns
        -------
        payload_dict : Requests payload in a dictionary
        """

        payload = {'query': sql_query,
                   'format': 'fits'}

        return payload

    def _parse_result(self, result, *, verbose=False, **kwargs):
        """
        Use get_gama_datafile to download a result URL
        """
        return get_gama_datafile(result)


GAMA = GAMAClass()


def get_gama_datafile(result, **kwargs):
    """Turn a URL into an HDUList object."""
    fitsfile = commons.FileContainer(result,
                                     encoding='binary',
                                     **kwargs)
    hdulist = fitsfile.get_fits()
    return Table(hdulist[1].data)


def find_data_url(result_page):
    """Find and return the URL of the data, given a results page."""
    result_relative_url_re = re.compile(r'Download the result file: '
                                        r'<a href="(\.\./tmp/.*?)">')
    re_result = result_relative_url_re.findall(result_page)
    if len(re_result) == 0:
        raise ValueError("Results did not contain a result url")
    return re_result[0]
