# Licensed under a 3-clause BSD style license - see LICENSE.rst
import numpy as np
import os
import pytest
import six

from ...utils.testing_tools import MockResponse
from ...exceptions import (InvalidQueryError)

from .. import AstrometryNet

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
