# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
VO Queries
"""

from astroquery.query import BaseQuery

from . import conf
from . import utils

__all__ = ['Registry', 'RegistryClass']


class VoBase(BaseQuery):
    """
    Base class for all VO queries.
    """

    def try_query(self, url, retries=2, timeout=60, params=None, data=None, files=None, verbose=False):
        """
        A wrapper to _request() function allowing for retries

        Parameters
        ----------
        url : str
        retries : int
            The maximum number of times the request will be tried.
        params : None or dict
        data : None or dict
        files : None or dict
            See `requests.request`
        timeout : int
        verbose : bool
        """

        retry = retries
        assert params is not None or data is not None, "Give either get_params or data"

        while retry:
            try:
                if data is not None:
                    response = self._request('POST', url, data=data, cache=False, timeout=timeout, files=files)
                else:
                    response = self._request('GET', url, params=params, cache=False, timeout=timeout)
                retry = retries-1
            except (Timeout, ReadTimeout, ReadTimeoutError, ConnectionError) as e:
                retry = retry-1
                if retry > 0:
                    if (verbose):
                        print("WARNING: Got a timeout; trying again.")
            except:
                raise
            else:
                return response


class RegistryClass(VoBase):
    """
    Registry query class.
    """

    def __init__(self):

        super(RegistryClass, self).__init__()
        self._TIMEOUT = 60   # seconds
        self._RETRIES = 2    # total number of times to try
        self._REGISTRY_TAP_SYNC_URL = conf.registry_tap_url + "/sync"

    def query(self, service_type="", keyword="", waveband="", source="", publisher="", order_by="", logic_string=' and ', verbose=False, return_http_response=False):
        """
        Query the Virtual Observatory registry to find services which can then be searched.

        Parameters
        ----------
        service_type : string, required
            Valid VO service types are: "conesearch", "simpleimageaccess", "simplespectralaccess", "tableaccess"
            They may be shortened to "cone", "image", "spectra", "spectrum", or "table" or "tap", respectively.
        keyword : string, optional
            Default is None.
            The query will return any services which contain this keyword in their ivoid, title, or description.
        waveband : string, optional
            Comma-delimited list of wavebands.  Results will contain all services that offer at least one of these wavebands.
            Legal values are listed below.
        source : string, optional
            Any substring in ivoid (a unique identifier of the service)
        publisher : string, optional
            The name of any publishing organization (e.g., "stsci", "heasarc")
        order_by : string, optional
            What column to order it by.  The returned columns are:
                "waveband","short_name","ivoid","res_description","access_url","reference_url","publisher", service_type"
        verbose : bool, optional
            Default is False.
            When True, the ADQL query computed from the keyword arguments will be printed.
        """

        adql = self._build_adql(service_type, keyword, waveband, source, publisher, order_by, verbose)
        if adql is None:
            raise ValueError('Unable to compute query based on input arguments.')

        if verbose:
            print('Registry:  sending query ADQL = {}\n'.format(adql))

        url = self._REGISTRY_TAP_SYNC_URL

        tap_params = {
            "request": "doQuery",
            "lang": "ADQL",
            "query": adql
        }

        response = self.try_query(url, data=tap_params, timeout=self._TIMEOUT, retries=self._RETRIES)

        if verbose:
            print('Queried: {}\n'.format(response.url))

        aptable = utils.astropy_table_from_votable_response(response)
        aptable.meta['astroquery.vo']['data'] = tap_params
        if return_http_response: return aptable, response
        return aptable

    def _build_adql(self, service_type="", keyword="", waveband="", source="", publisher="", order_by="", verbose=False):

        # Default values
        logic_string = " and "

        if "image" in service_type.lower():
            service_type = "simpleimageaccess"
        elif "spectr" in service_type.lower():
            service_type = "simplespectralaccess"
        elif "cone" in service_type.lower():
            service_type = "conesearch"
        elif 'tap' in service_type or 'table' in service_type:
            service_type = "tableaccess"
        else:
            raise ValueError("""
            service_type must be one of conesearch, simpleimageaccess, simplespectralaccess, tableaccess, or
            their alternate strings: cone, image, spectra, spectrum, table or tap.
            """)

        query_retcols = """
          select res.waveband,res.short_name,cap.ivoid,res.res_description,
          intf.access_url,res.reference_url,res_role.role_name as publisher,cap.cap_type as service_type
          from rr.capability as cap
            natural join rr.resource as res
            natural join rr.interface as intf
            natural join rr.res_role as res_role
            """

        query_where = " where "

        wheres = []
        if service_type != "":
            wheres.append("cap.cap_type like '%{}%'".format(service_type))

        # Currently not supporting SIAv2 in SIA library.
        if service_type == 'simpleimageaccess':
            wheres.append("standard_id != 'ivo://ivoa.net/std/sia#query-2.0'")
        if source != "":
            wheres.append("cap.ivoid like '%{}%'".format(source))
        if waveband != "":
            if ',' in waveband:
                allwavebands = []
                for w in waveband.split(','):
                    allwavebands.append("res.waveband like '%{}%' ".format(w).strip())
                wheres.append("(" + " or ".join(allwavebands) + ")")
            else:
                wheres.append("res.waveband like '%{}%'".format(waveband))

        wheres.append("res_role.base_role = 'publisher'")
        if publisher != "":
            wheres.append("res_role.role_name like '%{}%'".format(publisher))

        if keyword != "":
            keyword_where = """
             (res.res_description like '%{}%' or
            res.res_title like '%{}%' or
            cap.ivoid like '%{}%')
            """.format(keyword, keyword, keyword)
            wheres.append(keyword_where)

        query_where = query_where+logic_string.join(wheres)

        if order_by != "":
            query_order = "order by {}".format(order_by)
        else:
            query_order = ""

        query = query_retcols+query_where+query_order

        return query

    def query_counts(self, field, minimum=1, return_http_response=False, **kwargs):

        adql = self._build_counts_adql(field, minimum)

        if kwargs.get('verbose'):
            print('Registry:  sending query ADQL = {}\n'.format(adql))

        url = self._REGISTRY_TAP_SYNC_URL

        tap_params = {
            "request": "doQuery",
            "lang": "ADQL",
            "query": adql
        }

        response = self._request('POST', url, data=tap_params, cache=False)
        if kwargs.get('verbose'):
            print('Queried: {}\n'.format(response.url))

        aptable = utils.astropy_table_from_votable_response(response)
        aptable.meta['astroquery.vo']['data'] = tap_params
        if return_http_response: return aptable, response
        return aptable

    def _build_counts_adql(self, field, minimum=1):

        field_table = None
        field_alias = field
        query_where_filter = ''
        if field.lower() == 'waveband':
            field_table = 'rr.resource'
        elif field.lower() == 'publisher':
            field_table = 'rr.res_role'
            field = 'role_name'
            query_where_filter = ' where base_role = \'publisher\' '
        elif field.lower() == 'service_type':
            field_table = 'rr.capability'
            field = 'cap_type'

        if field_table is None:
            return None
        else:
            query_select = 'select ' + field + ' as ' + field_alias + ', count(' + field + ') as count_' + field_alias
            query_from = ' from ' + field_table
            query_where_count_min = ' where count_' + field_alias + ' >= ' + str(minimum)
            query_group_by = ' group by ' + field
            query_order_by = ' order by count_' + field_alias + ' desc'

            query = 'select * from (' + query_select + query_from + query_where_filter + query_group_by + ') as count_table' + query_where_count_min + query_order_by

            return query


Registry = RegistryClass()


def display_results(results):
    # Display results in a readable way including the
    # short_name, ivoid, res_description and reference_url.

    for row in results:
        md = '{} ({})'.format(row["short_name"], row["ivoid"])
        print(md)
        print(row['res_description'])
        print('(More info: {} )'.format(row["reference_url"]))
