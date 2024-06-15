# Licensed under a 3-clause BSD style license - see LICENSE.rst

import base64
import email
import json
import os.path
import re
import shutil
import subprocess
import time
import warnings
import webbrowser
import xml.etree.ElementTree as ET
from io import BytesIO
from typing import List, Optional, Tuple, Dict, Set

import astropy.utils.data
import keyring
import requests.exceptions
from astropy.table import Table, Column
from astropy.utils.decorators import deprecated_renamed_argument
from bs4 import BeautifulSoup

from astroquery import log
from . import conf
from ..exceptions import RemoteServiceError, NoResultsWarning, LoginError
from ..query import QueryWithLogin
from ..utils import schema

__doctest_skip__ = ['EsoClass.*']


def _check_response(content):
    """
    Check the response from an ESO service query for various types of error

    If all is OK, return True
    """
    if b"NETWORKPROBLEM" in content:
        raise RemoteServiceError("The query resulted in a network "
                                 "problem; the service may be offline.")
    elif b"# No data returned !" not in content:
        return True


class CalSelectorError(Exception):
    """
    Raised on failure to parse CalSelector's response.
    """
    pass


class AuthInfo:
    def __init__(self, username: str, password: str, token: str):
        self.username = username
        self.password = password
        self.token = token
        self.expiration_time = self._get_exp_time_from_token()

    def _get_exp_time_from_token(self) -> int:
        # "manual" decoding since jwt is not installed
        decoded_token = base64.b64decode(self.token.split(".")[1] + "==")
        return int(json.loads(decoded_token)['exp'])

    def expired(self) -> bool:
        # we anticipate the expiration time by 10 minutes to avoid issues
        return time.time() > self.expiration_time - 600


class EsoClass(QueryWithLogin):
    ROW_LIMIT = conf.row_limit
    USERNAME = conf.username
    QUERY_INSTRUMENT_URL = conf.query_instrument_url
    CALSELECTOR_URL = "https://archive.eso.org/calselector/v1/associations"
    DOWNLOAD_URL = "https://dataportal.eso.org/dataPortal/file/"
    AUTH_URL = "https://www.eso.org/sso/oidc/token"
    GUNZIP = "gunzip"

    def __init__(self):
        super().__init__()
        self._instrument_list = None
        self._survey_list = None
        self._auth_info: Optional[AuthInfo] = None

    def _activate_form(self, response, *, form_index=0, form_id=None, inputs={},
                       cache=True, method=None):
        """
        Parameters
        ----------
        method: None or str
            Can be used to override the form-specified method
        """
        # Extract form from response
        root = BeautifulSoup(response.content, 'html5lib')
        if form_id is None:
            form = root.find_all('form')[form_index]
        else:
            form = root.find_all('form', id=form_id)[form_index]
        # Construct base url
        form_action = form.get('action')
        if "://" in form_action:
            url = form_action
        elif form_action.startswith('/'):
            url = '/'.join(response.url.split('/', 3)[:3]) + form_action
        else:
            url = response.url.rsplit('/', 1)[0] + '/' + form_action
        # Identify payload format
        fmt = None
        form_method = form.get('method').lower()
        if form_method == 'get':
            fmt = 'get'  # get(url, params=payload)
        elif form_method == 'post':
            if 'enctype' in form.attrs:
                if form.attrs['enctype'] == 'multipart/form-data':
                    fmt = 'multipart/form-data'  # post(url, files=payload)
                elif form.attrs['enctype'] == 'application/x-www-form-urlencoded':
                    fmt = 'application/x-www-form-urlencoded'  # post(url, data=payload)
                else:
                    raise Exception("enctype={0} is not supported!".format(form.attrs['enctype']))
            else:
                fmt = 'application/x-www-form-urlencoded'  # post(url, data=payload)
        # Extract payload from form
        payload = []
        for form_elem in form.find_all(['input', 'select', 'textarea']):
            value = None
            is_file = False
            tag_name = form_elem.name
            key = form_elem.get('name')
            if tag_name == 'input':
                is_file = (form_elem.get('type') == 'file')
                value = form_elem.get('value')
                if form_elem.get('type') in ['checkbox', 'radio']:
                    if form_elem.has_attr('checked'):
                        if not value:
                            value = 'on'
                    else:
                        value = None
            elif tag_name == 'select':
                if form_elem.get('multiple') is not None:
                    value = []
                    if form_elem.select('option[value]'):
                        for option in form_elem.select('option[value]'):
                            if option.get('selected') is not None:
                                value.append(option.get('value'))
                    else:
                        for option in form_elem.select('option'):
                            if option.get('selected') is not None:
                                # bs4 NavigableString types have bad,
                                # undesirable properties that result
                                # in recursion errors when caching
                                value.append(str(option.string))
                else:
                    if form_elem.select('option[value]'):
                        for option in form_elem.select('option[value]'):
                            if option.get('selected') is not None:
                                value = option.get('value')
                        # select the first option field if none is selected
                        if value is None:
                            value = form_elem.select(
                                'option[value]')[0].get('value')
                    else:
                        # survey form just uses text, not value
                        for option in form_elem.select('option'):
                            if option.get('selected') is not None:
                                value = str(option.string)
                        # select the first option field if none is selected
                        if value is None:
                            value = str(form_elem.select('option')[0].string)

            if key in inputs:
                if isinstance(inputs[key], list):
                    # list input is accepted (for array uploads)
                    value = inputs[key]
                else:
                    value = str(inputs[key])

            if (key is not None):  # and (value is not None):
                if fmt == 'multipart/form-data':
                    if is_file:
                        payload.append(
                            (key, ('', '', 'application/octet-stream')))
                    else:
                        if type(value) is list:
                            for v in value:
                                entry = (key, ('', v))
                                # Prevent redundant key, value pairs
                                # (can happen if the form repeats them)
                                if entry not in payload:
                                    payload.append(entry)
                        elif value is None:
                            entry = (key, ('', ''))
                            if entry not in payload:
                                payload.append(entry)
                        else:
                            entry = (key, ('', value))
                            if entry not in payload:
                                payload.append(entry)
                else:
                    if type(value) is list:
                        for v in value:
                            entry = (key, v)
                            if entry not in payload:
                                payload.append(entry)
                    else:
                        entry = (key, value)
                        if entry not in payload:
                            payload.append(entry)

        # for future debugging
        self._payload = payload
        log.debug("Form: payload={0}".format(payload))

        if method is not None:
            fmt = method

        log.debug("Method/format = {0}".format(fmt))

        # Send payload
        if fmt == 'get':
            response = self._request("GET", url, params=payload, cache=cache)
        elif fmt == 'multipart/form-data':
            response = self._request("POST", url, files=payload, cache=cache)
        elif fmt == 'application/x-www-form-urlencoded':
            response = self._request("POST", url, data=payload, cache=cache)

        return response

    def _authenticate(self, *, username: str, password: str) -> bool:
        """
        Get the access token from ESO SSO provider
        """
        self._auth_info = None
        url_params = {"response_type": "id_token token",
                      "grant_type": "password",
                      "client_id": "clientid",
                      "client_secret": "clientSecret",
                      "username": username,
                      "password": password}
        log.info(f"Authenticating {username} on 'www.eso.org' ...")
        response = self._request('GET', self.AUTH_URL, params=url_params)
        if response.status_code == 200:
            token = json.loads(response.content)['id_token']
            self._auth_info = AuthInfo(username=username, password=password, token=token)
            log.info("Authentication successful!")
            return True
        else:
            log.error("Authentication failed!")
            return False

    def _get_auth_info(self, username: str, *, store_password: bool = False,
                       reenter_password: bool = False) -> Tuple[str, str]:
        """
        Get the auth info (user, password) for use in another function
        """

        if username is None:
            if not self.USERNAME:
                raise LoginError("If you do not pass a username to login(), "
                                 "you should configure a default one!")
            else:
                username = self.USERNAME

        service_name = "astroquery:www.eso.org"
        # Get password from keyring or prompt
        password, password_from_keyring = self._get_password(
            service_name, username, reenter=reenter_password)

        # When authenticated, save password in keyring if needed
        if password_from_keyring is None and store_password:
            keyring.set_password(service_name, username, password)

        return username, password

    def _login(self, *, username: str = None, store_password: bool = False,
               reenter_password: bool = False) -> bool:
        """
        Login to the ESO User Portal.

        Parameters
        ----------
        username : str, optional
            Username to the ESO Public Portal. If not given, it should be
            specified in the config file.
        store_password : bool, optional
            Stores the password securely in your keyring. Default is False.
        reenter_password : bool, optional
            Asks for the password even if it is already stored in the
            keyring. This is the way to overwrite an already stored passwork
            on the keyring. Default is False.
        """

        username, password = self._get_auth_info(username=username,
                                                 store_password=store_password,
                                                 reenter_password=reenter_password)

        return self._authenticate(username=username, password=password)

    def _get_auth_header(self) -> Dict[str, str]:
        if self._auth_info and self._auth_info.expired():
            log.info("Authentication token has expired! Re-authenticating ...")
            self._authenticate(username=self._auth_info.username,
                               password=self._auth_info.password)
        if self._auth_info and not self._auth_info.expired():
            return {'Authorization': 'Bearer ' + self._auth_info.token}
        else:
            return {}

    def list_instruments(self, *, cache=True):
        """ List all the available instrument-specific queries offered by the ESO archive.

        Returns
        -------
        instrument_list : list of strings
        cache : bool
            Defaults to True. If set overrides global caching behavior.
            See :ref:`caching documentation <astroquery_cache>`.

        """
        if self._instrument_list is None:
            url = "http://archive.eso.org/cms/eso-data/instrument-specific-query-forms.html"
            instrument_list_response = self._request("GET", url, cache=cache)
            root = BeautifulSoup(instrument_list_response.content, 'html5lib')
            self._instrument_list = []
            for element in root.select("div[id=col3] a[href]"):
                href = element.attrs["href"]
                if u"http://archive.eso.org/wdb/wdb/eso" in href:
                    instrument = href.split("/")[-2]
                    if instrument not in self._instrument_list:
                        self._instrument_list.append(instrument)
        return self._instrument_list

    def list_surveys(self, *, cache=True):
        """ List all the available surveys (phase 3) in the ESO archive.

        Returns
        -------
        survey_list : list of strings
        cache : bool
            Defaults to True. If set overrides global caching behavior.
            See :ref:`caching documentation <astroquery_cache>`.
        """
        if self._survey_list is None:
            survey_list_response = self._request(
                "GET", "http://archive.eso.org/wdb/wdb/adp/phase3_main/form",
                cache=cache)
            root = BeautifulSoup(survey_list_response.content, 'html5lib')
            self._survey_list = []
            collections_table = root.find('table', id='collections_table')
            other_collections = root.find('select', id='collection_name_option')
            # it is possible to have empty collections or other collections...
            collection_elts = (collections_table.find_all('input', type='checkbox')
                               if collections_table is not None
                               else [])
            other_elts = (other_collections.find_all('option')
                          if other_collections is not None
                          else [])
            for element in (collection_elts + other_elts):
                if 'value' in element.attrs:
                    survey = element.attrs['value']
                    if survey and survey not in self._survey_list and 'Any' not in survey:
                        self._survey_list.append(survey)
        return self._survey_list

    def query_surveys(self, *, surveys='', cache=True,
                      help=False, open_form=False, **kwargs):
        """
        Query survey Phase 3 data contained in the ESO archive.

        Parameters
        ----------
        survey : string or list
            Name of the survey(s) to query.  Should beone or more of the
            names returned by `~astroquery.eso.EsoClass.list_surveys`.  If
            specified as a string, should be a comma-separated list of
            survey names.
        cache : bool
            Defaults to True. If set overrides global caching behavior.
            See :ref:`caching documentation <astroquery_cache>`.

        Returns
        -------
        table : `~astropy.table.Table` or `None`
            A table representing the data available in the archive for the
            specified survey, matching the constraints specified in ``kwargs``.
            The number of rows returned is capped by the ROW_LIMIT
            configuration item. `None` is returned when the query has no
            results.

        """

        url = "http://archive.eso.org/wdb/wdb/adp/phase3_main/form"
        if open_form:
            webbrowser.open(url)
        elif help:
            self._print_surveys_help(url, cache=cache)
        else:
            survey_form = self._request("GET", url, cache=cache)
            query_dict = kwargs
            query_dict["wdbo"] = "csv/download"
            if isinstance(surveys, str):
                surveys = surveys.split(",")
            query_dict['collection_name'] = surveys
            if self.ROW_LIMIT >= 0:
                query_dict["max_rows_returned"] = int(self.ROW_LIMIT)
            else:
                query_dict["max_rows_returned"] = 10000

            survey_response = self._activate_form(survey_form, form_index=0,
                                                  form_id='queryform',
                                                  inputs=query_dict, cache=cache)

            content = survey_response.content
            # First line is always garbage
            content = content.split(b'\n', 1)[1]
            log.debug("Response content:\n{0}".format(content))
            if _check_response(content):
                table = Table.read(BytesIO(content), format="ascii.csv",
                                   comment="^#")
                return table
            else:
                warnings.warn("Query returned no results", NoResultsWarning)

    def query_main(self, *, column_filters={}, columns=[],
                   open_form=False, help=False, cache=True, **kwargs):
        """
        Query raw data contained in the ESO archive.

        Parameters
        ----------
        column_filters : dict
            Constraints applied to the query.
        columns : list of strings
            Columns returned by the query.
        open_form : bool
            If `True`, opens in your default browser the query form
            for the requested instrument.
        help : bool
            If `True`, prints all the parameters accepted in
            ``column_filters`` and ``columns`` for the requested
            ``instrument``.
        cache : bool
            Defaults to True. If set overrides global caching behavior.
            See :ref:`caching documentation <astroquery_cache>`.

        Returns
        -------
        table : `~astropy.table.Table`
            A table representing the data available in the archive for the
            specified instrument, matching the constraints specified in
            ``kwargs``. The number of rows returned is capped by the
            ROW_LIMIT configuration item.

        """
        url = self.QUERY_INSTRUMENT_URL + "/eso_archive_main/form"
        return self._query(url, column_filters=column_filters, columns=columns,
                           open_form=open_form, help=help, cache=cache, **kwargs)

    def query_instrument(self, instrument, *, column_filters={}, columns=[],
                         open_form=False, help=False, cache=True, **kwargs):
        """
        Query instrument-specific raw data contained in the ESO archive.

        Parameters
        ----------
        instrument : string
            Name of the instrument to query, one of the names returned by
            `~astroquery.eso.EsoClass.list_instruments`.
        column_filters : dict
            Constraints applied to the query.
        columns : list of strings
            Columns returned by the query.
        open_form : bool
            If `True`, opens in your default browser the query form
            for the requested instrument.
        help : bool
            If `True`, prints all the parameters accepted in
            ``column_filters`` and ``columns`` for the requested
            ``instrument``.
        cache : bool
            Defaults to True. If set overrides global caching behavior.
            See :ref:`caching documentation <astroquery_cache>`.

        Returns
        -------
        table : `~astropy.table.Table`
            A table representing the data available in the archive for the
            specified instrument, matching the constraints specified in
            ``kwargs``. The number of rows returned is capped by the
            ROW_LIMIT configuration item.

        """

        url = self.QUERY_INSTRUMENT_URL + '/{0}/form'.format(instrument.lower())
        return self._query(url, column_filters=column_filters, columns=columns,
                           open_form=open_form, help=help, cache=cache, **kwargs)

    def _query(self, url, *, column_filters={}, columns=[],
               open_form=False, help=False, cache=True, **kwargs):

        table = None
        if open_form:
            webbrowser.open(url)
        elif help:
            self._print_query_help(url)
        else:
            instrument_form = self._request("GET", url, cache=cache)
            query_dict = {}
            query_dict.update(column_filters)
            # TODO: replace this with individually parsed kwargs
            query_dict.update(kwargs)
            query_dict["wdbo"] = "csv/download"

            # Default to returning the DP.ID since it is needed for header
            # acquisition
            query_dict['tab_dp_id'] = kwargs.pop('tab_dp_id', 'on')

            for k in columns:
                query_dict["tab_" + k] = True
            if self.ROW_LIMIT >= 0:
                query_dict["max_rows_returned"] = int(self.ROW_LIMIT)
            else:
                query_dict["max_rows_returned"] = 10000
            # used to be form 0, but now there's a new 'logout' form at the top
            # (form_index = -1 and 0 both work now that form_id is included)
            instrument_response = self._activate_form(instrument_form,
                                                      form_index=-1,
                                                      form_id='queryform',
                                                      inputs=query_dict,
                                                      cache=cache)

            content = instrument_response.content
            # First line is always garbage
            content = content.split(b'\n', 1)[1]
            log.debug("Response content:\n{0}".format(content))
            if _check_response(content):
                table = Table.read(BytesIO(content), format="ascii.csv",
                                   comment='^#')
                return table
            else:
                warnings.warn("Query returned no results", NoResultsWarning)

    def get_headers(self, product_ids, *, cache=True):
        """
        Get the headers associated to a list of data product IDs

        This method returns a `~astropy.table.Table` where the rows correspond
        to the provided data product IDs, and the columns are from each of
        the Fits headers keywords.

        Note: The additional column ``'DP.ID'`` found in the returned table
        corresponds to the provided data product IDs.

        Parameters
        ----------
        product_ids : either a list of strings or a `~astropy.table.Column`
            List of data product IDs.
        cache : bool
            Defaults to True. If set overrides global caching behavior.
            See :ref:`caching documentation <astroquery_cache>`.

        Returns
        -------
        result : `~astropy.table.Table`
            A table where: columns are header keywords, rows are product_ids.

        """
        _schema_product_ids = schema.Schema(
            schema.Or(Column, [schema.Schema(str)]))
        _schema_product_ids.validate(product_ids)
        # Get all headers
        result = []
        for dp_id in product_ids:
            response = self._request(
                "GET", "http://archive.eso.org/hdr?DpId={0}".format(dp_id),
                cache=cache)
            root = BeautifulSoup(response.content, 'html5lib')
            hdr = root.select('pre')[0].text
            header = {'DP.ID': dp_id}
            for key_value in hdr.split('\n'):
                if "=" in key_value:
                    key, value = key_value.split('=', 1)
                    key = key.strip()
                    value = value.split('/', 1)[0].strip()
                    if key[0:7] != "COMMENT":  # drop comments
                        if value == "T":  # Convert boolean T to True
                            value = True
                        elif value == "F":  # Convert boolean F to False
                            value = False
                        # Convert to string, removing quotation marks
                        elif value[0] == "'":
                            value = value[1:-1]
                        elif "." in value:  # Convert to float
                            value = float(value)
                        else:  # Convert to integer
                            value = int(value)
                        header[key] = value
                elif key_value.startswith("END"):
                    break
            result.append(header)
        # Identify all columns
        columns = []
        column_types = []
        for header in result:
            for key in header:
                if key not in columns:
                    columns.append(key)
                    column_types.append(type(header[key]))
        # Add all missing elements
        for i in range(len(result)):
            for (column, column_type) in zip(columns, column_types):
                if column not in result[i]:
                    result[i][column] = column_type()
        # Return as Table
        return Table(result)

    @staticmethod
    def _get_filename_from_response(response: requests.Response) -> str:
        content_disposition = response.headers.get("Content-Disposition", "")
        filename = re.findall(r"filename=(\S+)", content_disposition)
        if not filename:
            raise RemoteServiceError(f"Unable to find filename for {response.url}")
        return os.path.basename(filename[0].replace('"', ''))

    @staticmethod
    def _find_cached_file(filename: str) -> bool:
        files_to_check = [filename]
        if filename.endswith(('fits.Z', 'fits.gz')):
            files_to_check.append(filename.rsplit(".", 1)[0])
        for file in files_to_check:
            if os.path.exists(file):
                log.info(f"Found cached file {file}")
                return True
        return False

    def _download_eso_file(self, file_link: str, destination: str,
                           overwrite: bool) -> Tuple[str, bool]:
        block_size = astropy.utils.data.conf.download_block_size
        headers = self._get_auth_header()
        with self._session.get(file_link, stream=True, headers=headers) as response:
            response.raise_for_status()
            filename = self._get_filename_from_response(response)
            filename = os.path.join(destination, filename)
            part_filename = filename + ".part"
            if os.path.exists(part_filename):
                log.info(f"Removing partially downloaded file {part_filename}")
                os.remove(part_filename)
            download_required = overwrite or not self._find_cached_file(filename)
            if download_required:
                with open(part_filename, 'wb') as fd:
                    for chunk in response.iter_content(chunk_size=block_size):
                        fd.write(chunk)
                os.rename(part_filename, filename)
        return filename, download_required

    def _download_eso_files(self, file_ids: List[str], destination: Optional[str],
                            overwrite: bool) -> List[str]:
        destination = destination or self.cache_location
        destination = os.path.abspath(destination)
        os.makedirs(destination, exist_ok=True)
        nfiles = len(file_ids)
        log.info(f"Downloading {nfiles} files ...")
        downloaded_files = []
        for i, file_id in enumerate(file_ids, 1):
            file_link = self.DOWNLOAD_URL + file_id
            log.info(f"Downloading file {i}/{nfiles} {file_link} to {destination}")
            try:
                filename, downloaded = self._download_eso_file(file_link, destination, overwrite)
                downloaded_files.append(filename)
                if downloaded:
                    log.info(f"Successfully downloaded dataset"
                             f" {file_id} to {filename}")
            except requests.HTTPError as http_error:
                if http_error.response.status_code == 401:
                    log.error(f"Access denied to {file_link}")
                else:
                    log.error(f"Failed to download {file_link}. {http_error}")
            except Exception as ex:
                log.error(f"Failed to download {file_link}. {ex}")
        return downloaded_files

    def _unzip_file(self, filename: str) -> str:
        """
        Uncompress the provided file with gunzip.

        Note: ``system_tools.gunzip`` does not work with .Z files
        """
        uncompressed_filename = None
        if filename.endswith(('fits.Z', 'fits.gz')):
            uncompressed_filename = filename.rsplit(".", 1)[0]
            if not os.path.exists(uncompressed_filename):
                log.info(f"Uncompressing file {filename}")
                try:
                    subprocess.run([self.GUNZIP, filename], check=True)
                except Exception as ex:
                    uncompressed_filename = None
                    log.error(f"Failed to unzip {filename}: {ex}")
        return uncompressed_filename or filename

    def _unzip_files(self, files: List[str]) -> List[str]:
        if shutil.which(self.GUNZIP):
            files = [self._unzip_file(file) for file in files]
        else:
            warnings.warn("Unable to unzip files "
                          "(gunzip is not available on this system)")
        return files

    @staticmethod
    def _get_unique_files_from_association_tree(xml: str) -> Set[str]:
        tree = ET.fromstring(xml)
        return {element.attrib['name'] for element in tree.iter('file')}

    def _save_xml(self, payload: bytes, filename: str, destination: str):
        destination = destination or self.cache_location
        destination = os.path.abspath(destination)
        os.makedirs(destination, exist_ok=True)
        filename = os.path.join(destination, filename)
        log.info(f"Saving Calselector association tree to {filename}")
        with open(filename, "wb") as fd:
            fd.write(payload)

    def get_associated_files(self, datasets: List[str], *, mode: str = "raw",
                             savexml: bool = False, destination: str = None) -> List[str]:
        """
        Invoke Calselector service to find calibration files associated to the provided datasets.

        Parameters
        ----------
        datasets : list of strings
            List of datasets for which calibration files should be retrieved.
        mode : string
            Calselector mode: 'raw' (default) for raw calibrations,
             or 'processed' for processed calibrations.
        savexml : bool
            If true, save to disk the XML association tree returned by Calselector.
        destination : string
            Directory where the XML files are saved (default = astropy cache).

        Returns
        -------
        files :
            List of unique datasets associated to the input datasets.
        """
        mode = "Raw2Raw" if mode == "raw" else "Raw2Master"
        post_data = {"dp_id": datasets, "mode": mode}
        response = self._session.post(self.CALSELECTOR_URL, data=post_data)
        response.raise_for_status()
        associated_files = set()
        content_type = response.headers['Content-Type']
        # Calselector can return one or more XML association trees depending on the input.
        # For a single dataset it returns one XML and content-type = 'application/xml'
        if 'application/xml' in content_type:
            filename = self._get_filename_from_response(response)
            xml = response.content
            associated_files.update(self._get_unique_files_from_association_tree(xml))
            if savexml:
                self._save_xml(xml, filename, destination)
        # For multiple datasets it returns a multipart message
        elif 'multipart/form-data' in content_type:
            msg = email.message_from_string(f'Content-Type: {content_type}\r\n' + response.content.decode())
            for part in msg.get_payload():
                filename = part.get_filename()
                xml = part.get_payload(decode=True)
                associated_files.update(self._get_unique_files_from_association_tree(xml))
                if savexml:
                    self._save_xml(xml, filename, destination)
        else:
            raise CalSelectorError(f"Unexpected content-type '{content_type}' for {response.url}")

        # remove input datasets from calselector results
        return list(associated_files.difference(set(datasets)))

    @deprecated_renamed_argument(('request_all_objects', 'request_id'), (None, None), since=['0.4.7', '0.4.7'])
    def retrieve_data(self, datasets, *, continuation=False, destination=None, with_calib=None,
                      request_all_objects=False, unzip=True, request_id=None):
        """
        Retrieve a list of datasets form the ESO archive.

        Parameters
        ----------
        datasets : list of strings or string
            List of datasets strings to retrieve from the archive.
        destination: string
            Directory where the files are copied.
            Files already found in the destination directory are skipped,
            unless continuation=True.
            Default to astropy cache.
        continuation : bool
            Force the retrieval of data that are present in the destination
            directory.
        with_calib : string
            Retrieve associated calibration files: None (default), 'raw' for
            raw calibrations, or 'processed' for processed calibrations.
        unzip : bool
            Unzip compressed files from the archive after download. `True` by
            default.

        Returns
        -------
        files : list of strings or string
            List of files that have been locally downloaded from the archive.

        Examples
        --------
        >>> dptbl = Eso.query_instrument('apex', pi_coi='ginsburg')
        >>> dpids = [row['DP.ID'] for row in dptbl if 'Map' in row['Object']]
        >>> files = Eso.retrieve_data(dpids)

        """
        return_string = False
        if isinstance(datasets, str):
            return_string = True
            datasets = [datasets]

        if with_calib and with_calib not in ('raw', 'processed'):
            raise ValueError("Invalid value for 'with_calib'. "
                             "It must be 'raw' or 'processed'")

        associated_files = []
        if with_calib:
            log.info(f"Retrieving associated '{with_calib}' calibration files ...")
            try:
                # batch calselector requests to avoid possible issues on the ESO server
                BATCH_SIZE = 100
                sorted_datasets = sorted(datasets)
                for i in range(0, len(sorted_datasets), BATCH_SIZE):
                    associated_files += self.get_associated_files(sorted_datasets[i:i + BATCH_SIZE], mode=with_calib)
                associated_files = list(set(associated_files))
                log.info(f"Found {len(associated_files)} associated files")
            except Exception as ex:
                log.error(f"Failed to retrieve associated files: {ex}")

        all_datasets = datasets + associated_files
        log.info("Downloading datasets ...")
        files = self._download_eso_files(all_datasets, destination, continuation)
        if unzip:
            files = self._unzip_files(files)
        log.info("Done!")
        return files[0] if files and len(files) == 1 and return_string else files

    def query_apex_quicklooks(self, *, project_id=None, help=False,
                              open_form=False, cache=True, **kwargs):
        """
        APEX data are distributed with quicklook products identified with a
        different name than other ESO products.  This query tool searches by
        project ID or any other supported keywords.

        Examples
        --------
        >>> tbl = Eso.query_apex_quicklooks(project_id='093.C-0144')
        >>> files = Eso.retrieve_data(tbl['Product ID'])
        """

        apex_query_url = 'http://archive.eso.org/wdb/wdb/eso/apex_product/form'

        table = None
        if open_form:
            webbrowser.open(apex_query_url)
        elif help:
            return self._print_instrument_help(apex_query_url, 'apex')
        else:

            payload = {'wdbo': 'csv/download'}
            if project_id is not None:
                payload['prog_id'] = project_id
            payload.update(kwargs)

            apex_form = self._request("GET", apex_query_url, cache=cache)
            apex_response = self._activate_form(
                apex_form, form_id='queryform', form_index=0, inputs=payload,
                cache=cache, method='application/x-www-form-urlencoded')

            content = apex_response.content
            if _check_response(content):
                # First line is always garbage
                content = content.split(b'\n', 1)[1]
                try:
                    table = Table.read(BytesIO(content), format="ascii.csv",
                                       guess=False,  # header_start=1,
                                       comment="#", encoding='utf-8')
                except ValueError as ex:
                    if 'the encoding parameter is not supported on Python 2' in str(ex):
                        # astropy python2 does not accept the encoding parameter
                        table = Table.read(BytesIO(content), format="ascii.csv",
                                           guess=False,
                                           comment="#")
                    else:
                        raise ex
            else:
                raise RemoteServiceError("Query returned no results")

            return table

    def _print_query_help(self, url, *, cache=True):
        """
        Download a form and print it in a quasi-human-readable way
        """
        log.info("List of accepted column_filters parameters.")
        log.info("The presence of a column in the result table can be "
                 "controlled if prefixed with a [ ] checkbox.")
        log.info("The default columns in the result table are shown as "
                 "already ticked: [x].")

        result_string = []

        resp = self._request("GET", url, cache=cache)
        doc = BeautifulSoup(resp.content, 'html5lib')
        form = doc.select("html body form pre")[0]
        # Unwrap all paragraphs
        paragraph = form.find('p')
        while paragraph:
            paragraph.unwrap()
            paragraph = form.find('p')
        # For all sections
        for section in form.select("table"):
            section_title = "".join(section.stripped_strings)
            section_title = "\n".join(["", section_title,
                                       "-" * len(section_title)])
            result_string.append(section_title)
            checkbox_name = ""
            checkbox_value = ""
            for tag in section.next_siblings:
                if tag.name == u"table":
                    break
                elif tag.name == u"input":
                    if tag.get(u'type') == u"checkbox":
                        checkbox_name = tag['name']
                        checkbox_value = u"[x]" if ('checked' in tag.attrs) else u"[ ]"
                        name = ""
                        value = ""
                    else:
                        name = tag['name']
                        value = ""
                elif tag.name == u"select":
                    options = []
                    for option in tag.select("option"):
                        options += ["{0} ({1})".format(option['value'], "".join(option.stripped_strings))]
                    name = tag[u"name"]
                    value = ", ".join(options)
                else:
                    name = ""
                    value = ""
                if u"tab_" + name == checkbox_name:
                    checkbox = checkbox_value
                else:
                    checkbox = "   "
                if name != u"":
                    result_string.append("{0} {1}: {2}"
                                         .format(checkbox, name, value))

        log.info("\n".join(result_string))
        return result_string

    def _print_surveys_help(self, url, *, cache=True):
        """
        Download a form and print it in a quasi-human-readable way
        """
        log.info("List of the parameters accepted by the "
                 "surveys query.")
        log.info("The presence of a column in the result table can be "
                 "controlled if prefixed with a [ ] checkbox.")
        log.info("The default columns in the result table are shown as "
                 "already ticked: [x].")

        result_string = []

        resp = self._request("GET", url, cache=cache)
        doc = BeautifulSoup(resp.content, 'html5lib')
        form = doc.select("html body form")[0]

        # hovertext from different labels are used to give more info on forms
        helptext_dict = {abbr['title'].split(":")[0].strip(): ":".join(abbr['title'].split(":")[1:])
                         for abbr in form.find_all('abbr')
                         if 'title' in abbr.attrs and ":" in abbr['title']}

        for fieldset in form.select('fieldset'):
            legend = fieldset.select('legend')
            if len(legend) > 1:
                raise ValueError("Form parsing error: too many legends.")
            elif len(legend) == 0:
                continue
            section_title = "\n\n" + "".join(legend[0].stripped_strings) + "\n"

            result_string.append(section_title)

            for section in fieldset.select('table'):

                checkbox_name = ""
                checkbox_value = ""
                for tag in section.next_elements:
                    if tag.name == u"table":
                        break
                    elif tag.name == u"input":
                        if tag.get(u'type') == u"checkbox":
                            checkbox_name = tag['name']
                            checkbox_value = (u"[x]"
                                              if ('checked' in tag.attrs)
                                              else u"[ ]")
                            name = ""
                            value = ""
                        else:
                            name = tag['name']
                            value = ""
                    elif tag.name == u"select":
                        options = []
                        for option in tag.select("option"):
                            options += ["{0} ({1})".format(option['value'] if 'value' in option else "",
                                                           "".join(option.stripped_strings))]
                        name = tag[u"name"]
                        value = ", ".join(options)
                    else:
                        name = ""
                        value = ""
                    if u"tab_" + name == checkbox_name:
                        checkbox = checkbox_value
                    else:
                        checkbox = "   "
                    if name != u"":
                        result_string.append("{0} {1}: {2}"
                                             .format(checkbox, name, value))
                        if name.strip() in helptext_dict:
                            result_string.append(helptext_dict[name.strip()])

        log.info("\n".join(result_string))
        return result_string


Eso = EsoClass()
