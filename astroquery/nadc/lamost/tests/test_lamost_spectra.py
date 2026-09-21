# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""LAMOST FITS layouts, unchanged flux arrays, and wavelength validation."""

from astropy.io import fits
import numpy as np
import pytest

from .. import parse_lrs_spectrum, parse_mrs_spectrum
from .helpers import DATA, write_spectrum


class TestLamostUtilityFunctions:
    """
    Test single-spectrum FITS readers.
    """

    @pytest.mark.parametrize('hdu_count', [1, 2])
    @pytest.mark.parametrize('dtype', [np.float32, np.float64])
    def test_parse_lrs_supported_layouts(self, tmp_path, hdu_count, dtype):
        flux = np.nextafter(np.arange(1, 17, dtype=dtype), dtype(np.inf))
        wavelength = 10 ** (3.6 + np.arange(16) * 0.001)
        if hdu_count == 1:
            primary = fits.PrimaryHDU(data=np.array([flux, np.ones_like(flux)]))
            primary.header['COEFF0'] = 3.6
            primary.header['COEFF1'] = 0.001
            hdul = fits.HDUList([primary])
        else:
            spectrum = fits.BinTableHDU.from_columns([
                fits.Column(name='flux', format='16E' if dtype == np.float32 else '16D', array=[flux]),
                fits.Column(name='ivar', format='16E', array=[np.ones(16)]),
                fits.Column(name='wavelength', format='16D', array=[wavelength]),
            ])
            hdul = fits.HDUList([fits.PrimaryHDU(), spectrum])
        filename = tmp_path / 'spectrum.fits'
        hdul.writeto(filename)
        hdul.close()

        result = parse_lrs_spectrum(filename)

        np.testing.assert_allclose(result[0], wavelength)
        np.testing.assert_array_equal(result[1], flux)
        assert len(result) == 2
        assert result[1].dtype.itemsize == np.dtype(dtype).itemsize

    @pytest.mark.parametrize('layout', [
        'three_hdus', 'empty_primary', 'missing_coeff', 'image_extension',
        'missing_column', 'mismatched_length',
    ])
    def test_parse_lrs_rejects_unsupported_layout(self, tmp_path, layout):
        hdus = [fits.PrimaryHDU()]
        if layout == 'three_hdus':
            hdus.extend([fits.ImageHDU(), fits.ImageHDU()])
        elif layout == 'missing_coeff':
            hdus = [fits.PrimaryHDU(data=np.ones((3, 16)))]
        elif layout == 'image_extension':
            hdus.append(fits.ImageHDU(data=np.ones((3, 16))))
        elif layout in {'missing_column', 'mismatched_length'}:
            columns = [fits.Column(name='flux', format='16E', array=[np.ones(16)])]
            if layout == 'mismatched_length':
                columns.append(fits.Column(name='wavelength', format='8E', array=[np.ones(8)]))
            hdus.append(fits.BinTableHDU.from_columns(columns))
        filename = tmp_path / 'unsupported.fits'
        with fits.HDUList(hdus) as hdul:
            hdul.writeto(filename)

        with pytest.raises(ValueError, match='(?i)(LRS|layout|COEFF|flux|spectrum)'):
            parse_lrs_spectrum(filename)

    def test_parse_lrs_spectrum_real_file(self, sample_lrs_fits):
        wavelength, flux = parse_lrs_spectrum(sample_lrs_fits)
        with fits.open(sample_lrs_fits) as hdus:
            np.testing.assert_array_equal(wavelength, hdus[1].data['WAVELENGTH'][0])
            np.testing.assert_array_equal(flux, hdus[1].data['FLUX'][0])
        assert all(isinstance(value, np.ndarray) for value in (wavelength, flux))
        assert wavelength.shape == flux.shape
        assert wavelength.size > 0
        assert wavelength.min() > 3000 and wavelength.max() < 10000

    def test_parse_mrs_spectrum(self, sample_mrs_fits):
        """Test MRS FITS with multiple bands"""
        data = parse_mrs_spectrum(sample_mrs_fits)

        # Verify dict with extension names as keys
        assert isinstance(data, dict)
        assert set(data) == {'B', 'R'}

        # Each band has 'wavelength' and 'flux'
        for band_name, band_data in data.items():
            assert 'wavelength' in band_data
            assert 'flux' in band_data
            assert isinstance(band_data['wavelength'], np.ndarray)
            assert isinstance(band_data['flux'], np.ndarray)
            assert len(band_data['wavelength']) > 0
            assert len(band_data['flux']) > 0
        with fits.open(sample_mrs_fits) as hdul:
            for band in ('B', 'R'):
                np.testing.assert_array_equal(data[band]['flux'], hdul[band].data['flux'][0])
                np.testing.assert_array_equal(data[band]['wavelength'], hdul[band].data['wavelength'][0])


@pytest.mark.parametrize('filename', ['mrs_dr8_excerpt.fits.gz', 'mrs_dr10_excerpt.fits.gz'])
def test_real_mrs_layouts_preserve_all_extensions(filename):
    path = DATA / filename
    result = parse_mrs_spectrum(path)
    with fits.open(path) as hdus:
        assert list(result) == [hdu.name for hdu in hdus[1:]]
        for hdu in hdus[1:]:
            if 'LOGLAM' in hdu.columns.names:
                expected_wave = np.power(10., np.asarray(hdu.data['LOGLAM'], dtype=float))
                expected_flux = hdu.data['FLUX']
            else:
                expected_wave = hdu.data['WAVELENGTH'][0]
                expected_flux = hdu.data['FLUX'][0]
            np.testing.assert_array_equal(result[hdu.name]['wavelength'], expected_wave)
            np.testing.assert_array_equal(result[hdu.name]['flux'], expected_flux)


@pytest.mark.parametrize('layout, diagnostic', [
    ('no_extensions', 'at least one spectrum extension'),
    ('image', 'nonempty binary table'), ('empty', 'nonempty binary table'),
    ('missing_flux', 'requires FLUX and WAVELENGTH'), ('missing_wave', 'requires FLUX and WAVELENGTH'),
    ('vector_loglam', 'nonempty numeric arrays of equal length'),
    ('scalar_wavelength', 'one table row of vector arrays'),
    ('mismatched', 'nonempty numeric arrays of equal length'),
    ('nonnumeric', 'nonempty numeric arrays of equal length'),
    ('ambiguous', 'ambiguous WAVELENGTH and LOGLAM'), ('duplicate', 'duplicate spectrum extension name'),
])
def test_mrs_rejects_unsupported_layouts(tmp_path, layout, diagnostic):
    columns = [fits.Column(name='FLUX', format='E', array=[1., 2.]),
               fits.Column(name='LOGLAM', format='D', array=[3.7, 3.8])]
    if layout == 'missing_flux':
        columns = columns[1:]
    elif layout == 'missing_wave':
        columns = columns[:1]
    elif layout == 'ambiguous':
        columns.append(fits.Column(name='WAVELENGTH', format='D', array=[5000., 6000.]))
    elif layout == 'scalar_wavelength':
        columns[1] = fits.Column(name='WAVELENGTH', format='D', array=[5000., 6000.])
    elif layout in ('vector_loglam', 'mismatched'):
        columns[0] = fits.Column(name='FLUX', format='2E', array=[[1., 2.]])
        columns[1] = fits.Column(name='LOGLAM', format='2D', array=[[3.7, 3.8]])
        if layout == 'mismatched':
            columns[1] = fits.Column(name='WAVELENGTH', format='3D', array=[[5000., 6000., 7000.]])
    elif layout == 'nonnumeric':
        columns[0] = fits.Column(name='FLUX', format='A', array=['a', 'b'])
    table = fits.BinTableHDU.from_columns(columns, name='B-123')
    if layout == 'empty':
        table = fits.BinTableHDU(data=table.data[:0])
    hdus = [fits.PrimaryHDU(), table]
    if layout == 'no_extensions':
        hdus = hdus[:1]
    elif layout == 'image':
        hdus[1] = fits.ImageHDU(data=np.ones(2))
    elif layout == 'duplicate':
        hdus.append(table.copy())
    path = tmp_path / 'invalid.fits'
    with fits.HDUList(hdus) as hdul:
        hdul.writeto(path)
    with pytest.raises(ValueError, match=diagnostic):
        parse_mrs_spectrum(path)


def test_historical_layout_is_mrs_only(tmp_path):
    path = tmp_path / 'historical.fits'
    with fits.HDUList([fits.PrimaryHDU(), fits.BinTableHDU.from_columns([
        fits.Column(name='FLUX', format='E', array=[2., 1.]),
        fits.Column(name='LOGLAM', format='E', array=[3.8, 3.7]),
    ])]) as hdus:
        hdus.writeto(path)
    result = parse_mrs_spectrum(path)['Extension_1']
    np.testing.assert_array_equal(result['flux'], [2., 1.])
    assert result['wavelength'][0] > result['wavelength'][1]
    assert result['wavelength'].dtype == np.float64
    with pytest.raises(ValueError):
        parse_lrs_spectrum(path)


@pytest.mark.parametrize('loglam', [np.nan, np.inf, -np.inf, -400., 400.],
                         ids=['nan', 'inf', 'minus_inf', 'underflow', 'overflow'])
def test_mrs_invalid_loglam_has_file_extension_and_pixel_diagnostics(tmp_path, loglam):
    path = write_spectrum(tmp_path / 'bad-loglam.fits', [3.7, loglam, 3.8], [1., 2., 3.], loglam=True)
    # Conversion failures must remain ValueError even with strict NumPy flags.
    with np.errstate(all='raise'), pytest.raises(ValueError) as caught:
        parse_mrs_spectrum(path)
    message = str(caught.value)
    assert str(path) in message
    assert "extension 'COADD_B' (HDU 1)" in message
    assert '1 invalid pixels' in message and 'zero-based index 1' in message


@pytest.mark.parametrize('wavelength', [np.nan, np.inf, -np.inf, 0., -1.])
def test_mrs_direct_wavelengths_must_be_finite_and_positive(tmp_path, wavelength):
    path = write_spectrum(tmp_path / 'bad-wave.fits', [5000., wavelength, 6000.], [1., 2., 3.])
    with pytest.raises(ValueError, match='finite and positive') as caught:
        parse_mrs_spectrum(path)
    assert 'zero-based index 1' in str(caught.value)


@pytest.mark.parametrize('loglam', [False, True])
def test_mrs_valid_wavelength_order_and_raw_flux_are_preserved(tmp_path, loglam):
    wavelength = np.array([.1, 10., 1., 5000.])
    flux = np.array([np.nan, np.inf, -1., 0.])
    path = write_spectrum(tmp_path / 'raw-flux.fits', np.log10(wavelength) if loglam else wavelength,
                          flux, loglam=loglam)
    result = parse_mrs_spectrum(path)['COADD_B']
    np.testing.assert_allclose(result['wavelength'], wavelength, rtol=1e-15)
    np.testing.assert_array_equal(result['flux'], flux)
