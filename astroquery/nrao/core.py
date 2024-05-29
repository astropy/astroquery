# Licensed under a 3-clause BSD style license - see LICENSE.rst

import os.path
import keyring
import numpy as np
import re
import tarfile
import string
import requests
import warnings
import json
import time

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
from ..query import BaseQuery, QueryWithLogin, BaseVOQuery
from . import conf, auth_urls, tap_urls
from astroquery.exceptions import CorruptDataWarning
from ..alma.tapsql import (_gen_str_sql, _gen_numeric_sql,
                     _gen_band_list_sql, _gen_datetime_sql, _gen_pol_sql, _gen_pub_sql,
                     _gen_science_sql, _gen_spec_res_sql, ALMA_DATE_FORMAT)
from .tapsql import (_gen_pos_sql)

__all__ = {'NraoClass',}

__doctest_skip__ = ['NraoClass.*']

NRAO_BANDS = {
    'L': (1*u.GHz,   2*u.GHz),
    'S': (2*u.GHz,   4*u.GHz),
    'C': (4*u.GHz,   8*u.GHz),
    'X': (8*u.GHz,  12*u.GHz),
    'U': (12*u.GHz, 18*u.GHz),
    'K': (18*u.GHz, 26*u.GHz),
    'A': (26*u.GHz, 39*u.GHz),
    'Q': (39*u.GHz, 50*u.GHz),
    'W': (80*u.GHz, 115*u.GHz)
}

TAP_SERVICE_PATH = 'tap'

NRAO_FORM_KEYS = {
    'Position': {
        'Source name (astropy Resolver)': ['source_name_resolver',
                                           'SkyCoord.from_name', _gen_pos_sql],
        'Source name (NRAO)': ['source_name', 'target_name', _gen_str_sql],
        'RA Dec (Sexagesimal)': ['ra_dec', 's_ra, s_dec', _gen_pos_sql],
        'Galactic (Degrees)': ['galactic', 'gal_longitude, gal_latitude',
                               _gen_pos_sql],
        'Angular resolution (arcsec)': ['spatial_resolution',
                                        'spatial_resolution', _gen_numeric_sql],
        'Field of view (arcsec)': ['fov', 's_fov', _gen_numeric_sql],
        'Configuration': ['configuration', 'configuration', _gen_numeric_sql],
        'Maximum UV Distance (meters)': ['max_uv_dist', 'max_uv_dist', _gen_numeric_sql]


    },
    'Project': {
        'Project code': ['project_code', 'project_code', _gen_str_sql],
        'Telescope': ['instrument', 'instrument_name', _gen_str_sql],
        'Number of Antennas': ['n_ants', 'num_antennas', _gen_str_sql],

    },
    'Time': {
        'Observation start': ['start_date', 't_min', _gen_datetime_sql],
        'Observation end': ['end_date', 't_max', _gen_datetime_sql],
        'Integration time (s)': ['integration_time', 't_exptime',
                                 _gen_numeric_sql]
    },
    'Polarization': {
        'Polarisation type (Single, Dual, Full)': ['polarisation_type',
                                                   'pol_states', _gen_pol_sql]
    },
    'Energy': {
        'Frequency (GHz)': ['frequency', 'center_frequencies', _gen_numeric_sql],
        'Bandwidth (Hz)': ['bandwidth', 'aggregate_bandwidth', _gen_numeric_sql],
        'Spectral resolution (KHz)': ['spectral_resolution',
                                      'em_resolution', _gen_spec_res_sql],
        'Band': ['band_list', 'band_list', _gen_band_list_sql]
    },

}

_OBSCORE_TO_NRAORESULT = {
    's_ra': 'RA',
    's_dec': 'Dec',
}


def _gen_sql(payload):
    sql = 'select * from tap_schema.obscore'
    where = ''
    unused_payload = payload.copy()
    if payload:
        for constraint in payload:
            for attrib_category in NRAO_FORM_KEYS.values():
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


# class NraoAuth(BaseVOQuery, BaseQuery):
#     """
#     TODO: this needs to be implemented
#     """
#     pass


class NraoClass(BaseQuery):
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
        # TODO self._auth = NraoAuth()

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
                    f"ERROR getting the NRAO Archive URL: {str(err)}")
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
                    f"ERROR getting the  NRAO Archive URL: {str(err)}")
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
                    f"ERROR getting the  NRAO Archive URL: {str(err)}")
                raise err
        return self._tap_url

    def query_tap(self, query, maxrec=None):
        """
        Send query to the NRAO TAP. Results in pyvo.dal.TapResult format.
        result.table in Astropy table format

        Parameters
        ----------
        maxrec : int
            maximum number of records to return

        """
        log.debug('TAP query: {}'.format(query))
        return self.tap.search(query, language='ADQL', maxrec=maxrec)

    def _get_dataarchive_url(self):
        return tap_urls[0]

    def query_object(self, object_name, *, payload=None, **kwargs):
        """
        Query the archive for a source name.

        Parameters
        ----------
        object_name : str
            The object name.  Will be resolved by astropy.coord.SkyCoord
        payload : dict
            Dictionary of additional keywords.  See `help`.
        """
        if payload is not None:
            payload['source_name_resolver'] = object_name
        else:
            payload = {'source_name_resolver': object_name}
        return self.query(payload=payload, **kwargs)

    def query_region(self, coordinate, radius, *,
                           get_query_payload=False,
                           payload=None, **kwargs):
        """
        Query the NRAO archive with a source name and radius

        Parameters
        ----------
        coordinates : str / `astropy.coordinates`
            the identifier or coordinates around which to query.
        radius : str / `~astropy.units.Quantity`, optional
            the radius of the region
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

        if get_query_payload:
            return payload

        return self.query(payload=payload, **kwargs)

    def query(self, payload, *, get_query_payload=False,
                    maxrec=None, **kwargs):
        """
        Perform a generic query with user-specified payload

        Parameters
        ----------
        payload : dictionary
            Please consult the `help` method
        legacy_columns : bool
            True to return the columns from the obsolete NRAO advanced query,
            otherwise return the current columns based on ObsCore model.
        get_query_payload : bool
            Flag to indicate whether to simply return the payload.
        maxrec : integer
            Cap on the amount of records returned.  Default is no limit.
            [ we don't know for sure that this is implemented for NRAO ]

        Returns
        -------

        Table with results.
        """

        if payload is None:
            payload = {}
        for arg in kwargs:
            value = kwargs[arg]
            if arg in payload:
                payload[arg] = '{} {}'.format(payload[arg], value)
            else:
                payload[arg] = value
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

        return result


    def _get_data(self, solr_id, email=None, workflow='runBasicMsWorkflow',
                  apply_flags=True
                 ):
        """
        This private function can, under a very limited set of circumstances,
        be used to retrieve the data download page from the NRAO data handler.
        Because the data handler is run through a fairly complex, multi-step,
        private API, we are not yet ready to make this service public.

        Parameters
        ----------
        workflow : 'runBasicMsWorkflow', "runDownloadWorkflow"
        """
        url = f'{self.archive_url}/portal/#/subscanViewer/{solr_id}'

        #self._session.headers['User-Agent'] = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"

        resp = self._request('GET', url, cache=False)
        resp.raise_for_status()

        eb_deets = self._request('GET',
                                 f'{self.archive_url}/archive-service/restapi_get_full_exec_block_details',
                                 params={'solr_id': solr_id},
                                 cache=False
                                )
        eb_deets.raise_for_status()
        assert len(self._session.cookies) > 0

        resp1b = self._request('GET',
                               f'{self.archive_url}/archive-service/restapi_spw_details_view',
                               params={'exec_block_id': solr_id.split(":")[-1]},
                               cache=False
                              )
        resp1b.raise_for_status()

        # returned data is doubly json-encoded
        jd = json.loads(eb_deets.json())
        locator = jd['curr_eb']['sci_prod_locator']
        project_code = jd['curr_eb']['project_code']

        instrument = ('VLBA' if 'vlba' in solr_id.lower() else
                      'VLA' if 'vla' in solr_id.lower() else
                      'EVLA' if 'nrao' in solr_id.lower() else
                      'GBT' if 'gbt' in solr_id.lower() else None)
        if instrument is None:
            raise ValueError("Invalid instrument")

        if instrument == 'VLBA':
            downloadDataFormat = "VLBARaw"
        elif instrument in ('VLA', 'EVLA'):
            # there are other options!
            downloadDataFormat = 'MS'

        post_data = {
          "emailNotification": email,
          "requestDescription": f"{instrument} Download Request",
          "archive": "VLA",
          "p_telescope": instrument,
          "p_project": project_code,
          "productLocator": locator,
          "requestCommand": "startVlaPPIWorkflow",
          "p_workflowEventName": workflow,
          "p_downloadDataFormat": downloadDataFormat,
          "p_intentsFileName": "intents_hifv.xml",
          "p_proceduresFileName": "procedure_hifv.xml"
        }

        if instrument in ('VLA', 'EVLA'):
            post_data['p_applyTelescopeFlags'] = apply_flags
            casareq = self._request('GET',
                                    f'{self.archive_url}/archive-service/restapi_get_casa_version_list',
                                    cache=False
                                   )
            casareq.raise_for_status()
            casavdata = json.loads(casareq.json())
            for casav in casavdata['casa_version_list']:
                if 'recommended' in casav['version']:
                    post_data['p_casaHome'] = casav['path']

        presp = self._request('POST',
                              f'{self.archive_url}/rh/submission',
                              data=post_data,
                              cache=False
                             )
        presp.raise_for_status()

        resp2 = self._request('GET', presp.url, cache=False)
        resp2.raise_for_status()

        for row in resp2.text.split():
            if 'window.location.href=' in row:
                subrespurl = row.split("'")[1]

        nextresp = self._request('GET', subrespurl, cache=False)
        wait_url = nextresp.url
        nextresp.raise_for_status()

        if f'{self.archive_url}/rh/requests/' not in wait_url:
            raise ValueError(f"Got wrong URL from post request: {wait_url}")

        # to get the right format of response, you need to specify this:
        # accept = {"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7"}

        while True:
            time.sleep(1)
            print(".", end='', flush=True)
            resp = self._request('GET', wait_url + "/state", cache=False)
            resp.raise_for_status()
            if resp.text == 'COMPLETE':
                break

        return wait_url



Nrao = NraoClass()
