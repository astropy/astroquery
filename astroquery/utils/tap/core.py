# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
=============
TAP plus
=============

@author: Juan Carlos Segovia
@contact: juan.carlos.segovia@sciops.esa.int

European Space Astronomy Centre (ESAC)
European Space Agency (ESA)

Created on 30 jun. 2016


"""
from astroquery.utils.tap import taputils
from astroquery.utils.tap.conn.tapconn import TapConn
from astroquery.utils.tap.xmlparser.tableSaxParser import TableSaxParser
from astroquery.utils.tap.model.job import Job
from astroquery.utils.tap.gui.login import LoginDialog
from astroquery.utils.tap.xmlparser.jobSaxParser import JobSaxParser
from astroquery.utils.tap.xmlparser.jobListSaxParser import JobListSaxParser
from astroquery.utils.tap.xmlparser.groupSaxParser import GroupSaxParser
from astroquery.utils.tap.xmlparser.sharedItemsSaxParser import SharedItemsSaxParser  # noqa
from astroquery.utils.tap.xmlparser import utils
from astroquery.utils.tap.model.filter import Filter
import six
import requests
from astroquery import log
import getpass
import os
from astropy.table.table import Table
import tempfile


__all__ = ['Tap', 'TapPlus']

VERSION = "20200428.1"
TAP_CLIENT_ID = f"aqtappy-{VERSION}"


class Tap:
    """TAP class
    Provides TAP capabilities
    """

    def __init__(self, url=None,
                 host=None,
                 server_context=None,
                 tap_context=None,
                 port=80, sslport=443,
                 default_protocol_is_https=False,
                 connhandler=None,
                 upload_context=None,
                 table_edit_context=None,
                 data_context=None,
                 datalink_context=None,
                 verbose=False):
        """Constructor

        Parameters
        ----------
        url : str, mandatory if no host is specified, default None
            TAP URL
        host : str, optional, default None
            host name
        server_context : str, mandatory, default None
            server context
        tap_context : str, mandatory, default None
            tap context
        upload_context : str, optional, default None
            upload context
        table_edit_context : str, mandatory, default None
            context for all actions to be performed over a existing table
        data_context : str, optional, default None
            data context
        datalink_context : str, optional, default None
            datalink context
        port : int, optional, default '80'
            HTTP port
        sslport : int, optional, default '443'
            HTTPS port
        default_protocol_is_https : bool, optional, default False
            Specifies whether the default protocol to be used is HTTPS
        connhandler : connection handler object, optional, default None
            HTTP(s) connection hander (creator). If no handler is provided, a
            new one is created.
        verbose : bool, optional, default 'False'
            flag to display information about the process
        """
        self.__internalInit()
        if url is not None:
            protocol, host, port, server, tap = self.__parseUrl(url)
            if server_context is None:
                server_context = server
            if tap_context is None:
                tap_context = tap
            if protocol == "http":
                tap = TapConn(ishttps=False,
                              host=host,
                              server_context=server_context,
                              tap_context=tap_context,
                              upload_context=upload_context,
                              table_edit_context=table_edit_context,
                              data_context=data_context,
                              datalink_context=datalink_context,
                              port=port,
                              sslport=sslport)
                self.__connHandler = tap
            else:
                # https port -> sslPort
                tap = TapConn(ishttps=True,
                              host=host,
                              server_context=server_context,
                              tap_context=tap_context,
                              upload_context=upload_context,
                              table_edit_context=table_edit_context,
                              data_context=data_context,
                              datalink_context=datalink_context,
                              port=port,
                              sslport=port)
                self.__connHandler = tap
        else:
            tap = TapConn(ishttps=default_protocol_is_https,
                          host=host,
                          server_context=server_context,
                          tap_context=tap_context,
                          upload_context=upload_context,
                          table_edit_context=table_edit_context,
                          data_context=data_context,
                          datalink_context=datalink_context,
                          port=port,
                          sslport=sslport)
            self.__connHandler = tap
        # if connectionHandler is set, use it (useful for testing)
        if connhandler is not None:
            self.__connHandler = connhandler
        if verbose:
            print(f"Created TAP+ (v{VERSION}) - Connection:\n{self.__connHandler}")

    def __internalInit(self):
        self.__connHandler = None

    def load_tables(self, verbose=False):
        """Loads all public tables

        Parameters
        ----------
        verbose : bool, optional, default 'False'
            flag to display information about the process

        Returns
        -------
        A list of table objects
        """
        return self.__load_tables(verbose=verbose)

    def load_table(self, table, verbose=False):
        """Loads the specified table

        Parameters
        ----------
        table : str, mandatory
            full qualified table name (i.e. schema name + table name)
        verbose : bool, optional, default 'False'
            flag to display information about the process

        Returns
        -------
        A table object
        """
        if table is None:
            raise ValueError("Table name is required")
        print(f"Retrieving table '{table}'")
        response = self.__connHandler.execute_tapget(f"tables?tables={table}",
                                                     verbose=verbose)
        if verbose:
            print(response.status, response.reason)
        self.__connHandler.check_launch_response_status(response,
                                                        verbose,
                                                        200)
        if verbose:
            print(f"Parsing table '{table}'...")
        tsp = TableSaxParser()
        tsp.parseData(response)
        if verbose:
            print("Done.")
        return tsp.get_table()

    def __load_tables(self, only_names=False, include_shared_tables=False,
                      verbose=False):
        """Loads all public tables

        Parameters
        ----------
        only_names : bool, TAP+ only, optional, default 'False'
            True to load table names only
        include_shared_tables : bool, TAP+, optional, default 'False'
            True to include shared tables
        verbose : bool, optional, default 'False'
            flag to display information about the process

        Returns
        -------
        A list of table objects
        """
        # share_info=true&share_accessible=true&only_tables=true
        flags = ""
        addedItem = False
        if only_names:
            flags = "only_tables=true"
            addedItem = True
        if include_shared_tables:
            if addedItem:
                flags += "&"
            flags += "share_accessible=true"
            addedItem = True
        log.info("Retrieving tables...")
        if flags != "":
            response = self.__connHandler.execute_tapget(f"tables?{flags}", verbose=verbose)
        else:
            response = self.__connHandler.execute_tapget("tables",
                                                         verbose=verbose)
        if verbose:
            print(response.status, response.reason)
        isError = self.__connHandler.check_launch_response_status(response,
                                                                  verbose,
                                                                  200)
        if isError:
            log.info(f"{response.status} {response.reason}")
            raise requests.exceptions.HTTPError(response.reason)
            return None
        log.info("Parsing tables...")
        tsp = TableSaxParser()
        tsp.parseData(response)
        log.info("Done.")
        return tsp.get_tables()

    def launch_job(self, query, name=None, output_file=None,
                   output_format="votable", verbose=False,
                   dump_to_file=False, upload_resource=None,
                   upload_table_name=None):
        """Launches a synchronous job

        Parameters
        ----------
        query : str, mandatory
            query to be executed
        output_file : str, optional, default None
            file name where the results are saved if dumpToFile is True.
            If this parameter is not provided, the jobid is used instead
        output_format : str, optional, default 'votable'
            results format
        verbose : bool, optional, default 'False'
            flag to display information about the process
        dump_to_file : bool, optional, default 'False'
            if True, the results are saved in a file instead of using memory
        upload_resource : str, optional, default None
            resource to be uploaded to UPLOAD_SCHEMA
        upload_table_name : str, optional, default None
            resource temporary table name associated to the uploaded resource.
            This argument is required if upload_resource is provided.

        Returns
        -------
        A Job object
        """
        query = taputils.set_top_in_query(query, 2000)
        if verbose:
            print(f"Launched query: '{query}'")
        if upload_resource is not None:
            if upload_table_name is None:
                raise ValueError("Table name is required when a resource " +
                                 "is uploaded")
            response = self.__launchJobMultipart(query,
                                                 upload_resource,
                                                 upload_table_name,
                                                 output_format,
                                                 "sync",
                                                 verbose,
                                                 name)
        else:
            response = self.__launchJob(query,
                                        output_format,
                                        "sync",
                                        verbose,
                                        name)
        # handle redirection
        if response.status == 303:
            # redirection
            if verbose:
                print("Redirection found")
            location = self.__connHandler.find_header(
                response.getheaders(),
                "location")
            if location is None:
                raise requests.exceptions.HTTPError("No location found "
                                                    "after redirection was "
                                                    "received (303)")
            if verbose:
                print(f"Redirect to {location}")
            subcontext = self.__extract_sync_subcontext(location)
            response = self.__connHandler.execute_tapget(subcontext,
                                                         verbose=verbose)
        job = Job(async_job=False, query=query, connhandler=self.__connHandler)
        isError = self.__connHandler.check_launch_response_status(response,
                                                                  verbose,
                                                                  200,
                                                                  False)
        headers = response.getheaders()
        suitableOutputFile = taputils.get_suitable_output_file(self.__connHandler,
                                                               False,
                                                               output_file,
                                                               headers,
                                                               isError,
                                                               output_format)
        job.outputFile = suitableOutputFile
        job.outputFileUser = output_file
        job.parameters['format'] = output_format
        job.set_response_status(response.status, response.reason)
        job.set_phase('PENDING')
        if isError:
            job.failed = True
            job.set_phase('ERROR')
            responseBytes = response.read()
            responseStr = responseBytes.decode('utf-8')
            if dump_to_file:
                if verbose:
                    print(f"Saving error to: {suitableOutputFile}")
                self.__connHandler.dump_to_file(suitableOutputFile,
                                                responseStr)
            raise requests.exceptions.HTTPError(
                taputils.parse_http_response_error(responseStr,
                                                   response.status))
        else:
            if verbose:
                print("Retrieving sync. results...")
            if dump_to_file:
                if verbose:
                    print(f"Saving results to: {suitableOutputFile}")
                self.__connHandler.dump_to_file(suitableOutputFile, response)
            else:
                results = utils.read_http_response(response, output_format)
                job.set_results(results)
            if verbose:
                print("Query finished.")
            job._phase = 'COMPLETED'
        return job

    def launch_job_async(self, query, name=None, output_file=None,
                         output_format="votable", verbose=False,
                         dump_to_file=False, background=False,
                         upload_resource=None, upload_table_name=None,
                         autorun=True):
        """Launches an asynchronous job

        Parameters
        ----------
        query : str, mandatory
            query to be executed
        output_file : str, optional, default None
            file name where the results are saved if dumpToFile is True.
            If this parameter is not provided, the jobid is used instead
        output_format : str, optional, default 'votable'
            results format
        verbose : bool, optional, default 'False'
            flag to display information about the process
        dump_to_file : bool, optional, default 'False'
            if True, the results are saved in a file instead of using memory
        background : bool, optional, default 'False'
            when the job is executed in asynchronous mode, this flag specifies
            whether the execution will wait until results are available
        upload_resource : str, optional, default None
            resource to be uploaded to UPLOAD_SCHEMA
        upload_table_name : str, optional, default None
            resource temporary table name associated to the uploaded resource.
            This argument is required if upload_resource is provided.
        autorun : boolean, optional, default True
            if 'True', sets 'phase' parameter to 'RUN',
            so the framework can start the job.

        Returns
        -------
        A Job object
        """
        if verbose:
            print(f"Launched query: '{query}'")
        if upload_resource is not None:
            if upload_table_name is None:
                raise ValueError(
                    "Table name is required when a resource is uploaded")
            response = self.__launchJobMultipart(query,
                                                 upload_resource,
                                                 upload_table_name,
                                                 output_format,
                                                 "async",
                                                 verbose,
                                                 name,
                                                 autorun)
        else:
            response = self.__launchJob(query,
                                        output_format,
                                        "async",
                                        verbose,
                                        name,
                                        autorun)
        isError = self.__connHandler.check_launch_response_status(response,
                                                                  verbose,
                                                                  303,
                                                                  False)
        job = Job(async_job=True, query=query, connhandler=self.__connHandler)
        headers = response.getheaders()
        suitableOutputFile = taputils.get_suitable_output_file(self.__connHandler,
                                                               True,
                                                               output_file,
                                                               headers,
                                                               isError,
                                                               output_format)
        job.outputFile = suitableOutputFile
        job.outputFileUser = output_file
        job.set_response_status(response.status, response.reason)
        job.parameters['format'] = output_format
        job.set_phase('PENDING')
        if isError:
            job.failed = True
            job.set_phase('ERROR')
            if dump_to_file:
                if verbose:
                    print(f"Saving error to: {suitableOutputFile}")
                self.__connHandler.dump_to_file(suitableOutputFile,
                                                response)
            raise requests.exceptions.HTTPError(response.reason)
        else:
            location = self.__connHandler.find_header(
                response.getheaders(),
                "location")
            jobid = taputils.get_jobid_from_location(location)
            if verbose:
                print(f"job {jobid}, at: {location}")
            job.jobid = jobid
            job.remoteLocation = location
            if autorun is True:
                job.set_phase('EXECUTING')
                if not background:
                    if verbose:
                        print("Retrieving async. results...")
                    # saveResults or getResults will block (not background)
                    if dump_to_file:
                        job.save_results(verbose)
                    else:
                        job.get_results()
                        log.info("Query finished.")
        return job

    def load_async_job(self, jobid=None, name=None, verbose=False,
                       load_results=True):
        """Loads an asynchronous job

        Parameters
        ----------
        jobid : str, mandatory if no name is provided, default None
            job identifier
        name : str, mandatory if no jobid is provided, default None
            job name
        verbose : bool, optional, default 'False'
            flag to display information about the process
        load_results : bool, optional, default 'True'
            load results associated to this job

        Returns
        -------
        A Job object
        """
        if name is not None:
            jobfilter = Filter()
            jobfilter.add_filter('name', name)
            jobs = self.search_async_jobs(jobfilter)
            if jobs is None or len(jobs) < 1:
                log.info(f"No job found for name '{name}'")
                return None
            jobid = jobs[0].jobid
        if jobid is None:
            log.info("No job identifier found")
            return None
        subContext = f"async/{jobid}"
        response = self.__connHandler.execute_tapget(subContext,
                                                     verbose=verbose)
        if verbose:
            print(response.status, response.reason)
            print(response.getheaders())
        isError = self.__connHandler.check_launch_response_status(response,
                                                                  verbose,
                                                                  200)
        if isError:
            log.info(response.reason)
            raise requests.exceptions.HTTPError(response.reason)
            return None
        # parse job
        jsp = JobSaxParser(async_job=True)
        job = jsp.parseData(response)[0]
        job.connHandler = self.__connHandler
        # load resulst
        if load_results:
            job.get_results()
        return job

    def list_async_jobs(self, verbose=False):
        """Returns all the asynchronous jobs

        Parameters
        ----------
        verbose : bool, optional, default 'False'
            flag to display information about the process

        Returns
        -------
        A list of Job objects
        """
        subContext = "async"
        response = self.__connHandler.execute_tapget(subContext,
                                                     verbose=verbose)
        if verbose:
            print(response.status, response.reason)
            print(response.getheaders())
        isError = self.__connHandler.check_launch_response_status(response,
                                                                  verbose,
                                                                  200)
        if isError:
            log.info(response.reason)
            raise requests.exceptions.HTTPError(response.reason)
            return None
        # parse jobs
        jsp = JobListSaxParser(async_job=True)
        jobs = jsp.parseData(response)
        if jobs is not None:
            for j in jobs:
                j.connHandler = self.__connHandler
        return jobs

    def __appendData(self, args):
        data = self.__connHandler.url_encode(args)
        result = ""
        firtsTime = True
        for k in data:
            if firtsTime:
                firtsTime = False
                result = f"{k}={data[k]}"
            else:
                result = f"{result}&{k}={data[k]}"
        return result

    def save_results(self, job, verbose=False):
        """Saves job results

        Parameters
        ----------
        job : Job, mandatory
            job
        verbose : bool, optional, default 'False'
            flag to display information about the process
        """
        job.save_results(verbose=verbose)

    def __launchJobMultipart(self, query, uploadResource, uploadTableName,
                             outputFormat, context, verbose, name=None,
                             autorun=True):
        uploadValue = f"{uploadTableName},param:{uploadTableName}"
        args = {
            "REQUEST": "doQuery",
            "LANG": "ADQL",
            "FORMAT": str(outputFormat),
            "tapclient": str(TAP_CLIENT_ID),
            "QUERY": str(query),
            "UPLOAD": ""+str(uploadValue)}
        if autorun is True:
            args['PHASE'] = 'RUN'
        if name is not None:
            args['jobname'] = name
        if isinstance(uploadResource, Table):
            fh = tempfile.NamedTemporaryFile(delete=False)
            uploadResource.write(fh, format='votable')
            fh.close()
            f = open(fh.name, "r")
            chunk = f.read()
            f.close()
            os.unlink(fh.name)
            name = 'pytable'
            args['format'] = 'votable'
        else:
            with open(uploadResource, "r") as fh:
                chunk = fh.read()
            name = os.path.basename(uploadResource)
        files = [[uploadTableName, name, chunk]]
        contentType, body = self.__connHandler.encode_multipart(args, files)
        response = self.__connHandler.execute_tappost(context,
                                                      body,
                                                      contentType,
                                                      verbose)
        if verbose:
            print(response.status, response.reason)
            print(response.getheaders())
        return response

    def __launchJob(self, query, outputFormat, context, verbose, name=None,
                    autorun=True):
        args = {
            "REQUEST": "doQuery",
            "LANG": "ADQL",
            "FORMAT": str(outputFormat),
            "tapclient": str(TAP_CLIENT_ID),
            "QUERY": str(query)}
        if autorun is True:
            args['PHASE'] = 'RUN'
        if name is not None:
            args['jobname'] = name
        data = self.__connHandler.url_encode(args)
        response = self.__connHandler.execute_tappost(subcontext=context,
                                                      data=data,
                                                      verbose=verbose)
        if verbose:
            print(response.status, response.reason)
            print(response.getheaders())
        return response

    def __extract_sync_subcontext(self, location):
        pos = location.find('sync')
        if pos < 0:
            return location
        return location[pos:]

    def __findCookieInHeader(self, headers, verbose=False):
        cookies = self.__connHandler.find_header(headers, 'Set-Cookie')
        if verbose:
            print(cookies)
        if cookies is None:
            return None
        else:
            items = cookies.split(';')
            for i in items:
                if i.startswith("JSESSIONID="):
                    return i
        return None

    def __parseUrl(self, url, verbose=False):
        isHttps = False
        if url.startswith("https://"):
            isHttps = True
            protocol = "https"
        else:
            protocol = "http"

        if verbose:
            print(f"is https: {isHttps}")

        urlInfoPos = url.find("://")

        if urlInfoPos < 0:
            raise ValueError("Invalid URL format")

        urlInfo = url[(urlInfoPos+3):]

        items = urlInfo.split("/")

        if verbose:
            print(f"'{urlInfo}'")
            for i in items:
                print(f"'{i}'")

        itemsSize = len(items)
        hostPort = items[0]
        portPos = hostPort.find(":")
        if portPos > 0:
            # port found
            host = hostPort[0:portPos]
            port = int(hostPort[portPos+1:])
        else:
            # no port found
            host = hostPort
            # no port specified: use defaults
            if isHttps:
                port = 443
            else:
                port = 80

        if itemsSize == 1:
            serverContext = ""
            tapContext = ""
        elif itemsSize == 2:
            serverContext = f"/{items[1]}"
            tapContext = ""
        elif itemsSize == 3:
            serverContext = f"/{items[1]}"
            tapContext = f"/{items[2]}"
        else:
            data = []
            for i in range(1, itemsSize-1):
                data.append(f"/{items[i]}")
            serverContext = utils.util_create_string_from_buffer(data)
            tapContext = f"/{items[itemsSize-1]}"
        if verbose:
            print(f"protocol: '{protocol}'")
            print(f"host: '{host}'")
            print(f"port: '{port}'")
            print(f"server context: '{serverContext}'")
            print(f"tap context: '{tapContext}'")
        return protocol, host, port, serverContext, tapContext

    def __str__(self):
        return (f"Created TAP+ (v{VERSION}) - Connection:\n{self.__connHandler}")


class TapPlus(Tap):
    """TAP plus class
    Provides TAP and TAP+ capabilities
    """
    def __init__(self, url=None,
                 host=None,
                 server_context=None,
                 tap_context=None,
                 port=80, sslport=443,
                 default_protocol_is_https=False,
                 connhandler=None,
                 upload_context=None,
                 table_edit_context=None,
                 data_context=None,
                 datalink_context=None,
                 verbose=True):
        """Constructor

        Parameters
        ----------
        url : str, mandatory if no host is specified, default None
            TAP URL
        host : str, optional, default None
            host name
        server_context : str, optional, default None
            server context
        tap_context : str, optional, default None
            tap context
        upload_context : str, optional, default None
            upload context
        table_edit_context : str, optional, default None
            context for all actions to be performed over a existing table
        data_context : str, optional, default None
            data context
        datalink_context : str, optional, default None
            datalink context
        port : int, optional, default '80'
            HTTP port
        sslport : int, optional, default '443'
            HTTPS port
        default_protocol_is_https : bool, optional, default False
            Specifies whether the default protocol to be used is HTTPS
        connhandler : connection handler object, optional, default None
            HTTP(s) connection hander (creator). If no handler is provided, a
            new one is created.
        verbose : bool, optional, default 'True'
            flag to display information about the process
        """

        super(TapPlus, self).__init__(url, host,
                                      server_context=server_context,
                                      tap_context=tap_context,
                                      upload_context=upload_context,
                                      table_edit_context=table_edit_context,
                                      data_context=data_context,
                                      datalink_context=datalink_context,
                                      port=port, sslport=sslport,
                                      default_protocol_is_https=default_protocol_is_https,  # noqa
                                      connhandler=connhandler,
                                      verbose=verbose)
        self.__internalInit()

    def __internalInit(self):
        self.__user = None
        self.__pwd = None
        self.__isLoggedIn = False

    def load_tables(self, only_names=False, include_shared_tables=False,
                    verbose=False):
        """Loads all public tables

        Parameters
        ----------
        only_names : bool, TAP+ only, optional, default 'False'
            True to load table names only
        include_shared_tables : bool, TAP+, optional, default 'False'
            True to include shared tables
        verbose : bool, optional, default 'False'
            flag to display information about the process

        Returns
        -------
        A list of table objects
        """
        return self._Tap__load_tables(only_names=only_names,
                                      include_shared_tables=include_shared_tables,  # noqa
                                      verbose=verbose)

    def load_data(self, params_dict=None, output_file=None, verbose=False):
        """Loads the specified data

        Parameters
        ----------
        params_dict : dictionary, mandatory
            list of request parameters
        output_file : string, optional, default None
            file where the results are saved.
            If it is not provided, the http response contents are returned.
        verbose : bool, optional, default 'False'
            flag to display information about the process

        Returns
        -------
        A table object if output_file is None.
        None if output_file is not None.
        """
        if verbose:
            print("Retrieving data.")
        connHandler = self.__getconnhandler()
        if not isinstance(params_dict, dict):
            raise ValueError("Parameters dictionary expected")
        data = connHandler.url_encode(params_dict)
        if verbose:
            print(f"Data request: {data}")
        response = connHandler.execute_datapost(data=data, verbose=verbose)
        if verbose:
            print(response.status, response.reason)
        connHandler.check_launch_response_status(response,
                                                 verbose,
                                                 200)
        if verbose:
            print("Reading...")
        if output_file is not None:
            file = open(output_file, "wb")
            file.write(response.read())
            file.close()
            if verbose:
                print("Done.")
            return None
        else:
            if 'format' in params_dict:
                output_format = params_dict['format'].lower()
            else:
                if 'FORMAT' in params_dict:
                    output_format = params_dict['FORMAT'].lower()
                else:
                    output_format = "votable"
            results = utils.read_http_response(response, output_format)
            if verbose:
                print("Done.")
            return results

    def load_groups(self, verbose=False):
        """Loads groups

        Parameters
        ----------
        verbose : bool, optional, default 'False'
            flag to display information about the process

        Returns
        -------
        A set of groups of a user
        """
        context = "share?action=GetGroups"
        connHandler = self.__getconnhandler()
        response = connHandler.execute_tapget(context, verbose=verbose)
        if verbose:
            print(response.status, response.reason)
            print(response.getheaders())
        connHandler.check_launch_response_status(response,
                                                 verbose,
                                                 200)
        if verbose:
            print("Parsing groups...")
        gsp = GroupSaxParser()
        gsp.parseData(response)
        print(f"Done. {len(gsp.get_groups())} groups found")
        if verbose:
            for g in gsp.get_groups():
                print(g.title)
        return gsp.get_groups()

    def load_group(self, group_name=None, verbose=False):
        """Load group with title being group_name

        Parameters
        ----------
        group_name : str, required
            group to be loaded
        verbose : bool, optional, default 'False'
            flag to display information about the process

        Returns
        -------
        A group with title being group_name
        """
        if group_name is None:
            raise ValueError("'group_name' must be specified")
        groups = self.load_groups(verbose)
        group = None
        for g in groups:
            if str(g.title) == str(group_name):
                group = g
                break
        return group

    def load_shared_items(self, verbose=False):
        """Loads shared items

        Parameters
        ----------
        verbose : bool, optional, default 'False'
            flag to display information about the process

        Returns
        -------
        A set of shared items
        """
        context = "share?action=GetSharedItems"
        connHandler = self.__getconnhandler()
        response = connHandler.execute_tapget(context, verbose=verbose)
        if verbose:
            print(response.status, response.reason)
            print(response.getheaders())
        connHandler.check_launch_response_status(response,
                                                 verbose,
                                                 200)
        if verbose:
            print("Parsing shared items...")
        ssp = SharedItemsSaxParser()
        ssp.parseData(response)
        print(f"Done. {len(ssp.get_shared_items())} shared items found")
        if verbose:
            for g in ssp.get_shared_items():
                print(g.title)
        return ssp.get_shared_items()

    def share_table(self, group_name=None,
                    table_name=None,
                    description=None,
                    verbose=False):
        """Shares a table with a group

        Parameters
        ----------
        group_name : str, required
            group in which table will be shared
        table_name : str, required
            table to be shared
        description : str, required
            description of the sharing
        verbose : bool, optional, default 'False'
            flag to display information about the process
        """
        if group_name is None or table_name is None:
            raise ValueError("Both 'group_name' and 'table_name' " +
                             "must be specified")
        if description is None:
            description = ""
        group = self.load_group(group_name, verbose)
        if group is None:
            raise ValueError(f"Group '{group_name}' not found.")
        table = self.load_table(table=table_name, verbose=verbose)
        if table is None:
            raise ValueError(f"Table '{table_name}' not found.")
        data = (f"action=CreateOrUpdateItem&resource_type=0&title="
                f"{table_name}"
                f"&description="
                f"{description}"
                f"&items_list="
                f"{group.id}|Group|Read")
        connHandler = self.__getconnhandler()
        response = connHandler.execute_share(data, verbose=verbose)
        if verbose:
            print(response.status, response.reason)
            print(response.getheaders())
        connHandler.check_launch_response_status(response,
                                                 verbose,
                                                 200)
        msg = f"Shared table '{table_name}' to group '{group_name}'."
        print(msg)

    def share_table_stop(self, group_name=None, table_name=None,
                         verbose=False):
        """Stop sharing a table

        Parameters
        ----------
        group_name : str, required
            group where the table is shared to
        table_name : str, required
            table to be stopped from being shared
        verbose : bool, optional, default 'False'
            flag to display information about the process
        """
        if group_name is None or table_name is None:
            raise ValueError("Both 'group_name' and 'table_name' " +
                             "must be specified")
        group = self.load_group(group_name, verbose)
        if group is None:
            raise ValueError(f"Group '{group_name}' not found.")
        shared_items = self.load_shared_items(verbose)
        shared_item = None
        for s in shared_items:
            if str(s.title) == str(table_name):
                # check group
                groups = s.shared_to_items
                for g in groups:
                    if group.id == g.id:
                        shared_item = s
                        break
                if shared_item is not None:
                    break
        if shared_item is None:
            raise ValueError(f"Table '{table_name}', shared to group '{group_name}', not found.")
        data = (f"action=RemoveItem&resource_type=0&resource_id="
                f"{shared_item.id}"
                f"&resource_type=0")
        connHandler = self.__getconnhandler()
        response = connHandler.execute_share(data, verbose=verbose)
        if verbose:
            print(response.status, response.reason)
            print(response.getheaders())
        connHandler.check_launch_response_status(response,
                                                 verbose,
                                                 200)

        msg = f"Stop sharing table '{table_name}' to group '{group_name}'."
        print(msg)

    def share_group_create(self, group_name=None, description=None,
                           verbose=False):
        """Creates a group

        Parameters
        ----------
        group_name : str, required
            group to be created
        description : str, required
            description of the group
        verbose : bool, optional, default 'False'
            flag to display information about the process
        """
        if group_name is None:
            raise ValueError("'group_name' must be specified")
        if description is None:
            description = ""
        group = self.load_group(group_name, verbose)
        if group is not None:
            raise ValueError(f"Group {group_name} already exists")
        data = (f"action=CreateOrUpdateGroup&resource_type=0&title="
                f"{group_name}"
                f"&description="
                f"{description}")
        connHandler = self.__getconnhandler()
        response = connHandler.execute_share(data, verbose=verbose)
        if verbose:
            print(response.status, response.reason)
            print(response.getheaders())
        connHandler.check_launch_response_status(response,
                                                 verbose,
                                                 200)
        msg = f"Created group '{group_name}'."
        print(msg)

    def share_group_delete(self,
                           group_name=None,
                           verbose=False):
        """Deletes a group

        Parameters
        ----------
        group_name : str, required
            group to be created
        verbose : bool, optional, default 'False'
            flag to display information about the process
        """
        if group_name is None:
            raise ValueError("'group_name' must be specified")
        group = self.load_group(group_name, verbose)
        if group is None:
            raise ValueError(f"Group '{group_name}' doesn't exist")
        data = (f"action=RemoveGroup&resource_type=0&group_id={group.id}")
        connHandler = self.__getconnhandler()
        response = connHandler.execute_share(data, verbose=verbose)
        if verbose:
            print(response.status, response.reason)
            print(response.getheaders())
        connHandler.check_launch_response_status(response,
                                                 verbose,
                                                 200)
        msg = f"Deleted group '{group_name}'."
        print(msg)

    def share_group_add_user(self,
                             group_name=None,
                             user_id=None,
                             verbose=False):
        """Adds user to a group

        Parameters
        ----------
        group_name : str, required
            group which user_id will be added in
        user_id : str, required
            user id to be added
        verbose : bool, optional, default 'False'
            flag to display information about the process
        """
        if group_name is None or user_id is None:
            raise ValueError("Both 'group_name' and 'user_id' " +
                             "must be specified")
        group = self.load_group(group_name, verbose)
        if group is None:
            raise ValueError(f"Group '{group_name}' doesn't exist")
        user_found_in_group = False
        for u in group.users:
            if str(u.id) == user_id:
                user_found_in_group = True
                break
        if user_found_in_group is True:
            raise ValueError(f"User id '{user_id}' found in group '{group_name}'")
        if self.is_valid_user(user_id, verbose) is False:
            raise ValueError(f"User id '{user_id}' not found.")
        users = ""
        for u in group.users:
            users = f"{users}{u.id},"
        users = users + user_id
        data = ("action=CreateOrUpdateGroup&group_id="
                f"{group.id}&title="
                f"{group.title}&description="
                f"{group.description}&users_list="
                f"{users}")
        connHandler = self.__getconnhandler()
        response = connHandler.execute_share(data, verbose=verbose)
        if verbose:
            print(response.status, response.reason)
            print(response.getheaders())
        connHandler.check_launch_response_status(response,
                                                 verbose,
                                                 200)
        msg = f"Added user '{user_id}' from group '{group_name}'."
        print(msg)

    def share_group_delete_user(self,
                                group_name=None,
                                user_id=None,
                                verbose=False):
        """Deletes user from a group

        Parameters
        ----------
        group_name : str, required
            group which user_id will be removed from
        user_id : str, required
            user id to be deleted
        verbose : bool, optional, default 'False'
            flag to display information about the process
        """
        if group_name is None or user_id is None:
            raise ValueError("Both 'group_name' and 'user_id' " +
                             "must be specified")
        group = self.load_group(group_name, verbose)
        if group is None:
            raise ValueError(f"Group '{group_name}' doesn't exist")
        user_found_in_group = False
        for u in group.users:
            if str(u.id) == user_id:
                user_found_in_group = True
                break
        if user_found_in_group is False:
            raise ValueError(f"User id '{user_id}' not found in group '{group_name}'")
        users = ""
        for u in group.users:
            if str(u.id) == str(user_id):
                continue
            users = f"{users}{u.id},"
        if str(users) != "":
            users = users[:-1]
        data = (f"action=CreateOrUpdateGroup&group_id="
                f"{group.id}&title="
                f"{group.title}&description="
                f"{group.description}&users_list="
                f"{users}")
        connHandler = self.__getconnhandler()
        response = connHandler.execute_share(data, verbose=verbose)
        if verbose:
            print(response.status, response.reason)
            print(response.getheaders())
        connHandler.check_launch_response_status(response,
                                                 verbose,
                                                 200)
        msg = f"Deleted user '{user_id}' from group '{group_name}'."
        print(msg)

    def is_valid_user(self, user_id=None, verbose=False):
        """Determines if the specified user exists in the system
        TAP+ only

        Parameters
        ----------
        user_id : str, mandatory
            user id to be checked
        verbose : bool, optional, default 'False'
            flag to display information about the process

        Returns
        -------
        Boolean indicating if the specified user exists
        """
        if user_id is None:
            raise ValueError("'user_id' must be specified")
        context = f"users?USER={user_id}"
        connHandler = self.__getconnhandler()
        response = connHandler.execute_tapget(context, verbose=verbose)
        if verbose:
            print(response.status, response.reason)
            print(response.getheaders())
        connHandler.check_launch_response_status(response,
                                                 verbose,
                                                 200)
        responseBytes = response.read()
        user = responseBytes.decode('utf-8')
        if verbose:
            print(f"USER response = {user}")
        return user.startswith(f"{user_id}:") and user.count("\\n") == 0

    def get_datalinks(self, ids, verbose=False):
        """Gets datalinks associated to the provided identifiers

        Parameters
        ----------
        ids : str list, mandatory
            list of identifiers
        verbose : bool, optional, default 'False'
            flag to display information about the process

        Returns
        -------
        A table object
        """
        if verbose:
            print("Retrieving datalink.")
        if ids is None:
            raise ValueError("Missing mandatory argument 'ids'")
        if isinstance(ids, six.string_types):
            ids_arg = f"ID={ids}"
        else:
            if isinstance(ids, int):
                ids_arg = f"ID={ids}"
            else:
                ids_arg = f"ID={','.join(str(item) for item in ids)}"
        if verbose:
            print(f"Datalink request: {ids_arg}")
        connHandler = self.__getconnhandler()
        response = connHandler.execute_datalinkpost(subcontext="links",
                                                    data=ids_arg,
                                                    verbose=verbose)
        if verbose:
            print(response.status, response.reason)
        connHandler.check_launch_response_status(response,
                                                 verbose,
                                                 200)
        if verbose:
            print("Done.")
        results = utils.read_http_response(response, "votable")

        return results

    def search_async_jobs(self, jobfilter=None, verbose=False):
        """Searches for jobs applying the specified filter

        Parameters
        ----------
        jobfilter : JobFilter, optional, default None
            job filter
        verbose : bool, optional, default 'False'
            flag to display information about the process

        Returns
        -------
        A list of Job objects
        """
        # jobs/list?[&session=][&limit=][&offset=][&order=][&metadata_only=true|false]
        subContext = "jobs/async"
        if jobfilter is not None:
            data = jobfilter.createUrlRequest()
            if data is not None:
                subContext = f"{subContext}?{self.__appendData(data)}"
        connHandler = self.__getconnhandler()
        response = connHandler.execute_tapget(subContext, verbose=verbose)
        if verbose:
            print(response.status, response.reason)
            print(response.getheaders())
        connHandler.check_launch_response_status(response,
                                                 verbose,
                                                 200)
        # parse jobs
        jsp = JobSaxParser(async_job=True)
        jobs = jsp.parseData(response)
        if jobs is not None:
            for j in jobs:
                j.connHandler = connHandler
        return jobs

    def remove_jobs(self, jobs_list, verbose=False):
        """Removes the specified jobs

        Parameters
        ----------
        jobs_list : str, mandatory
            jobs identifiers to be removed
        verbose : bool, optional, default 'False'
            flag to display information about the process

        """
        if jobs_list is None:
            return
        jobsIds = None
        if isinstance(jobs_list, str):
            jobsIds = jobs_list
        elif isinstance(jobs_list, list):
            jobsIds = ','.join(jobs_list)
        else:
            raise Exception("Invalid object type")
        if verbose:
            print(f"Jobs to be removed: {jobsIds}")
        data = f"JOB_IDS={jobsIds}"
        subContext = "deletejobs"
        connHandler = self.__getconnhandler()
        response = connHandler.execute_tappost(subContext,
                                               data,
                                               verbose=verbose)
        if verbose:
            print(response.status, response.reason)
            print(response.getheaders())
        connHandler.check_launch_response_status(response,
                                                 verbose,
                                                 200)
        msg = f"Removed jobs: '{jobs_list}'."
        print(msg)

    def login(self, user=None, password=None, credentials_file=None,
              verbose=False):
        """Performs a login.
        User and password arguments can be used or a file that contains
        user name and password
        (2 lines: one for user name and the following one for the password).
        If no arguments are provided, a prompt asking for user name and
        password will appear.

        Parameters
        ----------
        user : str, default None
            login name
        password : str, default None
            user password
        credentials_file : str, default None
            file containing user and password in two lines
        verbose : bool, optional, default 'False'
            flag to display information about the process
        """
        if credentials_file is not None:
            # read file: get user & password
            with open(credentials_file, "r") as ins:
                user = ins.readline().strip()
                password = ins.readline().strip()
        if user is None:
            user = six.moves.input("User: ")
            if user is None:
                print("Invalid user name")
                return
        if password is None:
            password = getpass.getpass("Password: ")
            if password is None:
                print("Invalid password")
                return
        self.__user = str(user)
        self.__pwd = str(password)
        self.__dologin(verbose)

    def login_gui(self, verbose=False):
        """Performs a login using a GUI dialog

        Parameters
        ----------
        verbose : bool, optional, default 'False'
            flag to display information about the process
        """
        connHandler = self.__getconnhandler()
        url = connHandler.get_host_url()
        loginDialog = LoginDialog(url)
        loginDialog.show_login()
        if loginDialog.is_accepted():
            self.__user = loginDialog.get_user()
            self.__pwd = loginDialog.get_password()
            # execute login
            self.__dologin(verbose)
        else:
            self.__isLoggedIn = False

    def __dologin(self, verbose=False):
        self.__isLoggedIn = False
        response = self.__execLogin(self.__user, self.__pwd, verbose)
        # check response
        connHandler = self.__getconnhandler()
        connHandler.check_launch_response_status(response,
                                                 verbose,
                                                 200)
        # extract cookie
        cookie = self._Tap__findCookieInHeader(response.getheaders())
        if cookie is not None:
            self.__isLoggedIn = True
            connHandler.set_cookie(cookie)
        print("OK: user logged in.")

    def logout(self, verbose=False):
        """Performs a logout

        Parameters
        ----------
        verbose : bool, optional, default 'False'
            flag to display information about the process
        """
        subContext = "logout"
        args = {}
        connHandler = self.__getconnhandler()
        data = connHandler.url_encode(args)
        response = connHandler.execute_secure(subContext, data)
        if verbose:
            print(response.status, response.reason)
            print(response.getheaders())
        self.__isLoggedIn = False

    def __execLogin(self, usr, pwd, verbose=False):
        subContext = "login"
        args = {
            "username": usr,
            "password": pwd}
        connHandler = self.__getconnhandler()
        data = connHandler.url_encode(args)
        response = connHandler.execute_secure(subContext, data, verbose)
        if verbose:
            print(response.status, response.reason)
            print(response.getheaders())
        return response

    def upload_table(self, upload_resource=None, table_name=None,
                     table_description=None,
                     format=None, verbose=False):
        """Uploads a table to the user private space

        Parameters
        ----------
        upload_resource : object, mandatory
            table to be uploaded: pyTable, file or URL.
        table_name : str, required if uploadResource is provided, default None
            resource temporary table name associated to the uploaded resource
        table_description : str, optional, default None
            table description
        format : str, optional, default 'VOTable'
            resource format
        verbose : bool, optional, default 'False'
            flag to display information about the process
        """

        if upload_resource is None:
            raise ValueError("Missing mandatory argument 'upload_resource'")
        if table_name is None:
            raise ValueError("Missing mandatory argument 'table_name'")
        if table_description is None:
            description = ""
        else:
            description = table_description
        if format is None:
            format = "votable"

        response = self.__uploadTableMultipart(resource=upload_resource,
                                               table_name=table_name,
                                               table_description=description,
                                               resource_format=format,
                                               verbose=verbose)
        if response.status == 303:
            location = self.__getconnhandler().find_header(
                response.getheaders(),
                "location")
            jobid = taputils.get_jobid_from_location(location)
            job = Job(async_job=True,
                      query=None,
                      connhandler=self.__getconnhandler())
            job.jobid = jobid
            job.name = 'Table upload'
            job.set_phase('EXECUTING')
            print(f"Job '{jobid}' created to upload table '{table_name}'.")
            return job
        else:
            print(f"Uploaded table '{table_name}'.")
            return None

    def __uploadTableMultipart(self, resource, table_name=None,
                               table_description=None,
                               resource_format="VOTable",
                               verbose=False):
        connHandler = self.__getconnhandler()
        if isinstance(resource, Table):
            args = {
                "TASKID": str(-1),
                "TABLE_NAME": str(table_name),
                "TABLE_DESC": str(table_description),
                "FORMAT": 'votable'}
            print("Sending pytable.")
            fh = tempfile.NamedTemporaryFile(delete=False)
            resource.write(fh, format='votable')
            fh.close()
            f = open(fh.name, "r")
            chunk = f.read()
            f.close()
            os.unlink(fh.name)
            files = [['FILE', 'pytable', chunk]]
            contentType, body = connHandler.encode_multipart(args, files)
        else:
            if not (str(resource).startswith("http")):  # upload from file
                args = {
                    "TASKID": str(-1),
                    "TABLE_NAME": str(table_name),
                    "TABLE_DESC": str(table_description),
                    "FORMAT": str(resource_format)}
                print(f"Sending file: {resource}")
                with open(resource, "r") as f:
                    chunk = f.read()
                files = [['FILE', os.path.basename(resource), chunk]]
                contentType, body = connHandler.encode_multipart(args, files)
            else:    # upload from URL
                args = {
                    "TASKID": str(-1),
                    "TABLE_NAME": str(table_name),
                    "TABLE_DESC": str(table_description),
                    "FORMAT": str(resource_format),
                    "URL": str(resource)}
                files = [['FILE', "", ""]]
                contentType, body = connHandler.encode_multipart(args, files)
        response = connHandler.execute_upload(body, contentType)
        if verbose:
            print(response.status, response.reason)
            print(response.getheaders())
        if response.status != 303 and response.status != 302:
            connHandler.check_launch_response_status(response,
                                                     verbose,
                                                     200)
        return response

    def upload_table_from_job(self, job=None, table_name=None,
                              table_description=None, verbose=False):
        """Creates a table to the user private space from a job

        Parameters
        ----------
        job: job, mandatory
            job used to create a table. Could be a string with the jobid or
            a job itself
        table_name : str, default 't'+jobid
            resource temporary table name associated to the uploaded resource
        table_description : str, optional, default None
            table description
        verbose : bool, optional, default 'False'
            flag to display information about the process
        """
        if job is None:
            raise ValueError("Missing mandatory argument 'job'")
        if isinstance(job, Job):
            j = job
            description = j.parameters['query']
        else:
            j = self.load_async_job(jobid=job, load_results=False)
            if j is None:
                raise ValueError(f"Job {job} not found")
                return
            description = j.parameters['query']
        if table_name is None:
            table_name = f"t{j.jobid}"
        if table_description is None:
            table_description = description
        if verbose:
            print(f"JOB = {j.jobid}")
        self.__uploadTableMultipartFromJob(resource=j.jobid,
                                           table_name=table_name,
                                           table_description=table_description,
                                           verbose=verbose)
        msg = f"Created table '{table_name}' from job: '{j.jobid}'."
        print(msg)

    def __uploadTableMultipartFromJob(self, resource, table_name=None,
                                      table_description=None, verbose=False):
        args = {
            "TASKID": str(-1),
            "JOBID": str(resource),
            "TABLE_NAME": str(table_name),
            "TABLE_DESC": str(table_description),
            "FORMAT": str(format)}
        files = [['FILE', "", ""]]
        connHandler = self.__getconnhandler()
        contentType, body = connHandler.encode_multipart(args, files)
        response = connHandler.execute_upload(body, contentType)
        if verbose:
            print(response.status, response.reason)
            print(response.getheaders())
        connHandler.check_launch_response_status(response,
                                                 verbose,
                                                 200)
        return response

    def delete_user_table(self, table_name=None, force_removal=False,
                          verbose=False):
        """Removes a user table

        Parameters
        ----------
        table_name : str, required
            table to be removed
        force_removal : bool, optional, default 'False'
            flag to indicate if removal should be forced
        verbose : bool, optional, default 'False'
            flag to display information about the process
        """
        if table_name is None:
            raise ValueError("Table name cannot be null")
        if force_removal is True:
            args = {
                    "TABLE_NAME": str(table_name),
                    "DELETE": "TRUE",
                    "FORCE_REMOVAL": "TRUE"}
        else:
            args = {
                    "TABLE_NAME": str(table_name),
                    "DELETE": "TRUE",
                    "FORCE_REMOVAL": "FALSE"}
        connHandler = self.__getconnhandler()
        data = connHandler.url_encode(args)
        response = connHandler.execute_upload(data, verbose=verbose)
        if verbose:
            print(response.status, response.reason)
            print(response.getheaders())
        connHandler.check_launch_response_status(response,
                                                 verbose,
                                                 200)
        msg = f"Table '{table_name}' deleted."
        print(msg)

    def update_user_table(self, table_name=None, list_of_changes=[],
                          verbose=False):
        """Updates a user table

        Parameters
        ----------
        table_name : str, required
            table to be updated
        list_of_changes : list, required
            list of lists, each one of them containing sets of
            [column_name, field_name, value].
            column_name is the name of the column to be updated
            field_name is the name of the tap field to be modified
            field name can be 'utype', 'ucd', 'flags' or 'indexed'
            value is the new value this field of this column will take
        verbose : bool, optional, default 'False'
            flag to display information about the process
        """
        if table_name is None:
            raise ValueError("Table name cannot be null")
        if len(list_of_changes) == 0:
            raise ValueError("List of changes cannot be empty")
        for change in list_of_changes:
            if change is None:
                raise ValueError("None of the changes can be null")
            if len(change) != 3:  # [column_name, field_name, value]
                raise ValueError("All of the changes must have three " +
                                 "elements: [column_name, field_name, value]")
            index = 0
            for value in change:
                if value is None:
                    raise ValueError("None of the values for the changes " +
                                     "can be null")
                if (index == 1 and value != 'utype' and value != 'ucd' and
                        value != 'flags' and value != 'indexed'):
                    raise ValueError("Position 2 of all changes must be " +
                                     "'utype', 'ucd', 'flags' or 'indexed'")
                index = index + 1

        table = self.load_table(table=table_name, verbose=verbose)
        if table is None:
            raise ValueError("Table name not found")
        columns = table.columns
        if len(columns) == 0:
            raise ValueError("Table has no columns")

        for change in list_of_changes:
            index = 0
            for value in change:
                if index == 0:
                    found = False
                    for c in columns:
                        if c.name == value:
                            found = True
                            break
                    if found is False:
                        raise ValueError(f"Column name introduced "
                                         f"{value}"
                                         f" was not found in the table")
                index = index + 1

        new_ra_column = TapPlus.__changesContainFlag(list_of_changes, "Ra")
        new_dec_column = TapPlus.__changesContainFlag(list_of_changes, "Dec")

        # check whether both (Ra/Dec) are present
        # or both are None
        if ((new_ra_column is not None and new_dec_column is None) or
                (new_ra_column is None and new_dec_column is not None)):
            raise ValueError("Both Ra and Dec must be specified when " +
                             "updating one of them.")

        args = TapPlus.get_table_update_arguments(table_name, columns,
                                                  list_of_changes)

        connHandler = self.__getconnhandler()
        data = connHandler.url_encode(args)
        response = connHandler.execute_table_edit(data, verbose=verbose)
        if verbose:
            print(response.status, response.reason)
            print(response.getheaders())
        connHandler.check_launch_response_status(response,
                                                 verbose,
                                                 200)
        msg = f"Table '{table_name}' updated."
        print(msg)

    @staticmethod
    def get_table_update_arguments(table_name, columns, list_of_changes):
        num_cols = len(columns)
        args = {
                "ACTION": "edit",
                "NUMTABLES": str(1),
                "TABLE0_NUMCOLS": str(num_cols),
                "TABLE0": str(table_name),
                }
        index = 0
        for column in columns:
            found_in_changes = False
            for change in list_of_changes:
                if (str(change[0]) == str(column.name)):
                    found_in_changes = True
                    break

            # set current values
            column_name, flags, indexed, ucd, utype = \
                TapPlus.get_current_column_values_for_update(column)

            # Update values if required
            if found_in_changes:
                flags, indexed, ucd, utype = \
                    TapPlus.get_new_column_values_for_update(list_of_changes,
                                                             column_name,
                                                             flags,
                                                             indexed,
                                                             ucd, utype)

            # Prepare http request parameters for a column
            args[f"TABLE0_COL{index}"] = str(column_name)
            args[f"TABLE0_COL{index}_UCD"] = str(ucd)
            args[f"TABLE0_COL{index}_UTYPE"] = str(utype)
            args[f"TABLE0_COL{index}_INDEXED"] = str(indexed)
            args[f"TABLE0_COL{index}_FLAGS"] = str(flags)
            index = index + 1
        return args

    @staticmethod
    def get_current_column_values_for_update(column):
        column_name = column.name
        flags = column.flags
        if str(flags) == '1':
            flags = 'Ra'
        elif str(flags) == '2':
            flags = 'Dec'
        elif str(flags) == '4':
            flags = 'Flux'
        elif str(flags) == '8':
            flags = 'Mag'
        elif str(flags) == '16':
            flags = 'PK'
        elif str(flags) == '33':
            flags = 'Ra'
        elif str(flags) == '34':
            flags = 'Dec'
        elif str(flags) == '38':
            flags = 'Flux'
        elif str(flags) == '40':
            flags = 'Mag'
        elif str(flags) == '48':
            flags = 'PK'
        else:
            flags = None
        indexed = (str(column.flag) == 'indexed' or
                   str(flags) == 'Ra' or
                   str(flags) == 'Dec' or
                   str(flags) == 'PK')
        ucd = str(column.ucd)
        utype = str(column.utype)
        return column_name, flags, indexed, ucd, utype

    @staticmethod
    def get_new_column_values_for_update(list_of_changes, column_name,
                                         c_flags, c_indexed, c_ucd, c_utype):
        found_new_flags = False
        found_new_indexed = False
        found_new_ucd = False
        found_new_utype = False
        n_flags = None
        n_indexed = None
        n_utype = None
        n_ucd = None
        for change in list_of_changes:
            if str(change[0]) == column_name:
                if str(change[1]) == 'flags':
                    n_flags = str(change[2])
                    found_new_flags = True
                if str(change[1]) == 'indexed':
                    n_indexed = str(change[2])
                    found_new_indexed = True
                if str(change[1]) == 'ucd':
                    n_ucd = str(change[2])
                    found_new_ucd = True
                if str(change[1]) == 'utype':
                    n_utype = str(change[2])
                    found_new_utype = True

        if found_new_ucd:
            ucd = n_ucd
        else:
            ucd = c_ucd

        if found_new_utype:
            utype = n_utype
        else:
            utype = c_utype

        if found_new_indexed:
            indexed = n_indexed
        else:
            indexed = c_indexed

        # index could be updated
        if found_new_flags:
            if n_flags is None or n_flags == '':
                if found_new_indexed:
                    indexed = str(n_indexed)
                else:
                    indexed = str(False)
            else:
                # Index required for PK, Ra, Dec
                if c_flags == 'Ra' or c_flags == 'Dec' or c_flags == 'PK':
                    indexed = str(True)
            flags = n_flags
        else:
            flags = c_flags

        return flags, indexed, ucd, utype

    def set_ra_dec_columns(self, table_name=None,
                           ra_column_name=None, dec_column_name=None,
                           verbose=False):
        """Set columns of a table as ra and dec respectively a user table

        Parameters
        ----------
        table_name : str, required
            table to be set
        ra_column_name : str, required
            ra column to be set
        dec_column_name : str, required
            dec column to be set
        verbose : bool, optional, default 'False'
            flag to display information about the process
        """

        if table_name is None:
            raise ValueError("Table name cannot be null")
        if ra_column_name is None:
            raise ValueError("Ra column name cannot be null")
        if dec_column_name is None:
            raise ValueError("Dec column name cannot be null")

        args = {
                "ACTION": "radec",
                "TABLE_NAME": str(table_name),
                "RA": str(ra_column_name),
                "DEC": str(dec_column_name),
                }
        connHandler = self.__getconnhandler()
        data = connHandler.url_encode(args)
        response = connHandler.execute_table_edit(data, verbose=verbose)
        isError = connHandler.check_launch_response_status(response,
                                                           verbose,
                                                           200)
        if isError:
            log.info(response.reason)
            raise requests.exceptions.HTTPError(response.reason)
        msg = f"Table '{table_name}' updated (ra/dec)."
        return msg

    def login(self, user=None, password=None, credentials_file=None,
              verbose=False):
        """Performs a login.
        User and password arguments can be used or a file that contains
        user name and password
        (2 lines: one for user name and the following one for the password).
        If no arguments are provided, a prompt asking for user name and
        password will appear.

        Parameters
        ----------
        user : str, default None
            login name
        password : str, default None
            user password
        credentials_file : str, default None
            file containing user and password in two lines
        verbose : bool, optional, default 'False'
            flag to display information about the process
        """
        if credentials_file is not None:
            # read file: get user & password
            with open(credentials_file, "r") as ins:
                user = ins.readline().strip()
                password = ins.readline().strip()
        if user is None:
            user = six.moves.input("User: ")
            if user is None:
                log.info("Invalid user name")
                return
        if password is None:
            password = getpass.getpass("Password: ")
            if password is None:
                log.info("Invalid password")
                return
        self.__user = str(user)
        self.__pwd = str(password)
        self.__dologin(verbose)

    def login_gui(self, verbose=False):
        """Performs a login using a GUI dialog

        Parameters
        ----------
        verbose : bool, optional, default 'False'
            flag to display information about the process
        """
        connHandler = self.__getconnhandler()
        url = connHandler.get_host_url()
        loginDialog = LoginDialog(url)
        loginDialog.show_login()
        if loginDialog.is_accepted():
            self.__user = loginDialog.get_user()
            self.__pwd = loginDialog.get_password()
            # execute login
            self.__dologin(verbose)
        else:
            self.__isLoggedIn = False

    def __dologin(self, verbose=False):
        self.__isLoggedIn = False
        response = self.__execLogin(self.__user, self.__pwd, verbose)
        # check response
        connHandler = self.__getconnhandler()
        isError = connHandler.check_launch_response_status(response,
                                                           verbose,
                                                           200)
        if isError:
            log.info(f"Login error: {response.reason}")
            raise requests.exceptions.HTTPError(f"Login error: {response.reason}")
        else:
            # extract cookie
            cookie = self._Tap__findCookieInHeader(response.getheaders())
            if cookie is not None:
                self.__isLoggedIn = True
                connHandler.set_cookie(cookie)
        print("OK")

    def logout(self, verbose=False):
        """Performs a logout

        Parameters
        ----------
        verbose : bool, optional, default 'False'
            flag to display information about the process
        """
        subContext = "logout"
        args = {}
        connHandler = self.__getconnhandler()
        data = connHandler.url_encode(args)
        response = connHandler.execute_secure(subContext, data)
        if verbose:
            print(response.status, response.reason)
            print(response.getheaders())
        self.__isLoggedIn = False

    @staticmethod
    def __columnsContainFlag(columns=None, flag=None, verbose=False):
        c = None
        if columns is not None and len(columns) > 0:
            for column in columns:
                f = column.flags
                if str(f) == '1' or str(f) == '33':
                    f = 'Ra'
                elif str(f) == '2' or str(f) == '34':
                    f = 'Dec'
                elif str(f) == '4' or str(f) == '38':
                    f = 'Flux'
                elif str(f) == '8' or str(f) == '40':
                    f = 'Mag'
                elif str(f) == '16' or str(f) == '48':
                    f = 'PK'
                else:
                    f = None
                if str(flag) == str(f):
                    c = column.name
                    break
        return c

    @staticmethod
    def __changesContainFlag(changes=None, flag=None, verbose=False):
        c = None
        if changes is not None and len(changes) > 0:
            for change in changes:
                if str(change[1]) == "flags":
                    value = str(change[2])
                    if str(flag) == str(value):
                        c = str(change[0])
                        break
        return c

    def __getconnhandler(self):
        return self._Tap__connHandler
