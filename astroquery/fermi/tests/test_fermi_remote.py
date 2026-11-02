# Licensed under a 3-clause BSD style license - see LICENSE.rst

import astropy.coordinates as coord
import pytest

from ... import fermi

FK5_COORDINATES = coord.SkyCoord(10.68471, 41.26875, unit=('deg', 'deg'))


@pytest.mark.remote_data
def test_FermiLAT_query_async():
    query_id = fermi.core.FermiLAT.query_object_async(
        FK5_COORDINATES, energyrange_MeV='1000,100000',
        obsdates='2013-01-01 00:00:00,2013-01-02 00:00:00')
    assert isinstance(query_id, str)
    assert query_id.startswith('L')

    status = fermi.core.FermiLAT.get_status(query_id)
    assert 'state' in status


@pytest.mark.remote_data
def test_FermiLAT_query():
    # Make a query that results in small SC and PH file sizes
    result = fermi.core.FermiLAT.query_object(
        FK5_COORDINATES, energyrange_MeV='1000,100000',
        obsdates='2013-01-01 00:00:00,2013-01-02 00:00:00')

    assert len(result) >= 1
    for rr in result:
        assert rr.startswith('https://')
        assert rr.endswith('_SC00.fits') or rr.endswith('_PH00.fits')


@pytest.mark.remote_data
def test_FermiLAT_query_zenithangle():
    result = fermi.core.FermiLAT.query_object(
        FK5_COORDINATES, energyrange_MeV='1000,100000',
        obsdates='2013-01-01 00:00:00,2013-01-02 00:00:00',
        zenithangle=85)
    assert len(result) >= 1


@pytest.mark.remote_data
def test_FermiLAT_allsky_query():
    # all-sky: radius > 60 deg, observation window <= 24 hours
    result = fermi.core.FermiLAT.query_object(
        '0.0,0.0', searchradius=180,
        obsdates='2008-08-04 15:43:36,2008-08-05 09:14:33',
        energyrange_MeV='100,300000')
    assert len(result) >= 1
