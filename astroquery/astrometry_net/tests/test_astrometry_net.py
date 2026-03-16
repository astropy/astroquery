# Licensed under a 3-clause BSD style license - see LICENSE.rst
import os
import json

import pytest
from unittest.mock import patch, mock_open

from .. import AstrometryNet

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')


def data_path(filename):
    return os.path.join(DATA_DIR, filename)


def test_api_key_property():
    """
    Check that an empty key is returned if the api key is not in
    the configuration file and that the expected message shows up in
    the log.
    """
    anet = AstrometryNet()
    with pytest.raises(RuntimeError, match='Astrometry.net API key not set'):
        anet.api_key


def test_empty_settings_property():
    """
    Check that the empty settings property returns something and that
    the keys match what we expect.
    """
    anet = AstrometryNet()
    empty = anet.empty_settings
    # Ironically, empty should not be devoid of content...
    assert empty
    assert set(empty.keys()) == set(anet._constraints.keys())


def test_show_allowed_settings(capsys):
    """
    Check that the expected content is printed to standard out when the
    show_allowed_settings method is called.
    """
    anet = AstrometryNet()
    anet.show_allowed_settings()
    output = capsys.readouterr()
    for key in anet._constraints.keys():
        assert "{}: type ".format(key) in output.out


def test_login_fails_with_no_api_key():
    """
    Test for expected behavior when the api_key is not set
    """
    anet = AstrometryNet()
    anet.api_key = ''
    with pytest.raises(RuntimeError, match='Astrometry.net API key not set'):
        anet._login()


def test_construct_payload():
    """
    Test that _construct_payload returns the expected dictionary
    """
    anet = AstrometryNet()
    settings = anet.empty_settings
    payload = anet._construct_payload(settings)
    assert list(payload.keys()) == ['request-json']
    assert payload['request-json'] == json.dumps(settings)


def test_setting_validation_basic():
    anet = AstrometryNet()
    # This gets us a list of settings, their types, and restrictions.
    constraints = anet._constraints
    for constraint, vals in constraints.items():
        if vals['type'] == str or vals['type'] == bool:
            settings = {constraint: 'asdiuhiuas'}
            with pytest.raises(ValueError) as e:
                anet._validate_settings(settings)
            if vals['type'] == str:
                assert settings[constraint] in str(e.value)
                assert 'is invalid. The valid values' in str(e.value)
            else:
                assert "must be of type" in str(e.value) and "'bool'" in str(e.value)
        else:
            # Pick a value smaller than the minimum value
            settings = {constraint: vals['allowed'][0] - 10}
            with pytest.raises(ValueError) as e:
                anet._validate_settings(settings)
            assert str(settings[constraint]) in str(e.value)
            assert 'The valid values are' in str(e.value)


def test_setting_validation_with_float_values():
    """
    Check that values that are supposed to be float are handled
    properly.
    """
    anet = AstrometryNet()

    # Try a setting that should be float and with a value that IS NOT
    # coercable to float.
    settings = {'center_ra': 'seven'}
    with pytest.raises(ValueError) as e:
        anet._validate_settings(settings)
    assert "Value for center_ra must be of type " in str(e.value)

    # Try a setting that should be float and with a value that IS
    # coercable to float.
    settings = {'center_ra': 7}
    # Nothing to assert here...success is this not raising an error
    anet._validate_settings(settings)


def test_setting_validation_with_bool_values():
    """
    Check that values that are supposed to be bool are handled
    properly.
    """
    anet = AstrometryNet()

    # Try a setting that should be bool but is not
    settings = {'crpix_center': 'seven'}
    with pytest.raises(ValueError) as e:
        anet._validate_settings(settings)
    assert "Value for crpix_center must be of type " in str(e.value)

    # Try a setting that should be bool and is bool
    settings = {'crpix_center': True}
    # Nothing to assert here...success is this not raising an error
    anet._validate_settings(settings)


def test_setting_validation_with_no_upper_bound():
    """
    Check that nothing happens when checking bounds for a
    setting with a lower but not upper bound. scale_lower is
    an example; it has a lower bound of 0 but no upper bound.
    """
    anet = AstrometryNet()

    # Try a setting that should be bool but is not
    settings = {'scale_lower': 1}
    # Nothing to assert here...success is this not raising an error
    anet._validate_settings(settings)


# Order in the required keys is meaningful; the first is supposed
# to be bigger, the second smaller.
@pytest.mark.parametrize("scale_type,required_keys", [
                         ('ev', ('scale_est', 'scale_err')),
                         ('ul', ('scale_upper', 'scale_lower'))
                         ])
def test_setting_validation_scale_type(scale_type, required_keys):
    """
    There are two scale types and each has a couple of other
    keywords that are expected to be present with them.
    """
    anet = AstrometryNet()

    settings = {'scale_type': scale_type}
    for key, value in zip(required_keys, [1, 0.1]):
        settings[key] = value

    # If an expected key is missing we should get an error. The missing
    # key here is "scale_unit"
    with pytest.raises(ValueError) as e:
        anet._validate_settings(settings)
    assert ('Scale type {} requires values '
            'for '.format(scale_type)) in str(e.value)

    # If we add the missing key then we should get no error
    settings['scale_units'] = 'arcsecperpix'
    # Nothing to assert here...success is this not raising an error
    anet._validate_settings(settings)


def test_invalid_setting_in_solve_from_source_list_name_raises_error():
    anet = AstrometryNet()
    anet.api_key = 'nonsensekey'
    with pytest.raises(ValueError) as e:
        # First four arguments are required but values are not checked until
        # after settings are checked (in the current implementation, at
        # least), so any values should work.
        # The keyword argument is definitely not one of the allowed ones.
        anet.solve_from_source_list([], [], [], [], im_a_bad_setting_name=5)
    assert 'im_a_bad_setting_name is not allowed' in str(e.value)


def test_get_query_payload_solve_from_source_list():
    anet = AstrometryNet()
    anet.api_key = 'fakekey'
    # Mock the _login method to prevent actual HTTP requests
    with patch.object(anet, '_login'):
        # Test that get_query_payload=True returns the payload dict
        payload = anet.solve_from_source_list([1, 2, 3], [4, 5, 6], 100, 100,
                                              get_query_payload=True)
        assert isinstance(payload, dict)
        assert 'request-json' in payload
        settings = json.loads(payload['request-json'])
        assert settings['x'] == [1.0, 2.0, 3.0]
        assert settings['y'] == [4.0, 5.0, 6.0]
        assert settings['image_width'] == 100
        assert settings['image_height'] == 100


def test_get_query_payload_solve_from_image():
    anet = AstrometryNet()
    anet.api_key = 'fakekey'
    with patch.object(anet, '_login'):
        anet._session_id = 'fakesessionid'
        with patch('builtins.open', mock_open()):
            payload = anet.solve_from_image('fake_image.fits',
                                            get_query_payload=True,
                                            center_ra=10.5,
                                            center_dec=20.3)
            assert isinstance(payload, dict)
            assert 'request-json' in payload
            settings = json.loads(payload['request-json'])
            assert settings['session'] == 'fakesessionid'
            assert settings['center_ra'] == 10.5
            assert settings['center_dec'] == 20.3
            # Verify that source list specific parameters are not present
            assert 'x' not in settings
            assert 'y' not in settings
            assert 'image_width' not in settings
            assert 'image_height' not in settings
