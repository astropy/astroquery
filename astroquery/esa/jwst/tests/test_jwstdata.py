# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
===============
JWST DATA Tests
===============

@author: Raul Gutierrez-Sanchez
@contact: raul.gutierrez@sciops.esa.int

European Space Astronomy Centre (ESAC)
European Space Agency (ESA)

Created on 05 nov. 2018


"""
import unittest
import os
import pytest

from astroquery.esa.jwst.tests.DummyTapHandler import DummyTapHandler
from astroquery.esa.jwst.tests.DummyDataHandler import DummyDataHandler

from astroquery.esa.jwst.core import JwstClass


def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)


def get_product_mock(params, *args, **kwargs):
    if(args[0] == 'file_name_id'):
        return "00000000-0000-0000-8740-65e2827c9895"
    else:
        return "jw00617023001_02102_00001_nrcb4_uncal.fits"


@pytest.fixture(autouse=True)
def get_product_request(request):
    try:
        mp = request.getfixturevalue("monkeypatch")
    except AttributeError:  # pytest < 3
        mp = request.getfuncargvalue("monkeypatch")
    mp.setattr(JwstClass, '_query_get_product', get_product_mock)
    return mp


class TestData(unittest.TestCase):

    def test_get_product(self):
        dummyTapHandler = DummyTapHandler()
        jwst = JwstClass(dummyTapHandler)
        # default parameters
        parameters = {}
        parameters['artifact_id'] = None
        with pytest.raises(ValueError) as err:
            jwst.get_product()
        assert "Missing required argument: 'artifact_id'" in err.value.args[0]
        # dummyDataHandler.check_call('get_product', parameters)
        # test with parameters
        dummyTapHandler.reset()
        parameters = {}
        params_dict = {}
        params_dict['RETRIEVAL_TYPE'] = 'PRODUCT'
        params_dict['DATA_RETRIEVAL_ORIGIN'] = 'ASTROQUERY'
        params_dict['ARTIFACTID'] = '00000000-0000-0000-8740-65e2827c9895'
        parameters['params_dict'] = params_dict
        parameters['output_file'] = 'jw00617023001_02102_00001_nrcb4_'\
                                    'uncal.fits'
        parameters['verbose'] = False
        jwst.get_product(artifact_id='00000000-0000-0000-8740-65e2827c9895')
        dummyTapHandler.check_call('load_data', parameters)


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
