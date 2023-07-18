# Licensed under a 3-clause BSD style license - see LICENSE.rst

import os

import numpy as np
from numpy.testing import assert_allclose

# performs similar tests as test_module.py, but performs
# the actual HTTP request rather than monkeypatching them.
# should be disabled or enabled at will - use the
# remote_data decorator from astropy:
import pytest

from astropy.table import Table
from astropy.io import fits
from astropy.wcs import WCS

from .. import conf, AstrometryNet
from ..core import _HAVE_SOURCE_DETECTION
from ...exceptions import TimeoutError

try:
    import scipy  # noqa
except ImportError:
    HAVE_SCIPY = False
else:
    HAVE_SCIPY = True

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')


def data_path(filename):
    return os.path.join(DATA_DIR, filename)


api_key = conf.api_key or os.environ.get('ASTROMETRY_NET_API_KEY')


def _calculate_wcs_separation_at_points(wcses, center, extent):
    """
    Calculate the maximum separation between the given WCS solutions at a grid of points.

    Parameters
    ----------
    wcses : list of `~astropy.wcs.WCS`
        The WCS solutions to compare.
    center : tuple of float
        The center of the grid of points to use for the comparison.
    extent : int
        The extent of the grid of points to use for the comparison.

    Returns
    -------
    max_separation : float
        The maximum separation between the WCS solutions at the grid of points.
    """
    grid_points = np.mgrid[center[0] - extent // 2:center[0] + extent // 2,
                           center[1] - extent // 2:center[1] + extent // 2]

    result_location = wcses[0].pixel_to_world(grid_points[0], grid_points[1])
    expected_location = wcses[1].pixel_to_world(grid_points[0], grid_points[1])

    return result_location.separation(expected_location)


@pytest.mark.filterwarnings("ignore:The WCS transformation has more axes:astropy.wcs.wcs.FITSFixedWarning")
@pytest.mark.skipif(not api_key, reason='API key not set.')
@pytest.mark.remote_data
def test_solve_by_source_list():
    a = AstrometryNet()
    a.api_key = api_key
    sources = Table.read(os.path.join(DATA_DIR, 'test-source-list.fit'))
    # The image_width, image_height and crpix_center below are set to match the
    # original solve on astrometry.net.
    image_width = 4109
    image_height = 4096
    result = a.solve_from_source_list(sources['X'], sources['Y'],
                                      image_width, image_height,
                                      crpix_center=True)

    expected_result = fits.getheader(os.path.join(DATA_DIR,
                                                  'wcs-sol-from-source-list-index-5200.fit'))

    wcs_r = WCS(result)
    wcs_e = WCS(header=expected_result)
    # Check that, at a a grid of points roughly in the center of the image, the WCS
    # solutions are the same to within 0.1 arcsec.
    # The grid created below covers about 1/4 of the pixels in the image.
    center = np.array([image_width // 2, image_height // 2])
    extent = image_width // 2

    separations = _calculate_wcs_separation_at_points([wcs_r, wcs_e], center, extent)
    assert (separations.arcsec).max() < 0.1


@pytest.mark.filterwarnings("ignore:The WCS transformation has more axes:astropy.wcs.wcs.FITSFixedWarning")
@pytest.mark.skipif(not api_key, reason='API key not set.')
@pytest.mark.remote_data
def test_solve_image_upload():
    # Test that solving by uploading an image works
    a = AstrometryNet()
    a.api_key = api_key
    image = os.path.join(DATA_DIR, 'thumbnail-image.fit.gz')

    image_width = 256
    image_height = 256
    # The test image only solves if it is not downsampled

    result = a.solve_from_image(image,
                                force_image_upload=True,
                                downsample_factor=1,
                                crpix_center=True)
    expected_result = fits.getheader(os.path.join(DATA_DIR,
                                                  'wcs-sol-from-thumbnail-image-index-5200.fit'))

    wcs_r = WCS(result)
    wcs_e = WCS(header=expected_result)
    # Check that, at a a grid of points roughly in the center of the image, the WCS
    # solutions are the same to within 0.1 arcsec.
    # The grid created below covers all of this small image.
    center = np.array([image_width // 2, image_height // 2])
    extent = image_width

    separations = _calculate_wcs_separation_at_points([wcs_r, wcs_e], center, extent)
    assert (separations.arcsec).max() < 0.1


@pytest.mark.skipif(not api_key, reason='API key not set.')
@pytest.mark.remote_data
def test_solve_image_upload_expected_failure():
    # Test that a solve failure is returned as expected
    a = AstrometryNet()
    a.api_key = api_key
    image = os.path.join(DATA_DIR, 'thumbnail-image.fit.gz')
    # The test image only solves if it is not downsampled
    result = a.solve_from_image(image,
                                force_image_upload=True,
                                downsample_factor=4)

    assert not result


@pytest.mark.filterwarnings("ignore:The WCS transformation has more axes:astropy.wcs.wcs.FITSFixedWarning")
@pytest.mark.skipif(not api_key, reason='API key not set.')
@pytest.mark.skipif(not _HAVE_SOURCE_DETECTION,
                    reason='photutils not installed')
@pytest.mark.skipif(not HAVE_SCIPY,
                    reason='no scipy, which photutils needs')
@pytest.mark.remote_data
def test_solve_image_detect_source_local():
    # Test that solving by uploading an image works
    a = AstrometryNet()
    a.api_key = api_key
    image = os.path.join(DATA_DIR, 'thumbnail-image.fit.gz')

    image_width = 256
    image_height = 256
    # The source detection parameters below (fwhm, detect_threshold)
    # are specific to this test image. They should not be construed
    # as a general recommendation.
    result = a.solve_from_image(image,
                                force_image_upload=False,
                                downsample_factor=1,
                                fwhm=1.5, detect_threshold=5,
                                center_ra=135.618, center_dec=49.786,
                                radius=0.5, crpix_center=True)

    # Use the result from the image solve for this test. The two WCS solutions really should be
    # nearly identical in thesee two cases. Note that the closeness of the match is affected by the
    # very low resolution of these images (256 x 256 pixels). That low resolution was
    # chosen to keep the test data small.
    expected_result = fits.getheader(os.path.join(DATA_DIR,
                                                  'wcs-sol-from-thumbnail-image-index-5200.fit'))

    wcs_r = WCS(result)
    wcs_e = WCS(header=expected_result)

    # Check that, at a a grid of points roughly in the center of the image, the WCS
    # solutions are the same to within 0.1 arcsec.
    # The grid created below covers all of this small image.
    center = np.array([image_width // 2, image_height // 2])
    extent = image_width

    separations = _calculate_wcs_separation_at_points([wcs_r, wcs_e], center, extent)

    # The tolerance is higher here than in the other tests because of the
    # low resolution of the test image. It leads to a difference in calculated
    # coordinates of up to 2 arcsec across the whole image. The likely reason
    # is that the source detection method is different locally than on
    # astrometry.net.
    assert (separations.arcsec).max() < 2.2

    # The headers should also be about the same in this case.
    for key in result:
        if key == 'COMMENT' or key == 'HISTORY':
            continue
        try:
            difference = expected_result[key] - result[key]
        except TypeError:
            pass

        assert_allclose(difference, 0, atol=1e-4)


@pytest.mark.skipif(not api_key, reason='API key not set.')
@pytest.mark.remote_data
def test_solve_timeout_behavior():
    a = AstrometryNet()
    a.api_key = api_key
    sources = Table.read(os.path.join(DATA_DIR, 'test-source-list.fit'))
    with pytest.raises(TimeoutError) as e:
        # The timeout is set very low to guarantee an error is raised.
        result = a.solve_from_source_list(sources['X'], sources['Y'],
                                          4109, 4096,
                                          crpix_center=True,
                                          solve_timeout=2)

    # Submission id should be the second argument of the
    # exception. The exception is in the value attribute of
    # pytest's ExceptionInfo object.
    submission_id = e.value.args[1]

    # The solve itself should succeed; check that it does.
    result = a.monitor_submission(submission_id, solve_timeout=120)

    expected_result = fits.getheader(os.path.join(DATA_DIR,
                                                  'wcs-sol-from-source-list-index-5200.fit'))

    for key in result:
        if key == 'COMMENT' or key == 'HISTORY':
            continue
        try:
            difference = expected_result[key] - result[key]
        except TypeError:
            pass
        assert_allclose(difference, 0, atol=1e-4)


@pytest.mark.skipif(not api_key, reason='API key not set.')
@pytest.mark.remote_data
def test_solve_from_image_default_behaviour():
    # Test that solving by uploading an image works
    a = AstrometryNet()
    a.api_key = api_key
    sources = Table.read(os.path.join(DATA_DIR, 'test-source-list.fit'))
    # The image_width, image_height and crpix_center below are set to match the
    # original solve on astrometry.net.
    result = a.solve_from_source_list(sources['X'], sources['Y'],
                                      4109, 4096,
                                      crpix_center=True)

    assert isinstance(result, fits.Header)


@pytest.mark.skipif(not api_key, reason='API key not set.')
@pytest.mark.remote_data
def test_solve_from_image_with_return_submission_id():
    # Test that solving by uploading an image works
    a = AstrometryNet()
    a.api_key = api_key
    sources = Table.read(os.path.join(DATA_DIR, 'test-source-list.fit'))
    # The image_width, image_height and crpix_center below are set to match the
    # original solve on astrometry.net.
    result = a.solve_from_source_list(sources['X'], sources['Y'],
                                      4109, 4096,
                                      crpix_center=True,
                                      return_submission_id=True)

    assert isinstance(result, tuple)
