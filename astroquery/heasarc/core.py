# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import print_function
from astropy.extern.six import BytesIO
from astropy.table import Table
from astropy.io import fits
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
                           get_query_payload=False,
                           display_mode='FitsDisplay'):
        """TODO: document this!

        (maybe start by copying over from some other service.)
        """
        request_payload = dict()
        request_payload['Entry'] = object_name
        request_payload['tablehead'] = ('BATCHRETRIEVALCATALOG_2.0 {}'
                                        .format(mission))
        request_payload['Action'] = 'Query'
        request_payload['displaymode'] = display_mode

        if get_query_payload:
            return request_payload

        response = self._request('GET', self.URL, params=request_payload,
                                 timeout=self.TIMEOUT, cache=cache)
        return response

    def _fallback(self, content):
        """
        Blank columns which have to be converted to float or in fail so
        lets fix that by replacing with -1's
        """

        data = BytesIO(content)
        header = fits.getheader(data, 1)  # Get header for column info
        colstart = [y for x, y in header.items() if "TBCOL" in x]
        collens = [int(float(y[1:]))
                   for x, y in header.items() if "TFORM" in x]
        new_table = []

        old_table = content.split("END")[-1].strip()
        for line in old_table.split("\n"):
            newline = []
            for n, tup in enumerate(zip(colstart, collens), start=1):
                cstart, clen = tup
                part = line[cstart - 1:cstart + clen]
                newline.append(part)
                if len(part.strip()) == 0:
                    if header["TFORM%i" % n][0] in ["F", "I"]:
                        # extra space is required to sperate column
                        newline[-1] = "-1".rjust(clen) + " "
            new_table.append("".join(newline))

        data = BytesIO(content.replace(old_table, "\n".join(new_table)))
        return Table.read(data, hdu=1)

    def _parse_result(self, response, verbose=False):
        # if verbose is False then suppress any VOTable related warnings
        if not verbose:
            commons.suppress_vo_warnings()
        try:
            data = BytesIO(response.content)
            table = Table.read(data, hdu=1)
            return table
        except ValueError:
            return self._fallback(response.content)


Heasarc = HeasarcClass()
