# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import print_function

import requests
import io
import numpy as np
#------------------
from ..query import BaseQuery
from ..utils.class_or_instance import class_or_instance
from ..utils import commons
import os
import astropy.units as u
import astropy.coordinates as coord
import astropy.utils.data as aud
import warnings
import json
from collections import defaultdict
# maintain compat with PY<2.7
from astropy.utils import OrderedDict
try:
    import astropy.io.vo.table as votable
except ImportError:
    import astropy.io.votable as votable
from astropy.table import Table

from . import VIZIER_SERVER

__all__ = ['vizquery', 'Vizier', 'VizierKeyword']

class Vizier(BaseQuery):
    TIMEOUT = 60
    VIZIER_URL = "http://"+VIZIER_SERVER()+"/viz-bin/votable"
    def __init__(self, columns=None, keywords=None):
        self.columns = columns
        self._keywords = None
        if keywords is not None:
            self.keywords = keywords

    @property
    def keywords(self):
        return self._keywords

    @keywords.setter
    def keywords(self, value):
        self._keywords = VizierKeyword(value)

    @keywords.deleter
    def keywords(self):
        del self._keywords

    @class_or_instance
    def query_object(self, object_name, catalog=None):
        response = self.query_object_async(object_name, catalog=catalog)
        result = self._parse_result(response)
        return result

    @class_or_instance
    def query_object_async(self, object_name, catalog=None):
        data_payload = self._args_to_payload(object_name, catalog=catalog, caller='query_object_async')
        response = commons.send_request(Vizier.VIZIER_URL, data_payload, Vizier.TIMEOUT)
        return response

    @class_or_instance
    def query_region(self, coordinates, radius=None, height=None, width=None, catalog=None):
        response = self.query_region_async(coordinates, radius=radius, height=height,
                                           width=width, catalog=catalog)
        result = self._parse_result(response)
        return result

    @class_or_instance
    def query_region_async(self, coordinates, radius=None, height=None, width=None, catalog=None):
        data_payload = self._args_to_payload(coordinates, radius=radius, height=height,
                                            width=width, catalog=catalog, caller='query_region_async')
        response = commons.send_request(Vizier.VIZIER_URL, data_payload, Vizier.TIMEOUT)
        return response

    @class_or_instance
    def _args_to_payload(self, *args, **kwargs):
        body = OrderedDict()
        caller = kwargs['caller']
        del kwargs['caller']
        catalog = kwargs.get('catalog')
        if catalog is not None:
            if isinstance(catalog, basestring):
                body['-source'] = catalog
            elif isinstance(catalog, list):
                body['-source'] = ",".join(catalog)
            else:
                raise TypeError("Catalog must be specified as list or string")
        if caller == 'query_object_async':
            body["-c"] = args[0]
        elif caller == 'query_region_async':
            c = commons.parse_coordinates(args[0])
            ra = str(c.icrs.ra.degrees)
            dec = str(c.icrs.dec.degrees)
            if dec[0] not in ['+', '-']:
               dec = '+' + dec
            body["-c"] = "".join([ra, dec])
            #decide whether box or radius
            if kwargs.get('radius') is not None:
                radius = kwargs['radius']
                unit, value = _parse_dimension(radius)
                switch = "-c.r" + unit
                body[switch] = value
            elif kwargs.get('width') is not None:
                width = kwargs['width']
                w_unit, w_value = _parse_dimension(width)
                switch = "-c.b" + w_unit
                height = kwargs.get('height')
                # is box a rectangle or square?
                if height is not None:
                    h_unit, h_value = _parse_dimension(height)
                    if h_unit != w_unit:
                        warnings.warn("Converting height to same unit as width")
                        h_value = u.Quantity(h_value, u.Unit
                                             (_str_to_unit(h_unit))).to(u.Unit(_str_to_unit(w_unit)))
                    body[switch] = "x".join([str(w_value), str(h_value)])
                else:
                    body[switch] = "x".join([str(w_value)]*2)
            elif kwargs.get('height'):
                warnings.warn("No width given - shape interpreted as square (height x height)")
                height = kwargs['height']
                h_unit, h_value = _parse_dimension(height)
                switch = "-c.b" + h_unit
                body[switch] = h_value
            else:
                raise Exception("At least one of radius, width/height must be specified")

        body["-out"]  = ",".join(['_RAJ2000', '_DEJ2000'])
        body["-out.max"] = 5
        script = "\n".join(["{key}={val}".format(key=key, val=val) for key, val  in body.items()])
        # add keywords
        if self.keywords is not None:
            script += str(self.keywords)
        return script

    @class_or_instance
    def _parse_result(self, response):
        try:
            s = io.BytesIO(response.content)
            voTable = votable.parse(s, pedantic=False)

            # Convert VOTABLE into a list of astropy Table.
            tableList = []
            for voTreeTable in voTable.iter_tables():
                if len(voTreeTable.array)>0:
                    # Table names come from the VOTABLE fields
                    names = []
                    for field in voTreeTable.fields:
                        names += [field.name.encode('ascii')]
                        # Table data come from the VOTABLE record array
                        tableList += [voTreeTable.to_table()]

            # Merge the Table list
            table = tableList[0]
            if len(tableList)>1:
                for t in tableList[1:]:
                    if len(t)>0:
                        for row in t:
                            table.add_row(row)

            return table
        except:
            warnings.warn("Error in parsing result, returning raw result instead")
            return response.content

def _parse_dimension(dim):
    if isinstance(dim, u.Quantity) and dim.unit in u.deg.find_equivalent_units():
                    if dim.unit == u.arcsec:
                        unit, value = 's', dim.value
                    elif dim.unit == u.arcmin:
                        unit, value = 'm', dim.value
                    else:
                        unit, value = 'd', dim.to(u.deg).value
    # otherwise must be an Angle or be specified in hours...
    else:
        try:
            new_dim = commons.parse_radius(dim)
            unit, value = 'd', new_dim.degrees
        except (u.UnitsException, coord.errors.UnitsError, AttributeError):
            raise u.UnitsException("Dimension not in proper units")

    return unit, value

def _str_to_unit(string):
    str_to_unit = {
                    's' : 'arcsec',
                    'm' : 'arcmin',
                    'd' : 'degree'
                   }
    return str_to_unit[string]

#--------------------------------------------------------
def vizquery(query, server=None):
    """
    VizieR search query.

    This function can be used to search all the catalogs available through the VizieR service.

    Parameters
    ----------
    query: dict
        A dictionary specifying the query.
        For acceptable keys, refer to the links given in the references section.
        The dictionary values can be any of the following types:
           * string
           * list of string
           * astropy.table.Table (containing columns "_RAJ2000" and "_DEJ2000" in degrees)
    server: str, optional
        The VizieR server to use. (See VizieR mirrors at http://vizier.u-strasbg.fr)
        If not specified, `server` is set by the `VIZIER_SERVER` configuration item.

    Returns
    -------
    table : `~astropy.table.Table`
        A table containing the results of the query

    References
    ----------
    * http://vizier.u-strasbg.fr/doc/asu-summary.htx
    * http://vizier.u-strasbg.fr/vizier/vizHelp/menu.htx

    """

    #Check VizieR server
    server = (VIZIER_SERVER() if server is None else server)

    # Always add calculated _RAJ2000 & _DEJ2000 to the query.
    # This is used for cross correlations between queries
    if '-out.add' in query:
        query["-out.add"] += ['_RAJ2000', '_DEJ2000']
    else:
        query["-out.add"]  = ['_RAJ2000', '_DEJ2000']

    # Assemble the actual query
    body = []
    for (key,value) in query.items():
        if type(value) is str:
            body += ["%s=%s"%(key, value)]
        elif type(value) is Table: # Value is a table, convert it to a string, list of positions
            pos = []
            for elem in np.array(value, copy=False):
                pos += ["%.8f%+.8f"%(elem['_RAJ2000'],elem['_DEJ2000'])] # Position with the format: _RAJ2000+_DEJ2000
            body += ["-out.add=_q"] # This calculated index is a reference to the input table
            body += ["%s=%s"%(key, "<<;"+";".join(pos))] # The proper convention: <<;pos1;pos2;pos3
        elif type(value) is list: # Value is a list, join it with commas
            body += ["%s=%s"%(key, ",".join(value))]
        else:
            raise Exception("Don't know how to handle %s"%repr(value))
    body = "\r\n".join(body)

    # Fetch the VOTABLE corresponding to the query
    r = requests.post("http://"+server+"/viz-bin/votable", data=body)
    s = io.BytesIO(r.content)
    voTable = votable.parse(s, pedantic=False)

    # Convert VOTABLE into a list of astropy Table.
    tableList = []
    for voTreeTable in voTable.iter_tables():
        if len(voTreeTable.array)>0:
            # Table names come from the VOTABLE fields
            names = []
            for field in voTreeTable.fields:
                names += [field.name.encode('ascii')]
            # Table data come from the VOTABLE record array
            tableList += [voTreeTable.to_table()]

    # Merge the Table list
    table = tableList[0]
    if len(tableList)>1:
        for t in tableList[1:]:
            if len(t)>0:
                for row in t:
                    table.add_row(row)

    return table

class VizierKeyword(object):
    def __init__(self, keywords):
        file_name = aud.get_pkg_data_filename(os.path.join("data", "inverse_dict.json"))
        with open(file_name, 'r') as f:
            self.keyword_dict = json.load(f)
        self._keywords = None
        self.keywords = keywords


    @property
    def keywords(self):
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
        valid_keys = [key for key in self.keyword_dict if key.lower() in values]
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
        s = ",".join([val for val in self.keywords[key]])
        keyword_name = "-kw." + key
        return keyword_name + "=" + s
