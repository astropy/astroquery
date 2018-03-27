# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import json
import warnings

from astropy.table import Table
from astropy.utils.data import get_pkg_data_contents
from astropy.utils.exceptions import AstropyUserWarning

from . import conf

__all__ = ['get_field_info', 'photoobj_defs', 'specobj_defs', 'crossid_defs']

# Default photometric and spectroscopic quantities to retrieve.
photoobj_defs = ['ra', 'dec', 'objid', 'run', 'rerun', 'camcol', 'field']
specobj_defs = ['z', 'plate', 'mjd', 'fiberID', 'specobjid', 'run2d',
                'instrument']
crossid_defs = ['ra', 'dec', 'psfMag_u', 'psfMagerr_u', 'psfMag_g',
                'psfMagerr_g', 'psfMag_r', 'psfMagerr_r', 'psfMag_i',
                'psfMagerr_i', 'psfMag_z', 'psfMagerr_z']


_cached_table_fields = {}


def get_field_info(cls, tablename, sqlurl, timeout=conf.timeout):
    key = (tablename, sqlurl)
    # Figure out the DR from the url
    data_release = int(sqlurl.split('/dr')[1].split('/')[0])

    # Empty tables could be cached when running local mock tests, those should
    # always be discarded
    if key not in _cached_table_fields or not _cached_table_fields[key]:
        request_payload = {'cmd': ("select * from dbo.fDocColumns('{0}')"
                                   .format(tablename)),
                           'format': 'json'}
        if data_release > 11:
            request_payload['searchtool'] = 'SQL'

        qryres = cls._request("GET", sqlurl, params=request_payload,
                              timeout=timeout)
        # we're compelled to use JSON because CSV responses are broken in
        # SDSS - sometimes there are improperly nested " characters.
        try:
            _cached_table_fields[key] = _columns_json_to_table(qryres.json())
        except ValueError:
            warnings.warn("Field info are not available for this data release",
                          AstropyUserWarning)
            _cached_table_fields[key] = Table(names=('name',))
    return _cached_table_fields[key]


def _columns_json_to_table(jsonobj):
    rows = jsonobj[0]['Rows']
    columns = dict([(nm, []) for nm in rows[0].keys()])

    for row in rows:
        for k, v in row.items():
            columns[k].append(v)

    return Table(columns)


# below here are builtin data files
def _load_builtin_table_fields():
    key1 = ('PhotoObjAll',
            'http://skyserver.sdss.org/dr12/en/tools/search/x_sql.aspx')
    _cached_table_fields[key1] = _columns_json_to_table(
        json.loads(get_pkg_data_contents('data/PhotoObjAll_dr12.json')))
    # PhotoObj and PhotoObjAll are the same in DR12
    key2 = ('PhotoObj',
            'http://skyserver.sdss.org/dr12/en/tools/search/x_sql.aspx')
    _cached_table_fields[key2] = _cached_table_fields[key1]

    key1 = ('SpecObjAll',
            'http://skyserver.sdss.org/dr12/en/tools/search/x_sql.aspx')
    _cached_table_fields[key1] = _columns_json_to_table(
        json.loads(get_pkg_data_contents('data/SpecObjAll_dr12.json')))
    # SpecObj and SpecObjAll are the same in DR12
    key2 = ('SpecObj',
            'http://skyserver.sdss.org/dr12/en/tools/search/x_sql.aspx')
    _cached_table_fields[key2] = _cached_table_fields[key1]


_load_builtin_table_fields()
