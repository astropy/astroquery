# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""Offline checks of the standalone activity example, including installed packages."""

import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest

from astroquery.nadc.lamost.tests.helpers import DATA, write_spectrum


@pytest.fixture(scope='module')
def activity():
    path = Path(__file__).resolve().parents[1] / 'lamost_activity.py'
    spec = importlib.util.spec_from_file_location('lamost_activity_example', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize('pixel,band', [(3892., 'V'), (4013., 'R')])
@pytest.mark.parametrize('bad_flux', [np.nan, np.inf, -np.inf, 0., -1.])
def test_activity_rejects_invalid_interpolation_neighbors(activity, pixel, band, bad_flux):
    wave = np.arange(3891., 4014.)
    flux = np.ones(wave.size)
    flux[wave == pixel] = bad_flux
    with pytest.raises(ValueError, match=f'Band {band} interpolation requires finite positive flux') as caught:
        activity.activity_index(wave, flux, 0.)
    assert f'zero-based index {int(pixel - wave[0])}' in str(caught.value)
    assert f'rest wavelength {pixel:g} Angstrom' in str(caught.value)


def test_activity_exact_edges_do_not_use_outside_neighbors_or_band_gaps(activity):
    wave = np.r_[3891., 3902.17 - 10., np.arange(3893., 4013.), 4002.20 + 10., 4013.]
    flux = np.ones(wave.size)
    flux[[0, -1]] = np.nan
    flux[wave == 3920.] = -1.  # This gap is outside all four bandpasses.
    assert activity.activity_index(wave, flux, 0.) == pytest.approx(.7848)


@pytest.mark.parametrize('rv', [np.nan, np.inf, -np.inf, -299792.458, -599584.916, [0., 1.]])
def test_activity_rejects_invalid_rv_with_value_error(activity, rv):
    wave = np.arange(3891., 4014.)
    with pytest.raises(ValueError, match='RV must be a finite scalar'):
        activity.activity_index(wave, np.ones(wave.size), rv)


def test_activity_rejects_integration_overflow(activity):
    wave = np.arange(3891., 4014.)
    with pytest.raises(ValueError, match='integration must produce finite positive mean flux'):
        activity.activity_index(wave, np.full(wave.size, 1e308), 0.)


def test_activity_rejects_nonfinite_final_ratio(activity):
    wave = np.arange(3891., 4014.)
    flux = np.full(wave.size, 1e-310)
    flux[(wave >= 3968.) & (wave <= 3971.)] = 1e300
    with pytest.raises(ValueError, match='activity index must be finite and positive'):
        activity.activity_index(wave, flux, 0.)


def test_activity_fixed_observation_remains_consistent(activity):
    reference = json.loads((DATA / 'legacy_samples.json').read_text())['activity_dr7_excerpt.fits.gz']
    value = activity.measure_file(DATA / 'activity_dr7_excerpt.fits.gz', reference['rv_kms'])
    assert value == pytest.approx(reference['independent_S_L'], rel=0., abs=reference['numerical_atol'])


def test_activity_batch_masks_errors_and_continues_in_input_order(activity, tmp_path):
    wave = np.arange(3891., 4014.)
    flux = np.ones(wave.size)
    good = write_spectrum(tmp_path / 'good.fits', wave, flux, obsid=102)
    flux[wave == 3892.] = np.nan
    bad = write_spectrum(tmp_path / 'bad.fits', wave, flux)
    missing = tmp_path / 'missing.fits'
    observations = [(bad, 0., 101), (good, 0., 102), (missing, 0., 103),
                    (good, 0., 999), (good, np.nan, 102), (good, 0., 102)]
    manifest = activity.measure_files(iter(observations))
    assert manifest.colnames == ['Local Path', 'OBSID', 'Status', 'Message', 'S_L']
    assert list(manifest['Local Path']) == [str(row[0]) for row in observations]
    assert list(manifest['OBSID']) == [str(row[2]) for row in observations]
    assert list(manifest['Status']) == ['ERROR', 'COMPLETE', 'ERROR', 'ERROR', 'ERROR', 'COMPLETE']
    assert manifest['S_L'].mask.tolist() == [True, False, True, True, True, False]
    np.testing.assert_allclose(manifest['S_L'][[1, 5]], .7848)
    assert 'Band V' in manifest['Message'][0]
    assert 'FileNotFoundError:' in manifest['Message'][2]
    assert 'OBSID=999' in manifest['Message'][3]
    assert 'RV must be a finite scalar' in manifest['Message'][4]
    assert manifest['Message'][1] == manifest['Message'][5] == ''


@pytest.mark.parametrize('count', [0, 2])
def test_activity_batch_empty_or_all_failed(activity, tmp_path, count):
    manifest = activity.measure_files([(tmp_path / 'missing.fits', 0., 101)] * count)
    assert len(manifest) == count
    assert manifest.colnames == ['Local Path', 'OBSID', 'Status', 'Message', 'S_L']
    assert manifest['S_L'].mask.tolist() == [True] * count


def test_activity_batch_does_not_hide_unexpected_errors(activity, monkeypatch):
    def unexpected_error(*args, **kwargs):
        raise RuntimeError('Unexpected calculation failure')

    monkeypatch.setattr(activity, 'measure_file', unexpected_error)
    with pytest.raises(RuntimeError, match='Unexpected calculation failure'):
        activity.measure_files([('spectrum.fits', 0., 101)])


@pytest.mark.parametrize('obsid', [None, 'bad'])
def test_activity_batch_reports_invalid_header_identity(activity, tmp_path, obsid):
    wave = np.arange(3891., 4014.)
    path = write_spectrum(tmp_path / 'bad-identity.fits', wave, np.ones(wave.size), obsid=obsid)
    manifest = activity.measure_files([(path, 0., 101)])
    assert manifest['Status'][0] == 'ERROR'
    assert manifest['S_L'].mask[0]
    assert 'ValueError:' in manifest['Message'][0] and 'OBSID must be an integer' in manifest['Message'][0]
