# Licensed under a 3-clause BSD style license - see LICENSE.rst
import numpy as np
import os
import pytest
import six

from astropy.table import Table
from astropy.io import fits

from ...utils.testing_tools import MockResponse
from ...exceptions import (InvalidQueryError)

from .. import AstrometryNet
from .. import conf

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')


def data_path(filename):
    return os.path.join(DATA_DIR, filename)


def test_setting_validation_basic():
    a = AstrometryNet()
    # This gets us a list of settings, their types, and restrictions.
    constraints = a._constraints
    for constraint, vals in six.iteritems(constraints):
        if vals['type'] == str or vals['type'] == bool:
            settings = {constraint: 'asdiuhiuas'}
            with pytest.raises(ValueError) as e:
                a._validate_settings(settings)
            if vals['type'] == str:
                assert settings[constraint] in str(e)
                assert 'is invalid. The valid values' in str(e)
            else:
                assert "must be of type <class 'bool'>" in str(e)
        else:
            # Pick a value smaller than the minimum value
            settings = {constraint: vals['allowed'][0] - 10}
            with pytest.raises(ValueError) as e:
                a._validate_settings(settings)
            print(str(e))
            assert str(settings[constraint]) in str(e)
            assert 'The valid values are' in str(e)


api_key = conf.api_key or os.environ.get('ASTROMETRY_NET_API_KEY')


@pytest.mark.skipif(not api_key, reason='API key not set.')
def test_solve_by_source_list():
    a = AstrometryNet()
    a.api_key = api_key
    sources = Table.read(os.path.join(DATA_DIR, 'test-source-list.fit'))
    # The image_width, image_height and crpix_center blo are set to match the
    # original solve on astrometry.net.
    result = a.solve_from_source_list(x=sources['X'], y=sources['Y'],
                                      image_width=4109, image_height=4096,
                                      crpix_center=True)

    expected_result = fits.getheader(os.path.join(DATA_DIR,
                                                  'test-wcs-sol.fit'))

    for key in result:
        try:
            difference = expected_result[key] - result[key]
        except TypeError:
            pass
        assert difference == 0
