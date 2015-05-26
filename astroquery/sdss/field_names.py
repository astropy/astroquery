# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from astropy.table import Table

from . import conf
from ..utils import commons

__all__ = ['get_field_info', 'photoobj_defs', 'specobj_defs', 'crossid_defs']

# Default photometric and spectroscopic quantities to retrieve.
photoobj_defs = ['ra', 'dec', 'objid', 'run', 'rerun', 'camcol', 'field']
specobj_defs = ['z', 'plate', 'mjd', 'fiberID', 'specobjid', 'run2d',
                'instrument']
crossid_defs = ['ra', 'dec', 'psfMag_u', 'psfMagerr_u', 'psfMag_g',
                'psfMagerr_g', 'psfMag_r', 'psfMagerr_r', 'psfMag_i',
                'psfMagerr_i', 'psfMag_z', 'psfMagerr_z']


_cached_table_fields = {}
def get_field_info(tablename, sqlurl, timeout=conf.timeout):
    key = (tablename, sqlurl)

    if key not in _cached_table_fields:
        request_payload = {'cmd': "select * from dbo.fDocColumns('{0}')".format(tablename), 'format': 'json'}
        qryres = commons.send_request(sqlurl, request_payload, timeout, request_type='GET')
        # we're compelled to use JSON because CSV responses are broken in SDSS -
        # sometimes there are improperly nested " characters.
        _cached_table_fields[key] = _columns_json_to_table(qryres.json())
    return _cached_table_fields[key]

def _columns_json_to_table(jsonobj):
    rows = jsonobj[0]['Rows']
    columns = dict([(nm, []) for nm in rows[0].keys()])

    for row in rows:
        for k, v in row.items():
            columns[k].append(v)

    return Table(columns)

# below here are builtin cached queries
