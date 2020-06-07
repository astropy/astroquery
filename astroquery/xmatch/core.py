# Licensed under a 3-clause BSD style license - see LICENSE.rst

import six
from astropy.io import ascii
import astropy.units as u
from astropy.table import Table

from . import conf
from ..query import BaseQuery
from ..utils import url_helpers, prepend_docstr_nosections, async_to_sync

try:
    from regions import CircleSkyRegion
except ImportError:
    print('Could not import regions, which is required for some of the '
          'functionalities of this module.')


@async_to_sync
class XMatchClass(BaseQuery):
    URL = conf.url
    TIMEOUT = conf.timeout

    def query(self, cat1, cat2, max_distance,
              colRA1=None, colDec1=None, colRA2=None, colDec2=None,
              area='allsky', cache=True, get_query_payload=False, **kwargs):
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
        max_distance : `~astropy.units.Quantity`
            Maximum distance to look for counterparts.
            Maximum allowed value is 180 arcsec.
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
        area : ``regions.CircleSkyRegion`` or 'allsky' str
            Restrict the area taken into account when performing the xmatch
            Default value is 'allsky' (no restriction). If a
            ``regions.CircleSkyRegion`` object is given, only sources in
            this region will be considered.

        Returns
        -------
        table : `~astropy.table.Table`
            Query results table
        """
        response = self.query_async(cat1, cat2, max_distance, colRA1, colDec1,
                                    colRA2, colDec2, area=area, cache=cache,
                                    get_query_payload=get_query_payload,
                                    **kwargs)
        if get_query_payload:
            return response
        return self._parse_text(response.text)

    @prepend_docstr_nosections("\n" + query.__doc__)
    def query_async(self, cat1, cat2, max_distance, colRA1=None, colDec1=None,
                    colRA2=None, colDec2=None, area='allsky', cache=True,
                    get_query_payload=False, **kwargs):
        """
        Returns
        -------
        response : `~requests.Response`
            The HTTP response returned from the service.
        """
        if max_distance > 180 * u.arcsec:
            raise ValueError(
                'max_distance argument must not be greater than 180')
        payload = {
            'request': 'xmatch',
            'distMaxArcsec': max_distance.to(u.arcsec).value,
            'RESPONSEFORMAT': 'csv',
            **kwargs
        }
        kwargs = {}

        self._prepare_sending_table(1, payload, kwargs, cat1, colRA1, colDec1)
        self._prepare_sending_table(2, payload, kwargs, cat2, colRA2, colDec2)
        self._prepare_area(payload, area)

        if get_query_payload:
            return payload, kwargs

        response = self._request(method='POST', url=self.URL, data=payload,
                                 timeout=self.TIMEOUT, cache=cache, **kwargs)
        response.raise_for_status()

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
            kwargs['files'] = {catstr: ('cat1.csv', fp.read())}
        else:
            # assume it's a file-like object, support duck-typing
            kwargs['files'] = {catstr: ('cat1.csv', cat.read())}

        if not self.is_table_available(cat):
            if ((colRA is None) or (colDec is None)):
                raise ValueError('Specify the name of the RA/Dec columns in' +
                                 ' the input table.')
            # if `cat1` is not a VizieR table,
            # it is assumed it's either a URL or an uploaded table
            payload['colRA{0}'.format(i)] = colRA
            payload['colDec{0}'.format(i)] = colDec

    def _prepare_area(self, payload, area):
        '''Set the area parameter in the payload'''
        if area is None or area == 'allsky':
            payload['area'] = 'allsky'
        elif isinstance(area, CircleSkyRegion):
            payload['area'] = 'cone'
            cone_center = area.center
            payload['coneRA'] = cone_center.icrs.ra.deg
            payload['coneDec'] = cone_center.icrs.dec.deg
            payload['coneRadiusDeg'] = area.radius.to_value(u.deg)
        else:
            raise ValueError('Unsupported area {}'.format(str(area)))

    def is_table_available(self, table_id):
        """Return True if the passed CDS table identifier is one of the
        available VizieR tables, otherwise False.

        """

        # table_id can actually be a Table instance, there is no point in
        # comparing those to stings
        if not isinstance(table_id, six.string_types):
            return False

        if (table_id[:7] == 'vizier:'):
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

    def _parse_text(self, text):
        """
        Parse a CSV text file that has potentially duplicated header names
        """
        header = text.split("\n")[0]
        colnames = header.split(",")
        for cn in colnames:
            if colnames.count(cn) > 1:
                ii = 1
                while colnames.count(cn) > 0:
                    colnames[colnames.index(cn)] = cn + "_{ii}".format(ii=ii)
                    ii += 1
        new_text = ",".join(colnames) + "\n" + "\n".join(text.split("\n")[1:])
        result = ascii.read(new_text, format='csv', fast_reader=False)

        return result


XMatch = XMatchClass()
