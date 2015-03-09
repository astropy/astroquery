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
import tarfile
from bs4 import BeautifulSoup

from astropy.extern.six.moves.urllib_parse import urljoin
from astropy.extern.six import BytesIO,iteritems
from astropy.extern import six
from astropy.table import Table, Column
from astropy import log
from astropy.utils.console import ProgressBar
from astropy import units as u
import astropy.io.votable as votable

from ..exceptions import (LoginError, RemoteServiceError, TableParseError,
                          InvalidQueryError)
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
                           science=True, payload=None, **kwargs):
        """
        Query the archive with a source name

        Parameters
        ----------
        object_name : str
            The object name.  Will be parsed by SESAME on the ALMA servers.
        cache : bool
            Cache the query?
        public : bool
            Return only publicly available datasets?
        science : bool
            Return only data marked as "science" in the archive?
        payload : dict
            Dictionary of additional keywords.  See `help`.
        kwargs : dict
            Passed to `query_async`
        """

        if payload is None:
            payload = {}
        payload.update({'source_name_sesame': object_name,})

        return self.query_async(payload, cache=cache, public=public,
                                science=science, **kwargs)

    def query_region_async(self, coordinate, radius, cache=True, public=True,
                           science=True, payload=None, **kwargs):
        """
        Query the ALMA archive with a source name and radius

        Parameters
        ----------
        coordinates : str / `astropy.coordinates`
            the identifier or coordinates around which to query.
        radius : str / `~astropy.units.Quantity`, optional
            the radius of the region
        cache : bool
            Cache the query?
        public : bool
            Return only publicly available datasets?
        science : bool
            Return only data marked as "science" in the archive?
        payload : dict
            Dictionary of additional keywords.  See `help`.
        kwargs : dict
            Passed to `query_async`
        """
        coordinate = commons.parse_coordinates(coordinate)
        cstr = coordinate.fk5.to_string(style='hmsdms', sep=':')
        rdc = "{cstr}, {rad}".format(cstr=cstr, rad=radius.to(u.deg).value)


        if payload is None:
            payload = {}
        payload.update({'raDecCoordinates': rdc})

        return self.query_async(payload, cache=cache, public=public,
                                science=science, **kwargs)

    def query_async(self, payload, cache=True, public=True, science=True):
        """
        Perform a generic query with user-specified payload

        Parameters
        ----------
        payload : dict
            A dictionary of payload keywords that are accepted by the ALMA
            archive system.  You can look these up by examining the forms at
            http://almascience.org/aq or using the `help` method
        cache : bool
            Cache the query?
        public : bool
            Return only publicly available datasets?
        science : bool
            Return only data marked as "science" in the archive?
        """

        url = urljoin(self._get_dataarchive_url(), 'aq/search.votable')

        payload.update({'viewFormat':'raw',})
        if public:
            payload['publicFilterFlag'] = 'public'
        if science:
            payload['scan_intent-asu'] = '=*TARGET*'

        self.validate_query(payload)

        response = self._request('GET', url, params=payload,
                                 timeout=self.TIMEOUT, cache=cache)
        response.raise_for_status()

        return response
    
    def validate_query(self, payload, cache=True):
        """
        Use the ALMA query validator service to check whether the keywords are
        valid
        """
        
        # Check that the keywords specified are allowed
        self._validate_payload(payload)

        vurl = self._get_dataarchive_url() + '/aq/validate'

        bad_kws = {}

        for kw in payload:
            vpayload = {'field':kw,
                        kw: payload[kw]}
            response = self._request('GET', vurl, params=vpayload, cache=cache,
                                     timeout=self.TIMEOUT)

            if response.content:
                bad_kws[kw] = response.content

        if bad_kws:
            raise InvalidQueryError("Invalid query parameters: "
                                    "{0}".format(bad_kws))



    def _get_dataarchive_url(self):
        """
        If the generic ALMA URL is used, query it to determine which mirror to
        access for querying data
        """
        if not hasattr(self, 'dataarchive_url'):
            if self.archive_url == 'http://almascience.org':
                response = self._request('GET', self.archive_url+"/aq", cache=False)
                response.raise_for_status()
                self.dataarchive_url = response.url.replace("/aq/","")
            else:
                self.dataarchive_url = self.archive_url
        return self.dataarchive_url

    def stage_data(self, uids):
        """
        Stage ALMA data

        Parameters
        ----------
        uids : list or str
            A list of valid UIDs or a single UID.
            UIDs should have the form: 'uid://A002/X391d0b/X7b'
        cache : True
            This is *forced* true, because the ALMA servers don't support repeats
            of the same request.
            Whether to cache the staging process.  This should generally be
            left as False when used interactively.

        Returns
        -------
        data_file_table : Table
            A table containing 3 columns: the UID, the file URL (for future
            downloading), and the file size
        """

        """
        With log.set_level(10)
        INFO: Staging files... [astroquery.alma.core]
        DEBUG: First request URL: https://almascience.eso.org/rh/submission [astroquery.alma.core]
        DEBUG: First request payload: {'dataset': [u'ALMA+uid___A002_X3b3400_X90f']} [astroquery.alma.core]
        DEBUG: First response URL: https://almascience.eso.org/rh/checkAuthenticationStatus/3f98de33-197e-4692-9afa-496842032ea9/submission [astroquery.alma.core]
        DEBUG: Request ID: 3f98de33-197e-4692-9afa-496842032ea9 [astroquery.alma.core]
        DEBUG: Submission URL: https://almascience.eso.org/rh/submission/3f98de33-197e-4692-9afa-496842032ea9 [astroquery.alma.core]
        .DEBUG: Data list URL: https://almascience.eso.org/rh/requests/anonymous/786823226 [astroquery.alma.core]
        """

        if isinstance(uids, six.string_types):
            uids = [uids]
        if not isinstance(uids, (list, tuple, np.ndarray)):
            raise TypeError("Datasets must be given as a list of strings.")

        log.info("Staging files...")

        self._get_dataarchive_url()

        url = urljoin(self.dataarchive_url, 'rh/submission')
        log.debug("First request URL: {0}".format(url))
        #'ALMA+uid___A002_X391d0b_X7b'
        #payload = [('dataset','ALMA+'+clean_uid(uid)) for uid in uids]
        payload = {'dataset':['ALMA+'+clean_uid(uid) for uid in uids]}
        log.debug("First request payload: {0}".format(payload))

        self._staging_log = {'first_post_url':url}

        # Request staging for the UIDs
        # This component cannot be cached, since the returned data can change
        # if new data are uploaded
        response = self._request('POST', url, data=payload,
                                 timeout=self.TIMEOUT, cache=False)
        self._staging_log['initial_response'] = response
        log.debug("First response URL: {0}".format(response.url))
        response.raise_for_status()

        if 'j_spring_cas_security_check' in response.url:
            time.sleep(1)
            # CANNOT cache this stage: it not a real data page!  results in
            # infinite loops
            response = self._request('POST', url, data=payload,
                                     timeout=self.TIMEOUT, cache=False)
            self._staging_log['initial_response'] = response
            if 'j_spring_cas_security_check' in response.url:
                log.warn("Staging request was not successful.  Try again?")
            response.raise_for_status()

        request_id = response.url.split("/")[-2]
        assert len(request_id) == 36
        self._staging_log['request_id'] = request_id
        log.debug("Request ID: {0}".format(request_id))

        # Submit a request for the specific request ID identified above
        submission_url = urljoin(self.dataarchive_url,
                                 os.path.join('rh/submission', request_id))
        log.debug("Submission URL: {0}".format(submission_url))
        self._staging_log['submission_url'] = submission_url
        has_completed = False
        staging_submission = self._request('GET', submission_url, cache=True)
        self._staging_log['staging_submission'] = staging_submission
        staging_submission.raise_for_status()

        data_page_url = staging_submission.url
        dpid = data_page_url.split("/")[-1]
        assert len(dpid) == 9
        self._staging_log['staging_page_id'] = dpid

        while not has_completed:
            time.sleep(1)
            # CANNOT cache this step: please_wait will happen infinitely
            data_page = self._request('GET', data_page_url, cache=False)
            if 'Please wait' not in data_page.text:
                has_completed = True
            print(".",end='')
        self._staging_log['data_page'] = data_page
        data_page.raise_for_status()
        staging_root = BeautifulSoup(data_page.content)
        downloadFileURL = staging_root.find('form').attrs['action']
        data_list_url = os.path.split(downloadFileURL)[0]

        # Old version, unreliable: data_list_url = staging_submission.url
        log.debug("Data list URL: {0}".format(data_list_url))
        self._staging_log['data_list_url'] = data_list_url

        time.sleep(1)
        data_list_page = self._request('GET', data_list_url, cache=True)
        self._staging_log['data_list_page'] = data_list_page
        data_list_page.raise_for_status()

        if 'Error' in data_list_page.text:
            errormessage = root.find('div', id='errorContent').string.strip()
            raise RemoteServiceError(errormessage)

        tbl = self._parse_staging_request_page(data_list_page)

        return tbl

    def _HEADER_data_size(self, files):
        """
        Given a list of file URLs, return the data size.  This is useful for
        assessing how much data you might be downloading!
        (This is discouraged by the ALMA archive, as it puts unnecessary load
        on their system)
        """
        totalsize = 0*u.B
        data_sizes = {}
        pb = ProgressBar(len(files))
        for ii,fileLink in enumerate(files):
            response = self._request('HEAD', fileLink, stream=False,
                                     cache=False, timeout=self.TIMEOUT)
            filesize = (int(response.headers['content-length'])*u.B).to(u.GB)
            totalsize += filesize
            data_sizes[fileLink] = filesize
            log.debug("File {0}: size {1}".format(fileLink, filesize))
            pb.update(ii+1)
            response.raise_for_status()

        return data_sizes,totalsize.to(u.GB)

    def download_files(self, files, cache=True):
        """
        Given a list of file URLs, download them

        Note: Given a list with repeated URLs, each will only be downloaded
        once, so the return may have a different length than the input list
        """
        downloaded_files = []
        for fileLink in unique(files):
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
        uids : list or str
            A list of valid UIDs or a single UID.
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
        file_urls = files['URL']
        totalsize = files['size'].sum()*files['size'].unit

        #log.info("Determining download size for {0} files...".format(len(files)))
        #each_size,totalsize = self.data_size(files)
        log.info("Downloading files of size {0}...".format(totalsize.to(u.GB)))
        # TODO: Add cache=cache keyword here.  Currently would have no effect.
        downloaded_files = self.download_files(file_urls)
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

    def _login(self, username, store_password=False):
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
            if system_tools.in_ipynb():
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
                                               urljoin(self.archive_url,
                                                       'rh/login')},
                                       data=data,
                                       cache=False)

        authenticated = ('You have successfully logged in' in
                         login_response.content)

        if authenticated:
            log.info("Authentication successful!")
        else:
            log.exception("Authentication failed!")
        # When authenticated, save password in keyring if needed
        if authenticated and password_from_keyring is None and store_password:
            keyring.set_password("astroquery:asa.alma.cl", username, password)
        return authenticated

    def get_cycle0_uid_contents(self, uid):
        """
        List the file contents of a UID from Cycle 0.  Will raise an error
        if the UID is from cycle 1+, since those data have been released in a
        different and more consistent format.
        See http://almascience.org/documents-and-tools/cycle-2/ALMAQA2Productsv1.01.pdf
        for details.
        """

        # First, check if UID is in the Cycle 0 listing
        if uid in self.cycle0_table['uid']:
            cycle0id = self.cycle0_table[self.cycle0_table['uid'] == uid][0]['ID']
            contents = [row['Files']
                        for row in self._cycle0_tarfile_content
                        if cycle0id in row['ID']]
            return contents
        else:
            info_url = urljoin(self._get_dataarchive_url(),
                               'documents-and-tools/cycle-2/ALMAQA2Productsv1.01.pdf')
            raise ValueError("Not a Cycle 0 UID.  See {0} for details about"
                             " cycle 1+ data release formats.".format(info_url))

    @property
    def _cycle0_tarfile_content(self):
        """
        In principle, this is a static file, but we'll retrieve it just in case
        """
        if not hasattr(self, '_cycle0_tarfile_content_table'):
            url = urljoin(self._get_dataarchive_url(),
                          'alma-data/archive/cycle-0-tarfile-content')
            response = self._request('GET', url, cache=True)

            # html.parser is needed because some <tr>'s have form:
            # <tr width="blah"> which the default parser does not pick up
            root = BeautifulSoup(response.content, 'html.parser')
            html_table = root.find('table',class_='grid listing')
            data = list(zip(*[(x.findAll('td')[0].text, x.findAll('td')[1].text)
                              for x in html_table.findAll('tr')]))
            columns = [Column(data=data[0], name='ID'),
                       Column(data=data[1], name='Files')]
            tbl = Table(columns)
            assert len(tbl) == response.text.count('<tr') == 8497
            self._cycle0_tarfile_content_table = tbl
        else:
            tbl = self._cycle0_tarfile_content_table
        return tbl

    @property
    def cycle0_table(self):
        """
        Return a table of Cycle 0 Project IDs and associated UIDs.

        The table is distributed with astroquery and was provided by Felix
        Stoehr.
        """
        if not hasattr(self,'_cycle0_table'):
            filename = urljoin(os.path.dirname(__file__),
                               'data/cycle0_delivery_asdm_mapping.txt')
            self._cycle0_table = Table.read(filename, format='ascii.no_header')
            self._cycle0_table.rename_column('col1', 'ID')
            self._cycle0_table.rename_column('col2', 'uid')
        return self._cycle0_table

    def get_files_from_tarballs(self, downloaded_files, regex='.*\.fits$',
                                path='cache_path', verbose=True):
        """
        Given a list of successfully downloaded tarballs, extract files
        with names matching a specified regular expression.  The default
        is to extract all FITS files

        Parameters
        ----------
        downloaded_files : list
            A list of downloaded files.  These should be paths on your local
            machine.
        regex : str
            A valid regular expression
        path : 'cache_path' or str
            If 'cache_path', will use the astroquery.Alma cache directory
            (``Alma.cache_location``), otherwise will use the specified path.
            Note that the subdirectory structure of the tarball will be
            maintained.

        Returns
        -------
        filelist : list
            A list of the extracted file locations on disk
        """

        if path == 'cache_path':
            path = self.cache_location
        elif not os.path.isdir(path):
            raise OSError("Specified an invalid path {0}.".format(path))

        fitsre = re.compile(regex)

        filelist = []

        for fn in downloaded_files:
            tf = tarfile.open(fn)
            for member in tf.getmembers():
                if fitsre.match(member.name):
                    if verbose:
                        log.info("Extracting {0} to {1}".format(member.name,
                                                                path))
                    tf.extract(member, path)
                    filelist.append(urljoin(path, member.name))

        return filelist

    def download_and_extract_files(self, urls, delete=True, regex='.*\.fits$',
                                   include_asdm=False, path='cache_path',
                                   verbose=True):
        """
        Given a list of tarball URLs:

            1. Download the tarball
            2. Extract all FITS files (or whatever matches the regex)
            3. Delete the downloaded tarball

        See ``Alma.get_files_from_tarballs`` for details

        Parameters
        ----------
        urls : str or list
            A single URL or a list of URLs
        include_asdm : bool
            Only affects cycle 1+ data.  If set, the ASDM files will be
            downloaded in addition to the script and log files.  By default,
            though, this file will be downloaded and deleted without extracting
            any information: you must change the regex if you want to extract
            data from an ASDM tarball
        """

        if isinstance(urls, six.string_types):
            urls = [urls]
        if not isinstance(urls, (list, tuple, np.ndarray)):
            raise TypeError("Datasets must be given as a list of strings.")

        all_files = []
        for url in urls:
            if url[-4:] != '.tar':
                raise ValueError("URLs should be links to tarballs.")

            tarfile_name = os.path.split(url)[-1]
            if tarfile_name in self._cycle0_tarfile_content['ID']:
                # It is a cycle 0 file: need to check if it contains FITS
                match = (self._cycle0_tarfile_content['ID'] == tarfile_name)
                if not any(re.match(regex,x) for x in
                           self._cycle0_tarfile_content['Files'][match]):
                    log.info("No FITS files found in {0}".format(tarfile_name))
                    continue
            else:
                if 'asdm' in tarfile_name and not include_asdm:
                    log.info("ASDM tarballs do not contain FITS files; skipping.")
                    continue

            tarball_name = self._request('GET', url, save=True,
                                         timeout=self.TIMEOUT)
            fitsfilelist = self.get_files_from_tarballs([tarball_name],
                                                        regex=regex, path=path,
                                                        verbose=verbose)

            if delete:
                log.info("Deleting {0}".format(tarball_name))
                os.remove(tarball_name)

            all_files += fitsfilelist
        return all_files

    def help(self, cache=True):
        """
        Return the valid query parameters
        """

        help_list = self._get_help_page(cache=cache)

        print("Valid ALMA keywords:")

        for title,section in help_list:
            print()
            print(title)
            for row in section:
                if len(row) == 2:
                    name,payload_keyword = row
                    print("  {0:33s}: {1:35s}".format(name,payload_keyword))
                elif len(row) == 4:
                    name,payload_keyword,checkbox,value = row
                    print("  {2} {0:29s}: {1:20s} = {3:15s}".format(name,
                                                                    payload_keyword,
                                                                    checkbox,
                                                                    value))
                else:
                    raise ValueError("Wrong number of rows - ALMA query page"
                                     " did not parse properly.")

    def _get_help_page(self, cache=True):
        if not hasattr(self, '_help_list'):
            querypage = self._request('GET', self._get_dataarchive_url()+"/aq/",
                                      cache=cache, timeout=self.TIMEOUT)
            root = BeautifulSoup(querypage.content)
            sections = root.findAll('td', class_='category')

            help_list = []
            for section in sections:
                title = section.find('div', class_='categorytitle').text.lstrip()
                help_section = (title,[])
                for inp in section.findAll('div', class_='inputdiv'):
                    sp = inp.find('span')
                    if sp is not None:
                        payload_keyword = sp.attrs['class'][0]
                        name = sp.text
                        help_section[1].append((name,payload_keyword))
                    else:
                        buttons = inp.findAll('input')
                        for b in buttons:
                            payload_keyword = b.attrs['name']
                            bid = b.attrs['id']
                            label = inp.find('label')
                            checked = b.attrs['checked'] == 'checked'
                            value = b.attrs['value']
                            if label.attrs['for'] == bid:
                                name = label.text
                            else:
                                raise TableParseError("ALMA query page has"
                                                      " an unrecognized entry")
                            checkbox = "[x]" if checked else "[ ]"
                            help_section[1].append((name, payload_keyword,
                                                    checkbox, value))
                help_list.append(help_section)
            self._help_list = help_list

        return self._help_list

    def _validate_payload(self, payload):
        if not hasattr(self, '_valid_params'):
            help_list = self._get_help_page()
            self._valid_params = [row[1]
                                  for title,section in help_list
                                  for row in section]
        invalid_params = [k for k in payload if k not in self._valid_params]
        if len(invalid_params) > 0:
            raise InvalidQueryError("The following parameters are not accepted "
                                    "by the ALMA query service:"
                                    " {0}".format(invalid_params))

    def _parse_staging_request_page(self, data_list_page):
        """
        Parse pages like this one:
        https://almascience.eso.org/rh/requests/anonymous/786572566

        that include links to data sets that have been requested and staged

        Parameters
        ----------
        data_list_page : requests.Response object

        """

        root = BeautifulSoup(data_list_page.content, 'html5lib')

        for link in root.findAll('a'):
            if 'script.sh' in link.text:
                download_script_url = urljoin(self.dataarchive_url,
                                              link['href'])

        download_script = self._request('GET', download_script_url,
                                        cache=False)
        download_script_target_urls = []
        for line in download_script.text.split('\n'):
            if line and line.split() and line.split()[0] == 'wget':
                download_script_target_urls.append(line.split()[1].strip('"'))

        if len(download_script_target_urls) == 0:
            raise RemoteServiceError("There was an error parsing the download "
                                     "script; it is empty.  "
                                     "You can access the download script "
                                     "directly from this URL: "
                                     "{0}".format(download_script_url))

        data_table = root.findAll('table', class_='list', id='report')[0]
        columns = {'uid':[], 'URL':[], 'size':[]}
        for tr in data_table.findAll('tr'):
            tds = tr.findAll('td')

            # Cannot check class if it is not defined
            cl = 'class' in tr.attrs

            if len(tds) > 1 and 'uid' in tds[0].text and (cl and
                                                          'Level' in tr['class'][0]):
                # New Style
                text = tds[0].text.strip().split()
                if text[0] in ('Asdm', 'Member'):
                    uid = text[-1]
            elif len(tds) > 1 and 'uid' in tds[1].text:
                # Old Style
                uid = tds[1].text.strip()
            elif cl and tr['class'] == 'Level_1':
                raise ValueError("A heading was found when parsing the download page but "
                                 "it was not parsed correctly")

            if len(tds) > 3 and (cl and tr['class'][0] == 'fileRow'):
                # New Style
                size,unit = re.search('(-|[0-9\.]*)([A-Za-z]*)', tds[2].text).groups()
                href = tds[1].find('a')
                if size == '':
                    # this is a header row
                    continue
                authorized = ('access_authorized.png' in tds[3].findChild('img')['src'])
                if authorized:
                    columns['uid'].append(uid)
                    if href and 'href' in href.attrs:
                        columns['URL'].append(href.attrs['href'])
                    else:
                        columns['URL'].append('None_Found')
                    unit = (u.Unit(unit) if unit in ('GB','MB')
                            else u.Unit('kB') if 'kb' in unit.lower()
                            else 1)
                    try:
                        columns['size'].append(float(size)*u.Unit(unit))
                    except ValueError: 
                        # size is probably a string?
                        columns['size'].append(-1*u.byte)
                    log.log(level=5, msg="Found a new-style entry.  "
                            "size={0} uid={1} url={2}".format(size, uid,
                                                              columns['URL'][-1]))
                else:
                    log.warn("Access to {0} is not authorized.".format(uid))
            elif len(tds) > 3 and tds[2].find('a'):
                # Old Style
                href = tds[2].find('a')
                size,unit = re.search('([0-9\.]*)([A-Za-z]*)', tds[3].text).groups()
                columns['uid'].append(uid)
                columns['URL'].append(href.attrs['href'])
                unit = (u.Unit(unit) if unit in ('GB','MB')
                        else u.Unit('kB') if 'kb' in unit.lower()
                        else 1)
                columns['size'].append(float(size)*u.Unit(unit))
                log.log(level=5, msg="Found an old-style entry.  "
                        "size={0} uid={1} url={2}".format(size, uid,
                                                          columns['URL'][-1]))

        columns['size'] = u.Quantity(columns['size'], u.Gbyte)

        if len(columns['uid']) == 0:
            raise RemoteServiceError("No valid UIDs were found in the staged "
                                     "data table.  Please include {0} and {1}"
                                     "in a bug report."
                                     .format(self._staging_log['data_list_url'],
                                             download_script_url))

        if len(download_script_target_urls) != len(columns['URL']):
            log.warn("There was an error parsing the data staging page.  "
                     "The results from the page and the download script "
                     "differ.  You can access the download script directly "
                     "from this URL: {0}".format(download_script_url))
        else:
            bad_urls = []
            for (rurl,url) in (zip(columns['URL'],
                                   download_script_target_urls)):
                if rurl == 'None_Found':
                    url_uid = os.path.split(url)[-1]
                    ind = np.where(np.array(columns['uid']) == url_uid)[0][0]
                    columns['URL'][ind] = url
                elif rurl != url:
                    bad_urls.append((rurl, url))
            if bad_urls:
                log.warn("There were mismatches between the parsed URLs "
                         "from the staging page ({0}) and the download "
                         "script ({1})."
                         .format(self._staging_log['data_list_url'],
                                 download_script_url))

        tbl = Table([Column(name=k, data=v) for k,v in iteritems(columns)])


        return tbl

Alma = AlmaClass()

def clean_uid(uid):
    """
    Return a uid with all unacceptable characters replaced with underscores
    """
    try:
        return uid.decode('utf-8').replace(u"/",u"_").replace(u":",u"_")
    except AttributeError:
        return uid.replace("/","_").replace(":","_")

def reform_uid(uid):
    """
    Convert a uid with underscores to the original format
    """
    return uid[:3]+"://" + "/".join(uid[6:].split("_"))

def unique(seq):
    """
    Return unique elements of a list, preserving order
    """
    seen = set()
    seen_add = seen.add
    return [x for x in seq if not (x in seen or seen_add(x))]
