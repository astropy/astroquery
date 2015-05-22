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

    if key in _cached_table_fields:
        info = _cached_table_fields[key]
    else:
        request_payload = {'cmd': "select * from dbo.fDocColumns('PhotoObj')", 'format': 'csv'}
        qryres = commons.send_request(sqlurl, request_payload, timeout, request_type='GET')
        info = Table.read(qryres.text, format='ascii.csv', header_start=1, data_start=2, guess=False)
        _cached_table_fields[key] = info
    return info
