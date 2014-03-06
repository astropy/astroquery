import requests
from lxml import etree

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

    def __init__(self,username=None,password=None):
        self.username = username
        self.password = password
        self.login(username,password)

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

        if tablename in self.existing_tables:
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
        return result
        
    def _existing_tables(self):
        """
        Internal function which finds the names of the tables already in use for a given set of user credentials.
        """

        self.check_all_jobs()
        self.existing_tables = [key for key in self.job_dict.keys() if self.job_dict[key] == 'COMPLETED']

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
                print "Fix this"
                
        response = self.session.get(CosmoSim.QUERY_URL+'/{}'.format(jobid)+'/phase',auth=(self.username,self.password),data={'print':'b'})
        print "Job {}: {}".format(self.current_job,response.content)
        return response.content

    def check_all_jobs(self):
        """
        Public function which creates a dictionary whose keys are jobids and whose values are the corresponding job statuses. 

        Returns
        -------
        job_dict: dict
            A dictionary whose keys are each jobid for a given set of user credentials and whose values are the phase status (e.g. - EXECUTING,COMPLETED,PENDING,ERROR).
        """

        checkalljobs = requests.get(CosmoSim.QUERY_URL,auth=(self.username,self.password),params={'print':'b'})
        pdb.set_trace()
        self.job_dict={}
        root = etree.fromstring(checkalljobs.content)
        
        for iter in root:
            self.job_dict['{}'.format(iter.values()[0])] = iter.find('{*}phase').text

        return self.job_dict

    def completed_job_info(self,jobid=None):

        self.check_all_jobs()
        if jobid is None:
            completed_jobids = [key for key in self.job_dict.keys() if self.job_dict[key] == 'COMPLETED']
            response_list = [self.session.get(CosmoSim.QUERY_URL+"/{}".format(completed_jobids[i]),auth=(self.username,self.password)) for i in range(len(completed_jobids))]
        else:
            response_list = [self.session.get(CosmoSim.QUERY_URL+"/{}".format(jobid),auth=(self.username,self.password))]
        pdb.set_trace()
        
        print response_list
        
        return

    def delete_job(self,jobid=None):

        self.check_all_jobs()

        if jobid is None:
            if hasattr(self,'current_job'):
                jobid = self.current_job
        
        result = self.session.delete(CosmoSim.QUERY_URL+"/{}".format(jobid),auth=(self.username,self.password),data={'follow':''})
        print 'Deleted job: {}'.format(jobid)
        
        return result

    def delete_all_jobs(self):

        self.check_all_jobs()
        
        for key in self.job_dict.keys():
            result = self.session.delete(CosmoSim.QUERY_URL+"/{}".format(key),auth=(self.username,self.password),data={'follow':''})
            print "Deleted job: {}".format(key)

        return 

    def to_file(self,):
        return
    
    
