# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
VO Queries
"""

from astroquery.query import BaseQuery
from astroquery.utils.tap.core import Tap

from . import conf

__all__ = ['Registry', 'RegistryClass']


class RegistryClass(BaseQuery):
    """
    Registry query class.
    """

    def __init__(self):

        super(RegistryClass, self).__init__()
        self._REGISTRY_TAP_SYNC_URL = conf.registry_tap_url + "/sync"

    def _get_tap_object(self, query, url, verbose=False):
        # pylint: disable=unused-argument
        # (query is only used when mocking a remote test.)
        return Tap(url, verbose=verbose)

    def _sync_tap_query(self, query, url=None, output_file=None,
                        output_format="votable", dump_to_file=False, verbose=False):
        """
        Convenience wrapper for performing a synchronous TAP query.

        Parameters
        ----------
        query : str, required
            ADQL query to be executed
        url : str, optional, default points to the STScI Registry TAP service
            Base URL for the desired TAP service.
        output_file : str, optional, default is to use the TAP job ID
            File name where the results are saved if dumpToFile is True.
        output_format : str, optional, default 'votable'
            results format
        dump_to_file : bool, optional, default is False
            If True, the results are saved in a file instead of using memory.
        verbose : bool, optional, default is False
            When True, the ADQL query computed from the keyword arguments will be printed.
        """
        if url is None:
            url = self._REGISTRY_TAP_SYNC_URL

        registry_tap = self._get_tap_object(query, url, verbose=verbose)
        job = registry_tap.launch_job(query, output_file=output_file, output_format=output_format,
                                      dump_to_file=dump_to_file, verbose=verbose)
        aptable = job.get_results()

        # Store addtional metadata from the response on the Astropy Table.
        # This can help in debugging and may have other uses. Other metadata could be added here.
        aptable.meta['astroquery.vo_service_discovery'] = {"url": url,
                                                           "query": query}

        return aptable

    def query(self, service_type="", keyword="", waveband="", source="", publisher="", order_by="",
              url=None, output_format="votable", output_file=None, dump_to_file=False, verbose=False):
        """
        Query the Virtual Observatory registry to find services which can then be searched.

        Parameters
        ----------
        service_type : str, required
            Valid VO service types are: "conesearch", "simpleimageaccess", "simplespectralaccess", "tableaccess"
            They may be shortened to "cone", "image", "spectra", "spectrum", or "table" or "tap", respectively.
        keyword : str, optional, default is None
            The query will return any services which contain this keyword in their ivoid, title, or description.
        waveband : str, optional, default is None
            Comma-delimited list of wavebands.  Results will contain all services that offer
            at least one of these wavebands. Legal values are listed below.
        source : str, optional, default is None
            Any substring in ivoid (a unique identifier of the service)
        publisher : str, optional, default is None
            The name of any publishing organization (e.g., "stsci", "heasarc")
        order_by : str, optional, default is None
            What column to order the results by.  The returned columns are:
                "waveband", "short_name", "ivoid", "res_description", "access_url",
                "reference_url", "publisher", service_type"
        url : str, optional, default points to the STScI Registry TAP service
            Base URL for the desired TAP service.
        output_file : str, optional, default is to use the TAP job ID
            File name where the results are saved if dumpToFile is True.
        output_format : str, optional, default 'votable'
            results format
        dump_to_file : bool, optional, default is False
            If True, the results are saved in a file instead of using memory.
        verbose : bool, optional, default is False
            When True, the ADQL query computed from the keyword arguments will be printed.
        """

        query = self._build_adql(service_type, keyword, waveband, source, publisher, order_by)
        if verbose:
            print('Registry:  sending query ADQL = {}\n'.format(query))

        aptable = self._sync_tap_query(query, url=url, output_file=output_file,
                                       output_format=output_format,
                                       dump_to_file=dump_to_file, verbose=verbose)

        return aptable

    def query_counts(self, field, minimum=1, url=None, output_file=None, output_format="votable",
                     dump_to_file=False, verbose=False):
        """
        Query the Virtual Observatory registry to find what values exist, and counts for each value,
        for the 'service_type', 'waveband', or 'publisher' fields in the main query.

        Parameters
        ----------
        field : str, required
            One of 'service_type', 'waveband' or 'publisher'
        minimum : int, optional, default is 1
        url : str, optional, default points to the STScI Registry TAP service
            Base URL for the desired TAP service.
        output_file : str, optional, default is to use the TAP job ID
            File name where the results are saved if dumpToFile is True.
        output_format : str, optional, default 'votable'
            results format
        dump_to_file : bool, optional, default is False
            If True, the results are saved in a file instead of using memory.
        verbose : bool, optional, default is False
            When True, the ADQL query computed from the keyword arguments will be printed.
        """

        query = self._build_counts_adql(field, minimum)

        if verbose:
            print('Registry:  sending query_counts ADQL = {}\n'.format(query))

        aptable = self._sync_tap_query(query, url=url, output_file=output_file,
                                       output_format=output_format,
                                       dump_to_file=dump_to_file, verbose=verbose)

        return aptable

    def _build_adql(self, service_type="", keyword="", waveband="", source="", publisher="", order_by=""):
        """
        Build the ADQL text for the Registry TAP query constrained by service_type, keyword, waveband,
        source or publisher.
        """

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

        if service_type not in ["simpleimageaccess", "simplespectralaccess", "conesearch", "tableaccess"]:
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

            query = ('select * from (' + query_select + query_from + query_where_filter + query_group_by +
                     ') as count_table' + query_where_count_min + query_order_by)

            return query


Registry = RegistryClass()
