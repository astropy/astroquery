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
        TO DO: documentation
        """
        
        self.session = requests.session()
        response = self.session.post(CosmoSim.QUERY_URL,auth=(self.username,self.password))

        if not response.ok:
            self.session = None
            response.raise_for_status()

    # will check to see if using private or public credentials
    def logged_in(self):
        """
        TO DO: documentation
        """
        print 'Need to implement when public default parameters (if any) are known...'

    
    def run_sql_query(self, query_string):
        """
        TO DO: documentation
        """

        result = self.session.post(CosmoSim.QUERY_URL,auth=(self.username,self.password),data={'query':query_string,'table':'mytest99','phase':'run'})
        root = etree.fromstring(result.content)
        self.current_job = root.find('{*}jobId').text
        return self.current_job
        #pdb.set_trace()

    def _existing_tables(self):
        """
        Internal function which finds the names of the tables already in use for a given set of user credentials.
        """
        return

    def check_query_status(self,jobid=None):
        """
        A public function which sends an http GET request for a given jobid 
        """

        if jobid is None:
            if hasattr(self,'current_job'):
                jobid = self.current_job
                
        response = self.session.get(CosmoSim.QUERY_URL+'/{}'.format(jobid)+'/phase',auth=(self.username,self.password),data={'print':'b'})
        print response.content
        return response.content

    def check_all_jobs(self):
        """
        Public function which creates a dictionary of job statuses. 

        Returns
        -------
        job_dict: dict
            A dictionary whose keys are each jobid for a given set of user credentials and whose values are the phase status (e.g. - EXECUTING,COMPLETED,PENDING).
        """

        checkalljobs = requests.get(CosmoSim.QUERY_URL,auth=(self.username,self.password),params={'print':'b'})
        
        self.job_dict={}
        root = etree.fromstring(checkalljobs.content)
        
        for iter in root:
            self.job_dict['{}'.format(iter.values()[0])] = iter.find('{*}phase').text

        return self.job_dict

    def delete_job(self):
        return

    def to_file(self,):
        return
    
    def _cosmosim_send_request(self,url,request_payload):
        """
        Internal function which sends the sql query request.

        Parameters
        ----------
        url : str
            The url to send the request to.
        request_payload : dict
            A dictionary of parameters for the POST request

        Returns
        -------
        response: `requests.Response` object
            The response for the HTTP POST request
        """
        
        if hasattr(self,'session'):
            response = self.session.post(url,data=re)
