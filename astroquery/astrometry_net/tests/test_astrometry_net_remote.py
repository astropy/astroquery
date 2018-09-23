# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import print_function

import os

# performs similar tests as test_module.py, but performs
# the actual HTTP request rather than monkeypatching them.
# should be disabled or enabled at will - use the
# remote_data decorator from astropy:
import pytest

from astropy.tests.helper import remote_data
from astropy.table import Table
from astropy.io import fits

from .. import conf, AstrometryNet

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')


def data_path(filename):
    return os.path.join(DATA_DIR, filename)


api_key = conf.api_key or os.environ.get('ASTROMETRY_NET_API_KEY')


@pytest.mark.skipif(not api_key, reason='API key not set.')
@remote_data
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
