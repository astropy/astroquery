# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
=====================
ESO Astroquery Module
=====================

European Southern Observatory (ESO)

"""

import base64
import email
import functools
import json
import os
import os.path
import sys
import re
import shutil
import subprocess
import time
import warnings
import xml.etree.ElementTree as ET
from typing import List, Optional, Tuple, Dict, Set, Union

import astropy.table
import astropy.utils.data
import keyring
import requests.exceptions
from astropy.table import Table, Column
from astropy.utils.decorators import deprecated_renamed_argument
from bs4 import BeautifulSoup
from pyvo.dal import TAPService
import pyvo.dal.exceptions as pde

from astroquery import log
from . import conf
from ..exceptions import RemoteServiceError, LoginError
from ..query import QueryWithLogin
from ..utils import schema
from .utils import py2adql, _split_str_as_list_of_str, \
    adql_sanitize_val, are_coords_valid, issue_table_length_warnings

__doctest_skip__ = ['EsoClass.*']


class CalSelectorError(Exception):
    """
    Raised on failure to parse CalSelector's response.
    """


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


class EsoNames:
    raw_table = "dbo.raw"
    phase3_table = "ivoa.ObsCore"
    raw_instruments_column = "instrument"
    phase3_collections_column = "obs_collection"

    @staticmethod
    def ist_table(instrument_name):
        return f"ist.{instrument_name}"


def unlimited_max_rec(func):
    """
    decorator to overwrite the ROW LIMIT
    for specific queries
    """
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        if not isinstance(self, EsoClass):
            raise ValueError(f"Expecting EsoClass, found {type(self)}")

        tmpvar = self.maxrec
        try:
            self.maxrec = sys.maxsize
            result = func(self, *args, **kwargs)
        finally:
            self.maxrec = tmpvar
        return result
    return wrapper


class EsoClass(QueryWithLogin):
    USERNAME = conf.username
    CALSELECTOR_URL = "https://archive.eso.org/calselector/v1/associations"
    DOWNLOAD_URL = "https://dataportal.eso.org/dataPortal/file/"
    AUTH_URL = "https://www.eso.org/sso/oidc/token"
    GUNZIP = "gunzip"

    def __init__(self):
        super().__init__()
        self._instruments: Optional[List[str]] = None
        self._collections: Optional[List[str]] = None
        self._auth_info: Optional[AuthInfo] = None
        self._hash = None
        self._maxrec = None

        self.maxrec = conf.row_limit

    @property
    def maxrec(self):
        return self._maxrec

    @maxrec.setter
    def maxrec(self, value):
        mr = sys.maxsize
        if value:
            if value > 0:
                mr = value
        self._maxrec = mr

    def tap_url(self) -> str:
        url = os.environ.get('ESO_TAP_URL', conf.tap_url)
        return url

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

    def _login(self, *args, username: str = None, store_password: bool = False,
               reenter_password: bool = False, **kwargs) -> bool:
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

    def try_download_pyvo_table(self,
                                query_str: str,
                                tap: TAPService) -> Optional[astropy.table.Table]:
        table_to_return = None

        def message(query_str):
            return (f"Error executing the following query:\n\n"
                    f"{query_str}\n\n"
                    "See examples here: https://archive.eso.org/tap_obs/examples\n\n")

        try:
            table_to_return = tap.search(query_str, maxrec=self.maxrec).to_table()
        except pde.DALQueryError as e:
            raise pde.DALQueryError(message(query_str)) from e
        except pde.DALFormatError as e:
            raise pde.DALFormatError(message(query_str) + f"cause: {e.cause}") from e
        except Exception as e:
            raise RuntimeError(
                f"Unhandled exception {type(e)}\n" + message(query_str)) from e

        return table_to_return

    def query_tap_service(self,
                          query_str: str,
                          ) -> Optional[astropy.table.Table]:
        """
        returns an astropy.table.Table from an adql query string
        Example use:
        eso._query_tap_service("Select * from ivoa.ObsCore")
        """
        table_to_return = None

        table_to_return = self.try_download_pyvo_table(query_str,
                                                       TAPService(self.tap_url()))

        issue_table_length_warnings(table_to_return, self.maxrec)

        return table_to_return

    @unlimited_max_rec
    def list_instruments(self) -> List[str]:
        """ List all the available instrument-specific queries offered by the ESO archive.

        Returns
        -------
        instrument_list : list of strings
        """
        if self._instruments is None:
            self._instruments = []
            query_str = ("select table_name from TAP_SCHEMA.tables "
                         "where schema_name='ist' order by table_name")
            res = self.query_tap_service(query_str)["table_name"].data
            self._instruments = list(map(lambda x: x.split(".")[1], res))
        return self._instruments

    @unlimited_max_rec
    def list_collections(self) -> List[str]:
        """ List all the available collections (phase 3) in the ESO archive.

        Returns
        -------
        collection_list : list of strings
        cache : bool
            Defaults to True. If set overrides global caching behavior.
            See :ref:`caching documentation <astroquery_cache>`.
        """
        if self._collections is None:
            self._collections = []
            t = EsoNames.phase3_table
            c = EsoNames.phase3_collections_column
            query_str = f"select distinct {c} from {t}"
            res = self.query_tap_service(query_str)[c].data
            self._collections = list(res)
        return self._collections

    @unlimited_max_rec
    def print_table_help(self, table_name: str) -> None:
        """
        Prints the columns contained in a given table
        """
        help_query = (
            f"select column_name, datatype from TAP_SCHEMA.columns "
            f"where table_name = '{table_name}'")
        available_cols = self.query_tap_service(help_query)
        nlines = len(available_cols) + 2
        n_ = astropy.conf.max_lines
        astropy.conf.max_lines = nlines
        log.info(f"\nColumns present in the table {table_name}:\n{available_cols}\n")
        astropy.conf.max_lines = n_

    def _query_on_allowed_values(
            self,
            table_name: str,
            column_name: str,
            allowed_values: Union[List[str], str] = None, *,
            ra: float = None, dec: float = None, radius: float = None,
            columns: Union[List, str] = None,
            top: int = None,
            count_only: bool = False,
            print_help: bool = False,
            **kwargs) -> Union[astropy.table.Table, int]:
        """
        Query instrument- or collection-specific data contained in the ESO archive.
         - instrument-specific data is raw
         - collection-specific data is processed
        """
        columns = columns or []
        filters = {**dict(kwargs)}

        if print_help:
            self.print_table_help(table_name)
            return

        if (('box' in filters)
            or ('coord1' in filters)
                or ('coord2' in filters)):
            message = 'box, coord1 and coord2 are deprecated; use ra, dec and radius instead'
            raise ValueError(message)

        if not are_coords_valid(ra, dec, radius):
            message = "Either all three (ra, dec, radius) must be present or none of them.\n"
            message += f"Values provided: ra = {ra}, dec = {dec}, radius = {radius}"
            raise ValueError(message)

        where_collections_strlist = []
        if allowed_values:
            if isinstance(allowed_values, str):
                allowed_values = _split_str_as_list_of_str(allowed_values)

            allowed_values = list(map(lambda x: f"'{x.strip()}'", allowed_values))
            where_collections_strlist = [f"{column_name} in (" + ", ".join(allowed_values) + ")"]

        where_constraints_strlist = [f"{k} = {adql_sanitize_val(v)}" for k, v in filters.items()]
        where_constraints = where_collections_strlist + where_constraints_strlist
        query = py2adql(table=table_name, columns=columns,
                        ra=ra, dec=dec, radius=radius,
                        where_constraints=where_constraints,
                        count_only=count_only,
                        top=top)

        table_to_return = self.query_tap_service(query_str=query)

        if count_only:  # this below is an int, not a table
            table_to_return = list(table_to_return[0].values())[0]

        return table_to_return

    def query_collections(
            self,
            collections: Union[List[str], str], *,
            ra: float = None, dec: float = None, radius: float = None,
            columns: Union[List, str] = None,
            top: int = None,
            count_only: bool = False,
            print_help=False,
            **kwargs) -> Union[astropy.table.Table, int]:
        return self._query_on_allowed_values(table_name=EsoNames.phase3_table,
                                             column_name=EsoNames.phase3_collections_column,
                                             allowed_values=collections,
                                             ra=ra, dec=dec, radius=radius,
                                             columns=columns,
                                             top=top,
                                             count_only=count_only,
                                             print_help=print_help,
                                             **kwargs)

    def query_main(
            self,
            instruments: Union[List[str], str] = None, *,
            ra: float = None, dec: float = None, radius: float = None,
            columns: Union[List, str] = None,
            top: int = None,
            count_only: bool = False,
            print_help=False,
            **kwargs) -> Union[astropy.table.Table, int]:
        return self._query_on_allowed_values(table_name=EsoNames.raw_table,
                                             column_name=EsoNames.raw_instruments_column,
                                             allowed_values=instruments,
                                             ra=ra, dec=dec, radius=radius,
                                             columns=columns,
                                             top=top,
                                             count_only=count_only,
                                             print_help=print_help,
                                             **kwargs)

    # ex query_instrument
    def query_instrument(
            self,
            instrument: str, *,
            ra: float = None, dec: float = None, radius: float = None,
            columns: Union[List, str] = None,
            top: int = None,
            count_only: bool = False,
            print_help=False,
            **kwargs) -> Union[astropy.table.Table, int]:
        return self._query_on_allowed_values(table_name=EsoNames.ist_table(instrument),
                                             column_name=None,
                                             allowed_values=None,
                                             ra=ra, dec=dec, radius=radius,
                                             columns=columns,
                                             top=top,
                                             count_only=count_only,
                                             print_help=print_help,
                                             **kwargs)

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
                "GET", f"https://archive.eso.org/hdr?DpId={dp_id}",
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
        for r in result:
            for (column, column_type) in zip(columns, column_types):
                if column not in r:
                    r[column] = column_type()
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
                    log.info(f"Successfully downloaded dataset {file_id} to {filename}")
            except requests.HTTPError as http_error:
                if http_error.response.status_code == 401:
                    log.error(f"Access denied to {file_link}")
                else:
                    log.error(f"Failed to download {file_link}. {http_error}")
            except RuntimeError as ex:
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
            msg = email.message_from_string(
                f'Content-Type: {content_type}\r\n' + response.content.decode())
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

    @deprecated_renamed_argument(('request_all_objects', 'request_id'), (None, None),
                                 since=['0.4.7', '0.4.7'])
    def retrieve_data(self, datasets, *, continuation=False, destination=None,
                      with_calib=None, unzip=True,
                      request_all_objects=None, request_id=None):
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
        _ = request_all_objects, request_id
        return_string = False
        if isinstance(datasets, str):
            return_string = True
            datasets = [datasets]
        if isinstance(datasets, astropy.table.column.Column):
            datasets = list(datasets)

        if with_calib and with_calib not in ('raw', 'processed'):
            raise ValueError("Invalid value for 'with_calib'. "
                             "It must be 'raw' or 'processed'")

        associated_files = []
        if with_calib:
            log.info(f"Retrieving associated '{with_calib}' calibration files ...")
            try:
                # batch calselector requests to avoid possible issues on the ESO server
                batch_size = 100
                sorted_datasets = sorted(datasets)
                for i in range(0, len(sorted_datasets), batch_size):
                    associated_files += self.get_associated_files(
                        sorted_datasets[i:i + batch_size], mode=with_calib)
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

    @deprecated_renamed_argument(('open_form', 'help'), (None, 'print_help'),
                                 since=['0.4.8', '0.4.8'])
    def query_apex_quicklooks(self, *, project_id=None, print_help=False,
                              open_form=False, **kwargs):
        """
        APEX data are distributed with quicklook products identified with a
        different name than other ESO products.  This query tool searches by
        project ID or any other supported keywords.

        Examples
        --------
        >>> tbl = ...
        >>> files = ...
        """
        # TODO All this function
        _ = project_id, print_help, open_form, kwargs
        raise NotImplementedError


Eso = EsoClass()
