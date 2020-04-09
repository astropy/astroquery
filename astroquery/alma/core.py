# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import print_function
import json
import os.path
import keyring
import numpy as np
import re
import tarfile
import string
import requests
from pkg_resources import resource_filename
from bs4 import BeautifulSoup

from six.moves.urllib_parse import urljoin
import six
from astropy.table import Table, Column, vstack as table_vstack
from astropy import log
from astropy.utils.console import ProgressBar
from astropy import units as u
import astropy.coordinates as coord
import astropy.io.votable as votable

from ..exceptions import (RemoteServiceError, TableParseError,
                          InvalidQueryError, LoginError)
from ..utils import commons
from ..utils.process_asyncs import async_to_sync
from ..query import QueryWithLogin
from . import conf, auth_urls

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
        elif self.dataarchive_url in ('http://almascience.org',
                                      'https://almascience.org'):
            raise ValueError("'dataarchive_url' was set to a disambiguation "
                             "page that is meant to redirect to a real "
                             "archive.  You should only reach this message "
                             "if you manually specified Alma.dataarchive_url. "
                             "If you did so, instead consider setting "
                             "Alma.archive_url.  Otherwise, report an error "
                             "on github.")
        return self.dataarchive_url

    def stage_data(self, uids, expand_tarfiles=False, return_json=False):
        """
        Obtain table of ALMA files

        Parameters
        ----------
        uids : list or str
            A list of valid UIDs or a single UID.
            UIDs should have the form: 'uid://A002/X391d0b/X7b'
        expand_tarfiles : bool
            Expand the tarfiles to obtain lists of all contained files.  If
            this is specified, the parent tarfile will *not* be included
        return_json : bool
            Return a list of the JSON data sets returned from the query.  This
            is primarily intended as a debug routine, but may be useful if there
            are unusual scheduling block layouts.

        Returns
        -------
        data_file_table : Table
            A table containing 3 columns: the UID, the file URL (for future
            downloading), and the file size
        """

        dataarchive_url = self._get_dataarchive_url()

        # allow for the uid to be specified as single entry
        if isinstance(uids, str):
            uids = [uids]

        tables = []
        for uu in uids:
            log.debug("Retrieving metadata for {0}".format(uu))
            uid = clean_uid(uu)
            req = self._request('GET', '{dataarchive_url}/rh/data/expand/{uid}'
                                .format(dataarchive_url=dataarchive_url,
                                        uid=uid),
                                cache=False)
            req.raise_for_status()
            try:
                jdata = req.json()
            # Note this exception does not work in Python 2.7
            except json.JSONDecodeError:
                if 'Central Authentication Service' in req.text or 'recentRequests' in req.url:
                    # this indicates a wrong server is being used;
                    # the "pre-feb2020" stager will be phased out
                    # when the new services are deployed
                    raise RemoteServiceError("Failed query!  This shouldn't happen - please "
                                             "report the issue as it may indicate a change in "
                                             "the ALMA servers.")
                else:
                    raise

            if return_json:
                tables.append(jdata)
            else:
                if jdata['type'] != 'PROJECT':
                    log.error("Skipped uid {uu} because it is not a project and"
                              "lacks the appropriate metadata; it is a "
                              "{jdata}".format(uu=uu, jdata=jdata['type']))
                    continue
                if expand_tarfiles:
                    table = uid_json_to_table(jdata, productlist=['ASDM',
                                                                  'PIPELINE_PRODUCT'])
                else:
                    table = uid_json_to_table(jdata,
                                              productlist=['ASDM',
                                                           'PIPELINE_PRODUCT'
                                                           'PIPELINE_PRODUCT_TARFILE',
                                                           'PIPELINE_AUXILIARY_TARFILE'])
                table['sizeInBytes'].unit = u.B
                table.rename_column('sizeInBytes', 'size')
                table.add_column(Column(data=['{dataarchive_url}/dataPortal/{name}'
                                              .format(dataarchive_url=dataarchive_url,
                                                      name=name)
                                              for name in table['name']],
                                        name='URL'))

                isp = self.is_proprietary(uid)
                table.add_column(Column(data=[isp for row in table],
                                        name='isProprietary'))

                tables.append(table)
                log.debug("Completed metadata retrieval for {0}".format(uu))

        if len(tables) == 0:
            raise ValueError("No valid UIDs supplied.")

        if return_json:
            return tables

        table = table_vstack(tables)

        return table

    def is_proprietary(self, uid):
        """
        Given an ALMA UID, query the servers to determine whether it is
        proprietary or not.  This will never be cached, since proprietarity is
        time-sensitive.
        """
        dataarchive_url = self._get_dataarchive_url()

        is_proprietary = self._request('GET',
                                       '{dataarchive_url}/rh/access/{uid}'
                                       .format(dataarchive_url=dataarchive_url,
                                               uid=clean_uid(uid)), cache=False)

        is_proprietary.raise_for_status()

        isp = is_proprietary.json()['isProprietary']

        return isp

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

    def download_files(self, files, savedir=None, cache=True,
                       continuation=True, skip_unauthorized=True):
        """
        Given a list of file URLs, download them

        Note: Given a list with repeated URLs, each will only be downloaded
        once, so the return may have a different length than the input list

        Parameters
        ----------
        files : list
            List of URLs to download
        savedir : None or str
            The directory to save to.  Default is the cache location.
        cache : bool
            Cache the download?
        continuation : bool
            Attempt to continue where the download left off (if it was broken)
        skip_unauthorized : bool
            If you receive "unauthorized" responses for some of the download
            requests, skip over them.  If this is False, an exception will be
            raised.
        """

        if self.USERNAME:
            auth = self._get_auth_info(self.USERNAME)
        else:
            auth = None

        downloaded_files = []
        if savedir is None:
            savedir = self.cache_location
        for fileLink in unique(files):
            try:
                log.debug("Downloading {0} to {1}".format(fileLink, savedir))
                check_filename = self._request('HEAD', fileLink, auth=auth,
                                               stream=True)
                check_filename.raise_for_status()
                if 'text/html' in check_filename.headers['Content-Type']:
                    raise ValueError("Bad query.  This can happen if you "
                                     "attempt to download proprietary "
                                     "data when not logged in")

                filename = self._request("GET", fileLink, save=True,
                                         savedir=savedir,
                                         timeout=self.TIMEOUT,
                                         cache=cache,
                                         auth=auth,
                                         continuation=continuation)
                downloaded_files.append(filename)
            except requests.HTTPError as ex:
                if ex.response.status_code == 401:
                    if skip_unauthorized:
                        log.info("Access denied to {url}.  Skipping to"
                                 " next file".format(url=fileLink))
                        continue
                    else:
                        raise(ex)
                elif ex.response.status_code == 403:
                    log.error("Access denied to {url}".format(url=fileLink))
                    if 'dataPortal' in fileLink and 'sso' not in fileLink:
                        log.error("The URL may be incorrect.  Try using "
                                  "{0} instead of {1}"
                                  .format(fileLink.replace('dataPortal/',
                                                           'dataPortal/sso/'),
                                          fileLink))
                    raise ex
                elif ex.response.status_code == 500:
                    # empirically, this works the second time most of the time...
                    filename = self._request("GET", fileLink, save=True,
                                             savedir=savedir,
                                             timeout=self.TIMEOUT,
                                             cache=cache,
                                             auth=auth,
                                             continuation=continuation)
                    downloaded_files.append(filename)
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
            table = Table.read(response.text, format='ascii.csv', fast_reader=False)

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
        As of February 2019, this issue appears to be half-fixed; the arraysize
        is no longer incorrect, but the data type remains incorrect.

        Since that problem was discovered and fixed, many other entries have
        the same error.  Feb 2019, the other instances are gone.

        According to the IVOA, the tables are wrong, not astropy.io.votable:
        http://www.ivoa.net/documents/VOTable/20130315/PR-VOTable-1.3-20130315.html#ToC11

        A new issue, #1340, noted that 'Release date' and 'Mosaic' both lack data type
        metadata, necessitating the hack below
        """
        lines = text.split(b"\n")
        newlines = []

        for ln in lines:
            if b'FIELD name="Band"' in ln:
                ln = ln.replace(b'datatype="char"', b'datatype="int"')
            elif b'FIELD name="Release date"' in ln or b'FIELD name="Mosaic"' in ln:
                ln = ln.replace(b'/>', b' arraysize="*"/>')
            newlines.append(ln)

        return b"\n".join(newlines)

    def _get_auth_info(self, username, store_password=False,
                       reenter_password=False):
        """
        Get the auth info (user, password) for use in another function
        """

        if username is None:
            if not self.USERNAME:
                raise LoginError("If you do not pass a username to login(), "
                                 "you should configure a default one!")
            else:
                username = self.USERNAME

        if hasattr(self, '_auth_url'):
            auth_url = self._auth_url
        else:
            raise LoginError("Login with .login() to acquire the appropriate"
                             " login URL")

        # Get password from keyring or prompt
        password, password_from_keyring = self._get_password(
            "astroquery:{0}".format(auth_url), username, reenter=reenter_password)

        # When authenticated, save password in keyring if needed
        if password_from_keyring is None and store_password:
            keyring.set_password("astroquery:{0}".format(auth_url), username, password)

        return username, password

    def _login(self, username=None, store_password=False,
               reenter_password=False, auth_urls=auth_urls):
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

        success = False
        for auth_url in auth_urls:
            # set session cookies (they do not get set otherwise)
            cookiesetpage = self._request("GET",
                                          urljoin(self._get_dataarchive_url(),
                                                  'rh/forceAuthentication'),
                                          cache=False)
            self._login_cookiepage = cookiesetpage
            cookiesetpage.raise_for_status()

            if (auth_url+'/cas/login' in cookiesetpage.request.url):
                # we've hit a target, we're good
                success = True
                break
        if not success:
            raise LoginError("Could not log in to any of the known ALMA "
                             "authorization portals: {0}".format(auth_urls))

        # Check if already logged in
        loginpage = self._request("GET", "https://{auth_url}/cas/login".format(auth_url=auth_url),
                                  cache=False)
        root = BeautifulSoup(loginpage.content, 'html5lib')
        if root.find('div', class_='success'):
            log.info("Already logged in.")
            return True

        self._auth_url = auth_url

        username, password = self._get_auth_info(username=username,
                                                 store_password=store_password,
                                                 reenter_password=reenter_password)

        # Authenticate
        log.info("Authenticating {0} on {1} ...".format(username, auth_url))
        # Do not cache pieces of the login process
        data = {kw: root.find('input', {'name': kw})['value']
                for kw in ('execution', '_eventId')}
        data['username'] = username
        data['password'] = password
        data['submit'] = 'LOGIN'

        login_response = self._request("POST", "https://{0}/cas/login".format(auth_url),
                                       params={'service': self._get_dataarchive_url()},
                                       data=data,
                                       cache=False)

        # save the login response for debugging purposes
        self._login_response = login_response
        # do not expose password back to user
        del data['password']
        # but save the parameters for debug purposes
        self._login_parameters = data

        authenticated = ('You have successfully logged in' in
                         login_response.text)

        if authenticated:
            log.info("Authentication successful!")
            self.USERNAME = username
        else:
            log.exception("Authentication failed!")

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
            self._valid_params.append('member_ous_id')
        invalid_params = [k for k in payload if k not in self._valid_params]
        if len(invalid_params) > 0:
            raise InvalidQueryError("The following parameters are not accepted"
                                    " by the ALMA query service:"
                                    " {0}".format(invalid_params))

    def get_project_metadata(self, projectid, cache=True):
        """
        Get the metadata - specifically, the project abstract - for a given project ID.
        """
        url = urljoin(self._get_dataarchive_url(), 'aq/')

        assert len(projectid) == 14, "Wrong length for project ID"
        assert projectid[4] == projectid[6] == projectid[12] == '.', "Wrong format for project ID"
        response = self._request('GET', "{0}meta/project/{1}".format(url, projectid),
                                 timeout=self.TIMEOUT,
                                 cache=cache)
        response.raise_for_status()

        return response.json()


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


def uid_json_to_table(jdata,
                      productlist=['ASDM', 'PIPELINE_PRODUCT',
                                   'PIPELINE_PRODUCT_TARFILE',
                                   'PIPELINE_AUXILIARY_TARFILE']):
    rows = []

    def flatten_jdata(this_jdata, mousID=None):
        if isinstance(this_jdata, list):
            for kk in this_jdata:
                if kk['type'] in productlist:
                    kk['mous_uid'] = mousID
                    rows.append(kk)
                elif len(kk['children']) > 0:
                    if len(kk['allMousUids']) == 1:
                        flatten_jdata(kk['children'], kk['allMousUids'][0])
                    else:
                        flatten_jdata(kk['children'])

    flatten_jdata(jdata['children'])

    keys = rows[-1].keys()

    columns = [Column(data=[row[key] for row in rows], name=key)
               for key in keys if key not in ('children', 'allMousUids')]

    columns = [col.astype(str) if col.dtype.name == 'object' else col for col
               in columns]

    return Table(columns)
