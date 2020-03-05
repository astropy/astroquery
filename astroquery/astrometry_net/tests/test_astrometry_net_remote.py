# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import print_function

import os

# performs similar tests as test_module.py, but performs
# the actual HTTP request rather than monkeypatching them.
# should be disabled or enabled at will - use the
# remote_data decorator from astropy:
import pytest

from astropy.table import Table
from astropy.io import fits

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


@pytest.mark.skipif(not api_key, reason='API key not set.')
@pytest.mark.remote_data
def test_solve_by_source_list():
    a = AstrometryNet()
    a.api_key = api_key
    sources = Table.read(os.path.join(DATA_DIR, 'test-source-list.fit'))
    # The image_width, image_height and crpix_center below are set to match the
    # original solve on astrometry.net.
    result = a.solve_from_source_list(sources['X'], sources['Y'],
                                      4109, 4096,
                                      crpix_center=True)

    expected_result = fits.getheader(os.path.join(DATA_DIR,
                                                  'test-wcs-sol.fit'))

    for key in result:
        try:
            difference = expected_result[key] - result[key]
        except TypeError:
            pass
        assert difference == 0


@pytest.mark.skipif(not api_key, reason='API key not set.')
@pytest.mark.remote_data
def test_solve_image_upload():
    # Test that solving by uploading an image works
    a = AstrometryNet()
    a.api_key = api_key
    image = os.path.join(DATA_DIR, 'thumbnail-image.fit.gz')
    # The test image only solves if it is not downsampled
    result = a.solve_from_image(image,
                                force_image_upload=True,
                                downsample_factor=1)
    expected_result = fits.getheader(os.path.join(DATA_DIR,
                                                  'thumbnail-wcs-sol.fit'))
    for key in result:
        try:
            difference = expected_result[key] - result[key]
        except TypeError:
            pass
        assert difference == 0


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
    # The source detection parameters below (fwhm, detect_threshold)
    # are specific to this test image. They should not be construed
    # as a general recommendation.
    result = a.solve_from_image(image,
                                force_image_upload=False,
                                downsample_factor=1,
                                fwhm=1.5, detect_threshold=5,
                                center_ra=135.618, center_dec=49.786,
                                radius=0.5)
    expected_result = fits.getheader(os.path.join(DATA_DIR,
                                                  'thumbnail-wcs-sol-from-photutils.fit'))
    for key in result:
        try:
            difference = expected_result[key] - result[key]
        except TypeError:
            pass
        assert difference == 0


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
                                                  'test-wcs-sol.fit'))

    for key in result:
        try:
            difference = expected_result[key] - result[key]
        except TypeError:
            pass
        assert difference == 0
