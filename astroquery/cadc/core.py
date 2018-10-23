# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
=============
Cadc TAP plus
=============

"""

from astroquery.cadc.tap import TapPlus

__all__ = ['Cadc', 'CadcTAP']

class CadcTAP(object):
    """
    Proxy class to default TapPlus object (pointing to CADA Archive)
    """
    def __init__(self, url=None, tap_plus_handler=None, verbose=False):
        """
        Initialize CadcTAP object

        Parameters
        ----------
        url : str, optional, default 'None;
            a url to use instead of the default 
        tap_plus_handler : TAP/TAP+ object, optional, default 'None'
            connection to use instead of the default one created
 
        Returns
        -------
        CadcTAP object
        """
        if tap_plus_handler is None:
            if url is None:
                self.__cadctap = TapPlus(url="http://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/tap",
                                         verbose=verbose)
            else:
                self.__cadctap = TapPlus(url=url, verbose=verbose)
        else:
            self.__cadctap = tap_plus_handler

    def get_tables(self, only_names=False, verbose=False,  authentication=None):
        """Loads all public tables
        TAP & TAP+

        Parameters
        ----------
        only_names : bool, TAP+ only, optional, default 'False'
            True to load table names only
        verbose : bool, optional, default 'False'
            flag to display information about the process
        authentication : AuthMethod object, mandatory, default 'None'
            authentication object to use

        Returns
        -------
        A list of table objects
        """
        return self.__cadctap.get_tables(only_names,
                                         verbose,
                                         authentication=authentication)

    def get_table(self, table, verbose=False, authentication=None):
        """Loads the specified table
        TAP+ only

        Parameters
        ----------
        table : str, mandatory
            full qualified table name (i.e. schema name + table name)
        verbose : bool, optional, default 'False'
            flag to display information about the process
        authentication : AuthMethod object, mandatory, default 'None'
            authentication object to use

        Returns
        -------
        A table object
        """
        return self.__cadctap.get_table(table, verbose, authentication=authentication)

    def run_query(self, query, operation, output_file=None, output_format="votable", 
                  verbose=False, save_to_file=False, background=False,
                  upload_resource=None, upload_table_name=None, authentication=None):
        """Launches a job
        TAP & TAP+

        Parameters
        ----------
        query : str, mandatory
            query to be executed
        operation : str, mandatory, 
            'sync' or 'async' to run a synchronous or asynchronous job
        output_file : str, optional, default None
            file name where the results are saved if dumpToFile is True.
            If this parameter is not provided, the jobid is used instead
        output_format : str, optional, default 'votable'
            results format, 'csv', 'tsv' and 'votable'
        verbose : bool, optional, default 'False'
            flag to display information about the process
        save_to_file : bool, optional, default 'False'
            if True, the results are saved in a file instead of using memory
        background : bool, optional, default 'False'
            when the job is executed in asynchronous mode, this flag specifies whether
            the execution will wait until results are available
        upload_resource: str, optional, default None
            resource to be uploaded to UPLOAD_SCHEMA
        upload_table_name: str, required if uploadResource is provided, default None
            resource temporary table name associated to the uploaded resource
        authentication : AuthMethod object, mandatory, default 'None'
            authentication object to use 

        Returns
        -------
        A Job object
        """
        return self.__cadctap.run_query(query,
                                        operation, 
                                        output_file=output_file,
                                        output_format=output_format,
                                        verbose=verbose,
                                        save_to_file=save_to_file,
                                        background=background,
                                        upload_resource=upload_resource,
                                        upload_table_name=upload_table_name,
                                        authentication=authentication)

    def load_async_job(self, jobid, verbose=False, authentication=None):
        """Loads an asynchronous job
        TAP & TAP+

        Parameters
        ----------
        jobid : str, mandatory
            job identifier
        verbose : bool, optional, default 'False'
            flag to display information about the process
        authentication : AuthMethod object, mandatory, default 'None'
            authentication object to use

        Returns
        -------
        A Job object
        """
        return self.__cadctap.load_async_job(jobid, verbose, authentication=authentication)

    def list_async_jobs(self, verbose=False, authentication=None):
        """Returns all the asynchronous jobs
        TAP & TAP+

        Parameters
        ----------
        verbose : bool, optional, default 'False'
            flag to display information about the process
        authentication : AuthMethod object, mandatory, default 'None'
            authentication object to use

        Returns
        -------
        A list of Job objects
        """
        return self.__cadctap.list_async_jobs(verbose, authentication=authentication)

    def save_results(self, job, verbose=False, authentication=None):
        """Saves job results
        TAP & TAP+

        Parameters
        ----------
        job : Job, mandatory
            job
        verbose : bool, optional, default 'False'
            flag to display information about the process
        authentication : AuthMethod object, mandatory, default 'None'
            authentication object to use
        """
        return self.__cadctap.save_results(job, verbose, authentication=authentication)

Cadc = CadcTAP()
