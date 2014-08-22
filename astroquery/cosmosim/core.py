from __future__ import print_function
import requests
import sys
from bs4 import BeautifulSoup
import keyring
import getpass
import logging

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



__all__ = ['CosmoSim']

class CosmoSim(QueryWithLogin):
    
    QUERY_URL = COSMOSIM_SERVER()
    SCHEMA_URL = 'http://www.cosmosim.org/query/account/databases/json'
    TIMEOUT = COSMOSIM_TIMEOUT()

    cosmosim_databases = ('MDR1','MDPL','Bolshoi','BolshoiP')

    def __init__(self):
        super(CosmoSim, self).__init__()
        self.session = requests.session()
 
    def _login(self, username):
        
        self.session = requests.session()
        self.username = username
        
        # Get password from keyring or prompt
        password_from_keyring = keyring.get_password("astroquery:www.cosmosim.org", self.username)
        if password_from_keyring is None:
            self.password = getpass.getpass("{0}, enter your CosmoSim password:\n".format(self.username))
        else:
            self.password = password_from_keyring
            
        # Authenticate
        print("Authenticating {0} on www.cosmosim.org...".format(self.username))
        authenticated = self.session.post(CosmoSim.QUERY_URL,auth=(self.username,self.password))
        if authenticated.status_code == 200:
            print("Authentication successful!")
        elif authenticated.status_code == 401:
            print("Authentication failed!")
        elif authenticated.status_code == 503:
            print("Service Temporarily Unavailable...")
            
        # Generating dictionary of existing tables
        self._existing_tables()

        if authenticated.status_code == 200 and password_from_keyring is None:
            keyring.set_password("astroquery:www.cosmosim.org", self.username, self.password)

        # Delete job
        soup = BeautifulSoup(authenticated.content)
        self.delete_job(jobid="{}".format(soup.find("uws:jobid").string),squash=True)
        
        return authenticated


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
            logging.warning("Table name {} is already taken.".format(tablename))
            print("Generated table name: {}".format(gen_tablename))
        elif tablename is None:
            result = self.session.post(CosmoSim.QUERY_URL,auth=(self.username,self.password),data={'query':query_string,'phase':'run'})
        else:
            result = self.session.post(CosmoSim.QUERY_URL,auth=(self.username,self.password),data={'query':query_string,'table':'{}'.format(tablename),'phase':'run'})
        
        soup = BeautifulSoup(result.content)
        self.current_job = str(soup.find("uws:jobid").string)
        print("Job created: {}".format(self.current_job))
        self._existing_tables()
        return result
        
    def _existing_tables(self):
        """
        Internal function which builds a dictionary of the tables already in use for a given set of user credentials. Keys are jobids and values are the tables which are stored under those keys.
        """

        checkalljobs = self.check_all_jobs()
        completed_jobs = [key for key in self.job_dict.keys() if self.job_dict[key] in ['COMPLETED','EXECUTING']]
        soup = BeautifulSoup(checkalljobs.content)
        self.table_dict={}
        
        for i in soup.find_all("uws:jobref"):
            jobid = i.get('xlink:href').split('/')[-1]
            if jobid in completed_jobs:
                self.table_dict[jobid] = '{}'.format(i.get('id'))

    def check_query_status(self,jobid=None):
        """
        A public function which sends an http GET request for a given jobid, and checks the server status. If no jobid is provided, it uses the most recent query (if one exists).

        Parameters
        ----------
        jobid : string
            The jobid of the sql query. If no jobid is given, it attemps to use the most recent job (if it exists in this session).
            
        Returns
        -------
        result : content of 'requests.models.Response' object
            The requests response phase
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
        print("Job {}: {}".format(jobid,response.content))
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
        soup = BeautifulSoup(checkalljobs.content)

        for i in soup.find_all("uws:jobref"):
            i_phase = str(i.find('uws:phase').string)
            if i_phase in ['COMPLETED','EXECUTING','ABORTED','ERROR']:
                self.job_dict['{}'.format(i.get('xlink:href').split('/')[-1])] = i_phase
            else:
                self.job_dict['{}'.format(i.get('id'))] = i_phase
                
        frame = sys._getframe(1)
        do_not_print_job_dict = ['completed_job_info','delete_all_jobs','_existing_tables','delete_job','download'] # list of methods which use check_all_jobs() for which I would not like job_dict to be printed to the terminal
        if frame.f_code.co_name in do_not_print_job_dict: 
            return checkalljobs
        else:
            print(self.job_dict)
            return checkalljobs

    def completed_job_info(self,jobid=None,output=False):
        """
        A public function which sends an http GET request for a given jobid with phase COMPLETED, and returns a list containing the response object. If no jobid is provided, a list of all responses with phase COMPLETED is generated.

        Parameters
        ----------
        jobid : string
            The jobid of the sql query.
        output : bool
            Print output of response(s) to the terminal
            
        Returns
        -------
        result : list
            A list of response object(s)
        """
        
        self.check_all_jobs()
        
        if jobid is None:
            completed_jobids = [key for key in self.job_dict.keys() if self.job_dict[key] == 'COMPLETED']
            response_list = [self.session.get(CosmoSim.QUERY_URL+"/{}".format(completed_jobids[i]),auth=(self.username,self.password)) for i in range(len(completed_jobids))]
        else:
            response_list = [self.session.get(CosmoSim.QUERY_URL+"/{}".format(jobid),auth=(self.username,self.password))]

        if output is True:
            for i in response_list:
                print(i.content)
        else:
            print(response_list)
            
        return response_list

    def delete_job(self,jobid=None,squash=None):
        """
        A public function which deletes a stored job from the server in any phase. If no jobid is given, it attemps to use the most recent job (if it exists in this session). If jobid is specified, then it deletes the corresponding job, and if it happens to match the existing current job, that variable gets deleted.
        
        Parameters
        ----------
        jobid : string
            The jobid of the sql query. If no jobid is given, it attemps to use the most recent job (if it exists in this session).
        output : bool
            Print output of response(s) to the terminal
            
        Returns
        -------
        result : list
            A list of response object(s)

        """
        
        self.check_all_jobs()

        if jobid is None:
            if hasattr(self,'current_job'):
                jobid = self.current_job

        if jobid is not None:
            if hasattr(self,'current_job'):
                if jobid == self.current_job:
                    del self.current_job

        if self.job_dict[jobid] in ['COMPLETED','ERROR','ABORTED','PENDING']:
            result = self.session.delete(CosmoSim.QUERY_URL+"/{}".format(jobid),auth=(self.username,self.password),data={'follow':''})
        else:
            print("Can only delete a job with phase: 'COMPLETED', 'ERROR', 'ABORTED', or 'PENDING'.")
            return 
            
        if not result.ok:
            result.raise_for_status()
        if squash is None:    
            print('Deleted job: {}'.format(jobid))
        
        return result

    def abort_job(self,jobid=None):
        """
        """

        self.check_all_jobs()

    def delete_all_jobs(self):
        """
        A public function which deletes all jobs from the server in any phase.
        """
        
        self.check_all_jobs()
        
        for key in self.job_dict.keys():
            result = self.session.delete(CosmoSim.QUERY_URL+"/{}".format(key),auth=(self.username,self.password),data={'follow':''})
            if not result.ok:
                result.raise_for_status()
            print("Deleted job: {}".format(key))

        return 

    def _generate_schema(self):
        """
        Internal function which builds a schema of all simulations within the database (in the form of a dictionary).
        """

        response = requests.get(CosmoSim.SCHEMA_URL,
                                auth=(self.username,self.password),
                                headers = {'Accept': 'application/json'})
        data = response.json()

        self.db_dict = {}
        for i in range(len(data['databases'])):
            self.db_dict['{}'.format(data['databases'][i]['name'])] = {}

            sstr = '{}'.format(data['databases'][i]['name'])
            sid = '{}'.format(data['databases'][i]['id'])
            self.db_dict[sstr]['id'] = sid
            sdesc = '{}'.format(data['databases'][i]['description'])
            self.db_dict[sstr]['description'] = sdesc
            self.db_dict[sstr]['tables'] = {}
            for j in range(len(data['databases'][i]['tables'])):
                sstr2 = '{}'.format(data['databases'][i]['tables'][j]['name'])
                self.db_dict[sstr]['tables'][sstr2] = {}
                sdata = data['databases'][i]['tables'][j]['id']
                self.db_dict[sstr]['tables'][sstr2]['id'] = sdata
                sdesc2 = data['databases'][i]['tables'][j]['description']
                self.db_dict[sstr]['tables'][sstr2]['description'] = sdesc2
                self.db_dict[sstr]['tables'][sstr2]['columns'] = {}
                tmpval = len(data['databases'][i]['tables'][j]['columns'])
                for k in range(tmpval):
                    sstr3 = '{}'.format(data['databases'][i]['tables'][j]['columns'][k]['name'])
                    self.db_dict[sstr]['tables'][sstr2]['columns'][sstr3] = {}
                    sdata2 = data['databases'][i]['tables'][j]['columns'][k]['id']
                    self.db_dict[sstr]['tables'][sstr2]['columns'][sstr3]['id'] = sdata2
                    sdesc3 = data['databases'][i]['tables'][j]['columns'][k]['description']
                    self.db_dict[sstr]['tables'][sstr2]['columns'][sstr3]['description'] = sdesc3

        return response

    def explore_db(self,db=None,table=None,col=None):
        """
        A public function which allows for the exploration of any simulation and its tables within the database. This function is meant to aid the user in constructing sql queries.
        
        Parameters
        ----------
        db : string
            The database to explore.
        table : string
            The table to explore.
        col : string
            The column to explore.
        """
        
        try:
            self.db_dict
        except AttributeError:
            self._generate_schema()
        
        if db is not None:
            if table is not None:
                if col is not None:
                    print("#"*(len(db)+4) + "\n# {} #\n".format(db) + "#"*(len(db)+4))
                    print("@ {}".format("tables"))
                    print("   @ {}".format(table))
                    print(" "*6 + "@ {}".format("columns"))
                    print(" "*9 + "@ {}".format('{}'.format(col)))
                    for i in self.db_dict['{}'.format(db)]['tables']['{}'.format(table)]['columns']['{}'.format(col)].keys():
                        print(" "*12 + "--> {}:{}".format(i,self.db_dict['{}'.format(db)]['tables']['{}'.format(table)]['columns']['{}'.format(col)][i]))
                    
                else:
                    print("#"*(len(db)+4) + "\n# {} #\n".format(db) + "#"*(len(db)+4))
                    print("@ {}".format("tables"))
                    print("   @ {}".format(table))
                    for i in self.db_dict['{}'.format(db)]['tables']['{}'.format(table)].keys():
                        if type(self.db_dict['{}'.format(db)]['tables']['{}'.format(table)][i]) == dict:
                            print(" "*6 + "@ {}".format(i))
                            for j in self.db_dict['{}'.format(db)]['tables']['{}'.format(table)][i].keys():
                                print(" "*9 + "--> {}".format(j))
                        else:
                            print(" "*6 + "$ {}".format(i))
                            print(" "*9 + "--> {}".format(self.db_dict['{}'.format(db)]['tables']['{}'.format(table)][i]))
                        

            else:    
                print("#"*(len(db)+4) + "\n# {} #\n".format(db) + "#"*(len(db)+4))
                for i in self.db_dict['{}'.format(db)].keys():
                    if type(self.db_dict['{}'.format(db)][i]) == dict:
                        print("@ {}".format(i))
                        for j in self.db_dict['{}'.format(db)][i].keys():
                            print("   --> {}".format(j))
                    else:
                        print("$ {}".format(i))
                        print("   --> {}".format(self.db_dict['{}'.format(db)][i]))
                            
        else:
            print("Must choose a database to explore:")
            for i in self.db_dict.keys():
                print(" ## " + "{}".format(i))
                            
        return 

    def download(self,jobid=None,filename=None):
        """
        A public function to download data from a job with COMPLETED phase.

        Keyword Args
        ------------
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
        tableurl = soup.find("uws:result").get("xlink:href")
        
        # This is where the request.content parsing happens
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
                print("Data written to file: {}".format(filename))
            return headers, data
