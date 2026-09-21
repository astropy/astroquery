# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""One-observation Ca II H&K example (Zhang et al. 2022, arXiv:2209.15255).

Run without arguments to download DR7/v2.0 observation 54901214. To use a
previously saved spectrum of the same observation without network access,
pass --filename and --rv.
"""

import argparse
from pathlib import Path
import tempfile

from astropy.io import fits
from astropy.table import Table
import numpy as np

from astroquery.nadc.lamost import LamostClass, parse_lrs_spectrum


OBSID = 54901214
REFERENCE_INDEX = 0.18038
REFERENCE_UNCERTAINTY = 0.003597
INDEPENDENT_INDEX = 0.1803738541038765


def metadata_fields(table):
    """Read the single normalized metadata record returned by the client."""
    if len(table) != 1:
        raise ValueError('Expected one spectrum metadata record.')
    return {name: table[name][0] for name in table.colnames}


def activity_index(wavelength, flux, rv):
    """Compute S_L from vacuum wavelengths, flux, and RV in km/s.

    Band centers and widths follow Table 2 of Zhang et al. (2022).
    Linear interpolation and trapezoidal weights define the numerical rule.
    This small example does not propagate uncertainties or calibrate S_MW.
    All pixels supporting a bandpass, including its interpolation neighbors,
    must have finite positive flux. Invalid inputs or numerical results raise
    ValueError; no pixels are dropped or filled to continue the calculation.
    """
    rv = np.asarray(rv, dtype=float)
    if rv.ndim != 0 or not np.isfinite(rv) or 1 + rv / 299792.458 <= 0:
        raise ValueError('RV must be a finite scalar with 1 + RV/c > 0.')
    with np.errstate(over='ignore', invalid='ignore'):
        wave = np.asarray(wavelength, dtype=float) / (1 + rv / 299792.458)
    flux = np.asarray(flux, dtype=float)
    if (wave.ndim != 1 or wave.size < 2 or flux.shape != wave.shape
            or not np.isfinite(wave).all() or not (np.diff(wave) > 0).all()):
        raise ValueError('Expected matching flux and strictly increasing finite wavelengths.')
    means = []
    # R and V rectangular continua; H and K triangular line cores.
    for band, center, half_width, triangular, step in [
        ('R', 4002.20, 10., False, .01), ('V', 3902.17, 10., False, .01),
        ('H', 3969.59, 1.09, True, .001), ('K', 3934.78, 1.09, True, .001),
    ]:
        grid = np.linspace(center - half_width, center + half_width,
                           round(2 * half_width / step) + 1)
        if grid[0] < wave[0] or grid[-1] > wave[-1]:
            raise ValueError(f'Spectrum does not cover all four bandpasses: missing {band} coverage.')
        # Include the samples bracketing the grid edges, but no extra neighbor
        # when an edge is exactly on an existing wavelength sample.
        left = np.searchsorted(wave, grid[0], side='right') - 1
        right = np.searchsorted(wave, grid[-1], side='left') + 1
        band_flux = flux[left:right]
        invalid = np.flatnonzero(~np.isfinite(band_flux) | (band_flux <= 0))
        if invalid.size:
            first = left + invalid[0]
            raise ValueError(
                f'Band {band} interpolation requires finite positive flux; '
                f'found {invalid.size} invalid pixels, first at zero-based index {first} '
                f'(rest wavelength {wave[first]:.8g} Angstrom): {flux[first]!r}.'
            )
        weights = np.maximum(0., 1 - abs(grid - center) / half_width) if triangular else np.ones(grid.size)
        weights[[0, -1]] *= .5
        with np.errstate(over='ignore', under='ignore', invalid='ignore'):
            mean = float(weights @ np.interp(grid, wave[left:right], band_flux) / weights.sum())
        if not np.isfinite(mean) or mean <= 0:
            raise ValueError(f'Band {band} integration must produce finite positive mean flux.')
        means.append(mean)
    r, v, h, k = means
    denominator = r + v
    if not np.isfinite(denominator) or denominator <= 0:
        raise ValueError('The R + V continuum denominator must be finite and positive.')
    value = (1.8 * 8 * 1.09 / 20) * (h + k) / denominator
    if not np.isfinite(value) or value <= 0:
        raise ValueError('The activity index must be finite and positive.')
    return value


def measure_file(filename, rv, *, expected_obsid=OBSID):
    """Check the requested observation's identity before computing its index.

    By default this verifies the fixed reference observation. For another
    target, supply its integer OBSID and the matching archive RV in km/s.
    """
    with fits.open(filename) as spectrum:
        if 'OBSID' not in spectrum[0].header:
            raise ValueError('Spectrum primary header is missing OBSID.')
        try:
            actual_obsid = int(spectrum[0].header['OBSID'])
        except (TypeError, ValueError, OverflowError) as error:
            raise ValueError('Spectrum primary header OBSID must be an integer.') from error
        if actual_obsid != expected_obsid:
            raise ValueError(f'This measurement requires OBSID={expected_obsid}.')
    wavelength, flux = parse_lrs_spectrum(filename)
    return activity_index(wavelength, flux, rv)


def measure_files(observations):
    """Measure local spectra and return a per-file status table.

    ``observations`` is an iterable of ``(filename, rv, expected_obsid)``
    triples. Each RV is in km/s and each OBSID must match the file header.
    The output columns are ``Local Path``, ``OBSID``, ``Status``, ``Message``,
    and ``S_L``. Status is ``COMPLETE`` or ``ERROR``; failed indices are masked.
    File I/O and data-validation errors are recorded and processing continues.
    Other exceptions propagate. Input order and repeated paths are preserved.
    """
    rows = []
    for filename, rv, expected_obsid in observations:
        try:
            value = measure_file(filename, rv, expected_obsid=expected_obsid)
        except (OSError, EOFError, ValueError) as error:
            rows.append((str(filename), str(expected_obsid), 'ERROR', f'{type(error).__name__}: {error}', np.nan))
        else:
            rows.append((str(filename), str(expected_obsid), 'COMPLETE', '', value))
    manifest = Table(rows=rows or None, names=('Local Path', 'OBSID', 'Status', 'Message', 'S_L'),
                     dtype=(str, str, str, str, float), masked=True)
    manifest['S_L'].mask = manifest['Status'] == 'ERROR'
    return manifest


def download_and_measure():
    """Select the release, retrieve metadata and FITS, then close resources."""
    client = LamostClass(data_release='dr7', sub_version='v2.0')
    metadata = metadata_fields(client.get_metadata(OBSID, cache=False))
    if int(metadata['obsid']) != OBSID:
        raise ValueError('Metadata does not identify the requested observation.')
    rv = float(metadata['rv'])
    spectra = client.get_spectra(OBSID)
    try:
        with tempfile.TemporaryDirectory() as directory:
            filename = Path(directory) / 'spectrum.fits'
            # Some archive headers require structural fixes when reserializing.
            # This local file is not a byte-for-byte copy of the HTTP response.
            spectra[0].writeto(filename, output_verify='fix')
            return measure_file(filename, rv)
    finally:
        for spectrum in spectra:
            spectrum.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--filename', type=Path, help='Previously saved OBSID=54901214 FITS file')
    parser.add_argument('--rv', type=float, help='Archive radial velocity in km/s; expected -24.78')
    args = parser.parse_args()
    if (args.filename is None) != (args.rv is None):
        parser.error('--filename and --rv must be provided together for offline use')
    value = download_and_measure() if args.filename is None else measure_file(args.filename, args.rv)
    np.testing.assert_allclose(value, INDEPENDENT_INDEX, rtol=0, atol=1e-7)
    print(f'OBSID={OBSID}: S_L={value:.9f}')
    print(f'Published S_L={REFERENCE_INDEX:.5f} +/- {REFERENCE_UNCERTAINTY:.6f}')


if __name__ == '__main__':
    main()
