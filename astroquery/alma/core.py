# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import print_function
import time
import sys
import os.path
import webbrowser
import getpass
import warnings
import keyring
import numpy as np
import re
from bs4 import BeautifulSoup

from astropy.extern.six import BytesIO
from astropy.extern import six
from astropy.table import Table, Column
from astropy import log
from astropy.utils.console import ProgressBar
from astropy import units as u
import astropy.io.votable as votable

from ..exceptions import LoginError, RemoteServiceError
from ..utils import schema, system_tools
from ..utils import commons
from ..utils.process_asyncs import async_to_sync
from ..query import BaseQuery, QueryWithLogin, suspend_cache
from . import conf

__doctest_skip__ = ['AlmaClass.*']


@async_to_sync
class AlmaClass(QueryWithLogin):

    TIMEOUT = conf.timeout
    archive_url = conf.archive_url

    def __init__(self):
        super(AlmaClass, self).__init__()

    def query_object_async(self, object_name, cache=True, public=True,
                           science=True):
        """
        Query the archive with a source name
        """

        payload = {'source_name_sesame': object_name,}

        return self.query_async(payload, cache=cache, public=public,
                                science=science)

    def query_region_async(self, coordinate, radius, cache=True, public=True,
                           science=True):
        """

        """
        coordinate = commons.parse_coordinates(coordinate)
        cstr = coordinate.fk5.to_string(style='hmsdms', sep=':')
        rdc = "{cstr}, {rad}".format(cstr=cstr, rad=radius.to(u.deg).value)

        payload = {'raDecCoordinates': rdc}

        return self.query_async(payload, cache=cache, public=public,
                                science=science)

    def query_async(self, payload, cache=True, public=True, science=True):
        """
        Perform a generic query with user-specified payload
        """
        url = os.path.join(self.archive_url, 'aq', 'search.votable')

        payload.update({'viewFormat':'raw',
                        'download':'true',})
        if public:
            payload['publicFilterFlag'] = 'public'
        if science:
            payload['scan_intent-asu'] = '=*TARGET*'

        response = self._request('GET', url, params=payload,
                                 timeout=self.TIMEOUT, cache=cache)

        return response

    def stage_data(self, uids, cache=False):
        """
        Stage ALMA data

        Parameters
        ----------
        uids : list
            A list of valid UIDs.
            UIDs should have the form: 'uid://A002/X391d0b/X7b'
        cache : bool
            Whether to cache the staging process.  This should generally be
            left as False when used interactively.

        Returns
        -------
        data_file_urls : list
            A list of the URLs that can be downloaded
        """

        log.info("Staging files...")

        url = os.path.join(self.archive_url, 'rh', 'submission')
        #'ALMA+uid___A002_X391d0b_X7b'
        #payload = [('dataset','ALMA+'+clean_uid(uid)) for uid in uids]
        payload = {'dataset':['ALMA+'+clean_uid(uid) for uid in uids]}

        self._staging_log = {}
        
        # Request staging for the UIDs
        response = self._request('POST', url, data=payload,
                                 timeout=self.TIMEOUT, cache=cache)
        self._staging_log['initial_response'] = response
        assert 'j_spring_cas_security_check' not in response.url

        request_id = response.url.split("/")[-2]
        self._staging_log['request_id'] = request_id


        # Submit a request for the specific request ID identified above
        submission_url = os.path.join(self.archive_url, 'rh', 'submission',
                                      request_id)
        self._staging_log['submission_url'] = submission_url
        submission = self._request('GET', submission_url, cache=cache)
        self._staging_log['submission'] = submission

        data_list_url = submission.url

        data_list_page = self._request('GET', data_list_url, cache=cache)
        self._staging_log['data_list_page'] = data_list_page

        root = BeautifulSoup(data_list_page.content, 'html5lib')

        data_table = root.findAll('table', class_='list', id='report')[0]
        hrefs = data_table.findAll('a')

        data_file_urls = [a['href'] for a in hrefs
                          if not a['href'].endswith('script')]

        return data_file_urls

    def data_size(self, files):
        """
        Given a list of file URLs, return the data size.  This is useful for
        assessing how much data you might be downloading!
        """
        totalsize = 0
        pb = ProgressBar(len(files))
        for ii,fileLink in enumerate(files):
            response = self._request('HEAD', fileLink, stream=True,
                                     cache=False, timeout=self.TIMEOUT)
            totalsize += int(response.headers['content-length'])
            pb.update(ii+1)

        return (totalsize*u.B).to(u.GB)

    def download_files(self, files, cache=True):
        """
        Given a list of file URLs, download them
        """
        downloaded_files = []
        for fileLink in files:
            filename = self._request("GET", fileLink, save=True,
                                     timeout=self.TIMEOUT)
            downloaded_files.append(filename)
        return downloaded_files

    def retrieve_data_from_uid(self, uids, cache=True):
        """
        Stage & Download ALMA data.  Will print out the expected file size
        before attempting the download.

        Parameters
        ----------
        uids : list
            A list of valid UIDs.
            UIDs should have the form: 'uid://A002/X391d0b/X7b'
        cache : bool
            Whether to cache the downloads.

        Returns
        -------
        downloaded_files : list
            A list of the downloaded file paths
        """
        if isinstance(uids, six.string_types):
            uids = [uids]
        if not isinstance(uids, (list, tuple, np.ndarray)):
            raise TypeError("Datasets must be given as a list of strings.")

        files = self.stage_data(uids, cache=cache)

        log.info("Determining download size for {0} files...".format(len(files)))
        totalsize = self.data_size(files)

        log.info("Downloading files of size {0}...".format(totalsize.to(u.GB)))
        downloaded_files = self.download_files(files, cache=cache)

        return downloaded_files

    def _parse_result(self, response, verbose=False):
        """
        Parse a VOtable response
        """
        if not verbose:
            commons.suppress_vo_warnings()

        tf = six.BytesIO(response.content)
        vo_tree = votable.parse(tf, pedantic=False, invalid='mask')
        first_table = vo_tree.get_first_table()
        table = first_table.to_table()
        return table

    def _login(self, username):
        # Check if already logged in
        loginpage = self._request("GET", "https://asa.alma.cl/cas/login",
                                  cache=False)
        root = BeautifulSoup(loginpage.content, 'html5lib')
        if root.find('div', class_='success'):
            log.info("Already logged in.")
            return True

        # Get password from keyring or prompt
        password_from_keyring = keyring.get_password("astroquery:asa.alma.cl",
                                                     username)
        if password_from_keyring is None:
            if __IPYTHON__:
                log.warn("You may be using an ipython notebook:"
                         " the password form will appear in your terminal.")
            password = getpass.getpass("{0}, enter your ALMA password:"
                                       "\n".format(username))
        else:
            password = password_from_keyring
        # Authenticate
        log.info("Authenticating {0} on asa.alma.cl ...".format(username))
        # Do not cache pieces of the login process
        data = {kw:root.find('input', {'name':kw})['value']
                for kw in ('lt','_eventId','execution')}
        data['username'] = username
        data['password'] = password

        login_response = self._request("POST", "https://asa.alma.cl/cas/login",
                                       params={'service':
                                               os.path.join(self.archive_url,
                                                            'rh', 'login')},
                                       data=data,
                                       cache=False)

        authenticated = ('You have successfully logged in' in
                         login_response.content)

        if authenticated:
            log.info("Authentication successful!")
        else:
            log.exception("Authentication failed!")
        # When authenticated, save password in keyring if needed
        if authenticated and password_from_keyring is None:
            keyring.set_password("astroquery:asa.alma.cl", username, password)
        return authenticated

Alma = AlmaClass()

def clean_uid(uid):
    """
    Return a uid with all unacceptable characters replaced with underscores
    """
    try:
        return uid.decode('utf-8').replace(u"/",u"_").replace(u":",u"_")
    except AttributeError:
        return uid.replace("/","_").replace(":","_")
