# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import print_function
from astropy.extern.six import BytesIO
from astropy.table import Table
from ..query import BaseQuery
from ..utils import commons
from ..utils import async_to_sync
from . import conf

__all__ = ['Heasarc', 'HeasarcClass']


@async_to_sync
class HeasarcClass(BaseQuery):
    """HEASARC query class.
    """

    URL = conf.server
    TIMEOUT = conf.timeout

    def query_object_async(self, object_name, mission, cache=True,
                           get_query_payload=False):
        """TODO: document this!

        (maybe start by copying over from some other service.)
        """
        request_payload = dict()
        request_payload['object_name'] = object_name
        request_payload['tablehead'] = ('BATCHRETRIEVALCATALOG_2.0 {}'
                                        .format(mission))
        request_payload['Action'] = 'Query'
        request_payload['displaymode'] = 'FitsDisplay'

        if get_query_payload:
            return request_payload

        response = self._request('GET', self.URL, params=request_payload,
                                 timeout=self.TIMEOUT, cache=cache)
        return response

    def _parse_result(self, response, verbose=False):
        # if verbose is False then suppress any VOTable related warnings
        if not verbose:
            commons.suppress_vo_warnings()

        data = BytesIO(response.content)
        table = Table.read(data, hdu=1)
        return table


Heasarc = HeasarcClass()
