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
from datetime import datetime
from astroquery.utils.tap.gui.login import LoginDialog
from astroquery.utils.tap.xmlparser.jobSaxParser import JobSaxParser
from astroquery.utils.tap.xmlparser.jobListSaxParser import JobListSaxParser
from astroquery.utils.tap.xmlparser import utils
from astroquery.utils.tap.model.filter import Filter
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
        print("Retrieving tables...")
        if flags != "":
            response = self.__connHandler.execute_get("tables?"+flags)
        else:
            response = self.__connHandler.execute_get("tables")
        if verbose:
            print(response.status, response.reason)
        isError = self.__connHandler.check_launch_response_status(response,
                                                                  verbose,
                                                                  200)
        if isError:
            print(response.status, response.reason)
            raise requests.exceptions.HTTPError(response.reason)
            return None
        print("Parsing tables...")
        tsp = TableSaxParser()
        tsp.parseData(response)
        print("Done.")
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
        upload_resource: str, optional, default None
            resource to be uploaded to UPLOAD_SCHEMA
        upload_table_name: str, required if uploadResource is provided, default None
            resource temporary table name associated to the uploaded resource

        Returns
        -------
        A Job object
        """
        query = taputils.set_top_in_query(query, 2000)
        if verbose:
            print("Launched query: '"+str(query)+"'")
        if upload_resource is not None:
            if upload_table_name is None:
                raise ValueError("Table name is required when a resource is uploaded")
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
                raise requests.exceptions.HTTPError("No location found after redirection was received (303)")
            if verbose:
                print("Redirect to %s", location)
            subcontext = self.__extract_sync_subcontext(location)
            response = self.__connHandler.execute_get(subcontext)
        job = Job(async_job=False, query=query, connhandler=self.__connHandler)
        isError = self.__connHandler.check_launch_response_status(response,
                                                                  verbose,
                                                                  200)
        suitableOutputFile = self.__getSuitableOutputFile(False,
                                                          output_file,
                                                          response.getheaders(),
                                                          isError,
                                                          output_format)
        job.outputFile = suitableOutputFile
        job.parameters['format'] = output_format
        job.set_response_status(response.status, response.reason)
        if isError:
            job.failed = True
            if dump_to_file:
                self.__connHandler.dump_to_file(suitableOutputFile, response)
            raise requests.exceptions.HTTPError(response.reason)
        else:
            if verbose:
                print("Retrieving sync. results...")
            if dump_to_file:
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
                         upload_resource=None, upload_table_name=None):
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
        upload_resource: str, optional, default None
            resource to be uploaded to UPLOAD_SCHEMA
        upload_table_name: str, required if uploadResource is provided, default None
            resource temporary table name associated to the uploaded resource

        Returns
        -------
        A Job object
        """
        if verbose:
            print("Launched query: '"+str(query)+"'")
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
                                                 name)
        else:
            response = self.__launchJob(query,
                                        output_format,
                                        "async",
                                        verbose,
                                        name)
        isError = self.__connHandler.check_launch_response_status(response,
                                                                  verbose,
                                                                  303)
        job = Job(async_job=True, query=query, connhandler=self.__connHandler)
        suitableOutputFile = self.__getSuitableOutputFile(True,
                                                          output_file,
                                                          response.getheaders(),
                                                          isError,
                                                          output_format)
        job.outputFile = suitableOutputFile
        job.set_response_status(response.status, response.reason)
        job.parameters['format'] = output_format
        if isError:
            job.set_failed(True)
            if dump_to_file:
                self.__connHandler.dump_to_file(suitableOutputFile, response)
            raise requests.exceptions.HTTPError(response.reason)
        else:
            location = self.__connHandler.find_header(
                response.getheaders(),
                "location")
            jobid = self.__getJobId(location)
            if verbose:
                print("job " + str(jobid) + ", at: " + str(location))
            job.jobid = jobid
            job.remoteLocation = location
            if not background:
                if verbose:
                    print("Retrieving async. results...")
                # saveResults or getResults will block (not background)
                if dump_to_file:
                    job.save_results(verbose)
                else:
                    job.get_results()
                    print("Query finished.")
        return job

    def load_async_job(self, jobid=None, name=None, verbose=False):
        """Loads an asynchronous job

        Parameters
        ----------
        jobid : str, mandatory if no name is provided, default None
            job identifier
        name : str, mandatory if no jobid is provided, default None
            job name
        verbose : bool, optional, default 'False'
            flag to display information about the process

        Returns
        -------
        A Job object
        """
        if name is not None:
            jobfilter = Filter()
            jobfilter.add_filter('name', name)
            jobs = self.search_async_jobs(jobfilter)
            if jobs is None or len(jobs) < 1:
                print("No job found for name '"+str(name)+"'")
                return None
            jobid = jobs[0].get_jobid()
        if jobid is None:
            print("No job identifier found")
            return None
        subContext = "async/" + str(jobid)
        response = self.__connHandler.execute_get(subContext)
        if verbose:
            print(response.status, response.reason)
            print(response.getheaders())
        isError = self.__connHandler.check_launch_response_status(response,
                                                                  verbose,
                                                                  200)
        if isError:
            print(response.reason)
            raise requests.exceptions.HTTPError(response.reason)
            return None
        # parse job
        jsp = JobSaxParser(async_job=True)
        job = jsp.parseData(response)[0]
        job.set_connhandler(self.__connHandler)
        # load resulst
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
        response = self.__connHandler.execute_get(subContext)
        if verbose:
            print(response.status, response.reason)
            print(response.getheaders())
        isError = self.__connHandler.check_launch_response_status(response,
                                                                  verbose,
                                                                  200)
        if isError:
            print(response.reason)
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
                result = k + '=' + data[k]
            else:
                result = result + "&" + k + '=' + data[k]
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
        job.save_results()

    def __getJobId(self, location):
        pos = location.rfind('/')+1
        jobid = location[pos:]
        return jobid

    def __launchJobMultipart(self, query, uploadResource, uploadTableName,
                             outputFormat, context, verbose, name=None):
        uploadValue = str(uploadTableName) + ",param:" + str(uploadTableName)
        args = {
            "REQUEST": "doQuery",
            "LANG": "ADQL",
            "FORMAT": str(outputFormat),
            "tapclient": str(TAP_CLIENT_ID),
            "PHASE": "RUN",
            "QUERY": str(query),
            "UPLOAD": ""+str(uploadValue)}
        if name is not None:
            args['jobname'] = name
        f = open(uploadResource, "r")
        chunk = f.read()
        f.close()
        files = [[uploadTableName, uploadResource, chunk]]
        contentType, body = self.__connHandler.encode_multipart(args, files)
        response = self.__connHandler.execute_post(context, body, contentType)
        if verbose:
            print(response.status, response.reason)
            print(response.getheaders())
        return response

    def __launchJob(self, query, outputFormat, context, verbose, name=None):
        args = {
            "REQUEST": "doQuery",
            "LANG": "ADQL",
            "FORMAT": str(outputFormat),
            "tapclient": str(TAP_CLIENT_ID),
            "PHASE": "RUN",
            "QUERY": str(query)}
        if name is not None:
            args['jobname'] = name
        data = self.__connHandler.url_encode(args)
        response = self.__connHandler.execute_post(context, data)
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
        return ("Created TAP+ (v"+VERSION+") - Connection: \n" +
                str(self.__connHandler))


class TapPlus(Tap):
    """TAP plus class
    Provides TAP and TAP+ capabilities
    """

    def __init__(self, url=None, host=None, server_context=None,
                 tap_context=None, port=80, sslport=443,
                 default_protocol_is_https=False, connhandler=None,
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
                                      include_shared_tables=include_shared_tables,
                                      verbose=verbose)

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
        print("Retrieving table '"+str(table)+"'")
        connHandler = self.__getconnhandler()
        response = connHandler.execute_get("tables?tables="+table)
        if verbose:
            print(response.status, response.reason)
        isError = connHandler.check_launch_response_status(response, verbose, 200)
        if isError:
            print(response.status, response.reason)
            raise requests.exceptions.HTTPError(response.reason)
            return None
        print("Parsing table '"+str(table)+"'...")
        tsp = TableSaxParser()
        tsp.parseData(response)
        print("Done.")
        return tsp.get_table()

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
                subContext = subContext + '?' + self.__appendData(data)
        connHandler = self.__getconnhandler()
        response = connHandler.execute_get(subContext)
        if verbose:
            print(response.status, response.reason)
            print(response.getheaders())
        isError = connHandler.check_launch_response_status(response,
                                                           verbose,
                                                           200)
        if isError:
            print(response.reason)
            raise requests.exceptions.HTTPError(response.reason)
            return None
        # parse jobs
        jsp = JobSaxParser(async_job=True)
        jobs = jsp.parseData(response)
        if jobs is not None:
            for j in jobs:
                j.set_connhandler(connHandler)
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
            print("Jobs to be removed: " + str(jobsIds))
        data = "JOB_IDS=" + jobsIds
        subContext = "deletejobs"
        connHandler = self.__getconnhandler()
        response = connHandler.execute_post(subContext, data)
        if verbose:
            print(response.status, response.reason)
            print(response.getheaders())
        isError = connHandler.check_launch_response_status(response, verbose, 200)
        if isError:
            print(response.reason)
            raise requests.exceptions.HTTPError(response.reason)

    def login(self, user=None, password=None, credentials_file=None,
              verbose=False):
        """Performs a login.
        User and password can be used or a file that contains user name and
        password
        (2 lines: one for user name and the following one for the password)

        Parameters
        ----------
        user : str, mandatory if 'file' is not provided, default None
            login name
        password : str, mandatory if 'file' is not provided, default None
            user password
        credentials_file : str, mandatory if no 'user' & 'password' are provided
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
            print("Invalid user name")
            return
        if password is None:
            print("Invalid password")
            return
        self.__user = user
        self.__pwd = password
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
            print("Login error: " + str(response.reason))
            raise requests.exceptions.HTTPError("Login error: " + str(response.reason))
        else:
            # extract cookie
            cookie = self._Tap__findCookieInHeader(response.getheaders())
            if cookie is not None:
                self.__isLoggedIn = True
                connHandler.set_cookie(cookie)

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
            "username": str(usr),
            "password": str(pwd)}
        connHandler = self.__getconnhandler()
        data = connHandler.url_encode(args)
        response = connHandler.execute_secure(subContext, data)
        if verbose:
            print(response.status, response.reason)
            print(response.getheaders())
        return response

    def __getconnhandler(self):
        return self._Tap__connHandler
