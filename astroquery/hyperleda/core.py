# Licensed under a 3-clause BSD style license - see LICENSE.rst

__author__ = "Iskren Y. Georgiev"
__author_email__ = "iskren.y.g@gmail.com"

# Based on: https://astroquery.readthedocs.io/en/latest/template.html

# Imports organized as shown below

# 1. local imports relative imports
# all Query classes should inherit from BaseQuery.
from ..query import BaseQuery
# has common functions required by most modules
from ..utils import commons
# prepend_docstr is a way to copy docstrings between methods
from ..utils import prepend_docstr_nosections
# async_to_sync generates the relevant query tools from _async methods
from ..utils import async_to_sync
from ..utils.class_or_instance import class_or_instance
# import configurable items declared in __init__.py
from . import conf

# 2. standard library imports

# 3. third party imports
import astropy.units as u
import astropy.coordinates as coord
import astropy.io.votable as votable
from astropy.table import Table, vstack
from astropy.io import fits

# export all the public classes and methods
__all__ = ['hyperleda', 'HyperLEDAClass']

# declare global variables and constants if any

# Begin main class
# Should be decorated with the async_to_sync imported previously


@async_to_sync
class HyperLEDAClass(BaseQuery):

    """
    Base class for querying data from the HyperLEDA database.

    http://leda.univ-lyon1.fr

    """

    URL = conf.server
    TIMEOUT = conf.timeout
    # The URL with the table of the main object properties
    URL_PROPERTIES = URL + '/leda/meandata.html'
    URL_HTTP_REQUEST = URL + '/fG.cgi'

    @class_or_instance
    def get_properties(self):
        """

        Get the available object properties in the HyperLEDA database.
        (See http://leda.univ-lyon1.fr/leda/meandata.html)

        Returns an `~astropy.table.Table` object.

        Returns
        -------

        prop_tbl : An `~astropy.table.Table` object with the available object
        properties in HyperLEDA

        Example
        --------
        >>> from astroquery.hyperleda import hyperleda
        >>>
        >>> properties_tbl = hyperleda.get_properties()
        >>> properties_tbl.pprint_all()

        """

        url_prop = self.URL_PROPERTIES
        response = self._request("GET", url_prop)
        prop_tbl = self._parse_result(response)

        return prop_tbl

    def _perp_param_lst(self, param_lst):

        # Prepare the parameter's list
        # These params are no longer in the leda tables
        for param in ['numtype', 'hptr', 'logavmm', 'e_logavmm']:
            if param in param_lst:
                param_lst.remove(param)

        param_str = str(param_lst)
        param_str = param_str[2:param_str.rfind('\'')]
        param_str = param_str.replace('\', \'', ',')
        return param_str

    @class_or_instance
    def query_object(self, obj_name, properties='all'):
        """

        Query an object from the HyperLEDA database.

        Returns the object properties in an `~astropy.table.Table` object.

        Example
        --------
        >>> from astroquery.hyperleda import hyperleda
        >>> result_table = hyperleda.query_object(obj_name = 'UGC12591',
                                           properties = 'objname,type,logr25,
                                           btc,v,modbest,al2000,de2000,
                                           celposJ(pgc)')
        >>> result_table.pprint()

        Parameters
        ----------
        obj_name : str

            Object ID recognizable by HyperLEDA or SIMBAD

        properties : str, or comma separated strings. Default: 'all'

            The full list of properties in HyperLEDA is available at
            http://leda.univ-lyon1.fr/leda/meandata.html
            or via
            hyperleda.get_properties().pprint_all()

        Returns
        -------

        Table : An `~astropy.table.Table` object with the object properties
            from HyperLEDA

        """

        if properties == 'all':
            prop_tbl = self.get_properties()
            param_lst = prop_tbl['field'].data.tolist()
            param_str = self._perp_param_lst(param_lst)
        else:
            param_str = properties

        url_http_request = self.URL_HTTP_REQUEST

        ls_SQL_search = "objname = objname('{:}')".format(obj_name)

        request_payload = dict(n='meandata', c='o', of='1,leda,simbad',
                               nra='l', nakd='1',
                               d='{:}'.format(param_str),
                               sql='{:}'.format(ls_SQL_search), ob='',
                               a='csv[|]')
        response = self._request("GET", url_http_request,
                                 params=request_payload)
        sql_result_tbl = Table.read(response.url, format='ascii', delimiter='|')

        return sql_result_tbl

    @class_or_instance
    def query_sql(self, search, properties='all'):
        """

        Perform SQL search in the HyperLEDA database.
        (See http://leda.univ-lyon1.fr/fullsql.html)

        Returns an `~astropy.table.Table` object with the results from the
        search containing the object properties.

        Parameters
        ----------
        search : str

            A string containing a valid SQL WHERE clause.

        properties : str, or comma separated strings. Default: 'all'

            The full list of properties in HyperLEDA is available at
            http://leda.univ-lyon1.fr/leda/meandata.html
            or via
            hyperleda.get_properties().pprint_all()

        Returns
        -------

        Table : An `~astropy.table.Table` object with the object properties from
        HyperLEDA

        Example
        --------
        >>> from astroquery.hyperleda import hyperleda
        >>> hl = hyperleda()
        >>> sql_tbl = hl.query_sql(search = "(mod0<=27 and t>=-3 and t<=0 and
                                              type='S0') or (mod0<=27 and t>=-3
                                              and t<=0 and type='S0-a')",
                                        properties = 'objname,type,logr25,btc,v,
                                            modbest,al2000,de2000,hl_names(pgc),
                                            celposJ(pgc)')
        >>> result_table.pprint()
        """

        if properties == 'all':
            prop_tbl = self.get_properties()
            param_lst = prop_tbl['field'].data.tolist()
            param_str = self._perp_param_lst(param_lst)
        else:
            param_str = properties

        url_http_request = self.URL_HTTP_REQUEST

        ls_SQL_search = search

        request_payload = dict(n='meandata', c='o', of='1,leda,simbad',
                               nra='l', nakd='1',
                               d='{:}'.format(param_str),
                               sql='{:}'.format(ls_SQL_search), ob='',
                               a='csv[|]')
        response = self._request("GET", url_http_request,
                                 params=request_payload)
        sql_result_tbl = Table.read(response.url, format='ascii', delimiter='|')

        return sql_result_tbl

    def _parse_result(self, response, verbose=False):
        # if verbose is False then suppress any VOTable related warnings
        if not verbose:
            commons.suppress_vo_warnings()
        # try to parse the result into an astropy.Table, else
        # return the raw result with an informative error message.
        try:
            # do something with regex to get the result into
            # astropy.Table form. return the Table.

            lind = response.text.find('/fG.cgi')
            rind = lind + response.text[lind:].find('"')
            ls_url_props_src = response.text[lind:rind]
            ls_url_props = self.URL + ls_url_props_src

            # Get the main table
            prop_tbl = Table.read(ls_url_props, format='ascii.html')
            prop_tbl.rename_columns(prop_tbl.colnames,
                                    ['field', 'type', 'units', 'description'])

            # Get the table with the available SQL functions
            sql_func_tbl = Table.read(response.url, format='ascii.html',
                                      htmldict={'table_id': 2})

            sql_func_tbl.add_column(col='--', name='units', index=2)
            sql_func_tbl.rename_columns(sql_func_tbl.colnames,
                                        ['field', 'type', 'units', 'description'])
            prop_tbl = vstack([prop_tbl, sql_func_tbl])
        except ValueError:
            # catch common errors here, but never use bare excepts
            # return raw result/ handle in some way
            pass

        return prop_tbl


# the default tool for users to interact with is an instance of the Class
hyperleda = HyperLEDAClass()

# once your class is done, tests should be written
# See ./tests for examples on this

# Next you should write the docs in astroquery/docs/module_name
# using Sphinx.
