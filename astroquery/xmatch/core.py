# Licensed under a 3-clause BSD style license - see LICENSE.rst

from astropy.extern import six
from astropy.io import ascii
from astropy.units import arcsec
from astropy.table import Table

from . import conf
from ..query import BaseQuery
from ..utils import (url_helpers,
                     prepend_docstr_noreturns, async_to_sync,
                     )


@async_to_sync
class XMatchClass(BaseQuery):
    URL = conf.url
    TIMEOUT = conf.timeout

    def query(self, cat1, cat2, max_distance, colRA1=None, colDec1=None,
              colRA2=None, colDec2=None, cache=True):
        """
        Query the `CDS cross-match service
        <http://cdsxmatch.u-strasbg.fr/xmatch>`_ by finding matches between
        two (potentially big) catalogues.

        Parameters
        ----------
        cat1 : str, file or `~astropy.table.Table`
            Identifier of the first table. It can either be a URL, the
            payload of a local file being uploaded, a CDS table
            identifier (either *simbad* for a view of SIMBAD data / to
            point out a given VizieR table) or a an AstroPy table.
            If the table is uploaded or accessed through a URL, it must be
            in VOTable or CSV format with the positions in J2000
            equatorial frame and as decimal degrees numbers.
        cat2 : str or file
            Identifier of the second table. Follows the same rules as *cat1*.
        max_distance : `~astropy.units.arcsec`
            Maximum distance in arcsec to look for counterparts.
            Maximum allowed value is 180.
        colRA1 : str
            Name of the column holding the right ascension. Only required
            if ``cat1`` is an uploaded table or a pointer to a URL.
        colDec1 : str
            Name of the column holding the declination. Only required if
            ``cat1`` is an uploaded table or a pointer to a URL.
        colRA2 : str
            Name of the column holding the right ascension. Only required
            if ``cat2`` is an uploaded table or a pointer to a URL.
        colDec2 : str
            Name of the column holding the declination. Only required if
            ``cat2`` is an uploaded table or a pointer to a URL.

        Returns
        -------
        table : `~astropy.table.Table`
            Query results table
        """
        response = self.query_async(cat1, cat2, max_distance, colRA1, colDec1,
                                    colRA2, colDec2, cache=cache)
        return ascii.read(response.text, format='csv')

    @prepend_docstr_noreturns("\n" + query.__doc__)
    def query_async(self, cat1, cat2, max_distance, colRA1=None, colDec1=None,
                    colRA2=None, colDec2=None, cache=True):
        """
        Returns
        -------
        response : `requests.Response`
            The HTTP response returned from the service.
        """
        if max_distance > 180 * arcsec:
            raise ValueError(
                'max_distance argument must not be greater than 180')
        payload = {
            'request': 'xmatch',
            'distMaxArcsec': max_distance.value,
            'RESPONSEFORMAT': 'csv',
        }
        kwargs = {}

        self._prepare_sending_table(1, payload, kwargs, cat1, colRA1, colDec1)
        self._prepare_sending_table(2, payload, kwargs, cat2, colRA2, colDec2)

        response = self._request(method='POST', url=self.URL, data=payload,
                                 timeout=self.TIMEOUT, cache=cache, **kwargs)
        return response

    def _prepare_sending_table(self, i, payload, kwargs, cat, colRA, colDec):
        '''Check if table is a string, a `astropy.table.Table`, etc. and set
        query parameters accordingly.
        '''
        catstr = 'cat{0}'.format(i)
        if isinstance(cat, six.string_types):
            payload[catstr] = cat
        elif isinstance(cat, Table):
            # write the Table's content into a new, temporary CSV-file
            # so that it can be pointed to via the `files` option
            # file will be closed when garbage-collected
            fp = six.StringIO()
            cat.write(fp, format='ascii.csv')
            fp.seek(0)
            kwargs['files'] = {catstr: fp}
        else:
            # assume it's a file-like object, support duck-typing
            kwargs['files'] = {catstr: cat}
        if not self.is_table_available(cat):
            if ((colRA is None) or (colDec is None)):
                raise ValueError('Specify the name of the RA/Dec columns in' +
                                 ' the input table.')
            # if `cat1` is not a VizieR table,
            # it is assumed it's either a URL or an uploaded table
            payload['colRA{0}'.format(i)] = colRA
            payload['colDec{0}'.format(i)] = colDec


    def is_table_available(self, table_id):
        """Return True if the passed CDS table identifier is one of the
        available VizieR tables, otherwise False.

        """
        if isinstance(table_id, six.string_types) and (table_id[:7] == 'vizier:'):
            table_id = table_id[7:]
        return table_id in self.get_available_tables()

    def get_available_tables(self, cache=True):
        """Get the list of the VizieR tables which are available in the
        xMatch service and return them as a list of strings.

        """
        response = self._request(
            'GET',
            url_helpers.urljoin_keep_path(self.URL, 'tables'),
            {'action': 'getVizieRTableNames', 'RESPONSEFORMAT': 'txt'},
            cache=cache,
        )

        content = response.text

        return content.splitlines()

XMatch = XMatchClass()
