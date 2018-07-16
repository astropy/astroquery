# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import print_function
import time
import os.path
import keyring
import numpy as np
import re
import tarfile
import string
import requests
from requests import HTTPError
import sys
from pkg_resources import resource_filename
from bs4 import BeautifulSoup

from astropy.extern.six.moves.urllib_parse import urljoin, urlparse
from astropy.extern.six import iteritems, StringIO
from astropy.extern import six
from astropy.table import Table, Column
from astropy import log
from astropy.utils.console import ProgressBar
from astropy import units as u
import astropy.coordinates as coord
import astropy.io.votable as votable

from ..exceptions import (RemoteServiceError, TableParseError,
                          InvalidQueryError, LoginError)
from ..utils import commons, url_helpers
from ..utils.process_asyncs import async_to_sync
from ..query import QueryWithLogin
from . import conf

__doctest_skip__ = ['AlmaClass.*']


@async_to_sync
class AlmaClass(QueryWithLogin):

    TIMEOUT = conf.timeout
    archive_url = conf.archive_url
    USERNAME = conf.username

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
        payload.update({'source_name_resolver': object_name, })

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
        rdc = "{cstr}, {rad}".format(cstr=cstr, rad=coord.Angle(radius).deg)

        if payload is None:
            payload = {}
        payload.update({'ra_dec': rdc})

        return self.query_async(payload, cache=cache, public=public,
                                science=science, **kwargs)

    def query_async(self, payload, cache=True, public=True, science=True,
                    max_retries=5,
                    get_html_version=False, get_query_payload=False, **kwargs):
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
            (note: HTML queries *cannot* be cached using the standard caching
            mechanism because the URLs are different each time
        public : bool
            Return only publicly available datasets?
        science : bool
            Return only data marked as "science" in the archive?

        """

        url = urljoin(self._get_dataarchive_url(), 'aq/')

        payload.update(kwargs)
        if get_html_version:
            payload.update({'result_view': 'observation', 'format': 'URL',
                            'download': 'true'})
        else:
            payload.update({'result_view': 'raw', 'format': 'VOTABLE',
                            'download': 'true'})
        if public:
            payload['public_data'] = 'public'
        if science:
            payload['science_observations'] = '=%TARGET%'

        self.validate_query(payload)

        if get_query_payload:
            return payload

        response = self._request('GET', url, params=payload,
                                 timeout=self.TIMEOUT,
                                 cache=cache and not get_html_version)
        self._last_response = response
        response.raise_for_status()

        if get_html_version:
            if 'run' not in response.text:
                if max_retries > 0:
                    log.info("Failed query.  Retrying up to {0} more times"
                             .format(max_retries))
                    return self.query_async(payload=payload, cache=False,
                                            public=public, science=science,
                                            max_retries=max_retries-1,
                                            get_html_version=get_html_version,
                                            get_query_payload=get_query_payload,
                                            **kwargs)
                raise RemoteServiceError("Incorrect return from HTML table query.")
            response2 = self._request('GET',
                                      "{0}/{1}/{2}".format(
                                          self._get_dataarchive_url(), 'aq',
                                          response.text),
                                      params={'query_url':
                                              response.url.split("?")[-1]},
                                      timeout=self.TIMEOUT,
                                      cache=False,
                                      )
            self._last_response = response2
            response2.raise_for_status()
            if len(response2.text) == 0:
                if max_retries > 0:
                    log.info("Failed (empty) query.  Retrying up to {0} more times"
                             .format(max_retries))
                    return self.query_async(payload=payload, cache=cache,
                                            public=public, science=science,
                                            max_retries=max_retries-1,
                                            get_html_version=get_html_version,
                                            get_query_payload=get_query_payload,
                                            **kwargs)
                raise RemoteServiceError("Empty return.")
            return response2

        else:
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
            vpayload = {'field': kw,
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
            if self.archive_url in ('http://almascience.org', 'https://almascience.org'):
                response = self._request('GET', self.archive_url + "/aq",
                                         cache=False)
                response.raise_for_status()
                # Jan 2017: we have to force https because the archive doesn't
                # tell us it needs https.
                self.dataarchive_url = response.url.replace("/aq/", "").replace("http://", "https://")
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

        if isinstance(uids, six.string_types + (np.bytes_,)):
            uids = [uids]
        if not isinstance(uids, (list, tuple, np.ndarray)):
            raise TypeError("Datasets must be given as a list of strings.")

        log.info("Staging files...")

        self._get_dataarchive_url()

        url = urljoin(self.dataarchive_url, 'rh/submission')
        log.debug("First request URL: {0}".format(url))
        # 'ALMA+uid___A002_X391d0b_X7b'
        payload = {'dataset': ['ALMA+' + clean_uid(uid) for uid in uids]}
        log.debug("First request payload: {0}".format(payload))

        self._staging_log = {'first_post_url': url}

        # Request staging for the UIDs
        # This component cannot be cached, since the returned data can change
        # if new data are uploaded
        response = self._request('POST', url, data=payload,
                                 timeout=self.TIMEOUT, cache=False)
        self._staging_log['initial_response'] = response
        log.debug("First response URL: {0}".format(response.url))
        if 'login' in response.url:
            raise ValueError("You must login before downloading this data set.")

        if response.status_code == 405:
            if hasattr(self, '_last_successful_staging_log'):
                log.warning("Error 405 received.  If you have previously staged "
                            "the same UIDs, the result returned is probably "
                            "correct, otherwise you may need to create a fresh "
                            "astroquery.Alma instance.")
                return self._last_successful_staging_log['result']
            else:
                raise HTTPError("Received an error 405: this may indicate you "
                                "have already staged the data.  Try downloading "
                                "the file URLs directly with download_files.")
        response.raise_for_status()

        if 'j_spring_cas_security_check' in response.url:
            time.sleep(1)
            # CANNOT cache this stage: it not a real data page!  results in
            # infinite loops
            response = self._request('POST', url, data=payload,
                                     timeout=self.TIMEOUT, cache=False)
            self._staging_log['initial_response'] = response
            if 'j_spring_cas_security_check' in response.url:
                log.warning("Staging request was not successful.  Try again?")
            response.raise_for_status()

        if 'j_spring_cas_security_check' in response.url:
            raise RemoteServiceError("Could not access data.  This error "
                                     "can arise if the data are private and "
                                     "you do not have access rights or are "
                                     "not logged in.")

        request_id = response.url.split("/")[-2]
        self._staging_log['request_id'] = request_id
        log.debug("Request ID: {0}".format(request_id))

        # Submit a request for the specific request ID identified above
        submission_url = urljoin(self.dataarchive_url,
                                 url_helpers.join('rh/submission', request_id))
        log.debug("Submission URL: {0}".format(submission_url))
        self._staging_log['submission_url'] = submission_url
        staging_submission = self._request('GET', submission_url, cache=True)
        self._staging_log['staging_submission'] = staging_submission
        staging_submission.raise_for_status()

        data_page_url = staging_submission.url
        self._staging_log['data_page_url'] = data_page_url
        dpid = data_page_url.split("/")[-1]
        self._staging_log['staging_page_id'] = dpid

        # CANNOT cache this step: please_wait will happen infinitely
        data_page = self._request('GET', data_page_url, cache=False)
        self._staging_log['data_page'] = data_page
        data_page.raise_for_status()

        has_completed = False
        while not has_completed:
            time.sleep(1)
            summary = self._request('GET', url_helpers.join(data_page_url,
                                                            'summary'),
                                    cache=False)
            summary.raise_for_status()
            print(".", end='')
            sys.stdout.flush()
            has_completed = summary.json()['complete']

        self._staging_log['summary'] = summary
        summary.raise_for_status()
        self._staging_log['json_data'] = json_data = summary.json()

        username = self.USERNAME if self.USERNAME else 'anonymous'

        # templates:
        # https://almascience.eso.org/dataPortal/requests/keflavich/946895898/ALMA/
        # 2013.1.00308.S_uid___A001_X196_X93_001_of_001.tar/2013.1.00308.S_uid___A001_X196_X93_001_of_001.tar
        # uid___A002_X9ee74a_X26f0/2013.1.00308.S_uid___A002_X9ee74a_X26f0.asdm.sdm.tar

        url_decomposed = urlparse(data_page_url)
        base_url = ('{uri.scheme}://{uri.netloc}/'
                    'dataPortal/requests/{username}/'
                    '{staging_page_id}/ALMA'.format(uri=url_decomposed,
                                                    staging_page_id=dpid,
                                                    username=username,
                                                    ))
        tbl = self._json_summary_to_table(json_data, base_url=base_url)
        self._staging_log['result'] = tbl
        self._staging_log['file_urls'] = tbl['URL']
        self._last_successful_staging_log = self._staging_log

        return tbl

    def _HEADER_data_size(self, files):
        """
        Given a list of file URLs, return the data size.  This is useful for
        assessing how much data you might be downloading!
        (This is discouraged by the ALMA archive, as it puts unnecessary load
        on their system)
        """
        totalsize = 0 * u.B
        data_sizes = {}
        pb = ProgressBar(len(files))
        for ii, fileLink in enumerate(files):
            response = self._request('HEAD', fileLink, stream=False,
                                     cache=False, timeout=self.TIMEOUT)
            filesize = (int(response.headers['content-length']) * u.B).to(u.GB)
            totalsize += filesize
            data_sizes[fileLink] = filesize
            log.debug("File {0}: size {1}".format(fileLink, filesize))
            pb.update(ii + 1)
            response.raise_for_status()

        return data_sizes, totalsize.to(u.GB)

    def download_files(self, files, savedir=None, cache=True, continuation=True):
        """
        Given a list of file URLs, download them

        Note: Given a list with repeated URLs, each will only be downloaded
        once, so the return may have a different length than the input list
        """
        downloaded_files = []
        if savedir is None:
            savedir = self.cache_location
        for fileLink in unique(files):
            try:
                filename = self._request("GET", fileLink, save=True,
                                         savedir=savedir,
                                         timeout=self.TIMEOUT, cache=cache,
                                         continuation=continuation)
                downloaded_files.append(filename)
            except requests.HTTPError as ex:
                if ex.response.status_code == 401:
                    log.info("Access denied to {url}.  Skipping to"
                             " next file".format(url=fileLink))
                    continue
                else:
                    raise ex
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
        if isinstance(uids, six.string_types + (np.bytes_,)):
            uids = [uids]
        if not isinstance(uids, (list, tuple, np.ndarray)):
            raise TypeError("Datasets must be given as a list of strings.")

        files = self.stage_data(uids)
        file_urls = files['URL']
        totalsize = files['size'].sum() * files['size'].unit

        # each_size, totalsize = self.data_size(files)
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

        if 'run?' in response.url:
            if response.text == "":
                raise RemoteServiceError("Empty return.")
            # this is a CSV-like table returned via a direct browser request
            import pandas
            table = Table.from_pandas(pandas.read_csv(StringIO(response.text)))

        else:
            fixed_content = self._hack_bad_arraysize_vofix(response.content)
            tf = six.BytesIO(fixed_content)
            vo_tree = votable.parse(tf, pedantic=False, invalid='mask')
            first_table = vo_tree.get_first_table()
            table = first_table.to_table(use_names_over_ids=True)

        return table

    def _hack_bad_arraysize_vofix(self, text):
        """
        Hack to fix an error in the ALMA votables present in most 2016 and 2017 queries.

        The problem is that this entry:
        '      <FIELD name="Band" datatype="char" ID="32817" xtype="adql:VARCHAR" arraysize="0*">\r',
        has an invalid ``arraysize`` entry.  Also, it returns a char, but it
        should be an int.

        Since that problem was discovered and fixed, many other entries have
        the same error.

        According to the IVOA, the tables are wrong, not astropy.io.votable:
        http://www.ivoa.net/documents/VOTable/20130315/PR-VOTable-1.3-20130315.html#ToC11
        """
        lines = text.split(b"\n")
        newlines = []

        for ln in lines:
            if b'FIELD name="Band"' in ln:
                ln = ln.replace(b'arraysize="0*"', b'arraysize="1*"')
                ln = ln.replace(b'datatype="char"', b'datatype="int"')
            elif b'arraysize="0*"' in ln:
                ln = ln.replace(b'arraysize="0*"', b'arraysize="*"')
            newlines.append(ln)

        return b"\n".join(newlines)

    def _login(self, username=None, store_password=False,
               reenter_password=False):
        """
        Login to the ALMA Science Portal.

        Parameters
        ----------
        username : str, optional
            Username to the ALMA Science Portal. If not given, it should be
            specified in the config file.
        store_password : bool, optional
            Stores the password securely in your keyring. Default is False.
        reenter_password : bool, optional
            Asks for the password even if it is already stored in the
            keyring. This is the way to overwrite an already stored passwork
            on the keyring. Default is False.
        """

        if username is None:
            if not self.USERNAME:
                raise LoginError("If you do not pass a username to login(), "
                                 "you should configure a default one!")
            else:
                username = self.USERNAME

        # Check if already logged in
        loginpage = self._request("GET", "https://asa.alma.cl/cas/login",
                                  cache=False)
        root = BeautifulSoup(loginpage.content, 'html5lib')
        if root.find('div', class_='success'):
            log.info("Already logged in.")
            return True

        # Get password from keyring or prompt
        password, password_from_keyring = self._get_password(
            "astroquery:asa.alma.cl", username, reenter=reenter_password)

        # Authenticate
        log.info("Authenticating {0} on asa.alma.cl ...".format(username))
        # Do not cache pieces of the login process
        data = {kw: root.find('input', {'name': kw})['value']
                for kw in ('lt', '_eventId', 'execution')}
        data['username'] = username
        data['password'] = password

        login_response = self._request("POST", "https://asa.alma.cl/cas/login",
                                       params={'service':
                                               urljoin(self.archive_url,
                                                       'rh/login')},
                                       data=data,
                                       cache=False)

        authenticated = ('You have successfully logged in' in
                         login_response.text)

        if authenticated:
            log.info("Authentication successful!")
            self.USERNAME = username
        else:
            log.exception("Authentication failed!")
        # When authenticated, save password in keyring if needed
        if authenticated and password_from_keyring is None and store_password:
            keyring.set_password("astroquery:asa.alma.cl", username, password)
        return authenticated

    def get_cycle0_uid_contents(self, uid):
        """
        List the file contents of a UID from Cycle 0.  Will raise an error
        if the UID is from cycle 1+, since those data have been released in
        a different and more consistent format.  See
        http://almascience.org/documents-and-tools/cycle-2/ALMAQA2Productsv1.01.pdf
        for details.
        """

        # First, check if UID is in the Cycle 0 listing
        if uid in self.cycle0_table['uid']:
            cycle0id = self.cycle0_table[
                self.cycle0_table['uid'] == uid][0]['ID']
            contents = [row['Files']
                        for row in self._cycle0_tarfile_content
                        if cycle0id in row['ID']]
            return contents
        else:
            info_url = urljoin(
                self._get_dataarchive_url(),
                'documents-and-tools/cycle-2/ALMAQA2Productsv1.01.pdf')
            raise ValueError("Not a Cycle 0 UID.  See {0} for details about "
                             "cycle 1+ data release formats.".format(info_url))

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
            html_table = root.find('table', class_='grid listing')
            data = list(zip(*[(x.findAll('td')[0].text,
                               x.findAll('td')[1].text)
                              for x in html_table.findAll('tr')]))
            columns = [Column(data=data[0], name='ID'),
                       Column(data=data[1], name='Files')]
            tbl = Table(columns)
            assert len(tbl) == 8497
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
        if not hasattr(self, '_cycle0_table'):
            filename = resource_filename(
                'astroquery.alma', 'data/cycle0_delivery_asdm_mapping.txt')

            self._cycle0_table = Table.read(filename, format='ascii.no_header')
            self._cycle0_table.rename_column('col1', 'ID')
            self._cycle0_table.rename_column('col2', 'uid')
        return self._cycle0_table

    def get_files_from_tarballs(self, downloaded_files, regex=r'.*\.fits$',
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
                    filelist.append(os.path.join(path, member.name))

        return filelist

    def download_and_extract_files(self, urls, delete=True, regex=r'.*\.fits$',
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
                if not any(re.match(regex, x) for x in
                           self._cycle0_tarfile_content['Files'][match]):
                    log.info("No FITS files found in {0}".format(tarfile_name))
                    continue
            else:
                if 'asdm' in tarfile_name and not include_asdm:
                    log.info("ASDM tarballs do not contain FITS files; "
                             "skipping.")
                    continue

            try:
                tarball_name = self._request('GET', url, save=True,
                                             timeout=self.TIMEOUT)
            except requests.ConnectionError as ex:
                self.partial_file_list = all_files
                log.error("There was an error downloading the file. "
                          "A partially completed download list is "
                          "in Alma.partial_file_list")
                raise ex
            except requests.HTTPError as ex:
                if ex.response.status_code == 401:
                    log.info("Access denied to {url}.  Skipping to"
                             " next file".format(url=url))
                    continue
                else:
                    raise ex

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

        print("Valid ALMA keywords.  Left column is the description, right "
              "column is the name of the keyword to pass to astroquery.alma"
              " queries:")

        for title, section in help_list:
            print()
            print(title)
            for row in section:
                if len(row) == 2:  # text value
                    name, payload_keyword = row
                    print("  {0:33s}: {1:35s}".format(name, payload_keyword))
                # elif len(row) == 3: # radio button
                #    name,payload_keyword,value = row
                #    print("  {0:33s}: {1:20s} = {2:15s}".format(name,
                #                                                    payload_keyword,
                #                                                    value))
                elif len(row) == 4:  # radio button or checkbox
                    name, payload_keyword, checkbox, value = row
                    if isinstance(checkbox, list):
                        checkbox_str = ", ".join(["{0}={1}".format(x, y)
                                                  for x, y in zip(checkbox, value)])
                        print("  {0:33s}: {1:20s} -> {2}"
                              .format(name, payload_keyword, checkbox_str))
                    else:
                        print("  {2} {0:29s}: {1:20s} = {3:15s}"
                              .format(name, payload_keyword, checkbox, value))
                else:
                    raise ValueError("Wrong number of rows - ALMA query page"
                                     " did not parse properly.")

    def _get_help_page(self, cache=True):
        if not hasattr(self, '_help_list') or not self._help_list:
            querypage = self._request(
                'GET', self._get_dataarchive_url() + "/aq/",
                cache=cache, timeout=self.TIMEOUT)
            root = BeautifulSoup(querypage.content, "html5lib")
            sections = root.findAll('td', class_='category')

            whitespace = re.compile(r"\s+")

            help_list = []
            for section in sections:
                title = section.find(
                    'div', class_='categorytitle').text.lstrip()
                help_section = (title, [])
                for inp in section.findAll('div', class_='inputdiv'):
                    sp = inp.find('span')
                    buttons = inp.findAll('input')
                    for b in buttons:
                        # old version:for=id=rawView; name=viewFormat
                        # new version:for=id=rawView; name=result_view
                        payload_keyword = b.attrs['name']
                        bid = b.attrs['id']
                        label = inp.find('label')
                        if sp is not None:
                            name = whitespace.sub(" ", sp.text)
                        elif label.attrs['for'] == bid:
                            name = whitespace.sub(" ", label.text)
                        else:
                            raise TableParseError("ALMA query page has"
                                                  " an unrecognized entry")
                        if b.attrs['type'] == 'text':
                            help_section[1].append((name, payload_keyword))
                        elif b.attrs['type'] == 'radio':
                            value = b.attrs['value']
                            if 'checked' in b.attrs:
                                checked = b.attrs['checked'] == 'checked'
                                checkbox = "(x)" if checked else "( )"
                            else:
                                checkbox = "( )"
                            help_section[1].append((name, payload_keyword,
                                                    checkbox, value))
                        elif b.attrs['type'] == 'checkbox':
                            if 'checked' in b.attrs:
                                checked = b.attrs['checked'] == 'checked'
                            else:
                                checked = False
                            value = b.attrs['value']
                            checkbox = "[x]" if checked else "[ ]"
                            help_section[1].append((name, payload_keyword,
                                                    checkbox, value))
                    select = inp.find('select')
                    if select is not None:
                        options = [("".join(filter_printable(option.text)),
                                    option.attrs['value'])
                                   for option in select.findAll('option')]
                        if sp is not None:
                            name = whitespace.sub(" ", sp.text)
                        else:
                            name = select.attrs['name']
                        checkbox = [o[0] for o in options]
                        value = [o[1] for o in options]
                        option_str = select.attrs['name']
                        help_section[1].append((name, option_str, checkbox, value))

                help_list.append(help_section)
            self._help_list = help_list

        return self._help_list

    def _validate_payload(self, payload):
        if not hasattr(self, '_valid_params'):
            help_list = self._get_help_page(cache=False)
            self._valid_params = [row[1]
                                  for title, section in help_list
                                  for row in section]
            if len(self._valid_params) == 0:
                raise ValueError("The query validation failed for unknown "
                                 "reasons.  Try again?")
            # These parameters are entirely hidden, but Felix says they are
            # allowed
            self._valid_params.append('download')
            self._valid_params.append('format')
        invalid_params = [k for k in payload if k not in self._valid_params]
        if len(invalid_params) > 0:
            raise InvalidQueryError("The following parameters are not accepted"
                                    " by the ALMA query service:"
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

        data_table = root.findAll('table', class_='list', id='report')[0]
        columns = {'uid': [], 'URL': [], 'size': []}
        for tr in data_table.findAll('tr'):
            tds = tr.findAll('td')

            # Cannot check class if it is not defined
            cl = 'class' in tr.attrs

            if (len(tds) > 1 and 'uid' in tds[0].text and
                    (cl and 'Level' in tr['class'][0])):
                # New Style
                text = tds[0].text.strip().split()
                if text[0] in ('Asdm', 'Member'):
                    uid = text[-1]
            elif len(tds) > 1 and 'uid' in tds[1].text:
                # Old Style
                uid = tds[1].text.strip()
            elif cl and tr['class'] == 'Level_1':
                raise ValueError("Heading was found when parsing the download "
                                 "page but it was not parsed correctly")

            if len(tds) > 3 and (cl and tr['class'][0] == 'fileRow'):
                # New Style
                size, unit = re.search(r'(-|[0-9\.]*)([A-Za-z]*)',
                                       tds[2].text).groups()
                href = tds[1].find('a')
                if size == '':
                    # this is a header row
                    continue
                authorized = ('access_authorized.png' in
                              tds[3].findChild('img')['src'])
                if authorized:
                    columns['uid'].append(uid)
                    if href and 'href' in href.attrs:
                        columns['URL'].append(href.attrs['href'])
                    else:
                        columns['URL'].append('None_Found')
                    unit = (u.Unit(unit) if unit in ('GB', 'MB')
                            else u.Unit('kB') if 'kb' in unit.lower()
                            else 1)
                    try:
                        columns['size'].append(float(size) * u.Unit(unit))
                    except ValueError:
                        # size is probably a string?
                        columns['size'].append(-1 * u.byte)
                    log.log(level=5, msg="Found a new-style entry.  "
                            "size={0} uid={1} url={2}"
                            .format(size, uid, columns['URL'][-1]))
                else:
                    log.warning("Access to {0} is not authorized.".format(uid))
            elif len(tds) > 3 and tds[2].find('a'):
                # Old Style
                href = tds[2].find('a')
                size, unit = re.search(r'([0-9\.]*)([A-Za-z]*)',
                                       tds[3].text).groups()
                columns['uid'].append(uid)
                columns['URL'].append(href.attrs['href'])
                unit = (u.Unit(unit) if unit in ('GB', 'MB')
                        else u.Unit('kB') if 'kb' in unit.lower()
                        else 1)
                columns['size'].append(float(size) * u.Unit(unit))
                log.log(level=5, msg="Found an old-style entry.  "
                        "size={0} uid={1} url={2}".format(size, uid,
                                                          columns['URL'][-1]))

        columns['size'] = u.Quantity(columns['size'], u.Gbyte)

        if len(columns['uid']) == 0:
            raise RemoteServiceError(
                "No valid UIDs were found in the staged data table. "
                "Please include {0} in a bug report."
                .format(self._staging_log['data_list_url']))

        tbl = Table([Column(name=k, data=v) for k, v in iteritems(columns)])

        return tbl

    def _json_summary_to_table(self, data, base_url):
        """
        """
        columns = {'uid': [], 'URL': [], 'size': []}
        for entry in data['node_data']:
            # de_type can be useful (e.g., MOUS), but it is not necessarily
            # specified
            # file_name and file_key *must* be specified.
            is_file = (entry['file_name'] != 'null' and
                       entry['file_key'] != 'null')
            if is_file:
                # "de_name": "ALMA+uid://A001/X122/X35e",
                columns['uid'].append(entry['de_name'][5:])
                if entry['file_size'] == 'null':
                    columns['size'].append(np.nan * u.Gbyte)
                else:
                    columns['size'].append(
                        (int(entry['file_size']) * u.B).to(u.Gbyte))
                # example template for constructing url:
                # https://almascience.eso.org/dataPortal/requests/keflavich/940238268/ALMA/
                # uid___A002_X9d6f4c_X154/2013.1.00546.S_uid___A002_X9d6f4c_X154.asdm.sdm.tar
                # above is WRONG... except for ASDMs, when it's right
                # should be:
                # 2013.1.00546.S_uid___A002_X9d6f4c_X154.asdm.sdm.tar/2013.1.00546.S_uid___A002_X9d6f4c_X154.asdm.sdm.tar
                #
                # apparently ASDMs are different from others:
                # templates:
                # https://almascience.eso.org/dataPortal/requests/keflavich/946895898/ALMA/
                # 2013.1.00308.S_uid___A001_X196_X93_001_of_001.tar/2013.1.00308.S_uid___A001_X196_X93_001_of_001.tar
                # uid___A002_X9ee74a_X26f0/2013.1.00308.S_uid___A002_X9ee74a_X26f0.asdm.sdm.tar
                url = url_helpers.join(base_url,
                                       entry['file_key'],
                                       entry['file_name'])
                if 'null' in url:
                    raise ValueError("The URL {0} was created containing "
                                     "'null', which is invalid.".format(url))
                columns['URL'].append(url)

        columns['size'] = u.Quantity(columns['size'], u.Gbyte)

        tbl = Table([Column(name=k, data=v) for k, v in iteritems(columns)])
        return tbl


Alma = AlmaClass()


def clean_uid(uid):
    """
    Return a uid with all unacceptable characters replaced with underscores
    """
    if not hasattr(uid, 'replace'):
        return clean_uid(str(uid.astype('S')))
    try:
        return uid.decode('utf-8').replace(u"/", u"_").replace(u":", u"_")
    except AttributeError:
        return uid.replace("/", "_").replace(":", "_")


def reform_uid(uid):
    """
    Convert a uid with underscores to the original format
    """
    return uid[:3] + "://" + "/".join(uid[6:].split("_"))


def unique(seq):
    """
    Return unique elements of a list, preserving order
    """
    seen = set()
    seen_add = seen.add
    return [x for x in seq if not (x in seen or seen_add(x))]


def filter_printable(s):
    """ extract printable characters from a string """
    return filter(lambda x: x in string.printable, s)
