from __future__ import print_function
import requests
import sys
from bs4 import BeautifulSoup
import keyring
import getpass
import time
import smtplib
import re
from six.moves.email_mime_multipart import MIMEMultipart
from six.moves.email_mime_base import MIMEBase
from six.moves.email_mime_text import MIMEText
from six.moves.email_mime_base import message

# Astropy imports
from astropy.table import Table
import astropy.units as u
import astropy.coordinates as coord
import astropy.io.votable as votable
from astropy import log as logging
from astropy.io import fits
from astropy.io import votable
import astropy.utils.data as aud

# Astroquery imports
from ..utils import commons
from ..query import QueryWithLogin
from . import conf

__all__ = ['CosmoSim']

class CosmoSimClass(QueryWithLogin):

    QUERY_URL = conf.query_url
    SCHEMA_URL = conf.schema_url
    TIMEOUT = conf.timeout

    def __init__(self):
        super(CosmoSimClass, self).__init__()
        self.session = self._BaseQuery__session
 
    def _login(self, username, password=None, store_password=False):

        # login after logging out (interactive)
        if not hasattr(self,'session'):
            self.session = requests.session()
            self._BaseQuery__session = self.session # NOTE FROM AG: I hope this works...

        # login after login (interactive)
        if hasattr(self,'username'):
            logging.warning("Attempting to login while another user ({}) is already logged in.".format(self.username))
            self.check_login_status()
            return
            
        self.username = username
        
        # Get password from keyring or prompt
        password_from_keyring = keyring.get_password("astroquery:www.cosmosim.org", self.username)
        if not password_from_keyring:
            logging.warning("No password was found in the keychain for the provided username.")
            if password:
                self.password = password
            else:
                self.password = getpass.getpass("{0}, enter your CosmoSim password:\n".format(self.username))
        else:
            logging.warning("Using the password found in the keychain for the provided username.")
            self.password = password_from_keyring
            
        # Authenticate
        print("Authenticating {0} on www.cosmosim.org...".format(self.username))
        authenticated = self._request('POST', CosmoSim.QUERY_URL,
                                      auth=(self.username,self.password),
                                      cache=False)
        if authenticated.status_code == 200:
            print("Authentication successful!")
        elif authenticated.status_code == 401:
            print("Authentication failed!")
        elif authenticated.status_code == 503:
            print("Service Temporarily Unavailable...")
            
        # Generating dictionary of existing tables
        self._existing_tables()

        if authenticated.status_code == 200 and password_from_keyring is None and store_password:
            keyring.set_password("astroquery:www.cosmosim.org", self.username, self.password)

        # Delete job; prevent them from piling up with phase PENDING
        if authenticated.status_code == 200:
            soup = BeautifulSoup(authenticated.content)
            self.delete_job(jobid=str(soup.find("uws:jobid").string),squash=True)
        
        return authenticated

    def logout(self,deletepw=False):
        """
        Public function which allows the user to logout of their cosmosim credentials.

        Parameters
        ----------
        deletepw : bool
            A hard logout - delete the password to the associated username from the keychain. The default is True.
        Returns
        -------
        """
        
        if hasattr(self,'username') and hasattr(self,'password') and hasattr(self,'session'):
            if deletepw is True:
                try:
                    keyring.delete_password("astroquery:www.cosmosim.org", self.username)
                    print("Removed password for {} in the keychain.".format(self.username))
                except:
                    print("Password for {} was never stored in the keychain.".format(self.username))
                    
            del self.session
            del self._BaseQuery__session
            del self.username
            del self.password
        else:
            logging.error("You must log in before attempting to logout.")

    def check_login_status(self):
        """
        Public function which checks the status of a user login attempt.
        """
        
        if hasattr(self,'username') and hasattr(self,'password') and hasattr(self,'session'):
            authenticated = self._request('POST', CosmoSim.QUERY_URL,
                                          auth=(self.username,self.password),
                                          cache=False)
            if authenticated.status_code == 200:
                print("Status: You are logged in as {}.".format(self.username))
                soup = BeautifulSoup(authenticated.content)
                self.delete_job(jobid=str(soup.find("uws:jobid").string),squash=True)
            else:
                logging.warning("Status: The username/password combination for {} appears to be incorrect.".format(self.username))
                print("Please re-attempt to login with your cosmosim credentials.")
        else:
            print("Status: You are not logged in.")

        
    def run_sql_query(self, query_string, tablename=None, queue=None,
                      mail=None, text=None, cache=True):
        """
        Public function which sends a POST request containing the sql query string.

        Parameters
        ----------
        query_string : string
            The sql query to be sent to the CosmoSim.org server.
        tablename : string
            The name of the table for which the query data will be stored under. If left blank or if it already exists, one will be generated automatically.
        queue : string
            The short/long queue option. Default is short.
        mail : string
            The user's email address for receiving job completion alerts.
        text : string
            The user's cell phone number for receiving job completion alerts.
        cache : bool
            Whether to cache the query locally
            
        Returns
        -------
        result : jobid
            The jobid of the query 
        """
        
        self._existing_tables()

        if not queue:
            queue = 'short'

        if tablename in self.table_dict.values():
            result = self._request('POST',
                                   CosmoSim.QUERY_URL,
                                   auth=(self.username,self.password),
                                   data={'query':query_string,'phase':'run','queue':queue},
                                   cache=cache)
            soup = BeautifulSoup(result.content)
            gen_tablename = str(soup.find(id="table").string)
            logging.warning("Table name {} is already taken.".format(tablename))
            print("Generated table name: {}".format(gen_tablename))
        elif tablename is None:
            result = self._request('POST', CosmoSim.QUERY_URL,
                                   auth=(self.username, self.password),
                                   data={'query':query_string, 'phase':'run',
                                         'queue':queue},
                                   cache=cache)
        else:
            result = self._request('POST', CosmoSim.QUERY_URL,
                                   auth=(self.username, self.password),
                                   data={'query':query_string,
                                         'table':'{}'.format(tablename),
                                         'phase':'run', 'queue':queue},
                                   cache=cache)
            self._existing_tables()
        
        soup = BeautifulSoup(result.content)
        self.current_job = str(soup.find("uws:jobid").string)
        print("Job created: {}".format(self.current_job))

        if mail or text:
            self._initialize_alerting(self.current_job,mail=mail,text=text)
            self._alert(self.current_job,queue)
        
        return self.current_job
        
    def _existing_tables(self):
        """
        Internal function which builds a dictionary of the tables already in use
        for a given set of user credentials. Keys are jobids and values are the
        tables which are stored under those keys.
        """

        checkalljobs = self.check_all_jobs()
        completed_jobs = [key for key in self.job_dict.keys() if self.job_dict[key] in ['COMPLETED','EXECUTING']]
        soup = BeautifulSoup(checkalljobs.content)
        self.table_dict={}
        
        for i in soup.find_all("uws:jobref"):
            jobid = i.get('xlink:href').split('/')[-1]
            if jobid in completed_jobs:
                self.table_dict[jobid] = '{}'.format(i.get('id'))

    def check_job_status(self,jobid=None):
        """
        A public function which sends an http GET request for a given jobid,
        and checks the server status. If no jobid is provided, it uses the most
        recent query (if one exists).

        Parameters
        ----------
        jobid : string
            The jobid of the sql query. If no jobid is given, it attempts to
            use the most recent job (if it exists in this session).
            
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
                
        response = self._request('GET',
                                 CosmoSim.QUERY_URL+'/{}'.format(jobid)+'/phase',
                                 auth=(self.username, self.password),
                                 data={'print':'b'},cache=False)
        logging.info("Job {}: {}".format(jobid,response.content))
        return response.content

    def check_all_jobs(self, phase=None, regex=None):
        """
        Public function which builds a dictionary whose keys are each jobid for a
        given set of user credentials and whose values are the phase status (e.g. -
        EXECUTING,COMPLETED,PENDING,ERROR).
        
        Parameters
        ----------
        phase : list
            A list of phase(s) of jobs to be checked on. If nothing provided, all are checked.
        regex : string
            A regular expression to match all tablenames to. Matching table names will be deleted.

        Returns
        -------
        checkalljobs : 'requests.models.Response' object
            The requests response for the GET request for finding all existing jobs.
        """
        
        checkalljobs = self._request('GET', CosmoSim.QUERY_URL,
                                     auth=(self.username, self.password),
                                        params={'print':'b'},cache=False)

        self.job_dict={}
        soup = BeautifulSoup(checkalljobs.content)

        for i in soup.find_all("uws:jobref"):
            i_phase = str(i.find('uws:phase').string)
            if i_phase in ['COMPLETED','EXECUTING','ABORTED','ERROR']:
                self.job_dict['{}'.format(i.get('xlink:href').split('/')[-1])] = i_phase
            else:
                self.job_dict['{}'.format(i.get('id'))] = i_phase
        
        if regex:
            pattern = re.compile("{}".format(regex))
            groups = [pattern.match(self.table_dict.values()[i]).group() for i in range(len(self.table_dict.values()))]
            matching_tables = [groups[i] for i in range(len(groups)) if groups[i] in self.table_dict.values()]
            self._existing_tables() # creates a fresh up-to-date table_dict
            
        frame = sys._getframe(1)
        do_not_print_job_dict = ['completed_job_info','general_job_info','delete_all_jobs',
                                 '_existing_tables','delete_job','download'] # list of methods which use check_all_jobs()
                                                                             # for which I would not like job_dict to be
                                                                             # printed to the terminal
        if frame.f_code.co_name in do_not_print_job_dict: 
            return checkalljobs
        else:
            if not phase:
                if not regex:
                    for i in self.job_dict.keys():
                        print("{} : {}".format(i,self.job_dict[i]))
                if regex:
                    for i in self.job_dict.keys():
                        if i in self.table_dict.keys():
                            if self.table_dict[i] in matching_tables:
                                print("{} : {} (Table: {})".format(i,
                                                                   self.job_dict[i],
                                                                   self.table_dict[i]))
            elif phase:
                phase = [phase[i].upper() for i in range(len(phase))]
                if not regex:
                    for i in self.job_dict.keys():
                        if self.job_dict[i] in phase:
                            print("{} : {}".format(i,self.job_dict[i]))
                if regex:
                    for i in self.job_dict.keys():
                        if self.job_dict[i] in phase:
                            if i in self.table_dict.keys():
                                if self.table_dict[i] in matching_tables:
                                    print("{} : {} (Table: {})".format(i,
                                                                       self.job_dict[i],
                                                                       self.table_dict[i]))
            return checkalljobs

    def completed_job_info(self,jobid=None,output=False):
        """
        A public function which sends an http GET request for a given jobid with phase
        COMPLETED, and returns a list containing the response object. If no jobid is provided,
        a list of all responses with phase COMPLETED is generated.

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
            completed_jobids = [key
                                for key in self.job_dict.keys()
                                if self.job_dict[key] == 'COMPLETED']
            response_list = [self.session.get(CosmoSim.QUERY_URL+"/{}".format(completed_jobids[i]),
                                              auth=(self.username,self.password))
                                              for i in range(len(completed_jobids))]
        else:
            if self.job_dict[jobid] == 'COMPLETED':
                response_list = [self.session.get(CosmoSim.QUERY_URL+"/{}".format(jobid),
                                                  auth=(self.username,self.password))]
            else:
                logging.warning("JobID must refer to a query with a phase of 'COMPLETED'.")
                return

        if output is True:
            for i in response_list:
                print(i.content)
        else:
            print(response_list)

        return response_list
        
    def general_job_info(self,jobid=None,output=False):
        """
        A public function which sends an http GET request for a given jobid with phase COMPLETED,
        ERROR, or ABORTED, and returns a list containing the response object. If no jobid is provided,
        the current job is used (if it exists).

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
        general_jobids = [key for key in self.job_dict.keys() if self.job_dict[key] in ['COMPLETED','ABORTED','ERROR']]
        if jobid in general_jobids:
            response_list = [self._request('GET',
                                           CosmoSim.QUERY_URL+"/{}".format(jobid),
                                           auth=(self.username,
                                                 self.password),cache=False)]
        else:
            try:
                hasattr(self,current_job)
                response_list = [self._request('GET',
                                               CosmoSim.QUERY_URL+"/{}".format(self.current_job),
                                               auth=(self.username,
                                                     self.password),cache=False)]
            except (AttributeError, NameError):
                logging.warning("No current job has been defined, and no jobid has been provided.")


        if output:
            for i in response_list:
                print(i.content)
        else:
            print(response_list)

        return response_list

            
    def delete_job(self,jobid=None,squash=None):
        """
        A public function which deletes a stored job from the server in any phase.
        If no jobid is given, it attemps to use the most recent job (if it exists
        in this session). If jobid is specified, then it deletes the corresponding job,
        and if it happens to match the existing current job, that variable gets deleted.
        
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

        if jobid:
            if hasattr(self,'current_job'):
                if jobid == self.current_job:
                    del self.current_job

        if self.job_dict[jobid] in ['COMPLETED','ERROR','ABORTED','PENDING']:
            result = self.session.delete(CosmoSim.QUERY_URL+"/{}".format(jobid),
                                         auth=(self.username,  self.password),
                                         data={'follow':''})
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


    def delete_all_jobs(self,phase=None,regex=None):
        """
        A public function which deletes any/all jobs from the server in any phase
        and/or with its tablename matching any desired regular expression.

        Parameters
        ----------
        phase : list
            A list of job phases to be deleted. If nothing provided, all are deleted.
        regex : string
            A regular expression to match all tablenames to. Matching table names will be deleted.
        """

        self.check_all_jobs()

        if regex:
            pattern = re.compile("{}".format(regex))
            groups = [pattern.match(self.table_dict.values()[i]).group() for i in range(len(self.table_dict.values()))]
            matching_tables = [groups[i] for i in range(len(groups)) if groups[i] in self.table_dict.values()]

        if phase:
            phase = [phase[i].upper() for i in range(len(phase))]
            if regex:
                for key in self.job_dict.keys():
                    if self.job_dict[key] in phase:
                        if key in self.table_dict.keys():
                            if self.table_dict[key] in matching_tables:
                                result = self.session.delete(CosmoSim.QUERY_URL+"/{}".format(key),
                                                             auth=(self.username,
                                                                   self.password),
                                                             data={'follow':''})
                                if not result.ok:
                                    result.raise_for_status()
                                print("Deleted job: {} (Table: {})".format(key,self.table_dict[key]))
            if not regex:
                for key in self.job_dict.keys():
                    if self.job_dict[key] in phase:
                        result = self.session.delete(CosmoSim.QUERY_URL+"/{}".format(key),
                                                     auth=(self.username,
                                                           self.password),
                                                     data={'follow':''})
                        if not result.ok:
                            result.raise_for_status()
                        print("Deleted job: {}".format(key))

        if not phase:
            if regex:
                for key in self.job_dict.keys():
                    if key in self.table_dict.keys():
                        if self.table_dict[key] in matching_tables:
                            result = self.session.delete(CosmoSim.QUERY_URL+"/{}".format(key),
                                                         auth=(self.username,
                                                               self.password),
                                                         data={'follow':''})
                            if not result.ok:
                                result.raise_for_status()
                            print("Deleted job: {} (Table: {})".format(key,self.table_dict[key]))
            if not regex:
                for key in self.job_dict.keys():
                    result = self.session.delete(CosmoSim.QUERY_URL+"/{}".format(key),
                                                 auth=(self.username,
                                                       self.password),
                                                 data={'follow':''})
                    if not result.ok:
                        result.raise_for_status()
                    print("Deleted job: {}".format(key))

        self._existing_tables()
        return 

    def _generate_schema(self):
        """
        Internal function which builds a schema of all simulations within
        the database (in the form of a dictionary).
        """

        response = self._request('GET', CosmoSim.SCHEMA_URL,
                                 auth=(self.username,self.password),
                                 headers={'Accept': 'application/json'},
                                 cache=False)
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
        A public function which allows for the exploration of any simulation and
        its tables within the database. This function is meant to aid the user in
        constructing sql queries.
        
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
        
        if db:
            if table:
                if col:
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

    def download(self,jobid=None,filename=None,format=None,cache=True):
        """
        A public function to download data from a job with COMPLETED phase.

        Parameters
        ----------
        jobid :
            Completed jobid to be downloaded
        filename : string
            If left blank, downloaded to the terminal. If specified, data is written out to file (directory can be included here).

        Returns
        -------
        headers, data : list, list
        """

        if not jobid:
            try:
                jobid = self.current_job
            except:
                raise
                   
        self.check_all_jobs()
        completed_job_responses = self.completed_job_info(jobid)
        soup = BeautifulSoup(completed_job_responses[0].content)
        tableurl = soup.find("uws:result").get("xlink:href")
        
        # This is where the request.content parsing happens
        raw_table_data = self._request('GET', tableurl, auth=(self.username,
                                                              self.password),cache=cache)
        raw_headers = raw_table_data.content.split('\n')[0]
        num_cols = len(raw_headers.split(','))
        num_rows = len(raw_table_data.content.split('\n'))-2
        headers = [raw_headers.split(',')[i].strip('"') for i in range(num_cols)]
        raw_data = [raw_table_data.content.split('\n')[i+1].split(",") for i in range(num_rows)]
        data = [map(eval,raw_data[i]) for i in range(num_rows)]

        if format:
            tbl = Table(data=map(list, zip(*data)),names=headers)
            if format in ['VOTable','votable']:
                votbl = votable.from_table(tbl)
                if not filename:
                    return votbl
                else:
                    if '.xml' in filename:
                        filename = filename.split('.')[0]
                    votable.writeto(votbl, "{}.xml".format(filename))
                    print("Data written to file: {}.xml".format(filename))
            elif format in ['FITS','fits']:
                print("Need to implement...")

        else:
            if not filename:
                return headers, data
            else:
                with open(filename, 'wb') as fh:
                    raw_table_data = self._request('GET', tableurl,
                                                   auth=(self.username,
                                                         self.password),
                                                   stream=True,cache=cache)
                    for block in raw_table_data.iter_content(1024):
                        if not block:
                            break
                        fh.write(block)
                    print("Data written to file: {}".format(filename))
                return headers, data

    def _check_phase(self,jobid):
        """
        A private function which checks the job phase of a query.
        
        Parameters
        ----------
        jobid : string
            The jobid of the sql query.
        """
        
        self._existing_tables()

        time.sleep(1)

        if jobid not in self.job_dict.keys():
            logging.error("Job not present in job dictionary.")
            return 

        else:
            phase = self.job_dict['{}'.format(jobid)]
            return phase

    def _mail(self,to,subject,text,*attach):
        """
        A private function which sends an SMS message to an email address.
        
        Parameters
        ----------
        to : string
            The email address receiving the job alert.
        subject : string
            The subject of the job alert.
        text : string
            The content of the job alert.
        """
        
        msg = MIMEMultipart()
        msg['From']=self._smsaddress
        msg['To']=to
        msg['Subject']=subject
        msg.attach(MIMEText(text))
        n=len(attach)
        for i in range(n):
            part = MIMEBase('application','octet-stream')    
            part.set_payload(open(attach[i],'rb').read())
            message.email.Encoders.encode_base64(part)
            part.add_header('Content-Disposition','attachment; filename="%s"' % os.path.basename(attach[i]))    
            msg.attach(part)
        mailServer=smtplib.SMTP('smtp.gmail.com',587)
        mailServer.ehlo()
        mailServer.starttls()
        mailServer.ehlo()
        mailServer.login(self._smsaddress, self._smspw)
        mailServer.sendmail(self._smsaddress, to, msg.as_string())
        mailServer.quit()

    def _text(self,fromwhom,number,text):
        """
        A private function which sends an SMS message to a cell phone number.
        
        Parameters
        ----------
        fromwhom : string
            The email address sending the alert: "donotreply.astroquery.cosmosim@gmail.com"
        number : string
            The user-provided cell phone receiving the job alert.
        text : string
            The content of the job alert.
        """

        server = smtplib.SMTP( "smtp.gmail.com", 587 )
        server.starttls()
        server.login(self._smsaddress, self._smspw)
        server.sendmail( '{}'.format(fromwhom), '{}@vtext.com'.format(number), '{}'.format(text) )
        server.quit()

    def _initialize_alerting(self,jobid,mail=None,text=None):
        """
        A private function which initializes the email/text alert service credentials.
        Also preemptively checks for job phase being COMPLETED, ABORTED, or ERROR so that
        users don't simply send alerts for old jobs.
        
        Parameters
        ----------
        jobid : string
            The jobid of the sql query.
        mail : string
            The user-provided email address receiving the job alert.
        text : string
            The user-provided cell phone receiving the job alert.
        """
        
        self._smsaddress = "donotreply.astroquery.cosmosim@gmail.com"
        password_from_keyring = keyring.get_password("astroquery:cosmosim.SMSAlert", self._smsaddress)

        if password_from_keyring:
            self._smspw = password_from_keyring
            
        if not password_from_keyring:
            logging.warning("CosmoSim SMS alerting has not been initialized.")
            print("Initializing SMS alerting.")
            keyring.set_password("astroquery:cosmosim.SMSAlert", self._smsaddress,"LambdaCDM")

            
        self.alert_email = mail
        self.alert_text = text

        # first check to see if the job has errored (or is a job that has already completed) before running on a loop
        phase = self._check_phase(jobid)
        if phase in ['COMPLETED','ABORTED','ERROR']:
            print("JobID {} has finished with status {}.".format(jobid,phase))
            self.alert_completed = True
        elif phase in ['EXECUTING','PENDING','QUEUED']:
            self.alert_completed = False
        else:
            self.alert_completed = False
        

    def _alert(self,jobid,queue='short'):
        """
        A private function which runs checks for job completion every 10 seconds for
        short-queue jobs and 60 seconds for long-queue jobs. Once job phase is COMPLETED,
        ERROR, or ABORTED, emails and/or texts the results of the query to the user.
        
        Parameters
        ----------
        jobid : string
            The jobid of the sql query.
        queue : string
            The short/long queue option. Default is short.
        """
        
        if queue == 'long':
            deltat = 60
        else:
            deltat = 10
            
        while self.alert_completed is False:

            phase = self._check_phase(jobid)

            if phase in ['COMPLETED','ABORTED','ERROR']:
                print("JobID {} has finished with status {}.".format(jobid,phase))
                self.alert_completed = True
                resp = self.general_job_info(jobid)

                if self.alert_email:
                    self._mail(self.alert_email,"Job {} Completed with phase {}.".format(jobid,phase),"{}".format(resp[0].content))

                if self.alert_text:
                    self._text(self._smsaddress,self.alert_text,"Job {} Completed with phase {}.".format(jobid,phase))

            time.sleep(deltat)

CosmoSim = CosmoSimClass()
