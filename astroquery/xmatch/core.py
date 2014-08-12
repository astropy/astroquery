# Licensed under a 3-clause BSD style license - see LICENSE.rst

from astropy.extern import six
from astropy.io import ascii
from astropy.units import arcsec
from astropy.table import Table

from . import conf
from ..query import BaseQuery
from ..utils import (commons, url_helpers,
                     prepend_docstr_noreturns, async_to_sync,
                     )


@async_to_sync
class XMatchClass(BaseQuery):
    URL = conf.url
    TIMEOUT = conf.timeout

    def query(self, cat1, cat2, max_distance, colRA1=None,
              colDec1=None, colRA2=None, colDec2=None):
        """Query the `CDS cross-match service
        <http://cdsxmatch.u-strasbg.fr/xmatch>`_ by finding matches between
        two (potentially big) catalogues.

        Parameters
        ----------
        cat1 : str, file or `~astropy.table.Table`
            Identifier of the first table. It can either be a URL, the
            payload of a local file being uploaded, a CDS table
            identifier (either *simbad* for a view of SIMBAD data / to
            point out a given VizieR table or a an AstroPy table.
            If the table is uploaded or accessed through a URL, it must be
            in VOTable or CSV format with the positions in J2000
            equatorial frame and as decimal degrees numbers.
            Note: If the passed argument is an AstroPy table, the column names
            are extracted from this object and the parameters `colRA1` and
            `colDec1` are ignored!
        cat2 : str or file
            Identifier of the second table. Follows the same rules as *cat1*.
        max_distance : `~astropy.units.arcsec`
            Maximum distance in arcsec to look for counterparts.
            Maximum allowed value is 180.
        colRA1 : str
            Name of the column holding the right ascension. Only required
            if `cat1` is an uploaded table or a pointer to a URL.
        colDec1 : str
            Name of the column holding the declination. Only required if
            `cat1` is an uploaded table or a pointer to a URL.
        colRA2 : str
            Name of the column holding the right ascension. Only required
            if `cat2` is an uploaded table or a pointer to a URL.
        colDec2 : str
            Name of the column holding the declination. Only required if
            `cat2` is an uploaded table or a pointer to a URL.

        Returns
        -------
        table : `~astropy.table.Table`
            Query results table

        """
        response = self.query_async(
            cat1, cat2, max_distance, colRA1, colDec1, colRA2, colDec2)
        return ascii.read(response.text, format='csv')

    @prepend_docstr_noreturns(query.__doc__)
    def query_async(
            self, cat1, cat2, max_distance, colRA1=None,
            colDec1=None, colRA2=None, colDec2=None):
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
        if isinstance(cat1, six.string_types):
            payload['cat1'] = cat1
        elif isinstance(cat1, Table):
            payload['colRA1'], payload['colDec1'] = cat1.colnames
            # write the Table's content into a new, temporary CSV-file
            # so that it can be pointed to via the `files` option
            # file will be closed when garbage-collected
            fp = six.StringIO()
            cat1.write(fp, format='ascii.csv')
            fp.seek(0)
            kwargs['files'] = {'cat1': fp}
        else:
            # assume it's a file-like object, support duck-typing
            kwargs['files'] = {'cat1': cat1}
        if not self.is_table_available(cat1) and\
                payload.get('colRA1') is None or\
                payload.get('colDec1') is None:
            # if `cat1` is not a VizieR table,
            # it is assumed it's either a URL or an uploaded table
            payload['colRA1'] = colRA1
            payload['colDec1'] = colDec1
        if isinstance(cat2, six.string_types):
            payload['cat2'] = cat2
        elif isinstance(cat2, Table):
            payload['colRA2'], payload['colDec2'] = cat2.colnames
            # write the Table's content into a new, temporary CSV-file
            # so that it can be pointed to via the `files` option
            # file will be closed when garbage-collected
            fp = six.StringIO()
            cat1.write(fp, format='ascii.csv')
            fp.seek(0)
            kwargs['files'] = {'cat1': fp}
        else:
            # assume it's a file-like object, support duck-typing
            kwargs['files'] = {'cat2': cat2}
        if not self.is_table_available(cat2) and\
                payload.get('colRA2') is None or\
                payload.get('colDec2') is None:
            # if `cat2` is not a VizieR table,
            # it is assumed it's either a URL or an uploaded table
            payload['colRA2'] = colRA2
            payload['colDec2'] = colDec2
        response = commons.send_request(
            self.URL, payload, self.TIMEOUT, **kwargs)
        return response

    def is_table_available(self, table_id):
        """Return True if the passed CDS table identifier is one of the
        available VizieR tables, otherwise False.

        """
        return table_id in self.get_available_tables()

    def get_available_tables(self):
        """Get the list of the VizieR tables which are available in the
        xMatch service and return them as a list of strings.

        """
        response = self._request(
            'GET',
            url_helpers.urljoin_keep_path(self.URL, 'tables'),
            {'action': 'getVizieRTableNames', 'RESPONSEFORMAT': 'txt'})

        content = response.text

        return content.splitlines()

XMatch = XMatchClass()
