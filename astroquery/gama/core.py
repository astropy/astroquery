"""Download GAMA data"""
import re
import os
import astropy.utils.data as aud
from astropy.io import fits
from astropy.table import Table
from ..query import BaseQuery
from ..utils.class_or_instance import class_or_instance
from ..utils import commons, async_to_sync

__all__ = ['GAMA']

@async_to_sync
class GAMA(BaseQuery):
    """
    TODO: document
    """

    request_url = 'http://www.gama-survey.org/dr2/query/'
    result_relative_url_re = re.compile(r'Download the result file: <a href="(\.\./tmp/.*?)">')
    timeout = 60

    @class_or_instance
    def query_sql_async(self, *args, **kwargs):
        """
        Query the GAMA database

        Returns
        -------
        The URL of the FITS file containing the results.
        """

        payload = self._parse_args(*args, **kwargs)

        if kwargs.get('get_query_payload'):
            return payload

        result = commons.send_request(self.request_url,
                                      payload,
                                      self.timeout)

        re_result = self.result_relative_url_re.findall(result.text)

        if len(re_result) == 0:
            raise ValueError("Results did not contain a result url")
        else:
            result_url = os.path.join(self.request_url, re_result[0])

        return result_url

    @class_or_instance
    def _parse_args(self, sql_query):
        """
        Parameters
        ----------
        sql_query : str
            An SQL query

        Returns
        -------
        Requests payload in a dictionary
        """

        payload = {'query': sql_query,
                   'format': 'fits'}

        return payload

    @class_or_instance
    def _parse_result(self, result, verbose=False, **kwargs):
        """
        Use get_gama_datafile to download a result URL
        """
        return get_gama_datafile(result)


def get_gama_datafile(result):
    """Turn a URL into an HDUList object."""
    with aud.get_readable_fileobj(result) as f:
        hdulist = fits.HDUList.fromstring(f.read())
    return Table(hdulist[1].data)


