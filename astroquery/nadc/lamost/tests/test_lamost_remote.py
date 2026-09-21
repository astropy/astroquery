# Licensed under a 3-clause BSD style license - see LICENSE.rst

import pytest
from astropy import units as u
from astropy.table import Table

from .. import conf
from ..core import LamostClass
from astroquery.exceptions import LoginError


pytestmark = pytest.mark.remote_data


@pytest.fixture
def lamost(tmp_path):
    with conf.set_temp('server', 'https://www.lamost.org/openapi'):
        client = LamostClass(token='', data_release='dr10', sub_version='v2.0')
    client.cache_location = tmp_path
    return client


@pytest.mark.parametrize('obsid, expected_rows', [(176604010, 1), (0, 0)])
def test_query_sql_remote(lamost, obsid, expected_rows):
    result = lamost.query_sql(
        f'SELECT obsid, ra, dec, teff, feh FROM combined WHERE obsid = {obsid} LIMIT 2',
        column_schema={
            'obsid': {'datatype': 'long'},
            'ra': {'datatype': 'double', 'unit': 'deg'},
            'dec': {'datatype': 'double', 'unit': 'deg'},
            'teff': {'datatype': 'float', 'unit': 'K'},
            'feh': {'datatype': 'float'},
        },
        cache=False,
    )

    assert isinstance(result, Table)
    assert len(result) == expected_rows
    assert result['obsid'].dtype.kind in 'iu'
    assert result['teff'].dtype.kind == 'f'
    assert result['teff'].unit == u.K
    if expected_rows:
        assert result['obsid'][0] == obsid
        assert result['ra'][0] == pytest.approx(10.008848, abs=1e-6)
        assert result['dec'][0] == pytest.approx(40.969976, abs=1e-6)


def test_get_dr_versions_remote(lamost):
    result = lamost.get_dr_versions()

    assert isinstance(result, list)
    assert len(result) > 0
    assert {"dr_version", "sub_version", "public_status"}.issubset(result[0])
    assert any(version['dr_version'] == 'dr10' and version['sub_version'] == 'v2.0' for version in result)


def test_invalid_token_redirect_remote(lamost):
    lamost.token = 'synthetic-invalid-lamost-token'
    lamost.data_release = 'dr7'
    with pytest.raises(LoginError, match='validity'):
        lamost.query_sql('SELECT obsid FROM catalogue LIMIT 1', cache=False)
