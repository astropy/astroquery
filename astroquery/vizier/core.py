# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import print_function

import sys
import os
import warnings
import json
from collections import defaultdict
import traceback
import tempfile

import astropy.units as u
import astropy.coordinates as coord
import astropy.table as tbl
import astropy.utils.data as aud
# maintain compat with PY<2.7
from astropy.utils import OrderedDict
import astropy.io.votable as votable

from ..query import BaseQuery
from ..utils import commons
from ..utils import async_to_sync
from ..utils import schema
from . import VIZIER_SERVER, VIZIER_TIMEOUT, ROW_LIMIT

PY3 = sys.version_info[0] >= 3

if PY3:
    basestring = (str, bytes)

__all__ = ['Vizier','VizierClass']

__doctest_skip__ = ['VizierClass.*']

@async_to_sync
class VizierClass(BaseQuery):
    TIMEOUT = VIZIER_TIMEOUT()
    VIZIER_SERVER = VIZIER_SERVER()
    ROW_LIMIT = ROW_LIMIT()
    
    _schema_columns = schema.Schema(schema.Or([str],None), error="columns must be a list of strings")
    _schema_column_filters = schema.Schema(schema.Or({str:str},None), error="column_filters must be a dictionary where both keys and values are strings")
    _schema_catalog = schema.Schema(schema.Or([str],str,None), error="catalog must be a list of strings or a single string")

    def __init__(self, columns=None, column_filters=None, catalog=None, keywords=None):
        self.columns = VizierClass._schema_columns.validate(columns)
        self.column_filters = VizierClass._schema_column_filters.validate(column_filters)
        self.catalog = VizierClass._schema_catalog.validate(catalog)
        self._keywords = None
        if keywords:
            self.keywords = keywords

    def _server_to_url(self, return_type='votable'):
        """
        Not generally meant to be modified, but there are different valid
        return types supported by Vizier, listed here:
        http://vizier.u-strasbg.fr/doc/asu-summary.htx

        HTML: VizieR
        votable: votable
        tab-separated-values: asu-tsv
        FITS ascii table: asu-fits
        FITS binary table: asu-binfits
        plain text: asu-txt
        """
        return "http://" + Vizier.VIZIER_SERVER + "/viz-bin/" + return_type

    @property
    def keywords(self):
        """The set of keywords to filter the Vizier search"""
        return self._keywords

    @keywords.setter
    def keywords(self, value):
        self._keywords = VizierKeyword(value)

    @keywords.deleter
    def keywords(self):
        self._keywords = None

    def find_catalogs(self, keywords, include_obsolete=False, verbose=False):
        """
        Search Vizier for catalogs based on a set of keywords, e.g. author name

        Parameters
        ----------
        keywords : list or string
            List of keywords, or space-separated set of keywords.
            From `Vizier <http://vizier.u-strasbg.fr/doc/asu-summary.htx>`_:
            "names or words of title of catalog. The words are and'ed, i.e.
            only the catalogues characterized by all the words are selected."
        include_obsolete : bool, optional
            If set to True, catalogs marked obsolete will also be returned.

        Returns
        -------
        Dictionary of the "Resource" name and the VOTable resource object.
        "Resources" are generally publications; one publication may contain
        many tables.

        Example
        -------
        >>> from astroquery.vizier import Vizier
        >>> catalog_list = Vizier.find_catalogs('Kang W51')
        >>> print(catalog_list)
        {u'J/ApJ/706/83': <astropy.io.votable.tree.Resource at 0x108d4d490>,
         u'J/ApJS/191/232': <astropy.io.votable.tree.Resource at 0x108d50490>}
        >>> print({k:v.description for k,v in catalog_list.iteritems()})
        {u'J/ApJ/706/83': u'Embedded YSO candidates in W51 (Kang+, 2009)',
         u'J/ApJS/191/232': u'CO survey of W51 molecular cloud (Bieging+, 2010)'}
        """

        if isinstance(keywords, list):
            keywords = " ".join(keywords)

        data_payload = {'-words':keywords, '-meta.all':1}
        response = commons.send_request(
            self._server_to_url(),
            data_payload,
            Vizier.TIMEOUT)
        result = self._parse_result(response, verbose=verbose, get_catalog_names=True)
        
        #Filter out the obsolete catalogs, unless requested
        if include_obsolete is False:
            for (key, resource) in result.items():
                for info in resource.infos:
                    if (info.name == 'status') and (info.value == 'obsolete'):
                        del result[key]
        
        return result

    def get_catalogs_async(self, catalog, verbose=False):
        """
        Query the Vizier service for a specific catalog

        Parameters
        ----------
        catalog : str or list, optional
            The catalog(s) that will be retrieved

        Returns
        -------
        response : `~request.response`
            Returned if asynchronous method used
        """

        data_payload = self._args_to_payload(catalog=catalog)
        response = commons.send_request(
            self._server_to_url(),
            data_payload,
            Vizier.TIMEOUT)
        return response

    def query_object_async(self, object_name, catalog=None):
        """
        Serves the same purpose as `astroquery.vizier.Vizier.query_object` but only
        returns the HTTP response rather than the parsed result.

        Parameters
        ----------
        object_name : str
            The name of the identifier.
        catalog : str or list, optional
            The catalog(s) which must be searched for this identifier.
            If not specified, all matching catalogs will be searched.

        Returns
        -------
        response : `requests.Response` object
            The response of the HTTP request.

        """
        catalog = VizierClass._schema_catalog.validate(catalog)
        center = {'-c': object_name}
        data_payload = self._args_to_payload(
            center=center,
            catalog=catalog)
        response = commons.send_request(
            self._server_to_url(),
            data_payload,
            Vizier.TIMEOUT)
        return response

    def query_region_async(
            self, coordinates, radius=None, inner_radius=None, width=None, height=None, catalog=None):
        """
        Serves the same purpose as `astroquery.vizier.Vizier.query_region` but only
        returns the HTTP response rather than the parsed result.

        Parameters
        ----------
        coordinates : str or `astropy.coordinates` object
            The target around which to search. It may be specified as a string
            in which case it is resolved using online services or as the appropriate
            `astropy.coordinates` object. ICRS coordinates may also be entered as
            a string.
        radius : convertible to `astropy.coordinates.angles.Angle`
            The radius of the circular region to query.
        inner_radius: convertible to `astropy.coordinates.angles.Angle`
            When set in addition to `radius`, the queried region becomes annular,
            with outer radius `radius` and inner radius `inner_radius`.
        width : convertible to `astropy.coordinates.angles.Angle`
            The width of the square region to query.
        height: convertible to `astropy.coordinates.angles.Angle`
            When set in addition to `width`, the queried region becomes rectangular,
            with the specified `width` and `height`.
        catalog : str or list, optional
            The catalog(s) which must be searched for this identifier.
            If not specified, all matching catalogs will be searched.

        Returns
        -------
        response : `requests.Response` object
            The response of the HTTP request.

        """
        catalog = VizierClass._schema_catalog.validate(catalog)
        center = {}
        if isinstance(coordinates, coord.SphericalCoordinatesBase) or isinstance(coordinates, basestring):
            c = commons.parse_coordinates(coordinates)
            ra = str(c.icrs.ra.degree)
            dec = str(c.icrs.dec.degree)
            if dec[0] not in ['+', '-']:
                dec = '+' + dec
            center["-c"] = "".join([ra, dec])
        elif isinstance(coordinates, tbl.Table):
            pos_list = []
            for pos in coord.ICRS(coordinates[coordinates.keys()[0]], coordinates[coordinates.keys()[1]], unit=(u.hourangle, u.deg)):
                ra_deg = pos.ra.to_string(unit="deg", decimal=True, precision=8)
                dec_deg = pos.dec.to_string(unit="deg", decimal=True, precision=8, alwayssign=True)
                pos_list += ["{}{}".format(ra_deg, dec_deg)]
            center["-c"] = "<<;"+";".join(pos_list)
        else:
            raise TypeError("{} must be one of: string, astropy coordinates, or table containing coordinates!")
        # decide whether box or radius
        if radius is not None:
            # is radius a disk or an annulus?
            if inner_radius is None:
                radius = coord.Angle(radius)
                unit, value = _parse_angle(radius)
                key = "-c.r" + unit
                center[key] = value
            else:
                i_radius = coord.Angle(inner_radius)
                o_radius = coord.Angle(radius)
                if i_radius.unit != o_radius.unit:
                    o_radius = o_radius.to(i_radius.unit)
                i_unit, i_value = _parse_angle(i_radius)
                o_unit, o_value = _parse_angle(o_radius)
                key = "-c.r" + i_unit
                center[key] = ",".join([str(i_value), str(o_value)])
        elif width is not None:
            # is box a rectangle or square?
            if height is None:
                width = coord.Angle(width)
                unit, value = _parse_angle(width)
                key = "-c.b" + unit
                center[key] = "x".join([str(value)] * 2)
            else:
                w_box = coord.Angle(width)
                h_box = coord.Angle(height)
                if w_box.unit != h_box.unit:
                    h_box = h_box.to(w_box.unit)
                w_unit, w_value = _parse_angle(h_box)
                h_unit, h_value = _parse_angle(w_box)
                key = "-c.b" + w_unit
                center[key] = "x".join([str(w_value), str(h_value)])
        else:
            raise Exception(
                "At least one of radius, width/height must be specified")
        data_payload = self._args_to_payload(
            center=center,
            catalog=catalog)
        response = commons.send_request(
            self._server_to_url(),
            data_payload,
            Vizier.TIMEOUT)
        return response

    def query_constraints_async(self, catalog=None, **kwargs):
        """
        Send a query to Vizier in which you specify constraints with keyword/value
        pairs.  See `the vizier constraints page
        <http://vizier.cfa.harvard.edu/vizier/vizHelp/cst.htx>`_ for details.

        Parameters
        ----------
        catalog : str or list, optional
            The catalog(s) which must be searched for this identifier.
            If not specified, all matching catalogs will be searched.
        kwargs : dict
            Any key/value pairs besides "catalog" will be parsed
            as additional column filters.

        Returns
        -------
        response : `requests.Response` object
            The response of the HTTP request.

        Examples
        --------
        >>> from astroquery.vizier import Vizier
        >>> # note that glon/glat constraints here *must* be floats
        >>> result = Vizier.query_constraints(catalog='J/ApJ/723/492/table1',GLON='>49.0 & < 51.0', GLAT='<0.0')
        >>> result[result.keys()[0]].pprint()
            GRSMC      GLON   GLAT   VLSR  ... RD09 _RA.icrs _DE.icrs
        ------------- ------ ------ ------ ... ---- -------- --------
        G049.49-00.41  49.49  -0.41  56.90 ... RD09   290.95    14.50
        G049.39-00.26  49.39  -0.26  50.94 ... RD09   290.77    14.48
        G049.44-00.06  49.44  -0.06  62.00 ... RD09   290.61    14.62
        G049.04-00.31  49.04  -0.31  66.25 ... RD09   290.64    14.15
        G049.74-00.56  49.74  -0.56  67.95 ... RD09   291.21    14.65
        G050.39-00.41  50.39  -0.41  41.17 ... RD09   291.39    15.29
        G050.24-00.61  50.24  -0.61  41.17 ... RD09   291.50    15.06
        G050.94-00.61  50.94  -0.61  40.32 ... RD09   291.85    15.68
        G049.99-00.16  49.99  -0.16  46.27 ... RD09   290.97    15.06
        G049.44-00.06  49.44  -0.06  46.27 ... RD09   290.61    14.62
        G049.54-00.01  49.54  -0.01  56.05 ... RD09   290.61    14.73
        G049.74-00.01  49.74  -0.01  48.39 ... RD09   290.71    14.91
        G049.54-00.91  49.54  -0.91  43.29 ... RD09   291.43    14.31
        G049.04-00.46  49.04  -0.46  58.60 ... RD09   290.78    14.08
        G049.09-00.06  49.09  -0.06  46.69 ... RD09   290.44    14.31
        G050.84-00.11  50.84  -0.11  50.52 ... RD09   291.34    15.83
        G050.89-00.11  50.89  -0.11  59.45 ... RD09   291.37    15.87
        G050.44-00.41  50.44  -0.41  64.12 ... RD09   291.42    15.34
        G050.84-00.76  50.84  -0.76  61.15 ... RD09   291.94    15.52
        G050.29-00.46  50.29  -0.46  14.81 ... RD09   291.39    15.18
        """

        catalog = VizierClass._schema_catalog.validate(catalog)
        data_payload = self._args_to_payload(
            catalog=catalog,
            column_filters=kwargs,
            center={'-c.rd':180}) 
        response = commons.send_request(
            self._server_to_url(),
            data_payload,
            Vizier.TIMEOUT)
        return response

    def _args_to_payload(self, *args, **kwargs):
        """
        accepts the arguments for different query functions and
        builds a script suitable for the Vizier votable CGI.
        """
        body = OrderedDict()
        center = kwargs.get('center')
        # process: catalog
        catalog = kwargs.get('catalog')
        if catalog is None:
            catalog = self.catalog
        if catalog is not None:
            if isinstance(catalog, basestring):
                body['-source'] = catalog
            elif isinstance(catalog, list):
                body['-source'] = ",".join(catalog)
            else:
                raise TypeError("Catalog must be specified as list or string")
        # process: columns
        columns = kwargs.get('columns')
        if columns is None:
            columns = self.columns
        if columns is None:
            columns = ["*"]
        # process: columns - always request computed positions in degrees
        if "_RAJ2000" not in columns:
            columns += ["_RAJ2000"]
        if "_DEJ2000" not in columns:
            columns += ["_DEJ2000"]
        # process: columns - identify sorting requests
        columns_out = []
        sorts_out = []
        for column in columns:
            if column[0] == '+':
                columns_out += [column[1:]]
                sorts_out += [column[1:]]
            elif column[0] == '-':
                columns_out += [column[1:]]
                sorts_out += [column]
            else:
                columns_out += [column]
        body['-out'] = ','.join(columns_out)
        if len(sorts_out)>0:
            body['-sort'] = ','.join(sorts_out)
        # process: maximum rows returned
        if Vizier.ROW_LIMIT < 0:
            body["-out.max"] = 'unlimited'
        else:
            body["-out.max"] = Vizier.ROW_LIMIT
        # process: column filters
        column_filters = kwargs.get('column_filters')
        if column_filters is None:
            column_filters = self.column_filters
        if column_filters is not None:
            for (key, value) in column_filters.items():
                body[key] = value
        # process: center
        if center is not None:
            for (key, value) in center.items():
                body[key] = value
        # add column metadata: name, unit, UCD1+, and description
        body["-out.meta"] = "huUD"
        # computed position should always be in decimal degrees
        body["-oc.form"] = "d"
        # create final script
        script = "\n".join(["{key}={val}".format(key=key, val=val)
                   for key, val in body.items()])
        # add keywords
        if not isinstance(self.keywords, property) and self.keywords is not None:
            script += "\n" + str(self.keywords)
        return script

    def _parse_result(self, response, get_catalog_names=False, verbose=False):
        """
        Parses the HTTP response to create an `astropy.table.Table`.
        Returns the raw result as a string in case of parse errors.

        Parameters
        ----------
        response : `requests.Response`
            The response of the HTTP POST request
        get_catalog_names : bool
            If specified, return only the table names (useful for table
            discovery)

        Returns
        -------
        `astroquery.utils.commons.TableList`
            An OrderedDict of `astropy.table.Table` objects.
            If there are errors in the parsing, then returns the raw results as a string.
        """
        if not verbose:
            commons.suppress_vo_warnings()
        try:
            tf = tempfile.NamedTemporaryFile()
            if PY3:
                tf.write(response.content)
            else:
                tf.write(response.content.encode('utf-8'))
            tf.file.flush()
            vo_tree = votable.parse(tf.name, pedantic=False)
            if get_catalog_names:
                return dict([(R.name,R) for R in vo_tree.resources])
            else:
                table_list = [(t.name, t.to_table())
                              for t in vo_tree.iter_tables() if len(t.array) > 0]
                return commons.TableList(table_list)

        except:
            traceback.print_exc()  # temporary for debugging
            warnings.warn(
                "Error in parsing result, returning raw result instead")
            return response.content


def _parse_angle(angle):
    """
    Retuns the Vizier-formatted units and values for box/radius
    dimensions in case of region queries.

    Parameters
    ----------
    angle : convertible to `astropy.coordinates.angles.Angle`

    Returns
    -------
    (unit, value) : tuple
        formatted for Vizier.
    """
    angle = coord.Angle(angle)
    if angle.unit == u.arcsec:
        unit, value = 's', angle.value
    elif angle.unit == u.arcmin:
        unit, value = 'm', angle.value
    else:
        unit, value = 'd', angle.to(u.deg).value
    return unit, value


class VizierKeyword(list):

    """Helper class for setting keywords for Vizier queries"""

    def __init__(self, keywords):
        file_name = aud.get_pkg_data_filename(
            os.path.join("data", "inverse_dict.json"))
        with open(file_name, 'r') as f:
            self.keyword_dict = json.load(f)
        self._keywords = None
        self.keywords = keywords

    @property
    def keywords(self):
        """ list or string for keyword(s) that must be set for the Vizier object."""
        return self._keywords

    @keywords.setter
    def keywords(self, values):
        if isinstance(values, basestring):
            values = list(values)
        keys = [key.lower() for key in self.keyword_dict]
        values = [val.lower() for val in values]
        # warn about unknown keywords
        for val in set(values) - set(keys):
            warnings.warn("{val} : No such keyword".format(val=val))
        valid_keys = [
            key for key in self.keyword_dict if key.lower() in values]
        # create a dict for each type of keyword
        set_keywords = defaultdict(list)
        for key in valid_keys:
            set_keywords[self.keyword_dict[key]].append(key)
        self._keywords = set_keywords

    @keywords.deleter
    def keywords(self):
        del self._keywords

    def __repr__(self):
        return "\n".join([self.get_keyword_str(key) for key in self.keywords])

    def get_keyword_str(self, key):
        """
        Helper function that returns the keywords, grouped into appropriate
        categories and suitable for the Vizier votable CGI.
        """
        s = ",".join([val for val in self.keywords[key]])
        keyword_name = "-kw." + key
        return keyword_name + "=" + s

Vizier = VizierClass()
