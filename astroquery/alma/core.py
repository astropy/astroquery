# Licensed under a 3-clause BSD style license - see LICENSE.rst

import os.path
import keyring
import numpy as np
import re
import tarfile
import string
import requests
import warnings

from pkg_resources import resource_filename
from bs4 import BeautifulSoup
import pyvo
from urllib.parse import urljoin

from astropy.table import Table, Column, vstack
from astroquery import log
from astropy.utils.console import ProgressBar
from astropy import units as u
from astropy.time import Time

try:
    from pyvo.dal.sia2 import SIA2_PARAMETERS_DESC, SIA2Service
except ImportError:
    # Can be removed once min version of pyvo is 1.5
    from pyvo.dal.sia2 import SIA_PARAMETERS_DESC as SIA2_PARAMETERS_DESC
    from pyvo.dal.sia2 import SIAService as SIA2Service

from ..exceptions import LoginError
from ..utils import commons
from ..utils.process_asyncs import async_to_sync
from ..query import BaseQuery, QueryWithLogin, BaseVOQuery
from .tapsql import (_gen_pos_sql, _gen_str_sql, _gen_numeric_sql,
                     _gen_band_list_sql, _gen_datetime_sql, _gen_pol_sql, _gen_pub_sql,
                     _gen_science_sql, _gen_spec_res_sql, ALMA_DATE_FORMAT)
from . import conf, auth_urls
from astroquery.exceptions import CorruptDataWarning

__all__ = {'AlmaClass', 'ALMA_BANDS'}

__doctest_skip__ = ['AlmaClass.*']


# Map from ALMA ObsCore result to ALMA original query result
# The map is provided in order to preserve the name of the columns in the
# original ALMA query original results and make it backwards compatible
# key - current column, value - original column name
_OBSCORE_TO_ALMARESULT = {
    'proposal_id': 'Project code',
    'target_name': 'Source name',
    's_ra': 'RA',
    's_dec': 'Dec',
    'gal_longitude': 'Galactic longitude',
    'gal_latitude': 'Galactic latitude',
    'band_list': 'Band',
    's_region': 'Footprint',
    'em_resolution': 'Frequency resolution',
    'antenna_arrays': 'Array',
    'is_mosaic': 'Mosaic',
    't_exptime': 'Integration',
    'obs_release_date': 'Release date',
    'frequency_support': 'Frequency support',
    'velocity_resolution': 'Velocity resolution',
    'pol_states': 'Pol products',
    't_min': 'Observation date',
    'obs_creator_name': 'PI name',
    'schedblock_name': 'SB name',
    'proposal_authors': 'Proposal authors',
    'sensitivity_10kms': 'Line sensitivity (10 km/s)',
    'cont_sensitivity_bandwidth': 'Continuum sensitivity',
    'pwv': 'PWV',
    'group_ous_uid': 'Group ous id',
    'member_ous_uid': 'Member ous id',
    'asdm_uid': 'Asdm uid',
    'obs_title': 'Project title',
    'type': 'Project type',
    'scan_intent': 'Scan intent',
    's_fov': 'Field of view',
    'spatial_scale_max': 'Largest angular scale',
    'qa2_passed': 'QA2 Status',
    #  TODO	COUNT
    'science_keyword': 'Science keyword',
    'scientific_category': 'Scientific category'
}


ALMA_BANDS = {
    '3': (84*u.GHz, 116*u.GHz),
    '4': (125*u.GHz, 163*u.GHz),
    '5': (163*u.GHz, 211*u.GHz),
    '6': (211*u.GHz, 275*u.GHz),
    '7': (275*u.GHz, 373*u.GHz),
    '8': (385*u.GHz, 500*u.GHz),
    '9': (602*u.GHz, 720*u.GHz),
    '10': (787*u.GHz, 950*u.GHz)
}


ALMA_FORM_KEYS = {
    'Position': {
        'Source name (astropy Resolver)': ['source_name_resolver',
                                           'SkyCoord.from_name', _gen_pos_sql],
        'Source name (ALMA)': ['source_name_alma', 'target_name', _gen_str_sql],
        'RA Dec (Sexagesimal)': ['ra_dec', 's_ra, s_dec', _gen_pos_sql],
        'Galactic (Degrees)': ['galactic', 'gal_longitude, gal_latitude',
                               _gen_pos_sql],
        'Angular resolution (arcsec)': ['spatial_resolution',
                                        'spatial_resolution', _gen_numeric_sql],
        'Largest angular scale (arcsec)': ['spatial_scale_max',
                                           'spatial_scale_max', _gen_numeric_sql],
        'Field of view (arcsec)': ['fov', 's_fov', _gen_numeric_sql]
    },
    'Energy': {
        'Frequency (GHz)': ['frequency', 'frequency', _gen_numeric_sql],
        'Bandwidth (Hz)': ['bandwidth', 'bandwidth', _gen_numeric_sql],
        'Spectral resolution (KHz)': ['spectral_resolution',
                                      'em_resolution', _gen_spec_res_sql],
        'Band': ['band_list', 'band_list', _gen_band_list_sql]
    },
    'Time': {
        'Observation date': ['start_date', 't_min', _gen_datetime_sql],
        'Integration time (s)': ['integration_time', 't_exptime',
                                 _gen_numeric_sql]
    },
    'Polarization': {
        'Polarisation type (Single, Dual, Full)': ['polarisation_type',
                                                   'pol_states', _gen_pol_sql]
    },
    'Observation': {
        'Line sensitivity (10 km/s) (mJy/beam)': ['line_sensitivity',
                                                  'sensitivity_10kms',
                                                  _gen_numeric_sql],
        'Continuum sensitivity (mJy/beam)': ['continuum_sensitivity',
                                             'cont_sensitivity_bandwidth',
                                             _gen_numeric_sql],
        'Water vapour (mm)': ['water_vapour', 'pvw', _gen_numeric_sql]
    },
    'Project': {
        'Project code': ['project_code', 'proposal_id', _gen_str_sql],
        'Project title': ['project_title', 'obs_title', _gen_str_sql],
        'PI name': ['pi_name', 'obs_creator_name', _gen_str_sql],
        'Proposal authors': ['proposal_authors', 'proposal_authors', _gen_str_sql],
        'Project abstract': ['project_abstract', 'proposal_abstract', _gen_str_sql],
        'Publication count': ['publication_count', 'NA', _gen_str_sql],
        'Science keyword': ['science_keyword', 'science_keyword', _gen_str_sql]
    },
    'Publication': {
        'Bibcode': ['bibcode', 'bib_reference', _gen_str_sql],
        'Title': ['pub_title', 'pub_title', _gen_str_sql],
        'First author': ['first_author', 'first_author', _gen_str_sql],
        'Authors': ['authors', 'authors', _gen_str_sql],
        'Abstract': ['pub_abstract', 'pub_abstract', _gen_str_sql],
        'Year': ['publication_year', 'pub_year', _gen_numeric_sql]
    },
    'Options': {
        'Public data only': ['public_data', 'data_rights', _gen_pub_sql],
        'Science observations only': ['science_observation',
                                      'science_observation', _gen_science_sql]
    }
}


# used to lookup the TAP service on an ARC
TAP_SERVICE_PATH = 'tap'

# standard ID URI to look for when expanding TAR files
DATALINK_STANDARD_ID = 'ivo://ivoa.net/std/DataLink#links-1.0'

# used to lookup the DataLink service on an ARC
DATALINK_SERVICE_PATH = 'datalink/sync'

# used to lookup the SIA service on an ARC
SIA_SERVICE_PATH = 'sia2'


def _gen_sql(payload):
    sql = 'select * from ivoa.obscore'
    where = ''
    unused_payload = payload.copy()
    if payload:
        for constraint in payload:
            for attrib_category in ALMA_FORM_KEYS.values():
                for attrib in attrib_category.values():
                    if constraint in attrib:
                        # use the value and the second entry in attrib which
                        # is the new name of the column
                        val = payload[constraint]
                        if constraint == 'em_resolution':
                            # em_resolution does not require any transformation
                            attrib_where = _gen_numeric_sql(constraint, val)
                        else:
                            attrib_where = attrib[2](attrib[1], val)
                        if attrib_where:
                            if where:
                                where += ' AND '
                            else:
                                where = ' WHERE '
                            where += attrib_where

                        # Delete this key to see what's left over afterward
                        #
                        # Use pop to avoid the slight possibility of trying to remove
                        # an already removed key
                        unused_payload.pop(constraint)

    if unused_payload:
        # Left over (unused) constraints passed.  Let the user know.
        remaining = [f'{p} -> {unused_payload[p]}' for p in unused_payload]
        raise TypeError(f'Unsupported arguments were passed:\n{remaining}')

    return sql + where


class AlmaAuth(BaseVOQuery, BaseQuery):
    """Authentication session information for passing credentials to an OIDC instance

    Assumes an OIDC system like Keycloak with a preconfigured client app called "oidc" to validate against.
    This does not use Tokens in the traditional OIDC sense, but rather uses the Keycloak specific endpoint
    to validate a username and password.  Passwords are then kept in a Python keyring.
    """

    _CLIENT_ID = 'oidc'
    _GRANT_TYPE = 'password'
    _INVALID_PASSWORD_MESSAGE = 'Invalid user credentials'
    _REALM_ENDPOINT = '/auth/realms/ALMA'
    _LOGIN_ENDPOINT = f'{_REALM_ENDPOINT}/protocol/openid-connect/token'
    _VERIFY_WELL_KNOWN_ENDPOINT = f'{_REALM_ENDPOINT}/.well-known/openid-configuration'

    def __init__(self):
        super().__init__()
        self._auth_hosts = auth_urls
        self._auth_host = None

    @property
    def auth_hosts(self):
        return self._auth_hosts

    @auth_hosts.setter
    def auth_hosts(self, auth_hosts):
        """
        Set the available hosts to check for login endpoints.

        Parameters
        ----------
        auth_hosts : array
            Available hosts name.  Checking each one until one returns a 200 for
            the well-known endpoint.
        """
        if auth_hosts is None:
            raise LoginError('Valid authentication hosts cannot be None')
        else:
            self._auth_hosts = auth_hosts

    def get_valid_host(self):
        if self._auth_host is None:
            for auth_url in self._auth_hosts:
                # set session cookies (they do not get set otherwise)
                url_to_check = f'https://{auth_url}{self._VERIFY_WELL_KNOWN_ENDPOINT}'
                response = self._request("HEAD", url_to_check, cache=False)

                if response.status_code == 200:
                    self._auth_host = auth_url
                    log.debug(f'Set auth host to {self._auth_host}')
                    break

        if self._auth_host is None:
            raise LoginError(f'No useable hosts to login to: {self._auth_hosts}')
        else:
            return self._auth_host

    def login(self, username, password):
        """
        Authenticate to one of the configured hosts.

        Parameters
        ----------
        username : str
            The username to authenticate with
        password : str
            The user's password
        """
        data = {
            'username': username,
            'password': password,
            'grant_type': self._GRANT_TYPE,
            'client_id': self._CLIENT_ID
        }

        login_url = f'https://{self.get_valid_host()}{self._LOGIN_ENDPOINT}'
        log.info(f'Authenticating {username} on {login_url}.')
        login_response = self._request('POST', login_url, data=data, cache=False)
        json_auth = login_response.json()

        if 'error' in json_auth:
            log.debug(f'{json_auth}')
            error_message = json_auth['error_description']
            if self._INVALID_PASSWORD_MESSAGE not in error_message:
                raise LoginError("Could not log in to ALMA authorization portal: "
                                 f"{self.get_valid_host()} Message from server: {error_message}")
            else:
                raise LoginError(error_message)
        elif 'access_token' not in json_auth:
            raise LoginError("Could not log in to any of the known ALMA authorization portals: \n"
                             f"No error from server, but missing access token from host: {self.get_valid_host()}")
        else:
            log.info(f'Successfully logged in to {self._auth_host}')


@async_to_sync
class AlmaClass(QueryWithLogin):

    TIMEOUT = conf.timeout
    archive_url = conf.archive_url
    USERNAME = conf.username

    def __init__(self):
        # sia service does not need disambiguation but tap does
        super().__init__()
        self._sia = None
        self._tap = None
        self._datalink = None
        self._sia_url = None
        self._tap_url = None
        self._datalink_url = None
        self._auth = AlmaAuth()

    @property
    def auth(self):
        return self._auth

    @property
    def datalink(self):
        if not self._datalink:
            self._datalink = pyvo.dal.adhoc.DatalinkService(self.datalink_url)
        return self._datalink

    @property
    def datalink_url(self):
        if not self._datalink_url:
            try:
                self._datalink_url = urljoin(self._get_dataarchive_url(), DATALINK_SERVICE_PATH)
            except requests.exceptions.HTTPError as err:
                log.debug(
                    f"ERROR getting the ALMA Archive URL: {str(err)}")
                raise err
        return self._datalink_url

    @property
    def sia(self):
        if not self._sia:
            self._sia = SIA2Service(baseurl=self.sia_url)
        return self._sia

    @property
    def sia_url(self):
        if not self._sia_url:
            try:
                self._sia_url = urljoin(self._get_dataarchive_url(), SIA_SERVICE_PATH)
            except requests.exceptions.HTTPError as err:
                log.debug(
                    f"ERROR getting the  ALMA Archive URL: {str(err)}")
                raise err
        return self._sia_url

    @property
    def tap(self):
        if not self._tap:
            self._tap = pyvo.dal.tap.TAPService(baseurl=self.tap_url, session=self._session)
        return self._tap

    @property
    def tap_url(self):
        if not self._tap_url:
            try:
                self._tap_url = urljoin(self._get_dataarchive_url(), TAP_SERVICE_PATH)
            except requests.exceptions.HTTPError as err:
                log.debug(
                    f"ERROR getting the  ALMA Archive URL: {str(err)}")
                raise err
        return self._tap_url

    def query_object_async(self, object_name, *, public=True,
                           science=True, payload=None, **kwargs):
        """
        Query the archive for a source name.

        Parameters
        ----------
        object_name : str
            The object name.  Will be resolved by astropy.coord.SkyCoord
        public : bool
            True to return only public datasets, False to return private only,
            None to return both
        science : bool
            True to return only science datasets, False to return only
            calibration, None to return both
        payload : dict
            Dictionary of additional keywords.  See `help`.
        """
        if payload is not None:
            payload['source_name_resolver'] = object_name
        else:
            payload = {'source_name_resolver': object_name}
        return self.query_async(public=public, science=science,
                                payload=payload, **kwargs)

    def query_region_async(self, coordinate, radius, *, public=True,
                           science=True, payload=None, **kwargs):
        """
        Query the ALMA archive with a source name and radius

        Parameters
        ----------
        coordinates : str / `astropy.coordinates`
            the identifier or coordinates around which to query.
        radius : str / `~astropy.units.Quantity`, optional
            the radius of the region
        public : bool
            True to return only public datasets, False to return private only,
            None to return both
        science : bool
            True to return only science datasets, False to return only
            calibration, None to return both
        payload : dict
            Dictionary of additional keywords.  See `help`.
        """
        rad = radius
        if not isinstance(radius, u.Quantity):
            rad = radius*u.deg
        obj_coord = commons.parse_coordinates(coordinate).icrs
        ra_dec = '{}, {}'.format(obj_coord.to_string(), rad.to(u.deg).value)
        if payload is None:
            payload = {}
        if 'ra_dec' in payload:
            payload['ra_dec'] += ' | {}'.format(ra_dec)
        else:
            payload['ra_dec'] = ra_dec

        return self.query_async(public=public, science=science,
                                payload=payload, **kwargs)

    def query_async(self, payload, *, public=True, science=True,
                    legacy_columns=False, get_query_payload=False,
                    maxrec=None, **kwargs):
        """
        Perform a generic query with user-specified payload

        Parameters
        ----------
        payload : dictionary
            Please consult the `help` method
        public : bool
            True to return only public datasets, False to return private only,
            None to return both
        science : bool
            True to return only science datasets, False to return only
            calibration, None to return both
        legacy_columns : bool
            True to return the columns from the obsolete ALMA advanced query,
            otherwise return the current columns based on ObsCore model.
        get_query_payload : bool
            Flag to indicate whether to simply return the payload.
        maxrec : integer
            Cap on the amount of records returned.  Default is no limit.

        Returns
        -------

        Table with results. Columns are those in the ALMA ObsCore model
        (see ``help_tap``) unless ``legacy_columns`` argument is set to True.
        """

        if payload is None:
            payload = {}
        for arg in kwargs:
            value = kwargs[arg]
            if 'band_list' == arg and isinstance(value, list):
                value = ' '.join([str(_) for _ in value])
            if arg in payload:
                payload[arg] = '{} {}'.format(payload[arg], value)
            else:
                payload[arg] = value

        if science is not None:
            payload['science_observation'] = science
        if public is not None:
            payload['public_data'] = public

        query = _gen_sql(payload)

        if get_query_payload:
            # Return the TAP query payload that goes out to the server rather
            # than the unprocessed payload dict from the python side
            return query

        result = self.query_tap(query, maxrec=maxrec)

        if result is not None:
            result = result.to_table()
        else:
            # Should not happen
            raise RuntimeError('BUG: Unexpected result None')
        if legacy_columns:
            legacy_result = Table()
            # add 'Observation date' column

            for col_name in _OBSCORE_TO_ALMARESULT:
                if col_name in result.columns:
                    if col_name == 't_min':
                        legacy_result['Observation date'] = \
                            [Time(_['t_min'], format='mjd').strftime(
                                ALMA_DATE_FORMAT) for _ in result]
                    else:
                        legacy_result[_OBSCORE_TO_ALMARESULT[col_name]] = \
                            result[col_name]
                else:
                    log.error("Invalid column mapping in OBSCORE_TO_ALMARESULT: "
                              "{}:{}.  Please "
                              "report this as an Issue."
                              .format(col_name, _OBSCORE_TO_ALMARESULT[col_name]))
            return legacy_result
        return result

    def query_sia(self, *, pos=None, band=None, time=None, pol=None,
                  field_of_view=None, spatial_resolution=None,
                  spectral_resolving_power=None, exptime=None,
                  timeres=None, publisher_did=None,
                  facility=None, collection=None,
                  instrument=None, data_type=None,
                  calib_level=None, target_name=None,
                  res_format=None, maxrec=None,
                  **kwargs):
        """
        Use standard SIA2 attributes to query the ALMA SIA service.

        Parameters
        ----------
        _SIA2_PARAMETERS

        Returns
        -------
        Results in ``pyvo.dal.sia2.SIA2Results`` format.
        result.table in Astropy table format
        """
        return self.sia.search(
            pos=pos,
            band=band,
            time=time,
            pol=pol,
            field_of_view=field_of_view,
            spatial_resolution=spatial_resolution,
            spectral_resolving_power=spectral_resolving_power,
            exptime=exptime,
            timeres=timeres,
            publisher_did=publisher_did,
            facility=facility,
            collection=collection,
            instrument=instrument,
            data_type=data_type,
            calib_level=calib_level,
            target_name=target_name,
            res_format=res_format,
            maxrec=maxrec,
            **kwargs)

    # SIA2_PARAMETERS_DESC contains links that Sphinx can't resolve.
    for var in ('POLARIZATION_STATES', 'CALIBRATION_LEVELS'):
        SIA2_PARAMETERS_DESC = SIA2_PARAMETERS_DESC.replace(f'`pyvo.dam.obscore.{var}`',
                                                            f'pyvo.dam.obscore.{var}')
    query_sia.__doc__ = query_sia.__doc__.replace('_SIA2_PARAMETERS', SIA2_PARAMETERS_DESC)

    def query_tap(self, query, maxrec=None):
        """
        Send query to the ALMA TAP. Results in pyvo.dal.TapResult format.
        result.table in Astropy table format

        Parameters
        ----------
        maxrec : int
            maximum number of records to return

        """
        log.debug('TAP query: {}'.format(query))
        return self.tap.search(query, language='ADQL', maxrec=maxrec)

    def help_tap(self):
        print('Table to query is "voa.ObsCore".')
        print('For example: "select top 1 * from ivoa.ObsCore"')
        print('The scheme of the table is as follows.\n')
        print('  {0:20s} {1:15s} {2:10} {3}'.
              format('Name', 'Type', 'Unit', 'Description'))
        print('-'*90)
        for tb in self.tap.tables.items():
            if tb[0] == 'ivoa.obscore':
                for col in tb[1].columns:
                    if col.datatype.content == 'char':
                        type = 'char({})'.format(col.datatype.arraysize)
                    else:
                        type = str(col.datatype.content)
                    unit = col.unit if col.unit else ''
                    print('  {0:20s} {1:15s} {2:10} {3}'.
                          format(col.name, type, unit, col.description))

    # update method pydocs
    query_region_async.__doc__ = query_region_async.__doc__.replace(
        '_SIA2_PARAMETERS', SIA2_PARAMETERS_DESC)
    query_object_async.__doc__ = query_object_async.__doc__.replace(
        '_SIA2_PARAMETERS', SIA2_PARAMETERS_DESC)
    query_async.__doc__ = query_async.__doc__.replace(
        '_SIA2_PARAMETERS', SIA2_PARAMETERS_DESC)

    def _get_dataarchive_url(self):
        """
        If the generic ALMA URL is used, query it to determine which mirror to
        access for querying data
        """
        if not hasattr(self, 'dataarchive_url'):
            if self.archive_url in ('http://almascience.org', 'https://almascience.org'):
                response = self._request('GET', self.archive_url, timeout=self.TIMEOUT,
                                         cache=False)
                response.raise_for_status()
                # Jan 2017: we have to force https because the archive doesn't
                # tell us it needs https.
                self.dataarchive_url = response.url.replace(
                    "/asax/", "").replace("/aq/", "").replace("http://", "https://")
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

    def get_data_info(self, uids, *, expand_tarfiles=False,
                      with_auxiliary=True, with_rawdata=True):
        """
        Return information about the data associated with ALMA uid(s)

        Parameters
        ----------
        uids : list or str
            A list of valid UIDs or a single UID.
            UIDs should have the form: 'uid://A002/X391d0b/X7b'
        expand_tarfiles : bool
            False to return information on the tarfiles packages containing
            the data or True to return information about individual files in
            these packages
        with_auxiliary : bool
            True to include the auxiliary packages, False otherwise
        with_rawdata : bool
            True to include raw data, False otherwise

        Returns
        -------
        Table with results or None. Table has the following columns: id (UID),
        access_url (URL to access data), service_def, content_length, content_type (MIME
        type), semantics, description (optional), error_message (optional)
        """
        if uids is None:
            raise AttributeError('UIDs required')
        if isinstance(uids, (str, bytes)):
            uids = [uids]
        if not isinstance(uids, (list, tuple, np.ndarray)):
            raise TypeError("Datasets must be given as a list of strings.")
        # TODO remove this loop and send uids at once when pyvo fixed
        result = None
        datalink_service_def_dict = {}
        for uid in uids:
            res = self.datalink.run_sync(uid)
            if res.status[0] != 'OK':
                raise Exception('ERROR {}: {}'.format(res.status[0],
                                                      res.status[1]))

            # Collect the ad-hoc DataLink services for later retrieval if expand_tarballs is set
            if expand_tarfiles:
                for adhoc_service in res.iter_adhocservices():
                    if self.is_datalink_adhoc_service(adhoc_service):
                        datalink_service_def_dict[adhoc_service.ID] = adhoc_service

            temp = res.to_table()

            result = temp if result is None else vstack([result, temp])
            to_delete = []
            for index, rr in enumerate(result):
                if rr['error_message'] is not None and \
                        rr['error_message'].strip():
                    log.warning('Error accessing info about file {}: {}'.
                                format(rr['access_url'], rr['error_message']))
                    # delete from results. Good thing to do?
                    to_delete.append(index)
        result.remove_rows(to_delete)
        if not with_auxiliary:
            result = result[np.core.defchararray.find(
                result['semantics'], '#aux') == -1]
        if not with_rawdata:
            result = result[np.core.defchararray.find(
                result['semantics'], '#progenitor') == -1]
        # if expand_tarfiles:
        # identify the tarballs that can be expandable and replace them
        # with the list of components
        expanded_result = None
        to_delete = []
        if expand_tarfiles:
            for index, row in enumerate(result):
                service_def_id = row['service_def']
                # service_def record, so check if it points to a DataLink document
                if service_def_id and service_def_id in datalink_service_def_dict:
                    # subsequent call to datalink
                    adhoc_service = datalink_service_def_dict[service_def_id]
                    recursive_access_url = self.get_adhoc_service_access_url(adhoc_service)
                    file_id = recursive_access_url.split('ID=')[1]
                    expanded_tar = self.get_data_info(file_id)
                    expanded_tar = expanded_tar[
                        expanded_tar['semantics'] != '#cutout']
                    if not expanded_result:
                        expanded_result = expanded_tar
                    else:
                        expanded_result = vstack(
                            [expanded_result, expanded_tar], join_type='exact')

                    # These DataLink entries have no access_url and are links to service_def RESOURCEs only,
                    # so they can be removed if expanded.
                    to_delete.append(index)
        # cleanup
        result.remove_rows(to_delete)
        # add the extra rows
        if expanded_result:
            result = vstack([result, expanded_result], join_type='exact')

        return result

    def is_datalink_adhoc_service(self, adhoc_service):
        standard_id = self.get_adhoc_service_parameter(adhoc_service, 'standardID')
        return standard_id == DATALINK_STANDARD_ID

    def get_adhoc_service_access_url(self, adhoc_service):
        return self.get_adhoc_service_parameter(adhoc_service, 'accessURL')

    def get_adhoc_service_parameter(self, adhoc_service, parameter_id):
        for p in adhoc_service.params:
            if p.ID == parameter_id:
                return p.value

    def is_proprietary(self, uid):
        """
        Given an ALMA UID, query the servers to determine whether it is
        proprietary or not.
        """
        query = "select distinct data_rights from ivoa.obscore where " \
                "member_ous_uid='{}'".format(uid)
        result = self.query_tap(query)
        if result:
            tableresult = result.to_table()
        if not result or len(tableresult) == 0:
            raise AttributeError('{} not found'.format(uid))
        if len(tableresult) == 1 and tableresult[0][0] == 'Public':
            return False
        return True

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
        for index, fileLink in enumerate(files):
            response = self._request('HEAD', fileLink, stream=False,
                                     cache=False, timeout=self.TIMEOUT)
            filesize = (int(response.headers['content-length']) * u.B).to(u.GB)
            totalsize += filesize
            data_sizes[fileLink] = filesize
            log.debug("File {0}: size {1}".format(fileLink, filesize))
            pb.update(index + 1)
            response.raise_for_status()

        return data_sizes, totalsize.to(u.GB)

    def download_files(self, files, *, savedir=None, cache=True,
                       continuation=True, skip_unauthorized=True,
                       verify_only=False):
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
        verify_only : bool
            Option to go through the process of checking the files to see if
            they're the right size, but not actually download them.  This
            option may be useful if a previous download run failed partway.
        """

        if self.USERNAME:
            auth = self._get_auth_info(self.USERNAME)
        else:
            auth = None

        downloaded_files = []
        if savedir is None:
            savedir = self.cache_location
        for file_link in unique(files):
            log.debug("Downloading {0} to {1}".format(file_link, savedir))
            try:
                check_filename = self._request('HEAD', file_link, auth=auth, timeout=self.TIMEOUT)
                check_filename.raise_for_status()
            except requests.HTTPError as ex:
                if ex.response.status_code == 401:
                    if skip_unauthorized:
                        log.info("Access denied to {url}.  Skipping to"
                                 " next file".format(url=file_link))
                        continue
                    else:
                        raise (ex)

            try:
                filename = os.path.basename(re.search("filename=(.*)",
                                            check_filename.headers['Content-Disposition']).groups()[0])
            except KeyError:
                log.info(f"Unable to find filename for {file_link}  "
                         "(missing Content-Disposition in header).  "
                         "Skipping to next file.")
                continue

            if savedir is not None:
                filename = os.path.join(savedir,
                                        filename)

            if verify_only:
                existing_file_length = os.stat(filename).st_size
                if 'content-length' in check_filename.headers:
                    length = int(check_filename.headers['content-length'])
                    if length == 0:
                        warnings.warn('URL {0} has length=0'.format(file_link))
                    elif existing_file_length == length:
                        log.info(f"Found cached file {filename} with expected size {existing_file_length}.")
                    elif existing_file_length < length:
                        log.info(f"Found cached file {filename} with size {existing_file_length} < expected "
                                 f"size {length}.  The download should be continued.")
                    elif existing_file_length > length:
                        warnings.warn(f"Found cached file {filename} with size {existing_file_length} > expected "
                                      f"size {length}.  The download is likely corrupted.",
                                      CorruptDataWarning)
                else:
                    warnings.warn(f"Could not verify {file_link} because it has no 'content-length'")

            try:
                if not verify_only:
                    self._download_file(file_link,
                                        filename,
                                        timeout=self.TIMEOUT,
                                        auth=auth,
                                        cache=cache,
                                        method='GET',
                                        head_safe=False,
                                        continuation=continuation)

                downloaded_files.append(filename)
            except requests.HTTPError as ex:
                if ex.response.status_code == 401:
                    if skip_unauthorized:
                        log.info("Access denied to {url}.  Skipping to"
                                 " next file".format(url=file_link))
                        continue
                    else:
                        raise (ex)
                elif ex.response.status_code == 403:
                    log.error("Access denied to {url}".format(url=file_link))
                    if 'dataPortal' in file_link and 'sso' not in file_link:
                        log.error("The URL may be incorrect.  Try using "
                                  "{0} instead of {1}"
                                  .format(file_link.replace('dataPortal/',
                                                            'dataPortal/sso/'),
                                          file_link))
                    raise ex
                elif ex.response.status_code == 500:
                    # empirically, this works the second time most of the time...
                    self._download_file(file_link,
                                        filename,
                                        timeout=self.TIMEOUT,
                                        auth=auth,
                                        cache=cache,
                                        method='GET',
                                        head_safe=False,
                                        continuation=continuation)

                    downloaded_files.append(filename)
                else:
                    raise ex
        return downloaded_files

    def _parse_result(self, response, verbose=False):
        """
        Parse a VOtable response
        """
        if not verbose:
            commons.suppress_vo_warnings()

        return response

    def retrieve_data_from_uid(self, uids, *, cache=True):
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
        if isinstance(uids, (str, bytes)):
            uids = [uids]
        if not isinstance(uids, (list, tuple, np.ndarray)):
            raise TypeError("Datasets must be given as a list of strings.")

        files = self.get_data_info(uids)
        # filter out blank access URLs
        # it is possible for there to be length-1 lists
        if len(files) == 1:
            file_urls = files['access_url']
            if isinstance(file_urls, str) and file_urls == '':
                raise ValueError(f"Cannot download uid {uids} because it has no file")
        else:
            file_urls = [url for url in files['access_url'] if url]

        totalsize = files['content_length'].sum()*u.B

        # each_size, totalsize = self.data_size(files)
        log.info("Downloading files of size {0}...".format(totalsize.to(u.GB)))
        # TODO: Add cache=cache keyword here.  Currently would have no effect.
        downloaded_files = self.download_files(file_urls)
        return downloaded_files

    def _get_auth_info(self, username, *, store_password=False,
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

        auth_url = self.auth.get_valid_host()

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

        self.auth.auth_hosts = auth_urls

        username, password = self._get_auth_info(username=username,
                                                 store_password=store_password,
                                                 reenter_password=reenter_password)

        self.auth.login(username, password)
        self.USERNAME = username

        return True

    def get_cycle0_uid_contents(self, uid):
        """
        List the file contents of a UID from Cycle 0.  Will raise an error
        if the UID is from cycle 1+, since those data have been released in
        a different and more consistent format.  See
        https://almascience.org/documents-and-tools/cycle-2/ALMAQA2Productsv1.01.pdf
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
            response = self._request('GET', url, cache=True, timeout=self.TIMEOUT)

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

    def get_files_from_tarballs(self, downloaded_files, *, regex=r'.*\.fits$',
                                path='cache_path', verbose=True):
        """
        Given a list of successfully downloaded tarballs, extract files
        with names matching a specified regular expression.  The default
        is to extract all FITS files

        NOTE: alma now supports direct listing and downloads of tarballs. See
        ``get_data_info`` and ``download_and_extract_files``

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

    def download_and_extract_files(self, urls, *, delete=True, regex=r'.*\.fits$',
                                   include_asdm=False, path='cache_path',
                                   verbose=True):
        """
        Given a list of tarball URLs, it extracts all the FITS files (or
        whatever matches the regex)

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

        if isinstance(urls, str):
            urls = [urls]
        if not isinstance(urls, (list, tuple, np.ndarray)):
            raise TypeError("Datasets must be given as a list of strings.")
        filere = re.compile(regex)

        all_files = []
        tar_files = []
        expanded_files = []
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

            tar_file = url.split('/')[-1]
            files = self.get_data_info(tar_file)
            if files:
                expanded_files += [x for x in files['access_url'] if
                                   filere.match(x.split('/')[-1])]
            else:
                tar_files.append(url)

        try:
            # get the tar files
            downloaded = self.download_files(tar_files, savedir=path)
            fitsfilelist = self.get_files_from_tarballs(downloaded,
                                                        regex=regex, path=path,
                                                        verbose=verbose)

            if delete:
                for tarball_name in downloaded:
                    log.info("Deleting {0}".format(tarball_name))
                    os.remove(tarball_name)

            all_files += fitsfilelist

            # download the other files
            all_files += self.download_files(expanded_files, savedir=path)

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
            else:
                raise ex
        return all_files

    def help(self, cache=True):
        """
        Return the valid query parameters
        """

        print("\nMost common ALMA query keywords are listed below. These "
              "keywords are part of the ALMA ObsCore model, an IVOA standard "
              "for metadata representation (3rd column). They were also "
              "present in original ALMA Web form and, for backwards "
              "compatibility can be accessed with their old names (2nd "
              "column).\n"
              "More elaborate queries on the ObsCore model "
              "are possible with `query_sia` or `query_tap` methods")
        print("  {0:33s} {1:35s} {2:35s}".format("Description",
                                                 "Original ALMA keyword",
                                                 "ObsCore keyword"))
        print("-"*103)
        for title, section in ALMA_FORM_KEYS.items():
            print()
            print(title)
            for row in section.items():
                print("  {0:33s} {1:35s} {2:35s}".format(row[0], row[1][0], row[1][1]))
        print('\nExamples of queries:')
        print("Alma.query('proposal_id':'2011.0.00131.S'}")
        print("Alma.query({'band_list': ['5', '7']}")
        print("Alma.query({'source_name_alma': 'GRB021004'})")
        print("Alma.query(payload=dict(project_code='2017.1.01355.L', "
              "source_name_alma='G008.67'))")

    def get_project_metadata(self, projectid, *, cache=True):
        """
        Get the metadata - specifically, the project abstract - for a given project ID.
        """
        if len(projectid) != 14:
            raise AttributeError('Wrong length for project ID')
        if not projectid[4] == projectid[6] == projectid[12] == '.':
            raise AttributeError('Wrong format for project ID')
        result = self.query_tap(
            "select distinct proposal_abstract from "
            "ivoa.obscore where proposal_id='{}'".format(projectid))

        return [result[0]['proposal_abstract']]


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
            for item in this_jdata:
                if item['type'] in productlist:
                    item['mous_uid'] = mousID
                    rows.append(item)
                elif len(item['children']) > 0:
                    if len(item['allMousUids']) == 1:
                        flatten_jdata(item['children'], item['allMousUids'][0])
                    else:
                        flatten_jdata(item['children'])

    flatten_jdata(jdata['children'])

    keys = rows[-1].keys()

    columns = [Column(data=[row[key] for row in rows], name=key)
               for key in keys if key not in ('children', 'allMousUids')]

    columns = [col.astype(str) if col.dtype.name == 'object' else col for col
               in columns]

    return Table(columns)
