import requests
import sys
from bs4 import BeautifulSoup
from lxml import etree
import numpy as np

# Astropy imports
from astropy.table import Table
import astropy.units as u
import astropy.coordinates as coord
import astropy.io.votable as votable
from astropy.io import fits
import astropy.utils.data as aud

# Astroquery imports
from ..utils import commons
from ..query import QueryWithLogin
from . import COSMOSIM_SERVER, COSMOSIM_TIMEOUT

import pdb

__all__ = ['CosmoSim']

class CosmoSim(QueryWithLogin):
    """
    TO DO: documentation
    """

    QUERY_URL = COSMOSIM_SERVER()
    TIMEOUT = COSMOSIM_TIMEOUT()

    cosmosim_databases = ('MDR1','MDPL','Bolshoi','BolshoiP')

    def __init__(self,username=None,password=None):
        self.username = username
        self.password = password
        self.login(username,password)
        self._existing_tables()

    def login(self,username,password):
        """
        Public function which sends a GET request to the base url, and checks for authentication of user credentials. This function is used upon instantiation of the class.

        Parameters
        ----------
        username : string
            The CosmoSim.org username.
        password : string
            The CosmoSim.org password.
        """
        
        self.session = requests.session()
        response = self.session.get(CosmoSim.QUERY_URL,auth=(self.username,self.password))
        self._existing_tables()

    def login(self,username,password):
        """
        Public function which sends a GET request to the base url, and checks for authentication of user credentials. This function is used upon instantiation of the class.

        Parameters
        ----------
        username : string
            The CosmoSim.org username.
        password : string
            The CosmoSim.org password.
        """
        
        self.session = requests.session()
        response = self.session.get(CosmoSim.QUERY_URL,auth=(self.username,self.password))

        if not response.ok:
            self.session = None
            response.raise_for_status()
    
    def run_sql_query(self, query_string,tablename=None):
        """
        Public function which sends a POST request containing the sql query string.

        Parameters
        ----------
        query_string : string
            The sql query to be sent to the CosmoSim.org server.
        tablename : string
            The name of the table for which the query data will be stored under. If left blank or if it already exists, one will be generated automatically.

        Returns
        -------
        result : 'requests.models.Response' object
            The requests response 
        """
        
        self._existing_tables()

        if tablename in self.table_dict.values():
            result = self.session.post(CosmoSim.QUERY_URL,auth=(self.username,self.password),data={'query':query_string,'phase':'run'})
            soup = BeautifulSoup(result.content)
            gen_tablename = str(soup.find(id="table").string)
            #root = etree.fromstring(result.content)
            #gen_tablename = [[subname.text for subname in name.iterfind('{*}parameter') if subname.attrib['id']=='table'] for name in root.iterfind('{*}parameters')][0][0]
            print "Table name {} is already taken.".format(tablename)
            print "Generated table name: {}".format(gen_tablename)
        elif tablename is None:
            result = self.session.post(CosmoSim.QUERY_URL,auth=(self.username,self.password),data={'query':query_string,'phase':'run'})
        else:
            result = self.session.post(CosmoSim.QUERY_URL,auth=(self.username,self.password),data={'query':query_string,'table':'{}'.format(tablename),'phase':'run'})
        
        soup = BeautifulSoup(result.content)
        self.current_job = str(soup.find("uws:jobid").string)
        #root = etree.fromstring(result.content)
        #self.current_job = root.find('{*}jobId').text
        print "Job created: {}".format(self.current_job)
        self._existing_tables()
        return result
        
    def _existing_tables(self):
        """
        Internal function which builds a dictionary of the tables already in use for a given set of user credentials. Keys are jobids and values are the tables which are stored under those keys.
        """

        checkalljobs = self.check_all_jobs()
        completed_jobs = [key for key in self.job_dict.keys() if self.job_dict[key] in ['COMPLETED','EXECUTING']]
        soup = BeautifulSoup(checkalljobs.content)
        root = etree.fromstring(checkalljobs.content)
        self.table_dict={}
        pdb.set_trace()
        for iter in root:
            jobid = '{}'.format(iter.values()[1].split(CosmoSim.QUERY_URL+"/")[1])
            if jobid in completed_jobs:
                self.table_dict[jobid] = '{}'.format(iter.values()[0])
        

    def check_query_status(self,jobid=None):
        """
        A public function which sends an http GET request for a given jobid, and checks the server status. If no jobid is provided, it uses the most recent query (if one exists).

        Parameters
        ----------
        jobid : string
            The jobid of the sql query. If none provided
        """
        
        if jobid is None:
            if hasattr(self,'current_job'):
                jobid = self.current_job
            else:
                try:
                    jobid = self.current_job
                except: 
                    raise AttributeError
                
        response = self.session.get(CosmoSim.QUERY_URL+'/{}'.format(jobid)+'/phase',auth=(self.username,self.password),data={'print':'b'})
        print "Job {}: {}".format(jobid,response.content)
        return response.content

    def check_all_jobs(self):
        """
        Public function which builds a dictionary whose keys are each jobid for a given set of user credentials and whose values are the phase status (e.g. - EXECUTING,COMPLETED,PENDING,ERROR).

        Returns
        -------
        checkalljobs : 'requests.models.Response' object
            The requests response for the GET request for finding all existing jobs.
        """
        
        checkalljobs = self.session.get(CosmoSim.QUERY_URL,auth=(self.username,self.password),params={'print':'b'})
        self.job_dict={}
        root = etree.fromstring(checkalljobs.content)
        
        for iter in root:
            if iter.find('{*}phase').text in ['COMPLETED','EXECUTING','ABORTED','ERROR']:
                self.job_dict['{}'.format(iter.values()[1].split(CosmoSim.QUERY_URL+"/")[1])] = iter.find('{*}phase').text
            else:
                self.job_dict['{}'.format(iter.values()[0])] = iter.find('{*}phase').text

        frame = sys._getframe(1)
        do_not_print_job_dict = ['completed_job_info','delete_all_jobs','_existing_tables','delete_job','download'] # list of methods which use check_all_jobs() for which I would not like job_dict to be printed to the terminal
        if frame.f_code.co_name in do_not_print_job_dict: 
            return checkalljobs
        else:
            print self.job_dict
            return checkalljobs

    def completed_job_info(self,jobid=None,output=None):

        self.check_all_jobs()
        
        if jobid is None:
            completed_jobids = [key for key in self.job_dict.keys() if self.job_dict[key] == 'COMPLETED']
            response_list = [self.session.get(CosmoSim.QUERY_URL+"/{}".format(completed_jobids[i]),auth=(self.username,self.password)) for i in range(len(completed_jobids))]
        else:
            response_list = [self.session.get(CosmoSim.QUERY_URL+"/{}".format(jobid),auth=(self.username,self.password))]

        if output is not None:
            for i in response_list:
                print i.content
        else:
            print response_list
            
        return response_list

    def delete_job(self,jobid=None):
        """
        A public function which deletes a stored job from the server in any phase. If no jobid is given, it attemps to use the most recent job (if it exists in this session). If jobid is specified, then it deletes the corresponding job, and if it happens to match the existing current job, that variable gets deleted.
        """
        
        self.check_all_jobs()

        if jobid is None:
            if hasattr(self,'current_job'):
                jobid = self.current_job

        if jobid is not None:
            if hasattr(self,'current_job'):
                if jobid == self.current_job:
                    del self.current_job

        if job_dict[jobid] in ['COMPLETED','ERROR','ABORTED']:
            result = self.session.delete(CosmoSim.QUERY_URL+"/{}".format(jobid),auth=(self.username,self.password),data={'follow':''})
        else:
            print "Can only delete a job with phase: 'COMPLETED','ERROR',or 'ABORTED'."
        pdb.set_trace()
        if not result.ok:
            result.raise_for_status()
        print 'Deleted job: {}'.format(jobid)
        
        return result

    def abort_job(self,jobid=None):
        """
        """

        self.check_all_jobs()

    def delete_all_jobs(self):

        self.check_all_jobs()
        
        for key in self.job_dict.keys():
            result = self.session.delete(CosmoSim.QUERY_URL+"/{}".format(key),auth=(self.username,self.password),data={'follow':''})
            if not result.ok:
                result.raise_for_status()
            print "Deleted job: {}".format(key)

        return 

    def download(self,jobid=None,filename=None):
        """
        A public function to download data from a job with COMPLETED phase.

        Keyword Args
        ----------
        jobid :
            Completed jobid to be downloaded
        filename : string
            If left blank, downloaded to the terminal. If specified, data is written out to file (directory can be included here).

        Returns
        -------
        headers, data : list, list
        """

        if jobid is None:
            try:
                jobid = self.current_job
            except:
                raise
                
        self.check_all_jobs()
        completed_job_responses = self.completed_job_info(jobid)
        soup = BeautifulSoup(completed_job_responses[0].content)
        #tableurl = 
        root = etree.fromstring(completed_job_responses[0].content)
        tableurl = [[list(c.attrib.values())[1] for c in e] for e in root.iter('{*}results') ][0][0]

        # This is where the requestrequest.content parsing happens
        raw_table_data = self.session.get(tableurl,auth=(self.username,self.password))
        raw_headers = raw_table_data.content.split('\n')[0]
        num_cols = len(raw_headers.split(','))
        num_rows = len(raw_table_data.content.split('\n'))-2
        headers = [raw_headers.split(',')[i].strip('"') for i in range(num_cols)]
        raw_data = [raw_table_data.content.split('\n')[i+1].split(",") for i in range(num_rows)]
        data = [map(eval,raw_data[i]) for i in range(num_rows)]
        
        if filename is None:
            return headers, data
        else:
            with open(filename, 'wb') as fh:
                raw_table_data = self.session.get(tableurl,auth=(self.username,self.password),stream=True)
                for block in raw_table_data.iter_content(1024):
                    if not block:
                        break
                    fh.write(block)
                print "Data written to file: {}".format(filename)
            return headers, data

    # will check to see if using private or public credentials
    def logged_in(self):
        """
        TO DO: documentation
        """
        print 'Need to implement when public default parameters (if any) are known...'
    
    def run_sql_query(self, query_string,tablename=None):
        """
        Public function which sends a POST request containing the sql query string.

        Parameters
        ----------
        query_string : string
            The sql query to be sent to the CosmoSim.org server.
        tablename : string
            The name of the table for which the query data will be stored under. If left blank or if it already exists, one will be generated automatically.

        Returns
        -------
        result : 'requests.models.Response' object
            The requests response 
        """
        
        self._existing_tables()

        if tablename in self.table_dict.values():
            result = self.session.post(CosmoSim.QUERY_URL,auth=(self.username,self.password),data={'query':query_string,'phase':'run'})
            root = etree.fromstring(result.content)
            gen_tablename = [[subname.text for subname in name.iterfind('{*}parameter') if subname.attrib['id']=='table'] for name in root.iterfind('{*}parameters')][0][0]
            print "Table name {} is already taken.".format(tablename)
            print "Generated table name: {}".format(gen_tablename)
        elif tablename is None:
            result = self.session.post(CosmoSim.QUERY_URL,auth=(self.username,self.password),data={'query':query_string,'phase':'run'})
        else:
            result = self.session.post(CosmoSim.QUERY_URL,auth=(self.username,self.password),data={'query':query_string,'table':'{}'.format(tablename),'phase':'run'})
            
        root = etree.fromstring(result.content)
        self.current_job = root.find('{*}jobId').text
        print "Job created: {}".format(self.current_job)
        self._existing_tables()
        return result
        
    def _existing_tables(self):
        """
        Internal function which builds a dictionary of the tables already in use for a given set of user credentials. Keys are jobids and values are the tables which are stored under those keys.
        """

        checkalljobs = self.check_all_jobs()
        completed_jobs = [key for key in self.job_dict.keys() if self.job_dict[key] in ['COMPLETED','EXECUTING']]
        root = etree.fromstring(checkalljobs.content)
        self.table_dict={}
        
        for iter in root:
            jobid = '{}'.format(iter.values()[1].split(CosmoSim.QUERY_URL+"/")[1])
            if jobid in completed_jobs:
                self.table_dict[jobid] = '{}'.format(iter.values()[0])
        

    def check_query_status(self,jobid=None):
        """
        A public function which sends an http GET request for a given jobid, and checks the server status. If no jobid is provided, it uses the most recent query (if one exists).

        Parameters
        ----------
        jobid : string
            The jobid of the sql query. If none provided
        """
        
        if jobid is None:
            if hasattr(self,'current_job'):
                jobid = self.current_job
            else:
                try:
                    jobid = self.current_job
                except: 
                    raise AttributeError
                
        response = self.session.get(CosmoSim.QUERY_URL+'/{}'.format(jobid)+'/phase',auth=(self.username,self.password),data={'print':'b'})
        print "Job {}: {}".format(jobid,response.content)
        return response.content

    def check_all_jobs(self):
        """
        Public function which builds a dictionary whose keys are each jobid for a given set of user credentials and whose values are the phase status (e.g. - EXECUTING,COMPLETED,PENDING,ERROR).

        Returns
        -------
        checkalljobs : 'requests.models.Response' object
            The requests response for the GET request for finding all existing jobs.
        """
        
        checkalljobs = self.session.get(CosmoSim.QUERY_URL,auth=(self.username,self.password),params={'print':'b'})
        self.job_dict={}
        root = etree.fromstring(checkalljobs.content)
        
        for iter in root:
            if iter.find('{*}phase').text in ['COMPLETED','EXECUTING','ABORTED','ERROR']:
                self.job_dict['{}'.format(iter.values()[1].split(CosmoSim.QUERY_URL+"/")[1])] = iter.find('{*}phase').text
            else:
                self.job_dict['{}'.format(iter.values()[0])] = iter.find('{*}phase').text

        frame = sys._getframe(1)
        do_not_print_job_dict = ['completed_job_info','delete_all_jobs','_existing_tables','delete_job','download'] # list of methods which use check_all_jobs() for which I would not like job_dict to be printed to the terminal
        if frame.f_code.co_name in do_not_print_job_dict: 
            return checkalljobs
        else:
            print self.job_dict
            return checkalljobs

    def completed_job_info(self,jobid=None,output=None):

        self.check_all_jobs()
        
        if jobid is None:
            completed_jobids = [key for key in self.job_dict.keys() if self.job_dict[key] == 'COMPLETED']
            response_list = [self.session.get(CosmoSim.QUERY_URL+"/{}".format(completed_jobids[i]),auth=(self.username,self.password)) for i in range(len(completed_jobids))]
        else:
            response_list = [self.session.get(CosmoSim.QUERY_URL+"/{}".format(jobid),auth=(self.username,self.password))]

        if output is not None:
            for i in response_list:
                print i.content
        else:
            print response_list
            
        return response_list

    def delete_job(self,jobid=None):
        """
        A public function which deletes a stored job from the server in any phase. If no jobid is given, it attemps to use the most recent job (if it exists in this session). If jobid is specified, then it deletes the corresponding job, and if it happens to match the existing current job, that variable gets deleted.
        """
        
        self.check_all_jobs()

        if jobid is None:
            if hasattr(self,'current_job'):
                jobid = self.current_job

        if jobid is not None:
            if hasattr(self,'current_job'):
                if jobid == self.current_job:
                    del self.current_job

        if job_dict[jobid] in ['COMPLETED','ERROR','ABORTED']:
            result = self.session.delete(CosmoSim.QUERY_URL+"/{}".format(jobid),auth=(self.username,self.password),data={'follow':''})
        else:
            print "Can only delete a job with phase: 'COMPLETED','ERROR',or 'ABORTED'."
        pdb.set_trace()
        if not result.ok:
            result.raise_for_status()
        print 'Deleted job: {}'.format(jobid)
        
        return result

    def abort_job(self,jobid=None):
        """
        """

        self.check_all_jobs()

    def delete_all_jobs(self):

        self.check_all_jobs()
        
        for key in self.job_dict.keys():
            result = self.session.delete(CosmoSim.QUERY_URL+"/{}".format(key),auth=(self.username,self.password),data={'follow':''})
            if not result.ok:
                result.raise_for_status()
            print "Deleted job: {}".format(key)

        return 

    def download(self,jobid=None,filename=None):
        """
        A public function to download data from a job with COMPLETED phase.

        Keyword Args
        ----------
        jobid :
            Completed jobid to be downloaded
        filename : string
            If left blank, downloaded to the terminal. If specified, data is written out to file (directory can be included here).

        Returns
        -------
        headers, data : list, list
        """

        if jobid is None:
            try:
                jobid = self.current_job
            except:
                raise
                
        #if hasattr(self,'session'):
        #    response = self.session.post(url,data=re)

        self.check_all_jobs()
        completed_job_responses = self.completed_job_info(jobid)
        root = etree.fromstring(completed_job_responses[0].content)
        tableurl = [[list(c.attrib.values())[1] for c in e] for e in root.iter('{*}results') ][0][0]

        # This is where the requestrequest.content parsing happens
        raw_table_data = self.session.get(tableurl,auth=(self.username,self.password))
        raw_headers = raw_table_data.content.split('\n')[0]
        num_cols = len(raw_headers.split(','))
        num_rows = len(raw_table_data.content.split('\n'))-2
        headers = [raw_headers.split(',')[i].strip('"') for i in range(num_cols)]
        raw_data = [raw_table_data.content.split('\n')[i+1].split(",") for i in range(num_rows)]
        data = [map(eval,raw_data[i]) for i in range(num_rows)]
    
        if filename is None:
            return headers, data
        else:
            with open(filename, 'wb') as fh:
                raw_table_data = self.session.get(tableurl,auth=(self.username,self.password),stream=True)
                for block in raw_table_data.iter_content(1024):
                    if not block:
                        break
                    fh.write(block)
                print "Data written to file: {}".format(filename)
            return headers, data
