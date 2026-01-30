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

import astropy.utils.data
import keyring
import requests
from astropy.table import Table, Column
from astropy.utils.decorators import deprecated_renamed_argument
from bs4 import BeautifulSoup
from pyvo.dal import TAPService
from pyvo.dal.exceptions import DALQueryError, DALFormatError

from astroquery import log
from . import conf
from ..exceptions import RemoteServiceError, LoginError, \
    NoResultsWarning, MaxResultsWarning
from ..query import QueryWithLogin
from ..utils import schema
from .utils import _UserParams, raise_if_coords_not_valid, _reorder_columns, \
    _raise_if_has_deprecated_keys, _build_adql_string, \
    DEFAULT_LEAD_COLS_PHASE3, DEFAULT_LEAD_COLS_RAW


__all__ = ['Eso', 'EsoClass']


class CalSelectorError(Exception):
    """
    Raised on failure to parse CalSelector's response.
    """


class _AuthInfo:
    def __init__(self, username: str, token: str):
        self.username = username
        self.token = token
        self.expiration_time = self._get_exp_time_from_token()

    def _get_exp_time_from_token(self) -> int:
        # "manual" decoding since jwt is not installed
        decoded_token = base64.b64decode(self.token.split(".")[1] + "==")
        return int(json.loads(decoded_token)['exp'])

    def _expired(self) -> bool:
        # we anticipate the expiration time by 10 minutes to avoid issues
        return time.time() > self.expiration_time - 600


class _EsoNames:
    raw_table = "dbo.raw"
    phase3_table = "ivoa.ObsCore"
    raw_instruments_column = "instrument"
    phase3_surveys_column = "obs_collection"

    @staticmethod
    def ist_table(instrument_name):
        """
        Returns the name of the instrument specific table (IST)
        """
        return f"ist.{instrument_name}"

    apex_quicklooks_table = ist_table.__func__("apex_quicklooks")
    apex_quicklooks_pid_column = "project_id"


def unlimited_maxrec(func):
    """
    decorator to overwrite maxrec for specific queries
    """
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        if not isinstance(self, EsoClass):
            raise ValueError(f"Expecting EsoClass, found {type(self)}")

        tmpvar = self.ROW_LIMIT
        try:
            self.ROW_LIMIT = sys.maxsize
            result = func(self, *args, **kwargs)
        finally:
            self.ROW_LIMIT = tmpvar
        return result
    return wrapper


class EsoClass(QueryWithLogin):
    """
    User facing class to query the ESO archive
    """
    USERNAME = conf.username
    CALSELECTOR_URL = "https://archive.eso.org/calselector/v1/associations"
    DOWNLOAD_URL = "https://dataportal.eso.org/dataPortal/file/"
    AUTH_URL = "https://www.eso.org/sso/oidc/token"
    GUNZIP = "gunzip"

    def __init__(self):
        super().__init__()
        self._auth_info: Optional[_AuthInfo] = None
        self._hash = None
        self._ROW_LIMIT = None
        self.ROW_LIMIT = conf.ROW_LIMIT

    @property
    def ROW_LIMIT(self):
        """
        Getter.
        Safeguard that truncates the number of records returned by a query
        """
        return self._ROW_LIMIT

    @ROW_LIMIT.setter
    def ROW_LIMIT(self, value):
        mr = self._ROW_LIMIT

        # type check
        if not (value is None or isinstance(value, int)):
            raise TypeError(f"ROW_LIMIT attribute must be of type int or None; found {type(value)}")

        if value is None or value < 1:
            mr = sys.maxsize
        else:
            mr = value

        self._ROW_LIMIT = mr

    def _tap_url(self) -> str:
        url = conf.tap_url
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
            self._auth_info = _AuthInfo(username=username, token=token)
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

    def _login(self, username: str = None, store_password: bool = False,
               reenter_password: bool = False) -> bool:
        """
        Login to the ESO User Portal.

        Parameters
        ----------
        username : str, optional
            Username to the ESO Public Portal. If not given, it should be
            specified in the config file.
        store_password : bool, optional
            Stores the password securely in your keyring. Default is `False`.
        reenter_password : bool, optional
            Asks for the password even if it is already stored in the
            keyring. This is the way to overwrite an already stored passwork
            on the keyring. Default is `False`.
        """

        username, password = self._get_auth_info(username=username,
                                                 store_password=store_password,
                                                 reenter_password=reenter_password)

        return self._authenticate(username=username, password=password)

    def _get_auth_header(self) -> Dict[str, str]:
        if self._auth_info and self._auth_info._expired():
            raise LoginError(
                "Authentication token has expired! Please log in again."
            )
        if self._auth_info and not self._auth_info._expired():
            return {'Authorization': 'Bearer ' + self._auth_info.token}
        else:
            return {}

    def _maybe_warn_about_table_length(self, table_rowlim_plus_one, row_limit_plus_one):
        """
        Issues a warning when a table is empty or when the
        results are truncated
        """
        if len(table_rowlim_plus_one) < 1:
            warnings.warn("Query returned no results", NoResultsWarning)

        if len(table_rowlim_plus_one) == row_limit_plus_one:
            warnings.warn(f"Results truncated to {self.ROW_LIMIT}. "
                          "To retrieve all the records set to None the ROW_LIMIT attribute",
                          MaxResultsWarning)

    def _try_download_pyvo_table(self,
                                 query_str: str,
                                 tap: TAPService) -> Optional[Table]:
        table_with_an_extra_row = Table()

        def message(query_str):
            return (f"Error executing the following query:\n\n"
                    f"{query_str}\n\n"
                    "See examples here: https://archive.eso.org/tap_obs/examples\n\n"
                    f"For maximum query freedom use the query_tap method:\n\n"
                    f' >>> Eso().query_tap( "{query_str}" )\n\n')

        try:
            row_limit_plus_one = self.ROW_LIMIT
            if self.ROW_LIMIT < sys.maxsize:
                row_limit_plus_one = self.ROW_LIMIT + 1

            table_with_an_extra_row = tap.search(query=query_str, maxrec=row_limit_plus_one).to_table()
            self._maybe_warn_about_table_length(table_with_an_extra_row, row_limit_plus_one)
        except DALQueryError:
            log.error(message(query_str))
        except DALFormatError as e:
            raise DALFormatError(message(query_str) + f"cause: {e.cause}") from e
        except Exception as e:
            raise type(e)(f"{e}\n" + message(query_str)) from e

        return table_with_an_extra_row[:self.ROW_LIMIT]

    def tap(self, authenticated: bool = False) -> TAPService:

        if authenticated and not self.authenticated():
            raise LoginError(
                "It seems you are trying to issue an authenticated query without "
                "being authenticated. Possible solutions:\n"
                "1. Set the query function argument authenticated=False"
                " OR\n"
                "2. Login with your username and password: "
                "<eso_class_instance>.login(username=<your_username>"
            )

        log.debug(f"Querying from {self._tap_url()}")
        if authenticated:
            h = self._get_auth_header()
            self._session.headers = {**self._session.headers, **h}
            tap_service = TAPService(self._tap_url(), session=self._session)
        else:
            tap_service = TAPService(self._tap_url())

        return tap_service

    def query_tap(self,
                  query: str, *,
                  authenticated: bool = False,
                  ) -> Table:
        """
        Query the ESO TAP service using a free ADQL string.

        Parameters
        ----------
        query_str : str
            The ADQL query string to be executed.
        authenticated : bool, optional
            If ``True``, the query is run as an authenticated user.
            Authentication must be performed beforehand via
            :meth:`astroquery.eso.EsoClass.login`. Authenticated queries
            may be slower. Default is ``False``.

        Returns
        -------
        astropy.table.Table

        Examples
        --------
        from astroquery.eso import Eso
        eso_instance = Eso()
        eso_instance.query_tap("SELECT * FROM ivoa.ObsCore")
        """
        table_to_return = Table()
        tap_service = self.tap(authenticated)
        table_to_return = self._try_download_pyvo_table(query, tap_service)
        return table_to_return

    @unlimited_maxrec
    @deprecated_renamed_argument('cache', None, since='0.4.12')
    def list_instruments(self, cache=True) -> List[str]:
        """
        List all the available instrument-specific queries offered by the ESO archive.

        Returns
        -------
        instrument_list : list of strings
        cache : bool
            Deprecated - unused.
        """
        _ = cache  # We're aware about disregarding the argument
        query_str = ("select table_name from TAP_SCHEMA.tables "
                     "where schema_name='ist' order by table_name")
        res = self.query_tap(query_str)["table_name"].data

        l_res = list(res)

        # Remove ist.apex_quicklooks, which is not actually a raw instrument
        if _EsoNames.apex_quicklooks_table in l_res:
            l_res.remove(_EsoNames.apex_quicklooks_table)

        l_res = list(map(lambda x: x.split(".")[1], l_res))

        return l_res

    @unlimited_maxrec
    @deprecated_renamed_argument('cache', None, since='0.4.12')
    def list_surveys(self, *, cache=True) -> List[str]:
        """
        List all the available surveys (phase 3) in the ESO archive.

        Returns
        -------
        collection_list : list of strings
        cache : bool
            Deprecated - unused.
        """
        _ = cache  # We're aware about disregarding the argument
        t = _EsoNames.phase3_table
        c = _EsoNames.phase3_surveys_column
        query_str = f"select distinct {c} from {t}"
        res = list(self.query_tap(query_str)[c].data)
        return res

    @unlimited_maxrec
    def list_column(self, table_name: str) -> None:
        """
        Prints the columns contained in a given table
        """
        help_query = (
            f"select column_name, datatype, xtype, unit "
            # TODO: The column description renders output unmanageable
            # f", description "
            f"from TAP_SCHEMA.columns "
            f"where table_name = '{table_name}'")
        available_cols = self.query_tap(help_query)

        count_query = f"select count(*) from {table_name}"
        num_records = list(self.query_tap(count_query)[0].values())[0]

        with (astropy.conf.set_temp(
                "max_lines", len(available_cols) + 2),
                astropy.conf.set_temp(
                "max_width", sys.maxsize)):
            log.info(f"\nColumns present in the table {table_name}:\n{available_cols}\n"
                     f"\nNumber of records present in the table {table_name}:\n{num_records}\n")

    def _query_on_allowed_values(
        self,
        user_params: _UserParams
    ) -> Union[Table, int, str, None]:
        if user_params.print_help:
            self.list_column(user_params.table_name)
            return

        _raise_if_has_deprecated_keys(user_params.column_filters)

        raise_if_coords_not_valid(user_params.cone_ra, user_params.cone_dec, user_params.cone_radius)

        query = _build_adql_string(user_params)

        if user_params.get_query_payload:
            return query

        ret_table = self.query_tap(query=query, authenticated=user_params.authenticated)
        return list(ret_table[0].values())[0] if user_params.count_only else ret_table

    @deprecated_renamed_argument(('open_form', 'cache'), (None, None),
                                 since=['0.4.12', '0.4.12'])
    def query_surveys(
            self,
            surveys: Union[List[str], str] = None, *,
            cone_ra: float = None, cone_dec: float = None, cone_radius: float = None,
            columns: Union[List, str] = None,
            column_filters: Optional[dict] = None,
            top: int = None,
            count_only: bool = False,
            get_query_payload: bool = False,
            help: bool = False,
            authenticated: bool = False,
            open_form: bool = False, cache: bool = False,
    ) -> Union[Table, int, str]:
        """
        Query survey Phase 3 data contained in the ESO archive.

        Parameters
        ----------
        surveys : str or list, optional
            Name of the survey(s) to query. Should be one or more of the
            names returned by :meth:`~astroquery.eso.EsoClass.list_surveys`. If specified
            as a string, it should be a comma-separated list of survey names.
            If not specified, returns records relative to all surveys. Default is ``None``.
        cone_ra : float, optional
            Cone Search Center - Right Ascension in degrees.
        cone_dec : float, optional
            Cone Search Center - Declination in degrees.
        cone_radius : float, optional
            Cone Search Radius in degrees.
        columns : str or list of str, optional
            Name of the columns the query should return. If specified as a string,
            it should be a comma-separated list of column names.
        top : int, optional
            When set to ``N``, returns only the top ``N`` records.
        count_only : bool, optional
            If ``True``, returns only an ``int``: the count of the records
            the query would return when set to ``False``. Default is ``False``.
        get_query_payload : bool, optional
            If ``True``, returns only a ``str``: the query string that
            would be issued to the TAP service. Default is ``False``.
        help : bool, optional
            If ``True``, prints all the parameters accepted in ``column_filters``
            and ``columns``. Default is ``False``.
        authenticated : bool, optional
            If ``True``, runs the query as an authenticated user.
            Authentication must be done beforehand via
            :meth:`~astroquery.eso.EsoClass.login`. Authenticated queries may be slower.
            Default is ``False``.
        column_filters : dict or None, optional
            Constraints applied to the query in ADQL syntax,
            e.g., ``{"exp_start": "between '2024-12-31' and '2025-12-31'"}``.
            Default is ``None``.
        open_form : bool, optional
            **Deprecated** - unused.
        cache : bool, optional
            **Deprecated** - unused.

        Returns
        -------
        astropy.table.Table, str, int or None
            - By default, returns an :class:`~astropy.table.Table` containing records
              based on the specified columns and constraints.
              Returns ``None`` if the query has no results.
            - When ``count_only`` is ``True``, returns an ``int`` representing the
              record count for the specified filters.
            - When ``get_query_payload`` is ``True``, returns the query string that
              would be issued to the TAP service given the specified arguments.
        """
        _ = open_form, cache  # make explicit that we are aware these arguments are unused
        column_filters = column_filters if column_filters else {}
        user_params = _UserParams(table_name=_EsoNames.phase3_table,
                                  column_name=_EsoNames.phase3_surveys_column,
                                  allowed_values=surveys,
                                  cone_ra=cone_ra,
                                  cone_dec=cone_dec,
                                  cone_radius=cone_radius,
                                  columns=columns,
                                  column_filters=column_filters,
                                  top=top,
                                  count_only=count_only,
                                  get_query_payload=get_query_payload,
                                  print_help=help,
                                  authenticated=authenticated,
                                  )
        t = self._query_on_allowed_values(user_params=user_params)
        t = _reorder_columns(t, DEFAULT_LEAD_COLS_PHASE3)
        return t

    @deprecated_renamed_argument(('open_form', 'cache'), (None, None),
                                 since=['0.4.12', '0.4.12'])
    def query_main(
            self,
            instruments: Union[List[str], str] = None, *,
            cone_ra: float = None, cone_dec: float = None, cone_radius: float = None,
            columns: Union[List, str] = None,
            column_filters: Optional[dict] = None,
            top: int = None,
            count_only: bool = False,
            get_query_payload: bool = False,
            help: bool = False,
            authenticated: bool = False,
            open_form: bool = False, cache: bool = False,
    ) -> Union[Table, int, str]:
        """
        Query raw data from all instruments contained in the ESO archive.

        Parameters
        ----------
        instruments : str or list, optional
            Name of the instruments to filter. Should be one or more of the
            names returned by :meth:`~astroquery.eso.EsoClass.list_instruments`. If specified
            as a string, it should be a comma-separated list of instrument names.
            If not specified, returns records relative to all instruments. Default is ``None``.
        cone_ra : float, optional
            Cone Search Center - Right Ascension in degrees.
        cone_dec : float, optional
            Cone Search Center - Declination in degrees.
        cone_radius : float, optional
            Cone Search Radius in degrees.
        columns : str or list of str, optional
            Name of the columns the query should return. If specified as a string,
            it should be a comma-separated list of column names.
        top : int, optional
            When set to ``N``, returns only the top ``N`` records.
        count_only : bool, optional
            If ``True``, returns only an ``int``: the count of the records
            the query would return when set to ``False``. Default is ``False``.
        get_query_payload : bool, optional
            If ``True``, returns only a ``str``: the query string that
            would be issued to the TAP service. Default is ``False``.
        help : bool, optional
            If ``True``, prints all the parameters accepted in ``column_filters``
            and ``columns``. Default is ``False``.
        authenticated : bool, optional
            If ``True``, runs the query as an authenticated user.
            Authentication must be done beforehand via
            :meth:`~astroquery.eso.EsoClass.login`. Authenticated queries may be slower.
            Default is ``False``.
        column_filters : dict or None, optional
            Constraints applied to the query in ADQL syntax,
            e.g., ``{"exp_start": "between '2024-12-31' and '2025-12-31'"}``.
            Default is ``None``.
        open_form : bool, optional
            **Deprecated** - unused.
        cache : bool, optional
            **Deprecated** - unused.

        Returns
        -------
        astropy.table.Table, str, int or None
            - By default, returns an :class:`~astropy.table.Table` containing records
              based on the specified columns and constraints.
              Returns ``None`` if the query has no results.
            - When ``count_only`` is ``True``, returns an ``int`` representing the
              record count for the specified filters.
            - When ``get_query_payload`` is ``True``, returns the query string that
              would be issued to the TAP service given the specified arguments.
        """
        _ = open_form, cache  # make explicit that we are aware these arguments are unused
        column_filters = column_filters if column_filters else {}
        user_params = _UserParams(table_name=_EsoNames.raw_table,
                                  column_name=_EsoNames.raw_instruments_column,
                                  allowed_values=instruments,
                                  cone_ra=cone_ra,
                                  cone_dec=cone_dec,
                                  cone_radius=cone_radius,
                                  columns=columns,
                                  column_filters=column_filters,
                                  top=top,
                                  count_only=count_only,
                                  get_query_payload=get_query_payload,
                                  print_help=help,
                                  authenticated=authenticated,
                                  )
        t = self._query_on_allowed_values(user_params)
        t = _reorder_columns(t, DEFAULT_LEAD_COLS_RAW)
        return t

    @deprecated_renamed_argument(('open_form', 'cache'), (None, None),
                                 since=['0.4.12', '0.4.12'])
    def query_instrument(
            self,
            instrument: str, *,
            cone_ra: float = None, cone_dec: float = None, cone_radius: float = None,
            columns: Union[List, str] = None,
            column_filters: Optional[dict] = None,
            top: int = None,
            count_only: bool = False,
            get_query_payload: bool = False,
            help: bool = False,
            authenticated: bool = False,
            open_form: bool = False, cache: bool = False,
    ) -> Union[Table, int, str]:
        """
        Query instrument-specific raw data contained in the ESO archive.

        Parameters
        ----------
        instrument : str
            Name of the instrument from which raw data is to be queried.
            Should be ONLY ONE of the names returned by
            :meth:`~astroquery.eso.EsoClass.list_instruments`.
        cone_ra : float, optional
            Cone Search Center - Right Ascension in degrees.
        cone_dec : float, optional
            Cone Search Center - Declination in degrees.
        cone_radius : float, optional
            Cone Search Radius in degrees.
        columns : str or list of str, optional
            Name of the columns the query should return. If specified as a string,
            it should be a comma-separated list of column names.
        top : int, optional
            When set to ``N``, returns only the top ``N`` records.
        count_only : bool, optional
            If ``True``, returns only an ``int``: the count of the records
            the query would return when set to ``False``. Default is ``False``.
        get_query_payload : bool, optional
            If ``True``, returns only a ``str``: the query string that
            would be issued to the TAP service. Default is ``False``.
        help : bool, optional
            If ``True``, prints all the parameters accepted in ``column_filters``
            and ``columns``. Default is ``False``.
        authenticated : bool, optional
            If ``True``, runs the query as an authenticated user.
            Authentication must be done beforehand via
            :meth:`~astroquery.eso.EsoClass.login`. Note that authenticated queries are slower.
            Default is ``False``.
        column_filters : dict or None, optional
            Constraints applied to the query in ADQL syntax,
            e.g., ``{"exp_start": "between '2024-12-31' and '2025-12-31'"}``.
            Default is ``None``.
        open_form : bool, optional
            **Deprecated** - unused.
        cache : bool, optional
            **Deprecated** - unused.

        Returns
        -------
        astropy.table.Table, str, int, or None
            - By default, returns an :class:`~astropy.table.Table` containing records
              based on the specified columns and constraints. Returns ``None`` if no results.
            - When ``count_only`` is ``True``, returns an ``int`` representing the
              record count for the specified filters.
            - When ``get_query_payload`` is ``True``, returns the query string that
              would be issued to the TAP service given the specified arguments.
        """
        _ = open_form, cache  # make explicit that we are aware these arguments are unused
        column_filters = column_filters if column_filters else {}
        user_params = _UserParams(table_name=_EsoNames.ist_table(instrument),
                                  column_name=None,
                                  allowed_values=None,
                                  cone_ra=cone_ra,
                                  cone_dec=cone_dec,
                                  cone_radius=cone_radius,
                                  columns=columns,
                                  column_filters=column_filters,
                                  top=top,
                                  count_only=count_only,
                                  get_query_payload=get_query_payload,
                                  print_help=help,
                                  authenticated=authenticated)
        t = self._query_on_allowed_values(user_params)
        t = _reorder_columns(t, DEFAULT_LEAD_COLS_RAW)
        return t

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
        for item in result:
            for (column, column_type) in zip(columns, column_types):
                if column not in item:
                    item[column] = column_type()
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

    def retrieve_data(self, datasets, *, continuation=False, destination=None,
                      with_calib=None, unzip=True):
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
        dptbl = Eso.query_instrument('apex', pi_coi='ginsburg')
        dpids = [row['DP.ID'] for row in dptbl if 'Map' in row['Object']]
        files = Eso.retrieve_data(dpids)

        """
        return_string = False
        if isinstance(datasets, str):
            return_string = True
            datasets = [datasets]
        if isinstance(datasets, Column):
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

    @deprecated_renamed_argument(('open_form', 'cache'), (None, None),
                                 since=['0.4.12', '0.4.12'])
    def query_apex_quicklooks(self,
                              project_id: Union[List[str], str] = None, *,
                              columns: Union[List, str] = None,
                              column_filters: Optional[dict] = None,
                              top: int = None,
                              count_only: bool = False,
                              get_query_payload: bool = False,
                              help: bool = False,
                              authenticated: bool = False,
                              open_form: bool = False, cache: bool = False,
                              ) -> Union[Table, int, str]:
        """
        APEX data are distributed with quicklook products identified with a
        different name than other ESO products. This query tool searches by
        project ID or any other supported keywords.

        Parameters
        ----------
        project_id : str
            ID of the project from which APEX quicklook data is to be queried.
        columns : str or list of str, optional
            Name of the columns the query should return. If specified as a string,
            it should be a comma-separated list of column names.
        top : int, optional
            When set to ``N``, returns only the top ``N`` records.
        count_only : bool, optional
            If ``True``, returns only an ``int``: the count of the records
            the query would return when set to ``False``. Default is ``False``.
        get_query_payload : bool, optional
            If ``True``, returns only a ``str``: the query string that
            would be issued to the TAP service. Default is ``False``.
        help : bool, optional
            If ``True``, prints all the parameters accepted in ``column_filters``
            and ``columns``. Default is ``False``.
        authenticated : bool, optional
            If ``True``, runs the query as an authenticated user.
            Authentication must be done beforehand via
            :meth:`~astroquery.eso.EsoClass.login`. Note that authenticated queries
            are slower. Default is ``False``.
        column_filters : dict or None, optional
            Constraints applied to the query in ADQL syntax,
            e.g., ``{"exp_start": "between '2024-12-31' and '2025-12-31'"}``.
            Default is ``None``.
        open_form : bool, optional
            **Deprecated** - unused.
        cache : bool, optional
            **Deprecated** - unused.

        Returns
        -------
        astropy.table.Table, str, int, or None
            - By default, returns an :class:`~astropy.table.Table` containing records
              based on the specified columns and constraints. Returns ``None`` if no results.
            - When ``count_only`` is ``True``, returns an ``int`` representing the
              record count for the specified filters.
            - When ``get_query_payload`` is ``True``, returns the query string that
              would be issued to the TAP service given the specified arguments.
        """
        _ = open_form, cache  # make explicit that we are aware these arguments are unused
        column_filters = column_filters if column_filters else {}
        user_params = _UserParams(table_name=_EsoNames.apex_quicklooks_table,
                                  column_name=_EsoNames.apex_quicklooks_pid_column,
                                  allowed_values=project_id,
                                  cone_ra=None, cone_dec=None, cone_radius=None,
                                  columns=columns,
                                  column_filters=column_filters,
                                  top=top,
                                  count_only=count_only,
                                  get_query_payload=get_query_payload,
                                  print_help=help,
                                  authenticated=authenticated)
        return self._query_on_allowed_values(user_params)


Eso = EsoClass()
