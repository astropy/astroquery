# Licensed under a 3-clause BSD style license - see LICENSE.rst


import requests
import warnings
import numpy as np
import sys
from bs4 import BeautifulSoup
import keyring
import time
import smtplib
import re
import os
import threading
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase, message
from email.mime.text import MIMEText

# Astropy imports
from astropy.table import Table
import astropy.io.votable as votable
from astroquery import log

# Astroquery imports
from ..query import QueryWithLogin
from . import conf
from ..exceptions import LoginError

conf.max_lines = -1
conf.max_width = -1

__all__ = ['CosmoSim']


class CosmoSimClass(QueryWithLogin):

    QUERY_URL = conf.query_url
    SCHEMA_URL = conf.schema_url
    TIMEOUT = conf.timeout
    USERNAME = conf.username

    def __init__(self):
        super().__init__()

    def _login(self, username=None, password=None, store_password=False,
               reenter_password=False):
        """
        Login to the CosmoSim database.

        Parameters
        ----------
        username : str, optional
            Username to the CosmoSim database. If not given, it should be
            specified in the config file.
        store_password : bool, optional
            Stores the password securely in your keyring. Default is False.
        reenter_password : bool, optional
            Asks for the password even if it is already stored in the
            keyring. This is the way to overwrite an already stored passwork
            on the keyring. Default is False.
        """
        if username is None:
            if self.USERNAME == "":
                raise LoginError("If you do not pass a username to login(), "
                                 "you should configure a default one!")
            else:
                username = self.USERNAME

        # login after logging out (interactive)
        if not hasattr(self, 'session'):
            self.session = requests.session()

        # login after login (interactive)
        if hasattr(self, 'username'):
            log.warning("Attempting to login while another user ({0}) "
                        "is already logged in.".format(self.username))
            self.check_login_status()
            return

        self.username = username

        # Get password from keyring or prompt
        self.password, password_from_keyring = self._get_password(
            "astroquery:www.cosmosim.org", username, reenter=reenter_password)

        # Authenticate
        warnings.warn("Authenticating {0} on www.cosmosim.org..."
                      .format(self.username))
        authenticated = self._request('POST', CosmoSim.QUERY_URL,
                                      auth=(self.username, self.password),
                                      cache=False)
        if authenticated.status_code == 200:
            warnings.warn("Authentication successful!")
        elif (authenticated.status_code == 401
              or authenticated.status_code == 403):
            warnings.warn("Authentication failed!")
        elif authenticated.status_code == 503:
            warnings.warn("Service Temporarily Unavailable...")

        # Generating dictionary of existing tables
        self._existing_tables()

        if (authenticated.status_code == 200
                and password_from_keyring is None and store_password):
            keyring.set_password("astroquery:www.cosmosim.org",
                                 self.username, self.password)

        # Delete job; prevent them from piling up with phase PENDING
        if authenticated.status_code == 200:
            soup = BeautifulSoup(authenticated.content, "lxml")
            self.delete_job(jobid=str(soup.find("uws:jobref")["id"]),
                            squash=True)

        return authenticated

    def logout(self, deletepw=False):
        """
        Public function which allows the user to logout of their cosmosim
        credentials.

        Parameters
        ----------
        deletepw : bool
            A hard logout - delete the password to the associated username
            from the keychain. The default is True.

        Returns
        -------
        """

        if (hasattr(self, 'username') and hasattr(self, 'password')
                and hasattr(self, 'session')):
            if deletepw is True:
                try:
                    keyring.delete_password("astroquery:www.cosmosim.org",
                                            self.username)
                    warnings.warn("Removed password for {0} in the keychain."
                                  .format(self.username))
                except keyring.errors.PasswordDeleteError:
                    warnings.warn("Password for {0} was never stored in the "
                                  "keychain.".format(self.username))

            del self.session
            del self.username
            del self.password
        else:
            log.error("You must log in before attempting to logout.")

    def check_login_status(self):
        """
        Public function which checks the status of a user login attempt.
        """

        if (hasattr(self, 'username') and hasattr(self, 'password')
                and hasattr(self, 'session')):
            authenticated = self._request('POST', CosmoSim.QUERY_URL,
                                          auth=(self.username, self.password),
                                          cache=False)
            if authenticated.status_code == 200:
                warnings.warn("Status: You are logged in as {0}."
                              .format(self.username))
                soup = BeautifulSoup(authenticated.content, "lxml")
                self.delete_job(jobid=str(soup.find("uws:jobref")["id"]),
                                squash=True)
            else:
                warnings.warn("Status: The username/password combination "
                              "for {0} appears to be incorrect."
                              .format(self.username))
                warnings.warn("Please re-attempt to login with your cosmosim "
                              "credentials.")
        else:
            warnings.warn("Status: You are not logged in.")

    def run_sql_query(self, query_string, tablename=None, queue=None,
                      mail=None, text=None, cache=True):
        """
        Public function which sends a POST request containing the sql query
        string.

        Parameters
        ----------
        query_string : string
            The sql query to be sent to the CosmoSim.org server.
        tablename : string
            The name of the table for which the query data will be stored
            under. If left blank or if it already exists, one will be
            generated automatically.
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
                                   auth=(self.username, self.password),
                                   data={'query': query_string, 'phase': 'run',
                                         'queue': queue},
                                   cache=cache)
            soup = BeautifulSoup(result.content, "lxml")
            phase = soup.find("uws:phase").string
            if phase in ['ERROR']:
                warnings.warn("No table was generated for job with phase "
                              "`{0}`".format(phase))
                gen_tablename = "{0}".format(phase)
            else:
                gen_tablename = str(soup.find(id="table").string)
            log.warning("Table name {0} is already taken."
                        .format(tablename))
            warnings.warn("Generated table name: {0}".format(gen_tablename))
        elif tablename is None:
            result = self._request('POST', CosmoSim.QUERY_URL,
                                   auth=(self.username, self.password),
                                   data={'query': query_string, 'phase': 'run',
                                         'queue': queue},
                                   cache=cache)
        else:
            result = self._request('POST', CosmoSim.QUERY_URL,
                                   auth=(self.username, self.password),
                                   data={'query': query_string,
                                         'table': str(tablename),
                                         'phase': 'run', 'queue': queue},
                                   cache=cache)
            self._existing_tables()

        soup = BeautifulSoup(result.content, "lxml")
        self.current_job = str(soup.find("uws:jobref")["id"])
        warnings.warn("Job created: {}".format(self.current_job))

        if mail or text:
            self._initialize_alerting(self.current_job, mail=mail, text=text)

        return self.current_job

    def _existing_tables(self):
        """
        Internal function which builds a dictionary of the tables already in
        use for a given set of user credentials. Keys are jobids and values
        are the tables which are stored under those keys.
        """
        checkalljobs = self.check_all_jobs()
        completed_jobs = [key for key in self.job_dict.keys()
                          if self.job_dict[key] in ['COMPLETED', 'EXECUTING']]
        soup = BeautifulSoup(checkalljobs.content, "lxml")
        self.table_dict = {}

        for tag in soup.find_all({"uws:jobref"}):
            jobid = tag.get('xlink:href').split('/')[-1]
            if jobid in completed_jobs:
                self.table_dict[jobid] = str(tag.get('id'))

    def check_job_status(self, jobid=None):
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
        result : content of `~requests.Response` object
            The requests response phase
        """

        if jobid is None:
            if hasattr(self, 'current_job'):
                jobid = self.current_job
            else:
                jobid = self.current_job

        response = self._request(
            'GET', CosmoSim.QUERY_URL + '/{}'.format(jobid) + '/phase',
            auth=(self.username, self.password), data={'print': 'b'},
            cache=False)

        log.info("Job {}: {}".format(jobid, response.content))
        return response.content

    def check_all_jobs(self, phase=None, regex=None, sortby=None):
        """
        Public function which builds a dictionary whose keys are each jobid
        for a given set of user credentials and whose values are the phase
        status (e.g. - EXECUTING,COMPLETED,PENDING,ERROR).

        Parameters
        ----------
        phase : list
            A list of phase(s) of jobs to be checked on. If nothing
            provided, all are checked.
        regex : string
            A regular expression to match all tablenames to. Matching table
            names will be included.  Note - Only tables/starttimes are
            associated with jobs which have phase COMPLETED.
        sortby : string
            An option to sort jobs (after phase and regex criteria have been
            taken into account) by either the execution start time
            (``starttime``), or by the table name (``'tablename'``).

        Returns
        -------
        checkalljobs : `~requests.Response` object
            The requests response for the GET request for finding all
            existing jobs.
        """
        checkalljobs = self._request('GET', CosmoSim.QUERY_URL,
                                     auth=(self.username, self.password),
                                     params={'print': 'b'}, cache=False)

        self.job_dict = {}
        soup = BeautifulSoup(checkalljobs.content, "lxml")

        for tag in soup.find_all({"uws:jobref"}):
            tag_phase = str(tag.find('uws:phase').string)
            if tag_phase in ['COMPLETED', 'EXECUTING', 'ABORTED', 'ERROR']:
                self.job_dict['{0}'.format(tag.get('xlink:href')
                                           .split('/')[-1])] = tag_phase
            else:
                self.job_dict[str(tag.get('id'))] = tag_phase

        if phase:
            phase = [phase[i].upper() for i in range(len(phase))]

        if regex:
            pattern = re.compile("{}".format(regex))
            try:
                groups = [pattern.match(self.table_dict.values()[i]).group()
                          for i in range(len(self.table_dict.values()))
                          if pattern.match(self.table_dict.values()[i])
                          is not None]
                matching_tables = [groups[i]
                                   for i in range(len(groups))
                                   if groups[i] in self.table_dict.values()]
            except AttributeError:
                warnings.warn('No tables matching the regular expression '
                              '`{0}` were found.'.format(regex))
                matching_tables = self.table_dict.values()

            if phase:
                if "COMPLETED" not in phase:
                    warnings.warn("No jobs with phase `{0}` matching "
                                  "the regular expression `{1}` were found.\n"
                                  "Matching regular expression `{1}` to all "
                                  "jobs with phase `COMPLETED` instead "
                                  "(unsorted):".format(phase, regex))
                else:
                    matching_tables = [[self.table_dict[i]
                                        for i in self.table_dict.keys()
                                        if self.table_dict[i] == miter
                                        and self.job_dict[i] in phase][0]
                                       for miter in matching_tables]
            self._existing_tables()  # creates a fresh up-to-date table_dict

        self._starttime_dict()

        if not sortby:
            if regex:
                matching = zip(*[[(i, self.job_dict[i], self.starttime_dict[i])
                                  for i in self.table_dict.keys()
                                  if self.table_dict[i] == miter][0]
                                 for miter in matching_tables])
                (matching_jobids, matching_phases,
                 matching_starttimes) = matching
        if sortby:
            if sortby.upper() == "TABLENAME":
                if 'matching_tables' not in locals():
                    matching_tables = sorted(self.table_dict.values())
                else:
                    matching_tables = sorted(matching_tables)
                matching = zip(*[[(i, self.job_dict[i], self.starttime_dict[i])
                                  for i in self.table_dict.keys()
                                  if self.table_dict[i] == miter][0]
                                 for miter in matching_tables])
                (matching_jobids, matching_phases,
                 matching_starttimes) = matching

            elif sortby.upper() == 'STARTTIME':
                if 'matching_tables' not in locals():
                    matching_starttimes = sorted(self.starttime_dict.values())
                    matching = zip(*[[(i, self.job_dict[i], self.table_dict[i])
                                      for i in self.starttime_dict.keys()
                                      if self.starttime_dict[i] == miter][0]
                                     for miter in matching_starttimes])
                    (matching_jobids, matching_phases,
                     matching_tables) = matching
                else:
                    matching_starttimes = [[self.starttime_dict[i]
                                            for i in self.table_dict.keys()
                                            if self.table_dict[i] == miter][0]
                                           for miter in matching_tables]
                    matching = zip(*[[(i, self.job_dict[i], self.table_dict[i])
                                      for i in self.starttime_dict.keys()
                                      if self.starttime_dict[i] == miter][0]
                                     for miter in matching_starttimes])
                    (matching_jobids, matching_phases,
                     matching_tables) = matching

        frame = sys._getframe(1)

        # list of methods which use check_all_jobs() for which I would not
        # like job_dict to be printed to the terminal
        do_not_print_job_dict = ['completed_job_info', 'general_job_info',
                                 'delete_all_jobs', '_existing_tables',
                                 'delete_job', 'download']

        if frame.f_code.co_name in do_not_print_job_dict:
            return checkalljobs
        else:
            if not phase and not regex:
                if not sortby:
                    t = Table()
                    t['JobID'] = list(self.job_dict.keys())
                    t['Phase'] = list(self.job_dict.values())
                    t.pprint()
                else:
                    if sortby.upper() == 'TABLENAME':
                        t = Table()
                        t['Tablename'] = matching_tables
                        t['Starttime'] = matching_starttimes
                        t['JobID'] = matching_jobids
                        t['Phase'] = matching_phases
                        t.pprint()
                    if sortby.upper() == 'STARTTIME':
                        t = Table()
                        t['Starttime'] = matching_starttimes
                        t['Tablename'] = matching_tables
                        t['JobID'] = matching_jobids
                        t['Phase'] = matching_phases
                        t.pprint()

            elif not phase and regex:
                t = Table()
                if sortby:
                    if sortby.upper() == 'STARTTIME':
                        t['Starttime'] = matching_starttimes
                        t['Tablename'] = matching_tables
                    if sortby.upper() == 'TABLENAME':
                        t['Tablename'] = matching_tables
                        t['Starttime'] = matching_starttimes
                if not sortby:
                    t['Tablename'] = matching_tables
                    t['Starttime'] = matching_starttimes
                t['JobID'] = matching_jobids
                t['Phase'] = matching_phases
                t.pprint()

            if phase and not regex:
                if len(phase) == 1 and "COMPLETED" in phase:
                    if not sortby:
                        matching_jobids = [key
                                           for key in self.job_dict.keys()
                                           if self.job_dict[key] in phase]
                        matching = zip(*[[(self.table_dict[i],
                                           self.job_dict[i],
                                           self.starttime_dict[i])
                                          for i in self.table_dict.keys()
                                          if i == miter][0]
                                         for miter in matching_jobids])
                        (matching_tables, matching_phases,
                         matching_starttimes) = matching

                    t = Table()
                    t['JobID'] = matching_jobids
                    t['Phase'] = matching_phases
                    t['Tablename'] = matching_tables
                    t['Starttime'] = matching_starttimes

                    if sortby:
                        if sortby.upper() == 'TABLENAME':
                            t['Tablename',
                              'Starttime', 'JobID', 'Phase'].pprint()
                        if sortby.upper() == 'STARTTIME':
                            t['Starttime',
                              'Tablename', 'JobID', 'Phase'].pprint()
                    else:
                        t.pprint()

                else:
                    if sortby:
                        warnings.warn('Sorting can only be applied to jobs '
                                      'with phase `COMPLETED`.')
                    if not sortby:
                        matching_jobids = [key
                                           for key in self.job_dict.keys()
                                           if self.job_dict[key] in phase]
                        matching_phases = [self.job_dict[key]
                                           for key in self.job_dict.keys()
                                           if self.job_dict[key] in phase]
                        t = Table()
                        t['JobID'] = matching_jobids
                        t['Phase'] = matching_phases
                        t.pprint()

            if phase and regex:
                t = Table()
                t['Tablename'] = matching_tables
                t['Starttime'] = matching_starttimes
                t['JobID'] = matching_jobids
                t['Phase'] = matching_phases

                if sortby:
                    if sortby.upper() == 'TABLENAME':
                        t.pprint()
                    if sortby.upper() == 'STARTTIME':
                        t['Starttime', 'Tablename', 'JobID', 'Phase'].pprint()
                else:
                    t.pprint()

            return checkalljobs

    def completed_job_info(self, jobid=None, output=False):
        """
        A public function which sends an http GET request for a given
        jobid with phase COMPLETED. If output is True, the function prints
        a dictionary to the screen, while always generating a global
        dictionary ``response_dict_current``. If no jobid is provided,
        a visual of all responses with phase COMPLETED is generated.

        Parameters
        ----------
        jobid : string
            The jobid of the sql query.
        output : bool
            Print output of response(s) to the terminal
        """

        self.check_all_jobs()

        if jobid is None:
            completed_jobids = [key for key in self.job_dict.keys()
                                if self.job_dict[key] == 'COMPLETED']
            response_list = [
                self._request(
                    'GET',
                    CosmoSim.QUERY_URL + "/{}".format(completed_jobids[i]),
                    auth=(self.username, self.password), cache=False)
                for i in range(len(completed_jobids))]
            self.response_dict_current = {}
            for i, vals in enumerate(completed_jobids):
                self.response_dict_current[vals] = (
                    self._generate_response_dict(response_list[i]))
        else:
            if self.job_dict[jobid] == 'COMPLETED':
                response_list = [
                    self._request(
                        'GET', CosmoSim.QUERY_URL + "/{}".format(jobid),
                        auth=(self.username, self.password), cache=False)]
                self.response_dict_current = {}
                self.response_dict_current[jobid] = (
                    self._generate_response_dict(response_list[0]))
            else:
                warnings.warn("JobID must refer to a query with a phase "
                              "of 'COMPLETED'.")
                return

        if output is True:
            dictkeys = self.response_dict_current.keys()
            if len(dictkeys) > 1:
                keys = [i for i in self.response_dict_current.keys()]
                phases = [self.job_dict[key] for key in keys]
                t = Table()
                t['JobID'] = keys
                t['Phase'] = phases
                t.pprint()
                warnings.warn("Use specific jobid to get more information, or "
                              "explore `self.response_dict_current`.")
            elif len(dictkeys) == 1:
                print(self.response_dict_current[dictkeys[0]]['content'])
            else:
                log.error('No completed jobs found.')
            return
        else:
            return

    def _generate_response_dict(self, response):
        """
        A private function which takes in a response object and creates a
        response dictionary.

        Parameters
        ----------
        response : `~requests.Response`
            requests response object

        Returns
        -------
        response_dict : dict
            A dictionary of some of the response object's methods
        """

        R = response
        response_dict = {'content': R.content,
                         'cookies': R.cookies,
                         'elapsed': R.elapsed,
                         'encoding': R.encoding,
                         'headers': R.headers,
                         'ok': R.ok,
                         'request': R.request,
                         'url': R.url}

        return response_dict

    def _starttime_dict(self):
        """
        A private function which generates a dictionary of jobids (must have
        phase COMPLETED) linked to starttimes.
        """

        completed_ids = [key
                         for key in self.job_dict.keys()
                         if self.job_dict[key] == 'COMPLETED']
        response_list = [self._request('GET',
                                       CosmoSim.QUERY_URL + "/{}".format(i),
                                       auth=(self.username, self.password),
                                       cache=False)
                         for i in completed_ids]
        soups = [BeautifulSoup(response_list[i].content, "lxml")
                 for i in range(len(response_list))]
        self.starttime_dict = {}
        for i in range(len(soups)):
            self.starttime_dict[str(completed_ids[i])] = str(
                soups[i].find('uws:starttime').string)

    def general_job_info(self, jobid=None, output=False):
        """
        A public function which sends an http GET request for a given
        jobid in any phase. If no jobid is provided, a summary of all
        jobs is generated.

        Parameters
        ----------
        jobid : string
            The jobid of the sql query.
        output : bool
            Print output of response(s) to the terminal
        """

        self.check_all_jobs()

        if jobid is None:
            print("Job Summary:\n"
                  "There are {0} jobs with phase: COMPLETED.\n"
                  "There are {1} jobs with phase: ERROR.\n"
                  "There are {2} jobs with phase: ABORTED.\n"
                  "There are {3} jobs with phase: PENDING.\n"
                  "There are {4} jobs with phase: EXECUTING.\n"
                  "There are {5} jobs with phase: QUEUED.\n"
                  "Try providing a jobid for the job you'd like to "
                  "know more about.\n To see a list of all jobs, use "
                  "`check_all_jobs()`."
                  .format(self.job_dict.values().count('COMPLETED'),
                          self.job_dict.values().count('ERROR'),
                          self.job_dict.values().count('ABORTED'),
                          self.job_dict.values().count('PENDING'),
                          self.job_dict.values().count('EXECUTING'),
                          self.job_dict.values().count('QUEUED')))
            return
        else:
            response_list = [self._request(
                'GET', CosmoSim.QUERY_URL + "/{}".format(jobid),
                auth=(self.username, self.password), cache=False)]

            if response_list[0].ok is False:
                log.error('Must provide a valid jobid.')
                return
            else:
                self.response_dict_current = {}
                self.response_dict_current[jobid] = (
                    self._generate_response_dict(response_list[0]))

        if output is True:
            dictkeys = self.response_dict_current.keys()
            print(self.response_dict_current[dictkeys[0]]['content'])
            return
        else:
            return

    def delete_job(self, jobid=None, squash=None):
        """
        A public function which deletes a stored job from the server in any
        phase.  If no jobid is given, it attempts to use the most recent job
        (if it exists in this session). If jobid is specified, then it
        deletes the corresponding job, and if it happens to match the
        existing current job, that variable gets deleted.

        Parameters
        ----------
        jobid : string
            The jobid of the sql query. If no jobid is given, it attempts to
            use the most recent job (if it exists in this session).
        output : bool
            Print output of response(s) to the terminal

        Returns
        -------
        result : list
            A list of response object(s)

        """

        self.check_all_jobs()

        if jobid is None:
            if hasattr(self, 'current_job'):
                jobid = self.current_job

        if jobid:
            if hasattr(self, 'current_job'):
                if jobid == self.current_job:
                    del self.current_job

        if self.job_dict[jobid] in ['COMPLETED', 'ERROR',
                                    'ABORTED', 'PENDING']:
            result = self.session.delete(
                CosmoSim.QUERY_URL + "/{}".format(jobid),
                auth=(self.username, self.password), data={'follow': ''})

        else:
            warnings.warn("Can only delete a job with phase: "
                          "'COMPLETED', 'ERROR', 'ABORTED', or 'PENDING'.")
            return

        if not result.ok:
            result.raise_for_status()
        if squash is None:
            warnings.warn('Deleted job: {}'.format(jobid))

        return result

    def abort_job(self, jobid=None):
        """
        """

        self.check_all_jobs()

    def delete_all_jobs(self, phase=None, regex=None):
        """
        A public function which deletes any/all jobs from the server in any
        phase and/or with its tablename matching any desired regular
        expression.

        Parameters
        ----------
        phase : list
            A list of job phases to be deleted. If nothing provided, all are
            deleted.
        regex : string
            A regular expression to match all tablenames to. Matching table
            names will be deleted.
        """

        self.check_all_jobs()

        if regex:
            pattern = re.compile("{}".format(regex))
            groups = [pattern.match(self.table_dict.values()[i]).group()
                      for i in range(len(self.table_dict.values()))]
            matching_tables = [groups[i] for i in range(len(groups))
                               if groups[i] in self.table_dict.values()]

        if phase:
            phase = [phase[i].upper() for i in range(len(phase))]
            if regex:
                for key in self.job_dict.keys():
                    if self.job_dict[key] in phase:
                        if key in self.table_dict.keys():
                            if self.table_dict[key] in matching_tables:
                                result = self.session.delete(
                                    CosmoSim.QUERY_URL + "/{}".format(key),
                                    auth=(self.username, self.password),
                                    data={'follow': ''})
                                if not result.ok:
                                    result.raise_for_status()
                                warnings.warn("Deleted job: {0} (Table: {1})"
                                              .format(key,
                                                      self.table_dict[key]))
            if not regex:
                for key in self.job_dict.keys():
                    if self.job_dict[key] in phase:
                        result = self.session.delete(
                            CosmoSim.QUERY_URL + "/{}".format(key),
                            auth=(self.username, self.password),
                            data={'follow': ''})
                        if not result.ok:
                            result.raise_for_status()
                        warnings.warn("Deleted job: {}".format(key))

        if not phase:
            if regex:
                for key in self.job_dict.keys():
                    if key in self.table_dict.keys():
                        if self.table_dict[key] in matching_tables:
                            result = self.session.delete(
                                CosmoSim.QUERY_URL + "/{}".format(key),
                                auth=(self.username, self.password),
                                data={'follow': ''})
                            if not result.ok:
                                result.raise_for_status()
                            warnings.warn("Deleted job: {0} (Table: {1})"
                                          .format(key, self.table_dict[key]))
            if not regex:
                for key in self.job_dict.keys():
                    result = self.session.delete(
                        CosmoSim.QUERY_URL + "/{}".format(key),
                        auth=(self.username, self.password),
                        data={'follow': ''})
                    if not result.ok:
                        result.raise_for_status()
                    warnings.warn("Deleted job: {}".format(key))

        self._existing_tables()
        return

    def _generate_schema(self):
        """
        Internal function which builds a schema of all simulations within
        the database (in the form of a dictionary).
        """

        response = self._request('GET', CosmoSim.SCHEMA_URL,
                                 auth=(self.username, self.password),
                                 headers={'Accept': 'application/json'},
                                 cache=False)
        data = response.json()
        self.db_dict = {}
        for i in range(len(data['databases'])):
            self.db_dict[str(data['databases'][i]['name'])] = {}

            sstr = str(data['databases'][i]['name'])
            sid = str(data['databases'][i]['id'])
            self.db_dict[sstr]['id'] = sid
            sdesc = str(data['databases'][i]['description'])
            self.db_dict[sstr]['description'] = sdesc
            self.db_dict[sstr]['tables'] = {}
            for j in range(len(data['databases'][i]['tables'])):
                sstr2 = str(data['databases'][i]['tables'][j]['name'])
                self.db_dict[sstr]['tables'][sstr2] = {}
                sdata = data['databases'][i]['tables'][j]['id']
                self.db_dict[sstr]['tables'][sstr2]['id'] = sdata
                sdesc2 = data['databases'][i]['tables'][j]['description']
                self.db_dict[sstr]['tables'][sstr2]['description'] = sdesc2
                self.db_dict[sstr]['tables'][sstr2]['columns'] = {}
                tmpval = len(data['databases'][i]['tables'][j]['columns'])
                for k in range(tmpval):
                    sdata2 = data['databases'][i]['tables'][j]['columns'][k]
                    sdata2_id = sdata2['id']
                    sstr3 = str(sdata2['name'])

                    sdesc3 = sdata2['description']
                    self.db_dict[sstr]['tables'][sstr2]['columns'][sstr3] = {
                        'id': sdata2_id,
                        'description': sdesc3}
        return response

    def explore_db(self, db=None, table=None, col=None):
        """
        A public function which allows for the exploration of any simulation
        and its tables within the database. This function is meant to aid
        the user in constructing sql queries.

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

        projects = np.sort(list(self.db_dict.keys()))
        largest = max([len(projects[i]) for i in range(len(projects))])
        t = Table()
        # db not specified
        if not db:
            warnings.warn("Must first specify a database.")
            proj_list = []
            attr_list = []
            info_list = []
            tmp2_largest = 0
            for proj in projects:
                size = len((self.db_dict['{0}'.format(proj)].keys()))
                proj_list += (['@ {}'.format(proj)]
                              + ['' for i in range(size - 1)]
                              + ['-' * (largest + 2)])
                tmp_largest = max([len(str(key))
                                   for key in self.db_dict[proj].keys()])
                attr_list += (['@ {}'.format(key)
                              if isinstance(self.db_dict[proj][key], dict)
                              else '{}:'.format(key)
                              for key in self.db_dict[proj].keys()]
                              + ['-' * (tmp_largest + 2)])
                tmpinfosize = max([len(self.db_dict[proj][key])
                                   if isinstance(self.db_dict[proj][key], str)
                                   else 0
                                   for key in self.db_dict[proj].keys()])
                if tmpinfosize > tmp2_largest:
                    tmp2_largest = tmpinfosize
            for proj in projects:
                info_list += ([self.db_dict[proj][key]
                              if isinstance(self.db_dict[proj][key], str)
                              else ""
                              for key in self.db_dict[proj].keys()] + ['-' * tmp2_largest])
            t['Projects'] = proj_list
            t['Project Items'] = attr_list
            t['Information'] = info_list
            t.pprint()
        # db specified
        if db:
            try:
                size1 = len(list(self.db_dict[str(db)].keys()))
                slist = [list(self.db_dict[db][key].keys())
                         if isinstance(self.db_dict[db][key], dict)
                         else key
                         for key in self.db_dict[db].keys()]
                size2 = len(max(slist, key=np.size))
            except (KeyError, NameError):
                log.error("Must first specify a valid database.")
                return
            # if col is specified, table must be specified, and I need to
            # check the max size of any given column in the structure
            if table:
                try:
                    size2 = max(size2, len(list(self.db_dict[db]['tables']
                                           [table]['columns'].keys())))
                    if col:
                        try:
                            size2 = max(size2, len(list(self.db_dict[db]['tables']
                                                   [table]['columns']
                                                   [col].keys())))
                        except (KeyError, NameError):
                            log.error("Must first specify a valid column "
                                      "of the `{0}` table within the `{1}`"
                                      " db".format(table, db))
                            return
                except (KeyError, NameError):
                    log.error("Must first specify a valid table within "
                              "the `{0}` db.".format(db))
                    return

            t['Projects'] = (['--> @ {}:'.format(db)] + ['' for i in range(size2 - 1)])
            t['Project Items'] = (
                ['--> @ {}:'.format(key)
                 if (isinstance(self.db_dict[db][key], dict)
                     and (len(list(self.db_dict[db][key].keys()))
                          == len(list(self.db_dict[db]['tables'].keys()))))
                 else '@ {}'.format(key)
                 if (isinstance(self.db_dict[db][key], dict)
                     and (len(list(self.db_dict[db][key].keys()))
                          != len(self.db_dict[db]['tables'].keys())))
                 else str(key)
                 for key in self.db_dict[db].keys()] + ['' for i in range(size2 - size1)])
            # if only db is specified
            if not table:
                if not col:
                    reordered = sorted(max(slist, key=np.size), key=len)
                    t['Tables'] = ['@ {}'.format(i)
                                   if isinstance(self.db_dict[db]['tables'][i],
                                                 dict)
                                   else str(i)
                                   for i in reordered]
            # if table has been specified
            else:
                reordered = (
                    [str(table)]
                    + sorted([key for key in self.db_dict[db]['tables'].keys()
                              if key != table], key=len))
                t['Tables'] = (
                    ['--> @ {}:'.format(i)
                     if (i == table and isinstance(self.db_dict[db]['tables'][i], dict))
                     else '@ {}'.format(i)
                     if (i != table and isinstance(self.db_dict[db]['tables'][i], dict))
                     else str(i)
                     for i in reordered] + ['' for j in range(size2 - len(reordered))])

                # if column has been specified
                if col:
                    tblcols_dict = self.db_dict[db]['tables'][table].keys()
                    t['Table Items'] = (
                        ['--> @ columns:']
                        + [i for i in tblcols_dict if i != 'columns']
                        + ['' for j in range(size2 - len(tblcols_dict))])
                    col_dict = (self.db_dict[db]['tables'][table]
                                ['columns'].keys())
                    reordered = ([str(col)] + [i for i in col_dict if i != col])

                    temp_columns = []

                    columns = self.db_dict[db]['tables'][table]['columns']
                    for i in reordered:
                        c = columns[i]
                        if isinstance(c, dict) and i == col:
                            temp_columns.append('--> @ {}:'.format(i))
                        elif not isinstance(c, dict) and i == col:
                            temp_columns.append('--> {}:'.format(i))
                        elif isinstance(c, dict) and i != col:
                            temp_columns.append('@ {}'.format(i))
                        else:
                            temp_columns.append(str(i))

                    if len(col_dict) < size2:
                        size_diff = size2 - len(col_dict)
                        t['Columns'] = (temp_columns + ['' for j in range(size_diff)])

                        colinfo_dict = col_dict = columns[col]
                        t['Col. Info'] = (
                            ['{} : {}'.format(i, colinfo_dict[i])
                             for i in colinfo_dict.keys()] + ['' for j in range(size2 - len(colinfo_dict))])
                    else:
                        t['Columns'] = temp_columns

                # if column has not been specified
                else:
                    tblcols_dict = self.db_dict[db]['tables'][table].keys()
                    col_dict = (
                        self.db_dict[db]['tables'][table]['columns'].keys())
                    reordered = sorted(col_dict, key=len)
                    if len(tblcols_dict) < size2:
                        size_diff = size2 - len(tblcols_dict)
                        tmp_table = self.db_dict[db]['tables'][table]
                        t['Table Items'] = (
                            ['@ {}'.format(i) if isinstance(tmp_table[i], dict)
                             else '{}:'.format(i) for i in tblcols_dict] + ['' for i in range(size_diff)])
                        t['Table Info'] = (
                            [str(tmp_table[i])
                             if not isinstance(tmp_table[i], dict)
                             else '' for i in tblcols_dict] + ['' for i in range(size_diff)])
                        if len(col_dict) < size2:
                            t['Columns'] = (
                                ['@ {}'.format(i)
                                 if isinstance(tmp_table['columns'][i], dict)
                                 else str(i)
                                 for i in reordered] + ['' for i in range(size2 - len(col_dict))])
                        else:
                            t['Columns'] = reordered
                    else:
                        t['Table Items'] = tblcols_dict
            t.pprint()

    def download(self, jobid=None, filename=None, format=None, cache=True):
        """
        A public function to download data from a job with COMPLETED phase.

        Parameters
        ----------
        jobid :
            Completed jobid to be downloaded
        filename : str
            If left blank, downloaded to the terminal. If specified, data is
            written out to file (directory can be included here).
        format : str
            The format of the data to be downloaded. Options are ``'csv'``,
            ``'votable'``, ``'votableB1'``, and ``'votableB2'``.
        cache : bool
            Whether to cache the data. By default, this is set to True.

        Returns
        -------
        headers, data : list, list
        """

        self.check_all_jobs()

        if not jobid:
            try:
                jobid = self.current_job
            except AttributeError:
                warnings.warn("No current job has been defined for "
                              "this session.")
                return

        if self.job_dict[str(jobid)] == 'COMPLETED':
            if not format:
                warnings.warn("Must specify a format:")
                t = Table()
                t['Format'] = ['csv', 'votable', 'votableB1', 'votableB2']
                t['Description'] = ['Comma-separated values file',
                                    'Put In Description',
                                    'Put In Description',
                                    'Put In Description']
                t.pprint()
            if format:
                results = self._request(
                    'GET', self.QUERY_URL + "/{}/results".format(jobid),
                    auth=(self.username, self.password))
                soup = BeautifulSoup(results.content, "lxml")
                urls = [i.get('xlink:href')
                        for i in soup.find_all({'uws:result'})]
                formatlist = [urls[i].split('/')[-1].upper()
                              for i in range(len(urls))]

            if format.upper() in formatlist:
                index = formatlist.index(format.upper())
                downloadurl = urls[index]
                if filename:
                    self._download_file(downloadurl,
                                        local_filepath=filename,
                                        auth=(self.username, self.password))
                elif not filename:
                    if format.upper() == 'CSV':
                        raw_table_data = self._request(
                            'GET', downloadurl,
                            auth=(self.username, self.password),
                            cache=cache).content
                        raw_headers = raw_table_data.split('\n')[0]
                        num_cols = len(raw_headers.split(','))
                        num_rows = len(raw_table_data.split('\n')) - 2
                        headers = [raw_headers.split(',')[i].strip('"')
                                   for i in range(num_cols)]
                        raw_data = [
                            raw_table_data.split('\n')[i + 1].split(",")
                            for i in range(num_rows)]
                        data = [map(eval, raw_data[i])
                                for i in range(num_rows)]
                        return headers, data
                    elif format.upper() in ['VOTABLEB1', 'VOTABLEB2']:
                        warnings.warn("Cannot view binary versions of votable "
                                      "within the terminal.\n Try saving them "
                                      "to the disk with the 'filename' option")
                        return
                    elif format.upper() == 'VOTABLE':
                        # for terminal output, get data in csv format
                        tmp_downloadurl = urls[formatlist.index('CSV')]
                        raw_table_data = self._request(
                            'GET', tmp_downloadurl,
                            auth=(self.username, self.password),
                            cache=cache).content
                        raw_headers = raw_table_data.split('\n')[0]
                        num_cols = len(raw_headers.split(','))
                        num_rows = len(raw_table_data.split('\n')) - 2
                        headers = [raw_headers.split(',')[i].strip('"')
                                   for i in range(num_cols)]
                        raw_data = [
                            raw_table_data.split('\n')[i + 1].split(",")
                            for i in range(num_rows)]
                        data = [map(eval, raw_data[i])
                                for i in range(num_rows)]
                        # store in astropy.Table object
                        tbl = Table(data=map(list, zip(*data)), names=headers)
                        # convert to votable format
                        votbl = votable.from_table(tbl)
                        return votbl

            elif format.upper() not in formatlist:
                print('Format not recognized. Please see formatting options:')
                t = Table()
                t['Format'] = ['csv', 'votable', 'votableB1', 'votableB2']
                t['Description'] = ['Comma-Separated Values File',
                                    'IVOA VOTable Format',
                                    'IVOA VOTable Format, Binary 1',
                                    'IVOA VOTable Format, Binary 2']
                t.pprint()

    def _check_phase(self, jobid):
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
            log.error("Job not present in job dictionary.")
            return

        else:
            phase = self.job_dict[str(jobid)]
            return phase

    def _mail(self, to, subject, text, *attach):
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
        msg['From'] = self._smsaddress
        msg['To'] = to
        msg['Subject'] = subject
        msg.attach(MIMEText(text))
        n = len(attach)
        for i in range(n):
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(open(attach[i], 'rb').read())
            message.email.Encoders.encode_base64(part)
            part.add_header('Content-Disposition', 'attachment; filename="{0}"'
                            .format(os.path.basename(attach[i])))
            msg.attach(part)
        mailServer = smtplib.SMTP('smtp.gmail.com', 587)
        mailServer.ehlo()
        mailServer.starttls()
        mailServer.ehlo()
        mailServer.login(self._smsaddress, self._smspw)
        mailServer.sendmail(self._smsaddress, to, msg.as_string())
        mailServer.quit()

    def _text(self, fromwhom, number, text):
        """
        A private function which sends an SMS message to a cell phone number.

        Parameters
        ----------
        fromwhom : string
            The email address sending the alert:
            "donotreply.astroquery.cosmosim@gmail.com"
        number : string
            The user-provided cell phone receiving the job alert.
        text : string
            The content of the job alert.
        """

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(self._smsaddress, self._smspw)
        server.sendmail(str(fromwhom), '{}@vtext.com'.format(number),
                        str(text))
        server.quit()

    def _initialize_alerting(self, jobid, mail=None, text=None):
        """
        A private function which initializes the email/text alert service
        credentials.  Also preemptively checks for job phase being
        COMPLETED, ABORTED, or ERROR so that users don't simply send alerts
        for old jobs.

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
        password_from_keyring = keyring.get_password(
            "astroquery:cosmosim.SMSAlert", self._smsaddress)

        if password_from_keyring:
            self._smspw = password_from_keyring

        if not password_from_keyring:
            log.warning("CosmoSim SMS alerting has not been initialized.")
            warnings.warn("Initializing SMS alerting.")
            keyring.set_password("astroquery:cosmosim.SMSAlert",
                                 self._smsaddress, "LambdaCDM")

        self.alert_email = mail
        self.alert_text = text

        # first check to see if the job has errored (or is a job that has
        # already completed) before running on a loop
        phase = self._check_phase(jobid)
        if phase in ['COMPLETED', 'ABORTED', 'ERROR']:
            warnings.warn("JobID {0} has finished with status {1}."
                          .format(jobid, phase))
            self.alert_completed = True
        elif phase in ['EXECUTING', 'PENDING', 'QUEUED']:
            self.alert_completed = False
        else:
            self.alert_completed = False


class AlertThread:
    """ Alert threading class

    The _alert() method will be started and it will run in the background
    until the application exits.
    """

    def __init__(self, jobid, queue='short'):
        """
        Parameters
        ----------
        jobid : string
            The jobid of the sql query.
        queue : string
            The short/long queue option. Default is short.
        """
        self.jobid = jobid
        self.queue = queue

        thread = threading.Thread(target=self._alert, args=(self.jobid,
                                                            self.queue))
        thread.daemon = True                            # Daemonize thread
        thread.start()                                  # Start the execution

    def _alert(self, jobid, queue):
        """
        A private function which runs checks for job completion every 10
        seconds for short-queue jobs and 60 seconds for long-queue
        jobs. Once job phase is COMPLETED, ERROR, or ABORTED, emails and/or
        texts the results of the query to the user.

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
            if phase in ['COMPLETED', 'ABORTED', 'ERROR']:
                warnings.warn("JobID {0} has finished with status {1}."
                              .format(jobid, phase))
                self.alert_completed = True
                time.sleep(1)
                self.general_job_info(jobid)
                if self.alert_email:
                    self._mail(
                        self.alert_email, ("Job {0} Completed with phase {1}."
                                           .format(jobid, phase)),
                        "{}".format(
                            self.response_dict_current[jobid]['content']))

                if self.alert_text:
                    self._text(self._smsaddress,
                               self.alert_text,
                               ("Job {0} Completed with phase {1}."
                                .format(jobid, phase)))

            time.sleep(deltat)


CosmoSim = CosmoSimClass()
