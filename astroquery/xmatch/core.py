import six

from . import XMATCH_URL, XMATCH_TIMEOUT
from ..query import BaseQuery
from ..utils import commons


class XMatchClass(BaseQuery):
    URL = XMATCH_URL()
    TIMEOUT = XMATCH_TIMEOUT()

    SUPPORTED_FORMATS = frozenset(['votable', 'json', 'csv', 'tsv'])

    def query(self, cat1, cat2, max_distance, format, colRA1=None,
              colDec1=None, colRA2=None, colDec2=None):
        """
        Parameters
        ----------
        cat1 : str or file
            Identifier of the first table. It can either be a URL, the
            payload of a local file being uploaded or a CDS table
            identifier (either *simbad* for a view of SIMBAD data, or to
            point out a given VizieR table.
            If the table is uploaded or accessed through a URL, it must be
            in VOTable or CSV format with the positions in J2000
            equatorial frame and as decimal degrees numbers.
        cat2 : str or file
            Identifier of the second table. Follows the same rules as *cat1*.
        max_distance : int, float
            Maximum distance in arcsec to look for counterparts.
            Maximum allowed value is 180.
        format : str
            Must be one of ['votable'|'json'|'csv'|'tsv'].
            Format of the result.
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

        """
        if max_distance > 180:
            raise ValueError(
                'max_distance argument must not be greater than 180')
        if format not in self.SUPPORTED_FORMATS:
            raise ValueError(
                'format argument must be one of the following: {0}'.format(
                    ', '.join(self.SUPPORTED_FORMATS)))
        payload = {
            'request': 'xmatch',
            'distMaxArcsec': max_distance,
            'RESPONSEFORMAT': format,
        }
        kwargs = {}
        if isinstance(cat1, six.string_types):
            payload['cat1'] = cat1
        elif isinstance(cat1, file):
            kwargs['files'] = {'cat1': cat1}
        if not self.is_table_available(cat1):
            # if `cat1` is not a VizieR table,
            # it is assumed it's either a URL or an uploaded table
            payload['colRA1'] = colRA1
            payload['colDec1'] = colDec1
        if isinstance(cat2, six.string_types):
            payload['cat2'] = cat2
        elif isinstance(cat2, file):
            kwargs['files'] = {'cat2': cat2}
        if not self.is_table_available(cat2):
            # if `cat2` is not a VizieR table,
            # it is assumed it's either a URL or an uploaded table
            payload['colRA2'] = colRA2
            payload['colDec2'] = colDec2
        response = commons.send_request(
            self.URL, payload, self.TIMEOUT, **kwargs)
        return response.text

    def is_table_available(self, table_id):
        """Return True if the passed CDS table identifier is one of the
        available VizieR tables, otherwise False.

        """
        return table_id in self.get_available_tables('txt').splitlines()

    def get_available_tables(self, format):
        """Get the list of the VizieR tables which are available in the
        xMatch service.

        Parameters
        ----------
        format : str
            Must be one of ['json'|'txt'].
            Format of the result.

        """
        if format not in frozenset(['json', 'txt']):
            raise ValueError('format argument must be "json" or "txt"')
        response = commons.send_request(
            'http://cdsxmatch.u-strasbg.fr/xmatch/api/v1/sync/tables',
            {'action': 'getVizieRTableNames', 'RESPONSEFORMAT': format},
            self.TIMEOUT, 'GET')
        return response.text

XMatch = XMatchClass()
