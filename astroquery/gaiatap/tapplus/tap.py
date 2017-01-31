# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
=============
Gaia TAP plus
=============

@author: Juan Carlos Segovia
@contact: juan.carlos.segovia@sciops.esa.int

European Space Astronomy Centre (ESAC)
European Space Agency (ESA)

Created on 30 jun. 2016


"""
from astropy import units
from astropy.units import Quantity
from astroquery.gaiatap.tapplus import taputils
from astroquery.gaiatap.tapplus.conn.tapconn import TapConn
from astroquery.gaiatap.tapplus.xmlparser.tableSaxParser import TableSaxParser
from astroquery.gaiatap.tapplus.model.job import Job
from datetime import datetime
from astroquery.gaiatap.tapplus.gui.login import LoginDialog
from astroquery.gaiatap.tapplus.xmlparser.jobSaxParser import JobSaxParser
from astroquery.gaiatap.tapplus.xmlparser.jobListSaxParser import JobListSaxParser
from astroquery.gaiatap.tapplus.xmlparser import utils
from astroquery.gaiatap.tapplus.model.filter import Filter
from astroquery.utils import commons
import astropy.units

__all__ = ['TapPlus']

VERSION = "1.0"
TAP_CLIENT_ID = "aqtappy " + VERSION
MAIN_GAIA_TABLE = "gaiadr1.gaia_source"
MAIN_GAIA_TABLE_RA = "ra"
MAIN_GAIA_TABLE_DEC = "dec"


class TapPlus(object):
    """TAP plus class
    Provides TAP and TAP+ capabilities
    """


    def __init__(self, url=None, host=None, server_context=None, tap_context=None, port=80, sslport=443, default_protocol_is_https=False, connhandler=None, verbose=True):
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
            HTTP(s) connection hander (creator). If no handler is provided, a new one is created.
        verbose : bool, optional, default 'True' 
            flag to display information about the process
        """
        self.__internalInit()
        if url is not None:
            protocol, host, port, server_context, tap_context = self.__parseUrl(url)
            if protocol == "http":
                self.__connHandler = TapConn(False, host, server_context, tap_context, port, sslport)
            else:
                #https port -> sslPort
                self.__connHandler = TapConn(True, host, server_context, tap_context, port, port)
        else:
            self.__connHandler = TapConn(default_protocol_is_https, host, server_context, tap_context, port, sslport)
            pass
        #if connectionHandler is set, use it (useful for testing)
        if connhandler is not None:
            self.__connHandler = connhandler
        if verbose:
            print ("Created TAP+ connection to:\n" + str(self.__connHandler))
        pass
    
    def __internalInit(self):
        self.__connHandler = None
        self.__user=None
        self.__pwd=None
        self.__isLoggedIn=False
        pass
        
    def load_tables(self, only_names=False, include_shared_tables=False, verbose=False):
        """Loads all public tables
        TAP & TAP+
         
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
        #share_info=true&share_accessible=true&only_tables=true
        flags = None
        addedItem = False
        if only_names:
            flags = "only_tables=true"
            addedItem = True
        if include_shared_tables:
            if addedItem:
                flags += "&"
            flags += "share_accessible=true"
            addedItem = True
        print ("Retrieving tables...")
        if flags is not None:
            response = self.__connHandler.execute_get("tables?"+flags)
        else:
            response = self.__connHandler.execute_get("tables")
        if verbose:
            print(response.status, response.reason)
        isError = self.__connHandler.check_launch_response_status(response, verbose, 200)
        if isError:
            print(response.status, response.reason)
            raise Exception(response.reason)
            return None
        print ("Parsing tables...")
        tsp = TableSaxParser()
        tsp.parseData(response)
        print ("Done.")
        return tsp.get_tables()
    
    def load_table(self, table, verbose=False):
        """Loads the specified table
        TAP+ only
         
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
        print ("Retrieving table '"+str(table)+"'")
        response = self.__connHandler.execute_get("tables?tables="+table)
        if verbose:
            print(response.status, response.reason)
        isError = self.__connHandler.check_launch_response_status(response, verbose, 200)
        if isError:
            print(response.status, response.reason)
            raise Exception(response.reason)
            return None
        print ("Parsing table '"+str(table)+"'...")
        tsp = TableSaxParser()
        tsp.parseData(response)
        print ("Done.")
        return tsp.get_table()
    
    def launch_job(self, query, name=None, async=False, output_file=None, output_format="votable", verbose=False, dump_to_file=False, background=False, upload_resource=None, upload_table_name=None):
        """Launches a job. By default: it is synchronous
        TAP & TAP+
         
        Parameters
        ----------
        query : str, mandatory
            query to be executed
        name : str, optional
            job name
        async : bool, optional, default 'False' (synchronous)
            executes the job in asynchronous/synchronous mode
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
            when the job is executed in asynchronous mode, this flag specifies whether 
            the execution will wait until results are available
        upload_resource: str, optional, default None
            resource to be uploaded to UPLOAD_SCHEMA
        upload_table_name: str, required if uploadResource is provided, default None
            resource temporary table name associated to the uploaded resource

        Returns
        -------
        A Job object
        """
        if async:
            return self.launch_async_job(query, name, output_file, output_format, verbose, dump_to_file, background, upload_resource, upload_table_name)
        else:
            return self.launch_sync_job(query, name, output_file, output_format, verbose, dump_to_file, upload_resource, upload_table_name)
    
    def launch_sync_job(self, query, name=None, output_file=None, output_format="votable", verbose=False, dump_to_file=False, upload_resource=None, upload_table_name=None):
        """Launches a synchronous job
        TAP & TAP+
        
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
        query = taputils.setTopInQuery(query, 2000)
        print ("Launched query: '"+str(query)+"'")
        if upload_resource is not None:
            if upload_table_name is None:
                raise ValueError("Table name is required when a resource is uploaded")
            response = self.__launchJobMultipart(query, upload_resource, upload_table_name, output_format, "sync", verbose, name)
        else:
            response = self.__launchJob(query, output_format, "sync", verbose, name)
        job = Job(async=False, query=query, connhandler=self.__connHandler)
        isError = self.__connHandler.check_launch_response_status(response, verbose, 200)
        suitableOutputFile = self.__getSuitableOutputFile(False, output_file, response.getheaders(), isError)
        job.set_output_file(suitableOutputFile)
        job.set_output_format(output_format)
        job.set_response_status(response.status, response.reason)
        if isError:
            job.set_failed(True)
            if dump_to_file:
                self.__connHandler.dump_to_file(suitableOutputFile, response)
            raise Exception(response.reason)
        else:
            print ("Retrieving sync. results...")
            if dump_to_file:
                self.__connHandler.dump_to_file(suitableOutputFile, response)
            else:
                results = utils.read_http_response(response, output_format)
                job.set_results(results)
            print ("Query finished.")
            job.set_phase('COMPLETED')
        return job
    
    def launch_async_job(self, query, name=None, output_file=None, output_format="votable", verbose=False, dump_to_file=False, background=False, upload_resource=None, upload_table_name=None):
        """Launches an asynchronous job
        TAP & TAP+
        
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
            when the job is executed in asynchronous mode, this flag specifies whether 
            the execution will wait until results are available
        upload_resource: str, optional, default None
            resource to be uploaded to UPLOAD_SCHEMA
        upload_table_name: str, required if uploadResource is provided, default None
            resource temporary table name associated to the uploaded resource

        Returns
        -------
        A Job object
        """
        print ("Launched query: '"+str(query)+"'")
        if upload_resource is not None:
            if upload_table_name is None:
                raise ValueError("Table name is required when a resource is uploaded")
            response = self.__launchJobMultipart(query, upload_resource, upload_table_name, output_format, "async", verbose, name)
        else:
            response = self.__launchJob(query, output_format, "async", verbose, name)
        isError = self.__connHandler.check_launch_response_status(response, verbose, 303)
        job = Job(async=True, query=query, connhandler=self.__connHandler)
        suitableOutputFile = self.__getSuitableOutputFile(True, output_file, response.getheaders(), isError)
        job.set_output_file(suitableOutputFile)
        job.set_response_status(response.status, response.reason)
        job.set_output_format(output_format)
        if isError:
            job.set_failed(True)
            if dump_to_file:
                self.__connHandler.dump_to_file(suitableOutputFile, response)
            raise Exception(response.reason)
        else:
            location = self.__connHandler.find_header(response.getheaders(), "location")
            jobid = self.__getJobId(location)
            if verbose:
                print ("job "+ str(jobid) + ", at: " + str(location))
            job.set_jobid(jobid)
            job.set_remote_location(location)
            if not background:
                print ("Retrieving async. results...")
                #saveResults or getResults will block (not background)
                if dump_to_file:
                    job.save_results(verbose)
                else:
                    job.get_results()
                    print ("Query finished.")
                pass
        return job
    
    def load_async_job(self, jobid=None, name=None, verbose=False):
        """Loads an asynchronous job
        TAP & TAP+
        
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
            jobfilter.add_filter('name',name) 
            jobs = self.search_async_jobs(jobfilter)
            if jobs is None or len(jobs) < 1:
                print ("No job found for name '"+str(name)+"'")
                return None
            jobid = jobs[0].get_jobid()
        if jobid is None:
            print ("No job identifier found")
            return None
        subContext = "async/" + str(jobid)
        response = self.__connHandler.execute_get(subContext);
        if verbose:
            print(response.status, response.reason)
            print(response.getheaders())
        isError = self.__connHandler.check_launch_response_status(response, verbose, 200)
        if isError:
            print (response.reason)
            raise Exception(response.reason)
            return None
        #parse job
        jsp = JobSaxParser(async=True)
        job = jsp.parseData(response)[0]
        job.set_connhandler(self.__connHandler)
        #load resulst
        job.get_results()
        return job
    
    def search_async_jobs(self, jobfilter=None, verbose=False):
        """Searches for jobs applying the specified filter
        TAP+ only
        
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
        #jobs/list?[&session=][&limit=][&offset=][&order=][&metadata_only=true|false]
        subContext = "jobs/async"
        if jobfilter is not None:
            data = jobfilter.createUrlRequest()
            if data is not None:
                subContext = subContext + '?' + self.__appendData(data)
            pass
        response = self.__connHandler.execute_get(subContext);
        if verbose:
            print(response.status, response.reason)
            print(response.getheaders())
        isError = self.__connHandler.check_launch_response_status(response, verbose, 200)
        if isError:
            print (response.reason)
            raise Exception(response.reason)
            return None
        #parse jobs
        jsp = JobSaxParser(async=True)
        jobs = jsp.parseData(response)
        if jobs is not None:
            for j in jobs:
                j.set_connhandler(self.__connHandler)
        return jobs

    def list_async_jobs(self, verbose=False):
        """Returns all the asynchronous jobs
        TAP & TAP+
        
        Parameters
        ----------
        verbose : bool, optional, default 'False' 
            flag to display information about the process

        Returns
        -------
        A list of Job objects
        """
        subContext = "async"
        response = self.__connHandler.execute_get(subContext);
        if verbose:
            print(response.status, response.reason)
            print(response.getheaders())
        isError = self.__connHandler.check_launch_response_status(response, verbose, 200)
        if isError:
            print (response.reason)
            raise Exception(response.reason)
            return None
        #parse jobs
        jsp = JobListSaxParser(async=True)
        jobs = jsp.parseData(response)
        if jobs is not None:
            for j in jobs:
                j.set_connhandler(self.__connHandler)
        return jobs
    
    def query_object(self, coordinate, radius=None, width=None, height=None, async=False, verbose=False):
        """Launches a job
        TAP & TAP+
        
        Parameters
        ----------
        coordinate : astropy.coordinate, mandatory
            coordinates center point
        radius : astropy.units, required if no 'width' nor 'height' are provided
            radius (deg)
        width : astropy.units, required if no 'radius' is provided
            box width
        height : astropy.units, required if no 'radius' is provided
            box height
        async : bool, optional, default 'False'
            executes the query (job) in asynchronous/synchronous mode (default synchronous)
        verbose : bool, optional, default 'False' 
            flag to display information about the process

        Returns
        -------
        The job results (astropy.table).
        """
        coord = self.__getCoordInput(coordinate, "coordinate")
        job = None
        if radius is not None:
            job = self.cone_search(coord, radius, async=async, verbose=verbose)
        else:
            raHours, dec = commons.coord_to_radec(coord)
            ra = raHours * 15.0 # Converts to degrees
            widthQuantity = self.__getQuantityInput(width, "width")
            heightQuantity = self.__getQuantityInput(height, "height")
            widthDeg = widthQuantity.to(units.deg)
            heightDeg = heightQuantity.to(units.deg)
            query = "SELECT DISTANCE(POINT('ICRS',"+str(MAIN_GAIA_TABLE_RA)+","+str(MAIN_GAIA_TABLE_DEC)+"), \
                POINT('ICRS',"+str(ra)+","+str(dec)+")) AS dist, * \
                FROM "+str(MAIN_GAIA_TABLE)+" WHERE CONTAINS(\
                POINT('ICRS',"+str(MAIN_GAIA_TABLE_RA)+","+str(MAIN_GAIA_TABLE_DEC)+"),\
                BOX('ICRS',"+str(ra)+","+str(dec)+", "+str(widthDeg.value)+", "+str(heightDeg.value)+"))=1 \
                ORDER BY dist ASC"
            job = self.launch_job(query, async=async, verbose=verbose)
        return job.get_results()
    
    def query_object_async(self, coordinate, radius=None, width=None, height=None, verbose=False):
        """Launches a job (async)
        TAP & TAP+
        
        Parameters
        ----------
        coordinate : astropy.coordinate, mandatory
            coordinates center point
        radius : astropy.units, required if no 'width' nor 'height' are provided
            radius
        width : astropy.units, required if no 'radius' is provided
            box width
        height : astropy.units, required if no 'radius' is provided
            box height
        async : bool, optional, default 'False'
            executes the query (job) in asynchronous/synchronous mode (default synchronous)
        verbose : bool, optional, default 'False' 
            flag to display information about the process

        Returns
        -------
        The job results (astropy.table).
        """
        return self.query_object(coordinate, radius, width, height, async=True, verbose=verbose)
    
    def query_region(self, coordinate, radius=None, width=None):
        print ("Not available")
        return None
    
    def query_region_async(self, coordinate, radius=None, width=None):
        print ("Not available")
        return None
    
    def get_images(self, coordinate):
        print ("Not available")
        return None
    
    def get_images_async(self, coordinate):
        print ("Not available")
        return None
    
    def cone_search(self, coordinate, radius, async=False, background=False, output_file=None, output_format="votable", verbose=False, dump_to_file=False):
        """Cone search sorted by distance
        TAP & TAP+
        
        Parameters
        ----------
        coordinate : astropy.coordinate, mandatory
            coordinates center point
        radius : astropy.units, mandatory
            radius
        async : bool, optional, default 'False'
            executes the job in asynchronous/synchronous mode (default synchronous)
        background : bool, optional, default 'False'
            when the job is executed in asynchronous mode, this flag specifies whether 
            the execution will wait until results are available
        output_file : str, optional, default None
            file name where the results are saved if dumpToFile is True. 
            If this parameter is not provided, the jobid is used instead
        output_format : str, optional, default 'votable'
            results format
        verbose : bool, optional, default 'False' 
            flag to display information about the process
        dump_to_file : bool, optional, default 'False'
            if True, the results are saved in a file instead of using memory

        Returns
        -------
        A Job object
        """
        coord = self.__getCoordInput(coordinate, "coordinate")
        raHours, dec = commons.coord_to_radec(coord)
        ra = raHours * 15.0 # Converts to degrees
        if radius is not None:
            radiusQuantity = self.__getQuantityInput(radius, "radius")
            radiusDeg = commons.radius_to_unit(radiusQuantity, unit='deg')
        query = "SELECT DISTANCE(POINT('ICRS',"+str(MAIN_GAIA_TABLE_RA)+","+str(MAIN_GAIA_TABLE_DEC)+"), \
            POINT('ICRS',"+str(ra)+","+str(dec)+")) AS dist, * \
            FROM "+str(MAIN_GAIA_TABLE)+" WHERE CONTAINS(\
            POINT('ICRS',"+str(MAIN_GAIA_TABLE_RA)+","+str(MAIN_GAIA_TABLE_DEC)+"),\
            CIRCLE('ICRS',"+str(ra)+","+str(dec)+", "+str(radiusDeg)+"))=1 \
            ORDER BY dist ASC"
        if async:
            return self.launch_async_job(query=query, output_file=output_file, output_format=output_format, verbose=verbose, dump_to_file=dump_to_file, background=background)
        else:
            return self.launch_sync_job(query=query, output_file=output_file, output_format=output_format, verbose=verbose, dump_to_file=dump_to_file)
        pass
    
    def remove_jobs(self, jobs_list, verbose=False):
        """Removes the specified jobs
        TAP+
        
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
            jobsIds = str
        elif isinstance(jobs_list, list):
            jobsIds = ','.join(jobs_list)
            pass
        else:
            raise Exception("Invalid object type")
        if verbose:
            print ("Jobs to be removed: " + str(jobsIds))
        data = "JOB_IDS=" + jobsIds
        subContext = "deletejobs"
        response = self.__connHandler.execute_post(subContext, data)
        if verbose:
            print(response.status, response.reason)
            print(response.getheaders())
        isError = self.__connHandler.check_launch_response_status(response, verbose, 200)
        if isError:
            print (response.reason)
            raise Exception(response.reason)
        pass
    
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
        TAP & TAP+
        
        Parameters
        ----------
        job : Job, mandatory
            job
        verbose : bool, optional, default 'False' 
            flag to display information about the process
        """
        job.save_results()
        pass
    
    def __getJobId(self, location):
        pos = location.rfind('/')+1
        jobid = location[pos:]
        return jobid
    
    def __launchJobMultipart(self, query, uploadResource, uploadTableName, outputFormat, context, verbose, name=None):
        uploadValue = str(uploadTableName) + ",param:" + str(uploadTableName)
        args = {
            "REQUEST": "doQuery", \
            "LANG":    "ADQL", \
            "FORMAT":  str(outputFormat), \
            "PHASE":  "RUN", \
            "QUERY":   str(query), \
            "UPLOAD": ""+str(uploadValue)}
        if name is not None:
            args['jobname'] = name
        #f = open(uploadResource, "rb")
        #chunk = f.read().decode('utf8')
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
            "REQUEST": "doQuery", \
            "LANG":    "ADQL", \
            "FORMAT":  str(outputFormat), \
            "PHASE":  "RUN", \
            "QUERY":   str(query)}
        if name is not None:
            args['jobname'] = name
        data = self.__connHandler.url_encode(args)
        response = self.__connHandler.execute_post(context, data)
        if verbose:
            print(response.status, response.reason)
            print(response.getheaders())
        return response
    
    def __getSuitableOutputFile(self, async, outputFile, headers, isError):
        dateTime = datetime.now().strftime("%Y%m%d%H%M%S")
        ext = self.__connHandler.get_suitable_extension(headers)
        fileName = ""
        if outputFile is None:
            if async == False:
                fileName = "sync_" + str(dateTime) + ext
            else:
                fileName = "async_" + str(dateTime) + ext
        else:
            fileName = outputFile
        if isError:
            fileName += ".error"
        return fileName
    
    def login(self, user=None, password=None, credentials_file=None, verbose=False):
        """Performs a login.
        TAP+ only
        User and password can be used or a file that contains user name and password
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
            #read file: get user & password
            with open(credentials_file, "r") as ins:
                user = ins.readline()
                password = ins.readline()
            pass
        if user is None:
            print ("Invalid user name")
            return
        if password is None:
            print ("Invalid password")
            return
        self.__user = user
        self.__pwd = password
        self.__dologin(verbose)
        pass
    
    def login_gui(self, verbose=False):
        """Performs a login using a GUI dialog
        TAP+ only
        
        Parameters
        ----------
        verbose : bool, optional, default 'False' 
            flag to display information about the process
        """
        url = self.__connHandler.get_host_url()
        loginDialog = LoginDialog(url)
        loginDialog.show_login()
        if loginDialog.is_accepted():
            self.__user = loginDialog.get_user()
            self.__pwd = loginDialog.get_password()
            #execute login
            self.__dologin(verbose)
        else:
            self.__isLoggedIn = False
        pass
    
    def __dologin(self, verbose=False):
        self.__isLoggedIn = False
        response = self.__execLogin(self.__user, self.__pwd, verbose)
        #check response
        isError = self.__connHandler.check_launch_response_status(response, verbose, 200)
        if isError:
            print ("Login error: " + str(response.reason))
            raise Exception("Login error: " + str(response.reason))
        else:
            #extract cookie
            cookie = self.__findCookieInHeader(response.getheaders())
            if cookie is not None:
                self.__isLoggedIn = True
                self.__connHandler.set_cookie(cookie)
        pass
    
    def logout(self, verbose=False):
        """Performs a logout
        TAP+ only
        
        Parameters
        ----------
        verbose : bool, optional, default 'False' 
            flag to display information about the process
        """
        subContext = "logout"
        args = {}
        data = self.__connHandler.url_encode(args)
        response = self.__connHandler.execute_secure(subContext, data)
        if verbose:
            print(response.status, response.reason)
            print(response.getheaders())
        self.__isLoggedIn = False
        pass
    
    def __execLogin(self, usr, pwd, verbose=False):
        subContext = "login"
        args = {
            "username": str(usr), \
            "password":    str(pwd)}
        data = self.__connHandler.url_encode(args)
        response = self.__connHandler.execute_secure(subContext, data)
        if verbose:
            print(response.status, response.reason)
            print(response.getheaders())
        return response
    
    def __findCookieInHeader(self, headers, verbose=False):
        cookies = self.__connHandler.find_header(headers, 'Set-Cookie')
        if verbose:
            print (cookies)
        if cookies is None:
            return None
        else:
            items = cookies.split(';')
            for i in items:
                if i.startswith("JSESSIONID="):
                    return i
        return None
    
    def __checkQuantityInput(self, value, msg):
        if not (isinstance(value, str) or isinstance(value, astropy.units.Quantity)):
            raise ValueError(str(msg) + " must be either a string or astropy.coordinates")
    
    def __getQuantityInput(self, value, msg):
        if value is None:
            raise ValueError("Missing required argument: '"+str(msg)+"'")
        if not (isinstance(value, str) or isinstance(value, astropy.units.Quantity)):
            raise ValueError(str(msg) + " must be either a string or astropy.coordinates")
        if isinstance(value, str):
            q = Quantity(value)
            return q
        else:
            return value
    
    def __checkCoordInput(self, value, msg):
        if not (isinstance(value, str) or isinstance(value, commons.CoordClasses)):
            raise ValueError(str(msg) + " must be either a string or astropy.coordinates")
    
    def __getCoordInput(self, value, msg):
        if not (isinstance(value, str) or isinstance(value, commons.CoordClasses)):
            raise ValueError(str(msg) + " must be either a string or astropy.coordinates")
        if isinstance(value, str):
            c = commons.parse_coordinates(value)
            return c
        else:
            return value
    
    def __parseUrl(self, url, verbose=False):
        isHttps = False
        if url.startswith("https://"):
            isHttps = True
            protocol = "https"
        else:
            protocol = "http"
        
        if verbose:
            print ("is https: " + str(isHttps))
        
        urlInfoPos = url.find("://")
        
        if urlInfoPos < 0:
            raise ValueError("Invalid URL format")
        
        urlInfo = url[(urlInfoPos+3):]
        
        items = urlInfo.split("/")
        
        if verbose:
            print ("'" + urlInfo + "'")
            for i in items:
                print ("'" + i + "'")
        
        itemsSize = len(items)
        hostPort = items[0]
        portPos = hostPort.find(":")
        if portPos > 0:
            #port found
            host = hostPort[0:portPos]
            port = int(hostPort[portPos+1:])
        else:
            #no port found
            host = hostPort
            #no port specified: use defaults
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
            pass
        if verbose:
            print ("protocol: '%s'" % protocol)
            print ("host: '%s'" % host)
            print ("port: '%d'" % port)
            print ("server context: '%s'" % serverContext)
            print ("tap context: '%s'" % tapContext)
        return protocol, host, port, serverContext, tapContext

    
    pass
