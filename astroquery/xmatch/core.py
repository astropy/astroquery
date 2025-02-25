# Licensed under a 3-clause BSD style license - see LICENSE.rst

from io import StringIO, BytesIO

from astropy.io import votable
import astropy.units as u
from astropy.table import Table
from requests import HTTPError

from astroquery.query import BaseQuery
from astroquery.exceptions import InvalidQueryError
from astroquery.utils import url_helpers, prepend_docstr_nosections, async_to_sync

from . import conf
try:
    from regions import CircleSkyRegion
except ImportError:
    print('Could not import regions, which is required for some of the '
          'functionalities of this module.')


@async_to_sync
class XMatchClass(BaseQuery):
    URL = conf.url
    TIMEOUT = conf.timeout

    def query(self, cat1, cat2, max_distance, *,
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
        cat2 : str, file or `~astropy.table.Table`
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
        cache : bool
            Defaults to True. If set overrides global caching behavior.
            See :ref:`caching documentation <astroquery_cache>`.

        Returns
        -------
        table : `~astropy.table.Table`
            Query results table
        """
        response = self.query_async(cat1, cat2, max_distance, colRA1=colRA1, colDec1=colDec1,
                                    colRA2=colRA2, colDec2=colDec2, area=area, cache=cache,
                                    get_query_payload=get_query_payload,
                                    **kwargs)
        if get_query_payload:
            return response

        content = BytesIO(response.content)
        return Table.read(content, format='votable', use_names_over_ids=True)

    @prepend_docstr_nosections("\n" + query.__doc__)
    def query_async(self, cat1, cat2, max_distance, *, colRA1=None, colDec1=None,
                    colRA2=None, colDec2=None, area='allsky', cache=True,
                    get_query_payload=False, **kwargs):
        """
        Returns
        -------
        response : `~requests.Response`
            The HTTP response returned from the service.
        """
        if max_distance > 180 * u.arcsec:
            raise ValueError('max_distance argument must not be greater than 180".')
        payload = {'request': 'xmatch',
                   'distMaxArcsec': max_distance.to(u.arcsec).value,
                   'RESPONSEFORMAT': 'votable',
                   **kwargs}

        kwargs = {}

        self._prepare_sending_table(1, payload, kwargs, cat1, colRA1, colDec1)
        self._prepare_sending_table(2, payload, kwargs, cat2, colRA2, colDec2)
        self._prepare_area(payload, area)

        if get_query_payload:
            return payload, kwargs

        response = self._request(method='POST', url=self.URL, data=payload,
                                 timeout=self.TIMEOUT, cache=cache, **kwargs)

        if response.status_code == 403:
            raise HTTPError("Your IP address has been banned from the XMatch server. "
                            "This means that you sent too many cross-matching jobs in "
                            "parallel to the service, blocking other astronomers. Please"
                            " contact the CDS team at cds-question[at]unistra.fr to "
                            "find a solution.")

        try:
            response.raise_for_status()
        except HTTPError as err:
            error_votable = votable.parse(BytesIO(response.content))
            error_reason = error_votable.get_info_by_id('QUERY_STATUS').content
            raise InvalidQueryError(error_reason) from err

        return response

    def _prepare_sending_table(self, cat_index, payload, kwargs, cat, colRA, colDec):
        '''Check if table is a string, a `astropy.table.Table`, etc. and set
        query parameters accordingly.
        '''
        catstr = 'cat{0}'.format(cat_index)
        if isinstance(cat, str):
            if (self.is_table_available(cat) and not cat.startswith("vizier:")):
                # if we detect that the given name is a vizier table, we can make
                # it comply to the API, see issue #3191
                cat = f"vizier:{cat}"
            payload[catstr] = cat
        else:
            # create the dictionary of uploaded files
            if "files" not in kwargs:
                kwargs["files"] = {}
            if isinstance(cat, Table):
                # write the Table's content into a new, temporary CSV-file
                # so that it can be pointed to via the `files` option
                # file will be closed when garbage-collected

                fp = StringIO()
                cat.write(fp, format='ascii.csv')
                fp.seek(0)
                kwargs['files'].update({catstr: (f'cat{cat_index}.csv', fp.read())})
            else:
                # assume it's a file-like object, support duck-typing
                kwargs['files'].update({catstr: (f'cat{cat_index}.csv', cat.read())})

        if not self.is_table_available(cat):
            if ((colRA is None) or (colDec is None)):
                raise ValueError(
                    f"'{cat}' is not available on the XMatch server. If you are "
                    "using a VizieR table name, note that only tables with "
                    "coordinates are available on the XMatch server. If you are "
                    f"using a local table, the arguments 'colRA{cat_index}' and "
                    f"'colDec{cat_index}' must be provided.")
            # if `cat1` is not a VizieR table,
            # it is assumed it's either a URL or an uploaded table
            payload['colRA{0}'.format(cat_index)] = colRA
            payload['colDec{0}'.format(cat_index)] = colDec

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
        if not isinstance(table_id, str):
            return False

        if table_id.startswith('vizier:'):
            table_id = table_id[7:]

        return table_id in self.get_available_tables()

    def get_available_tables(self, *, cache=True):
        """Get the list of the VizieR tables which are available in the
        xMatch service and return them as a list of strings.

        Parameters
        ----------
        cache : bool
            Defaults to True. If set overrides global caching behavior.
            See :ref:`caching documentation <astroquery_cache>`.
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
