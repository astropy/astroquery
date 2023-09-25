# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
================
eJWST DATA Tests
================

European Space Astronomy Centre (ESAC)
European Space Agency (ESA)

"""
import os
import pytest
from requests import HTTPError

from astroquery.esa.jwst.tests.DummyTapHandler import DummyTapHandler
from astroquery.esa.jwst.core import JwstClass


def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)


def get_product_mock(params, *args, **kwargs):
    if kwargs and kwargs.get('file_name'):
        return "00000000-0000-0000-8740-65e2827c9895"
    else:
        return "jw00617023001_02102_00001_nrcb4_uncal.fits"


@pytest.fixture(autouse=True)
def get_product_request(request):
    mp = request.getfixturevalue("monkeypatch")
    mp.setattr(JwstClass, '_query_get_product', get_product_mock)
    return mp


class TestData:

    def test_get_product(self):
        dummyTapHandler = DummyTapHandler()
        jwst = JwstClass(tap_plus_handler=dummyTapHandler, show_messages=False)
        # default parameters
        parameters = {}
        parameters['artifact_id'] = None
        with pytest.raises(ValueError) as err:
            jwst.get_product()
        assert "Missing required argument: 'artifact_id'" in err.value.args[0]
        # test with parameters
        dummyTapHandler.reset()
        parameters = {}
        params_dict = {}
        params_dict['RETRIEVAL_TYPE'] = 'PRODUCT'
        params_dict['TAPCLIENT'] = 'ASTROQUERY'
        params_dict['ARTIFACTID'] = '00000000-0000-0000-8740-65e2827c9895'
        parameters['params_dict'] = params_dict
        parameters['output_file'] = 'jw00617023001_02102_00001_nrcb4_uncal.fits'
        parameters['verbose'] = False
        jwst.get_product(artifact_id='00000000-0000-0000-8740-65e2827c9895')
        dummyTapHandler.check_call('load_data', parameters)


@pytest.mark.remote_data
def test_login_error():
    jwst = JwstClass()
    with pytest.raises(HTTPError) as err:
        jwst.login(user="dummy", password="dummy")
    assert "Unauthorized" in err.value.args[0]
