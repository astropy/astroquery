# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
=============
TAP plus
=============

"""
from astroquery.cadc.tap import taputils
from astroquery.cadc.tap.conn.tapconn import TapConn
from astroquery.cadc.tap.xmlparser.tableSaxParser import TableSaxParser
from astroquery.cadc.tap.model.job import Job
from datetime import datetime
from astroquery.cadc.tap.xmlparser.jobSaxParser import JobSaxParser
from astroquery.cadc.tap.xmlparser.jobListSaxParser import JobListSaxParser
from astroquery.cadc.tap.xmlparser import utils
import requests

__all__ = ['Tap', 'TapPlus']

VERSION = "1.0.1"
TAP_CLIENT_ID = "aqtappy-" + VERSION

class Tap(object):
    """TAP class
    Provides TAP capabilities
    """
    def __init__(self, url=None, host=None, server_context=None,
                 tap_context=None, port=80, sslport=443,
                 default_protocol_is_https=False, connhandler=None,
                 verbose=False):
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
        port : int, optional, default '80'
            HTTP port
        sslport : int, optional, default '443'
            HTTPS port
        default_protocol_is_https : bool, optional, default False
            Specifies whether the default protocol to be used is HTTPS
        connhandler connection handler object, optional, default None
            HTTP(s) connection hander (creator). If no handler is provided, a
            new one is created.
        verbose : bool, optional, default 'False'
            flag to display information about the process
        """
        self.__internalInit()
        if url is not None:
            protocol, host, port, server_context, tap_context = self.__parseUrl(url)
            if protocol == "http":
                self.__connHandler = TapConn(False,
                                             host,
                                             server_context,
                                             tap_context,
                                             port,
                                             sslport)
            else:
                # https port -> sslPort
                self.__connHandler = TapConn(True,
                                             host,
                                             server_context,
                                             tap_context,
                                             port,
                                             port)
        else:
            self.__connHandler = TapConn(default_protocol_is_https,
                                         host,
                                         server_context,
                                         tap_context,
                                         port,
                                         sslport)
        # if connectionHandler is set, use it (useful for testing)
        if connhandler is not None:
            self.__connHandler = connhandler
        if verbose:
            print("Created TAP+ (v"+VERSION+") - Connection:\n" + str(self.__connHandler))

    def __internalInit(self):
        self.__connHandler = None

    def get_tables(self, verbose=False, authentication=None):
        """Loads all public tables

        Parameters
        ----------
        verbose : bool, optional, default 'False'
            flag to display information about the process
        authentication : AuthMethod object, mandatory, default 'None'
            authentication object to use

        Returns
        -------
        A list of table objects
        """
        return self.__get_tables(verbose=verbose, authentication=authentication)

    def __get_tables(self, only_names=False, verbose=False, authentication=None):
        """Loads all public tables

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
        if authentication == None:
            raise ValueError(
                'Authentication Required')
        auth = authentication.get_auth_method()
        if auth == 'netrc':
                table='auth-tables' 
        else:
            table='tables'
        flags = ""
        addedItem = False
        if only_names:
            flags = "only_tables=true"
            addedItem = True
        if verbose:
            print("Retrieving tables...")
        if flags != "":
            if auth == 'certificate':
                response = self.__connHandler.execute_get_secure("tables?"+flags, authentication=authentication)
            else:
                response = self.__connHandler.execute_get(table+"?"+flags, 
                                                          authentication=authentication)
        else:
            if auth == 'certificate':
                response = self.__connHandler.execute_get_secure("tables", authentication=authentication)
            else:
                response = self.__connHandler.execute_get(table, 
                                                          authentication=authentication)
        if verbose:
            print('GET tables response ',response.status, response.reason)
        isError = self.__connHandler.check_launch_response_status(response,
                                                                  verbose,
                                                                  200)
        if isError:
            if verbose:   
                print(response.status, response.reason)
            raise requests.exceptions.HTTPError(response.reason)
            return None
        if verbose:
            print("Parsing tables...")
        tsp = TableSaxParser()
        tsp.parseData(response)
        if verbose:
            print("Done.")
        return tsp.get_tables()

    def run_query(self, query, operation, output_file=None, output_format="votable", verbose=False,
                  save_to_file=False, upload_resource=None, upload_table_name=None, 
                  background=False, authentication=None):
        """Launches a synchronous job

        Parameters
        ----------
        query : str, mandatory
            query to be executed
        operation : str, mandatory
                    'sync' or 'async' to run a synchronous or asynchronous job
        output_file : str, optional, default None
        return logger
            file name where the results are saved if dumpToFile is True.
            If this parameter is not provided, the jobid is used instead
        output_format : str, optional, default 'votable'
            results format
        verbose : bool, optional, default 'False'
            flag to display information about the process
        save_to_file : bool, optional, default 'False'
            if True, the results are saved in a file instead of using memory
        upload_resource: str, optional, default None
            resource to be uploaded to UPLOAD_SCHEMA
        upload_table_name: str, required if uploadResource is provided, default None
            resource temporary table name associated to the uploaded resource
        background : bool, optional, default 'False'
                     when the job is executed in asynchronous mode, this flag specifies whether
                     the execution will wait until results are available
        authentication : AuthMethod object, mandatory, default 'None'
            authentication object to use

        Returns
        -------
        A Job object
        """
        if authentication == None:
            raise ValueError(
                'Authentication Required')
        if operation != 'async' and operation != 'sync':
           raise ValueError(
               'Operation must be "sync" or "async", not "%s"' % operation)
        if authentication.get_auth_method() == 'netrc':
            context = 'auth-' + operation
        else:
            context = operation
        if operation == 'sync':
            query = taputils.set_top_in_query(query, 2000)
        if verbose:
            print("Ran query: '"+str(query)+"'")
        if upload_resource is not None:
            if upload_table_name is None:
                raise ValueError("Table name is required when a resource is uploaded")
            response = self.__runQueryMultipart(query,
                                                upload_resource,
                                                upload_table_name,
                                                output_format,
                                                context,
                                                verbose,
                                                authentication)
        else:
            response = self.__runQuery(query,
                                       output_format,
                                       context,
                                       verbose, 
                                       authentication)
        if operation == 'sync':
           # handle redirection
           while response.status == 303 or response.status == 302:
               # redirection
               if verbose:
                   print("Redirection found")
               location = self.__connHandler.find_header(
                   response.getheaders(),
                   "location")
               if location is None:
                   raise requests.exceptions.HTTPError("No location found after redirection was received (303)")
               if verbose:
                   print("Redirect to %s", location)
               subcontext = self.__extract_sync_subcontext(location)
               if authentication.get_auth_method() == 'certificate':
                   response = self.__connHandler.execute_get_secure(subcontext, 
                                                                    otherlocation=location,
                                                                    authentication=authentication)
               else:
                   response = self.__connHandler.execute_get(subcontext, 
                                                             otherlocation=location,
                                                             authentication=authentication)
        if operation == 'sync':
            code = 200
        else:
            code = 303
        isError = self.__connHandler.check_launch_response_status(response,
                                                                  verbose,
                                                                  code)
        if operation == 'sync':
            is_async = False
        else:
            is_async = True
        job = Job(async_job=is_async, query=query, connhandler=self.__connHandler)
        suitableOutputFile = self.__getSuitableOutputFile(False,
                                                          output_file,
                                                          response.getheaders(),
                                                          isError,
                                                          output_format)
        job.set_output_file(suitableOutputFile)
        job.set_response_status(response.status, response.reason)
        job.set_output_format(output_format)
        if isError:
            job.set_failed(True)
            if save_to_file:
                self.__connHandler.save_to_file(suitableOutputFile, response)
            raise requests.exceptions.HTTPError(response.reason)
        else:
            if operation == 'sync':
                if verbose:
                    print("Retrieving sync. results...")
                if save_to_file:
                    self.__connHandler.save_to_file(suitableOutputFile, response)
                else:
                    results = utils.read_http_response(response, output_format)
                    job.set_results(results)
                if verbose:
                    print("Query finished.")
                job.set_phase('COMPLETED')
            else:
                location = self.__connHandler.find_header(
                    response.getheaders(),
                    "location")
                jobid = self.__getJobId(location)
                runresponse = self.__runAsyncQuery(jobid, verbose, authentication=authentication)
                isNextError = self.__connHandler.check_launch_response_status(runresponse,
                                                                              verbose,
                                                                              303)
                if isNextError:
                    job.set_failed(True)
                    if save_to_file:
                        self.__connHandler.save_to_file(suitableOutputFile, runresponse)
                    raise requests.exceptions.HTTPError(runresponse.reason)
                else:
                    if verbose:
                        print("job " + str(jobid) + ", at: " + str(location))
                    job.set_jobid(jobid)
                    job.set_remote_location(location)
                    if not background:
                        if verbose:
                            print("Retrieving async. results...")
                        if save_to_file:
                            job.save_results(verbose, authentication)
                        else:
                            job.get_results(verbose=verbose, authentication=authentication)
                            if verbose:
                                print("Query finished.")
        return job

    def load_async_job(self, jobid=None, verbose=False, authentication=None):
        """Loads an asynchronous job

        Parameters
        ----------
        jobid : str, mandatory if no name is provided, default None
            job identifier
        verbose : bool, optional, default 'False'
            flag to display information about the process
        authentication : AuthMethod object, mandatory, default 'None'
            authentication object to use

        Returns
        -------
        A Job object
        """
        if authentication == None:
            raise ValueError(
                'Authentication Required')
        if jobid is None:
            if verbose:
                print("No job identifier found")
            return None
        if authentication.get_auth_method() == 'netrc':
            subContext = "auth-async/" + str(jobid)
        else:
            subContext = "async/" + str(jobid)
        if authentication.get_auth_method() == 'certificate':
            response = self.__connHandler.execute_get_secure(subContext, 
                                                             authentication=authentication)
        else:
            response = self.__connHandler.execute_get(subContext, 
                                                      authentication=authentication)
        if verbose:
            print(response.status, response.reason)
            print(response.getheaders())
        isError = self.__connHandler.check_launch_response_status(response,
                                                                  verbose,
                                                                  200)
        if isError:
            if verbose:
                print(response.reason)
            raise requests.exceptions.HTTPError(response.reason)
            return None
        # parse job
        jsp = JobSaxParser(async_job=True)
        job = jsp.parseData(response)[0]
        job.set_connhandler(self.__connHandler)
        # load resulst
        job.get_results(verbose, authentication=authentication)
        return job

    def list_async_jobs(self, verbose=False, authentication=None):
        """Returns all the asynchronous jobs

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
        if authentication == None:
            raise ValueError(
                'Authentication Required')
        auth_type = authentication.get_auth_method()
        if auth_type != 'netrc' and auth_type != 'certificate':
            raise ValueError(
                'list_async_jobs() requires authentication')
        if auth_type == 'netrc':
            subContext = "auth-async"
        else:
            subContext = "async"
        if auth_type == 'certificate':
            response = self.__connHandler.execute_get_secure(subContext, authentication=authentication)
        else:
            response = self.__connHandler.execute_get(subContext, authentication=authentication)
        if verbose:
            print(response.status, response.reason)
            print(response.getheaders())
        isError = self.__connHandler.check_launch_response_status(response,
                                                                  verbose,
                                                                  200)
        if isError:
            if verbose:
                print(response.reason)
            raise requests.exceptions.HTTPError(response.reason)
            return None
        # parse jobs
        jsp = JobListSaxParser(async_job=True)
        jobs = jsp.parseData(response)
        if jobs is not None:
            for j in jobs:
                j.set_connhandler(self.__connHandler)
        return jobs

    def save_results(self, job, verbose=False, authentication=None):
        """Saves job results

        Parameters
        ----------
        job : Job, mandatory
            job
        verbose : bool, optional, default 'False'
            flag to display information about the process
        authentication : AuthMethod object, mandatory, default 'None'
            authentication object to use
        """
        if authentication == None:
            raise ValueError(
                'Authentication Required')
        job.save_results(verbose=verbose, authentication=authentication)

    def __getJobId(self, location):
        pos = location.rfind('/')+1
        jobid = location[pos:]
        return jobid

    def __runQueryMultipart(self, query, uploadResource, uploadTableName,
                            outputFormat, context, verbose, authentication=None):
        uploadValue = str(uploadTableName) + ",param:" + str(uploadTableName)
        args = {
            "REQUEST": "doQuery",
            "LANG": "ADQL",
            "FORMAT": str(outputFormat),
            "tapclient": str(TAP_CLIENT_ID),
            "QUERY": str(query),
            "UPLOAD": ""+str(uploadValue)}
        f = open(uploadResource, "r")
        chunk = f.read()
        f.close()
        files = [[uploadTableName, uploadResource, chunk]]
        contentType, body = self.__connHandler.encode_multipart(args, files)
        if authentication.get_auth_method() == 'certificate':
            response = self.__connHandler.execute_post_secure(context, body, contentType, authentication=authentication)
        else:
            response = self.__connHandler.execute_post(context, 
                                                       body, 
                                                       contentType,
                                                       authentication=authentication)
        if verbose:
            print(response.status, response.reason)
            print(response.getheaders())
        return response

    def __runQuery(self, query, outputFormat, context, verbose, authentication=None):
        args = {
            "REQUEST": "doQuery",
            "LANG": "ADQL",
            "FORMAT": str(outputFormat),
            "tapclient": str(TAP_CLIENT_ID),
            "QUERY": str(query)}
        data = self.__connHandler.url_encode(args)
        if authentication.get_auth_method() == 'certificate':
            response = self.__connHandler.execute_post_secure(context, data, authentication=authentication)
        else:
            response = self.__connHandler.execute_post(context, 
                                                       data,
                                                       authentication=authentication)
        if verbose:
            print(response.status, response.reason)
            print(response.getheaders())
        return response

    def __runAsyncQuery(self, jobid, verbose, authentication=None):
        args = {
            "PHASE": "RUN"}
        data = self.__connHandler.url_encode(args)
        if authentication.get_auth_method() == 'netrc':
            jobpath = 'auth-async/' + jobid + '/phase'
        else:
            jobpath = 'async/' + jobid + '/phase'
        if authentication.get_auth_method() == 'certificate':
            response = self.__connHandler.execute_post_secure(jobpath, data, authentication=authentication)
        else:
            response = self.__connHandler.execute_post(jobpath, 
                                                       data, 
                                                       authentication=authentication)
        if verbose:
            print(response.status, response.reason)
            print(response.getheaders())
        return response

    def __getSuitableOutputFile(self, async_job, outputFile, headers, isError,
                                output_format):
        dateTime = datetime.now().strftime("%Y%m%d%H%M%S")
        ext = self.__connHandler.get_suitable_extension(headers)
        fileName = ""
        if outputFile is None:
            if not async_job:
                fileName = "sync_" + str(dateTime) + ext
            else:
                ext = self.__connHandler.get_suitable_extension_by_format(
                    output_format)
                fileName = "async_" + str(dateTime) + ext
        else:
            fileName = outputFile
        if isError:
            fileName += ".error"
        return fileName

    def __extract_sync_subcontext(self, location):
        pos = location.find('sync')
        if pos < 0:
            return location
        return location[pos:]

    def __parseUrl(self, url, verbose=False):
        isHttps = False
        if url.startswith("https://"):
            isHttps = True
            protocol = "https"
        else:
            protocol = "http"

        if verbose:
            print("is https: " + str(isHttps))

        urlInfoPos = url.find("://")

        if urlInfoPos < 0:
            raise ValueError("Invalid URL format")

        urlInfo = url[(urlInfoPos+3):]

        items = urlInfo.split("/")

        if verbose:
            print("'" + urlInfo + "'")
            for i in items:
                print("'" + i + "'")

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
            serverContext = "/"+items[1]
            tapContext = ""
        elif itemsSize == 3:
            serverContext = "/"+items[1]
            tapContext = "/"+items[2]
        else:
            data = []
            for i in range(1, itemsSize-1):
                data.append("/"+items[i])
            serverContext = utils.util_create_string_from_buffer(data)
            tapContext = "/"+items[itemsSize-1]
        if verbose:
            print("protocol: '%s'" % protocol)
            print("host: '%s'" % host)
            print("port: '%d'" % port)
            print("server context: '%s'" % serverContext)
            print("tap context: '%s'" % tapContext)
        return protocol, host, port, serverContext, tapContext

    def __str__(self):
        return ("Created TAP+ (v" + VERSION + ") - Connection: \n" + str(self.__connHandler))


class TapPlus(Tap):
    """TAP plus class
    Provides TAP and TAP+ capabilities
    """
    def __init__(self, url=None, host=None, server_context=None,
                 tap_context=None, port=80, sslport=443,
                 default_protocol_is_https=False, connhandler=None,
                 verbose=False):
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
        port : int, optional, default '80'
            HTTP port
        sslport : int, optional, default '443'
            HTTPS port
        default_protocol_is_https : bool, optional, default False
            Specifies whether the default protocol to be used is HTTPS
        connhandler connection handler object, optional, default None
            HTTP(s) connection hander (creator). If no handler is provided, a
            new one is created.
        verbose : bool, optional, default 'True'
            flag to display information about the process
        """
        super(TapPlus, self).__init__(url, host, server_context, tap_context,
                                      port, sslport, default_protocol_is_https,
                                      connhandler, verbose)

    def get_tables(self, only_names=False, verbose=False, authentication=None):
        """Loads all public tables

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
        return self._Tap__get_tables(only_names=only_names,
                                     verbose=verbose,
                                     authentication=authentication)

    def get_table(self, table, verbose=False, authentication=None):
        """Loads the specified table

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
        if authentication == None:
            raise ValueError(
                'Authentication Required')
        if verbose:
             print("Retrieving table '"+str(table)+"'")
        connHandler = self.__getconnhandler()
        if authentication.get_auth_method() == 'certificate':
            response = connHandler.execute_get_secure("tables", authentication=authentication)
        else:
            if authentication.get_auth_method() == 'netrc':
                authtable='auth-tables'
            else:
                authtable='tables'
            response = connHandler.execute_get(authtable, 
                                               authentication=authentication)
        if verbose:
            print('GET table response ',response.status, response.reason)
        isError = connHandler.check_launch_response_status(response, verbose, 200)
        if isError:
            if verbose:
                print(response.status, response.reason)
            raise requests.exceptions.HTTPError(response.reason)
            return None
        if verbose:
            print("Parsing table '"+str(table)+"'...")
        tsp = TableSaxParser()
        tsp.parseData(response)
        if verbose:
            print("Done.")
        return tsp.get_table(table)

    def __getconnhandler(self):
        return self._Tap__connHandler
