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
import warnings
from pkg_resources import resource_filename
from bs4 import BeautifulSoup
import pyvo

from six.moves.urllib_parse import urljoin
import six
from astropy.table import Table, Column, vstack as table_vstack
from astropy import log
from astropy.utils.console import ProgressBar
from astropy.utils.exceptions import AstropyDeprecationWarning
from astropy import units as u
from astropy.time import Time

from ..exceptions import (RemoteServiceError, LoginError)
from ..utils import commons
from ..utils.process_asyncs import async_to_sync
from ..query import QueryWithLogin
from .tapsql import _gen_pos_sql, _gen_str_sql, _gen_numeric_sql,\
    _gen_band_list_sql, _gen_datetime_sql, _gen_pol_sql, _gen_pub_sql,\
    _gen_science_sql, _gen_spec_res_sql, ALMA_DATE_FORMAT
from . import conf, auth_urls

__all__ = {'AlmaClass', 'ALMA_BANDS'}

__doctest_skip__ = ['AlmaClass.*']


ALMA_TAP_PATH = 'tap'
ALMA_SIA_PATH = 'sia'

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
        'Bandwidth (GHz)': ['bandwidth', 'bandwidth', _gen_numeric_sql],
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
        'Science observations only': ['science_observations', 'calib_level',
                                      _gen_science_sql]
    }
}


def _gen_sql(payload):
    sql = 'select * from ivoa.obscore'
    where = ''
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
    return sql + where


@async_to_sync
class AlmaClass(QueryWithLogin):

    TIMEOUT = conf.timeout
    archive_url = conf.archive_url
    USERNAME = conf.username

    def __init__(self):
        # sia service does not need disambiguation but tap does
        super(AlmaClass, self).__init__()
        self._sia = None
        self._tap = None
        self.sia_url = None
        self.tap_url = None

    @property
    def sia(self):
        if not self._sia:
            base_url = self._get_dataarchive_url()
            if base_url.endswith('/'):
                self.sia_url = base_url + ALMA_SIA_PATH
            else:
                self.sia_url = base_url + '/' + ALMA_SIA_PATH
            self._sia = pyvo.dal.sia2.SIAService(baseurl=self.sia_url)
        return self._sia

    @property
    def tap(self):
        if not self._tap:
            base_url = self._get_dataarchive_url()
            if base_url.endswith('/'):
                self.tap_url = base_url + ALMA_TAP_PATH
            else:
                self.tap_url = base_url + '/' + ALMA_TAP_PATH
            self._tap = pyvo.dal.tap.TAPService(baseurl=self.tap_url)
        return self._tap

    def query_object_async(self, object_name, cache=None, public=True,
                           science=True, payload=None, **kwargs):
        """
        Query the archive for a source name.

        Parameters
        ----------
        object_name : str
            The object name.  Will be resolved by astropy.coord.SkyCoord
        cache : deprecated
        public : bool
            Return only publicly available datasets?
        science : bool
            Return only data marked as "science" in the archive?
        payload : dict
            Dictionary of additional keywords.  See `help`.
        """
        if payload is not None:
            payload['source_name_resolver'] = object_name
        else:
            payload = {'source_name_resolver': object_name}
        return self.query_async(public=public, science=science,
                                payload=payload, **kwargs)

    def query_region_async(self, coordinate, radius, cache=None, public=True,
                           science=True, payload=None, **kwargs):
        """
        Query the ALMA archive with a source name and radius

        Parameters
        ----------
        coordinates : str / `astropy.coordinates`
            the identifier or coordinates around which to query.
        radius : str / `~astropy.units.Quantity`, optional
            the radius of the region
        cache : Deprecated
            Cache the query?
        public : bool
            Return only publicly available datasets?
        science : bool
            Return only data marked as "science" in the archive?
        payload : dict
            Dictionary of additional keywords.  See `help`.
        """
        rad = radius
        if not isinstance(radius, u.Quantity):
            rad = radius*u.deg
        obj_coord = commons.parse_coordinates(coordinate)
        ra_dec = '{}, {}'.format(obj_coord.to_string(), rad.to(u.deg).value)
        if payload is None:
            payload = {}
        if 'ra_dec' in payload:
            payload['ra_dec'] += ' | {}'.format(ra_dec)
        else:
            payload['ra_dec'] = ra_dec

        return self.query_async(public=public, science=science,
                                payload=payload, **kwargs)

    def query_async(self, payload, cache=None, public=True, science=True,
                    legacy_columns=False, max_retries=None,
                    get_html_version=None,
                    get_query_payload=None, **kwargs):
        """
        Perform a generic query with user-specified payload

        Parameters
        ----------
        payload : dictionary
            Please consult the `help` method
        cache : deprecated
        public : bool
            Return only publicly available datasets?
        science : bool
            Return only data marked as "science" in the archive?
        legacy_columns : bool
            True to return the columns from the obsolete ALMA advanced query,
            otherwise return the current columns based on ObsCore model.

        Returns
        -------

        Table with results. Columns are those in the ALMA ObsCore model
        (see ``help_tap``) unless ``legacy_columns`` argument is set to True.
        """
        local_args = dict(locals().items())

        for arg in local_args:
            # check if the deprecated attributes have been used
            for deprecated in ['cache', 'max_retries', 'get_html_version',
                               'get_query_payload']:
                if arg[0] == deprecated and arg[1] is not None:
                    warnings.warn(
                        ("Argument '{}' has been deprecated "
                         "since version 4.0.1 and will be ignored".format(arg[0])),
                        AstropyDeprecationWarning)
                    del kwargs[arg[0]]

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

        if science:
            payload['science_observations'] = True

        if public is not None:
            if public:
                payload['public_data'] = True
            else:
                payload['public_data'] = False
        query = _gen_sql(payload)
        result = self.query_tap(query, **kwargs)
        if result:
            result = result.to_table()
        else:
            return result
        if legacy_columns:
            legacy_result = Table()
            # add 'Observation date' column

            for ii in _OBSCORE_TO_ALMARESULT:
                if ii in result.columns:
                    if ii == 't_min':
                        legacy_result['Observation date'] = \
                            [Time(_['t_min'], format='mjd').strftime(
                                ALMA_DATE_FORMAT) for _ in result]
                    else:
                        legacy_result[_OBSCORE_TO_ALMARESULT[ii]] = \
                            result[ii]
                else:
                    log.error("Invalid column mapping in OBSCORE_TO_ALMARESULT: "
                              "{}:{}.  Please "
                              "report this as an Issue."
                              .format(ii, _OBSCORE_TO_ALMARESULT[ii]))
            return legacy_result
        return result

    def query_sia(self, pos=None, band=None, time=None, pol=None,
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

        Returns
        -------
        Results in `pyvo.dal.SIAResults` format.
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

    def query_tap(self, query, **kwargs):
        """
        Send query to the ALMA TAP. Results in pyvo.dal.TapResult format.
        result.table in Astropy table format
        """
        return self.tap.search(query, language='ADQL', **kwargs)

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
        '_SIA2_PARAMETERS', pyvo.dal.sia2.SIA_PARAMETERS_DESC)
    query_object_async.__doc__ = query_object_async.__doc__.replace(
        '_SIA2_PARAMETERS', pyvo.dal.sia2.SIA_PARAMETERS_DESC)
    query_async.__doc__ = query_async.__doc__.replace(
        '_SIA2_PARAMETERS', pyvo.dal.sia2.SIA_PARAMETERS_DESC)

    def _get_dataarchive_url(self):
        """
        If the generic ALMA URL is used, query it to determine which mirror to
        access for querying data
        """
        if not hasattr(self, 'dataarchive_url'):
            if self.archive_url in ('http://almascience.org', 'https://almascience.org'):
                response = self._request('GET', self.archive_url,
                                         cache=False)
                response.raise_for_status()
                # Jan 2017: we have to force https because the archive doesn't
                # tell us it needs https.
                self.dataarchive_url = response.url.replace("http://", "https://")
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

        return response

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

    def _json_summary_to_table(self, data, base_url):
        """
        Special tool to convert some JSON metadata to a table Obsolete as of
        March 2020 - should be removed along with stage_data_prefeb2020
        """
        from ..utils import url_helpers
        from six import iteritems
        columns = {'mous_uid': [], 'URL': [], 'size': []}
        for entry in data['node_data']:
            # de_type can be useful (e.g., MOUS), but it is not necessarily
            # specified
            # file_name and file_key *must* be specified.
            is_file = \
                (entry['file_name'] != 'null' and entry['file_key'] != 'null')
            if is_file:
                # "de_name": "ALMA+uid://A001/X122/X35e",
                columns['mous_uid'].append(entry['de_name'][5:])
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
