# Licensed under a 3-clause BSD style license - see LICENSE.rst

import requests
import warnings

import pyvo
from urllib.parse import urljoin

from astroquery import log
from astropy import units as u

from ..utils import commons
from ..query import BaseVOQuery
from . import conf, tap_urls
from ..alma.tapsql import (_gen_str_sql, _gen_numeric_sql,
                           _gen_datetime_sql)
from .tapsql import (_gen_pos_sql, _gen_pub_sql, _gen_pol_sql,
                     _gen_band_list_nrao_sql)

__all__ = {'NraoClass', 'NRAO_BANDS'}

__doctest_skip__ = ['NraoClass.*']

TAP_SERVICE_PATH = 'tap'

NRAO_FORM_KEYS = {
    # s_resolution not filled in for VLA, thus configuration is also available
    # s_fov is mostly meaningless in NRAO archive, thus removed ability to search
    # on it.

    # NRAO archive returns a scan per row and t_exptime is the length of each scan
    # so there is not a simple way to get total integration time on source from TAP
    # returns. Output would need to be manipulated to get the total integration for
    # each observation.
    'Position': {
        'Source name (astropy Resolver)': ['source_name_resolver',
                                           'SkyCoord.from_name', _gen_pos_sql],
        'Source name (NRAO)': ['source_name', 'target_name', _gen_str_sql],
        'RA Dec (Sexagesimal)': ['ra_dec', 's_ra, s_dec', _gen_pos_sql],
        'Galactic (Degrees)': ['galactic', 'gal_longitude, gal_latitude',
                               _gen_pos_sql],
        'Angular resolution (arcsec)': ['spatial_resolution',
                                        's_resolution', _gen_numeric_sql],
        'Maximum UV Distance (meters)': ['max_uv_dist', 'max_uv_dist', _gen_numeric_sql]
    },
    'Project': {
        'Project code': ['project_code', 'project_code', _gen_str_sql],
        'Telescope': ['instrument', 'instrument_name', _gen_str_sql],
        'Number of Antennas': ['n_ants', 'num_antennas', _gen_numeric_sql],
        'Configuration': ['configuration', 'configuration', _gen_str_sql],
    },
    'Time': {
        'Observation start': ['start_date', 't_min', _gen_datetime_sql],
    },
    'Polarization': {
        'Polarization type:\n\
         (Single-circular/linear,\n\
          Dual-circular/linear,\n\
          Full-circular/linear)': ['polarization_type',
                                                     'pol_states',
                                                     _gen_pol_sql]
    },
    'Energy': {
        'Bandwidth (Hz)': ['bandwidth', 'aggregate_bandwidth', _gen_numeric_sql],
        'Maximum Frequency (GHz)': ['freq_max', 'freq_max', _gen_numeric_sql],
        'Minimum Frequency (GHz)': ['freq_min', 'freq_min', _gen_numeric_sql],
        'Band': ['band_list', 'band_list', _gen_band_list_nrao_sql]
    },
    'Options': {
        'Public data only': ['public_data', 'proprietary_status', _gen_pub_sql],
        'Data Product Type': ['data_type', 'dataproduct_type', _gen_str_sql],
    }

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


class NraoClass(BaseVOQuery):
    TIMEOUT = conf.timeout
    archive_url = conf.archive_url
    USERNAME = conf.username

    def __init__(self):
        # sia service does not need disambiguation but tap does
        super().__init__()
        self._tap = None
        self._tap_url = None
        # TODO self._auth = NraoAuth()

    @property
    def auth(self):
        return self._auth

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

    def query_region(self, coordinate, radius, *, public=None,
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
        public : bool
            True to return only public datasets, False to return private only,
            None to return both
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

        return self.query(public=public, payload=payload, **kwargs)

    def query(self, payload, *, public=None, get_query_payload=False,
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

        if public is not None:
            if 'public_data' in kwargs:
                warnings.warn("Both public and public_data are set. "
                              "The ``public`` kwarg takes precedence. "
                              "If you want ``public_data`` to be respected, "
                              "set ``public=None``.")
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

        return result
        
    def help(self, cache=True):
        """
        Return the valid query parameters
        """

        print("\nMost common NRAO query keywords are listed below. These "
              "keywords are part of the NRAO ObsCore model, an IVOA standard "
              "for metadata representation (3rd column). We also include "
              "aliases for some keywords to maintain similarity with "
              "the ALMA astroquery module for the sake of convenience\n"
              "More elaborate queries on the ObsCore model "
              "are possible with `query_tap` methods")
        print("  {0:33s} {1:35s} {2:35s}".format("Description",
                                                 "Astroquery keyword",
                                                 "ObsCore keyword"))
        print("-"*103)
        for title, section in NRAO_FORM_KEYS.items():
            print()
            print(title)
            for row in section.items():
                print("  {0:33s} {1:35s} {2:35s}".format(row[0], row[1][0], row[1][1]))
        print('\nExamples of queries:')
        print("Nrao.query('{project_code':'21A-409')}")
        print("Nrao.query({'source_name': 'L1157', 'band_list': ['Q', 'K']})")
        print("Nrao.query({'source_name': 'HOPS-376'})")
        print("Nrao.query({'source_name': 'HOPS-376', 'instrument': 'ALMA'})")
        print("Nrao.query({'source_name_resolver': 'HOPS 376', 'instrument': 'EVLA'})")
        print("Nrao.query({'source_name_resolver': 'M1', 'instrument': 'VLBA'})")
        print("Nrao.query(payload=dict(project_code='13B-318', "
              "source_name='Per27'))")


Nrao = NraoClass()
