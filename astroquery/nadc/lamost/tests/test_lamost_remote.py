# Licensed under a 3-clause BSD style license - see LICENSE.rst

import pytest
import numpy as np
from astropy import units as u
from astropy.coordinates import SkyCoord
from astropy.io import fits
from astropy.table import Table
from collections import Counter

from .. import conf
from ..core import LamostClass
from astroquery.exceptions import LoginError, RemoteServiceError


pytestmark = pytest.mark.remote_data


@pytest.fixture
def lamost(tmp_path):
    with conf.set_temp('server', 'https://www.lamost.org/openapi'):
        client = LamostClass(token='', data_release='dr10', sub_version='v2.0')
    client.cache_location = tmp_path
    return client


def test_query_region_remote(lamost):
    center = SkyCoord(10.0004738, 40.9952444, unit='deg', frame='icrs')
    result = lamost.query_region(center, 0.2 * u.deg, cache=False)
    independent = lamost.query_sql(
        'SELECT obsid, ra, dec FROM catalogue '
        "WHERE spos(ra,dec) @ scircle '<(10.0004738d,40.9952444d),0.2d>' LIMIT 1000",
        output_format='csv', cache=False,
    )

    assert isinstance(result, Table)
    assert len(result) == 195
    assert 176604010 in result['obsid']
    assert len(independent) < 1000
    assert set(result['obsid']) == set(independent['obsid'])
    positions = SkyCoord(result['ra'], result['dec'], unit='deg')
    assert (center.separation(positions) <= 0.2 * u.deg).all()


def test_filtered_nearest_and_all_matches_remote(lamost):
    center = SkyCoord(10.0004738, 40.9952444, unit='deg')
    reference = lamost.query_sql(
        'SELECT obsid,ra,dec,teff,logg,feh,snrg FROM combined '
        "WHERE spos(ra,dec) @ scircle '<(10.0004738d,40.9952444d),0.2d>' "
        'AND teff BETWEEN 4500 AND 6500 AND logg BETWEEN 3.5 AND 5 '
        'AND feh BETWEEN -1 AND 0.5 AND snrg>=30 LIMIT 1001', output_format='csv', cache=False)
    assert len(reference) == 40
    distances = center.separation(SkyCoord(reference['ra'], reference['dec'], unit='deg'))
    args = dict(coordinates=center, radius='0.2 deg', teff_range=(4500, 6500),
                logg_range=(3.5, 5), feh_range=(-1, .5), snr_min=30, cache=False)
    matches = lamost.query_stellar_parameters(**args, max_rows=1000)
    assert Counter(matches['obsid']) == Counter(reference['obsid'])
    for query in (lamost.query_stellar_parameters, lamost.query_spectra):
        nearest = query(**args, nearest_only=True, columns=reference.colnames)
        assert len(nearest) == 1
        distance = center.separation(SkyCoord(nearest['ra'], nearest['dec'], unit='deg'))[0]
        assert distance.arcsec == pytest.approx(distances.min().arcsec, abs=1e-5)
        assert 4500 <= nearest['teff'][0] <= 6500 and nearest['snrg'][0] >= 30


def test_proximity_keeps_duplicate_inputs_and_pagination_remote(lamost):
    # Two identical cones still describe two separate input objects.
    position = {'proximity': {'radecTextarea': '10.0004738,40.9952444,720\n10.0004738,40.9952444,720',
                              'proximity_nearestonly': False}}
    reference = lamost.query_sql(
        "SELECT obsid FROM combined WHERE spos(ra,dec) @ scircle '<(10.0004738d,40.9952444d),0.2d>' "
        'ORDER BY obsid LIMIT 1001', output_format='csv', cache=False)
    assert len(reference) == 195
    actual = []
    for page in (1, 2):
        table = lamost.query_catalog('combined', columns=['obsid'], position_constraints=position,
                                     max_rows=200, page=page, sort_by='obsid', cache=False)
        actual.extend(zip(map(int, table['inputobjs_input_line']), map(int, table['obsid'])))
    expected = [(i, int(obsid)) for i in (1, 2) for obsid in reference['obsid']]
    assert actual == expected


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


@pytest.mark.parametrize('obsid, expected_rows', [(176604010, 1), (0, 0)])
def test_query_catalog_remote(lamost, obsid, expected_rows):
    result = lamost.query_catalog(
        'combined', columns=['obsid', 'ra', 'dec'],
        column_constraints=[{'column_name': 'obsid', 'operation': 'equal', 'constraint': str(obsid)}],
        max_rows=2, cache=False,
    )

    assert isinstance(result, Table)
    assert len(result) == expected_rows
    assert result.meta['catalog'] == 'combined'
    assert result['obsid'].dtype.kind in 'iu'
    if expected_rows:
        assert result['obsid'][0] == obsid
        assert result['ra'][0] == pytest.approx(10.008848, abs=1e-6)
        assert result['dec'][0] == pytest.approx(40.969976, abs=1e-6)


def test_query_spectra_nearest_remote(lamost):
    center = SkyCoord(10.0004738, 40.9952444, unit='deg', frame='icrs')
    result = lamost.query_spectra(
        center, 0.2 * u.deg, nearest_only=True,
        columns=['obsid', 'ra', 'dec'], cache=False,
    )

    assert len(result) == 1
    assert result['obsid'][0] == 176604010
    assert result['ra'][0] == pytest.approx(10.008848, abs=1e-6)
    assert result['dec'][0] == pytest.approx(40.969976, abs=1e-6)


def test_get_dr_versions_remote(lamost):
    result = lamost.get_dr_versions()

    assert isinstance(result, list)
    assert len(result) > 0
    assert {"dr_version", "sub_version", "public_status"}.issubset(result[0])
    assert any(version['dr_version'] == 'dr10' and version['sub_version'] == 'v2.0' for version in result)


@pytest.mark.filterwarnings('ignore::astropy.io.fits.verify.VerifyWarning')
def test_get_spectra_remote(lamost, tmp_path):
    # This archive product has extraneous NAXIS1/NAXIS2 primary-header cards.
    lamost.cache_location = tmp_path
    spectra = lamost.get_spectra(176604010)
    try:
        assert len(spectra) == 1
        spectrum = spectra[0]
        assert isinstance(spectrum, fits.HDUList)
        assert len(spectrum) == 2
        assert spectrum[0].header['OBSID'] == 176604010
        wavelength = spectrum[1].data['WAVELENGTH'][0]
        flux = spectrum[1].data['FLUX'][0]
        assert wavelength.shape == flux.shape == (3909,)
        assert np.isfinite(flux).all()
        assert (np.diff(wavelength) > 0).all()
        assert wavelength[0] == pytest.approx(3699.986, abs=0.01)
        assert wavelength[-1] == pytest.approx(9099.135, abs=0.01)
    finally:
        for spectrum in spectra:
            spectrum.close()


def test_get_metadata_and_stellar_parameters_remote(lamost):
    metadata = lamost.get_metadata(176604010, cache=False)
    assert len(metadata) == 1
    assert metadata['obsid'].dtype.kind in 'iu'
    assert metadata['obsid'][0] == 176604010
    for name in ('ra', 'teff', 'rv', 'snrg'):
        assert metadata[name].dtype.kind == 'f'
        assert not np.ma.is_masked(metadata[name][0])
    assert metadata['ra'][0] == pytest.approx(10.008848, abs=1e-6)
    result = lamost.query_stellar_parameters(
        SkyCoord(10.008848, 40.969976, unit='deg'), '5 arcsec', nearest_only=True, cache=False,
    )
    assert list(result['obsid']) == [176604010]
    # Numeric conversion is required; units are attached only if the service
    # declares them (the reference combined schema currently omits this unit).
    assert result['teff'].dtype.kind == 'f'
    assert result['teff'][0] == pytest.approx(metadata['teff'][0], abs=.01)


def test_mrs_metadata_preserves_exposures_and_nulls_remote(lamost):
    with lamost._request_metadata(1007903112, resolution='medium', cache=False) as response:
        data = response.json()
    metadata = lamost.get_metadata(1007903112, resolution='medium', cache=False)
    assert len(metadata) == len(data['rows']) > 1
    assert metadata['obsid'].dtype.kind in 'iu'
    for i, row in enumerate(data['rows']):
        assert metadata['band'][i] == row['band']
        for name in ('lmjm', 'ra', 'snr', 'teff_lasp', 'rv_br0'):
            assert metadata[name].dtype.kind in ('iu' if name == 'lmjm' else 'f')
            if row[name] in (None, ''):
                assert np.ma.is_masked(metadata[name][i])
            else:
                assert not np.ma.is_masked(metadata[name][i])
                assert metadata[name][i] == pytest.approx(float(row[name]))


def test_related_observations_remote(lamost):
    result = lamost.query_repeat_observations(obsid=176604010, cache=False)
    assert result['unique_id']
    assert 176604010 in list(map(int, result['related_obsids_low']))
    assert len(set(result['related_obsids_low'])) == len(result['related_obsids_low'])


def test_unknown_related_observation_remote(lamost):
    result = lamost.query_repeat_observations(obsid=0, cache=False)
    assert result['unique_id'] is None
    assert result['related_obsids_low'] == result['related_obsids_medium'] == result['related_obsids'] == []


def test_unknown_catalog_product_remote(lamost, tmp_path):
    destination = tmp_path / 'catalog.fits.gz'
    destination.write_bytes(b'original file')
    with pytest.raises(RemoteServiceError):
        lamost.download_catalog('does_not_exist', filename=destination.name, save_dir=tmp_path)
    assert destination.read_bytes() == b'original file'
    assert list(tmp_path.iterdir()) == [destination]


def test_invalid_token_redirect_remote(lamost):
    lamost.token = 'synthetic-invalid-lamost-token'
    lamost.data_release = 'dr7'
    with pytest.raises(LoginError, match='validity'):
        lamost.query_sql('SELECT obsid FROM catalogue LIMIT 1', cache=False)


def test_dr8_mrs_record_envelope_remote(lamost):
    lamost.data_release, lamost.sub_version = 'dr8', 'v1.0'
    with lamost._request_metadata(635003103, resolution='medium', cache=False) as response:
        data = response.json()
        table = lamost._parse_table_response(response)
    assert len(table) == len(data['rows']) > 1
    assert table.meta['total'] == data['total']
    assert list(table['obsid']) == [row['obsid'] for row in data['rows']]
    assert list(table['band']) == [row['band'] for row in data['rows']]
    for i, row in enumerate(data['rows']):
        if row['lmjm'] is None:
            assert np.ma.is_masked(table['lmjm'][i])
        else:
            assert table['lmjm'][i] == row['lmjm']
