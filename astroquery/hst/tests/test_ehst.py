# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""

@author: Javier Duran
@contact: javier.duran@sciops.esa.int

European Space Astronomy Centre (ESAC)
European Space Agency (ESA)

Created on 13 Ago. 2018


"""
import unittest
import os
import pytest

from astroquery.hst.core import HstClass
#import astropy.units as u
#from astropy.coordinates.sky_coordinate import SkyCoord
#from astropy.units import Quantity
#import numpy as np

def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)


class TestTap(unittest.TestCase):

    def test_get_product(self):
        ehst = HstClass()
        # default parameters
        parameters = {}
        parameters['observation_id'] = "J6FL25S4Q"
        parameters['calibration_level'] = "RAW"
        parameters['verbose'] = False
        ehst.test_get_product(
        dummyTapHandler.check_call('load_tables', parameters)
        # test with parameters
        dummyTapHandler.reset()
        parameters = {}
        parameters['only_names'] = True
        parameters['include_shared_tables'] = True
        parameters['verbose'] = True
        tap.load_tables(True, True, True)
        dummyTapHandler.check_call('load_tables', parameters)

    def test_get_artifact(self):
        ehst = HstClass()
        # default parameters
        parameters = {}
        parameters['artifact_id'] = 'O5HKAX030_FLT.FITS'
        parameters['verbose'] = False

    def test_get_postcard(self):
        ehst = HstClass()
        # default parameters
        parameters = {}
        parameters['table'] = 'table'
        parameters['verbose'] = False
        tap.load_table('table')
        dummyTapHandler.check_call('load_table', parameters)
        # test with parameters
        dummyTapHandler.reset()
        parameters = {}
        parameters['table'] = 'table'
        parameters['verbose'] = True
        tap.load_table('table', verbose=True)
        dummyTapHandler.check_call('load_table', parameters)
    
    def test_get_metadata(self):
        ehst = HstClass()
        # default parameters
        parameters = {}
        parameters['table'] = 'table'
        parameters['verbose'] = False
        tap.load_table('table')
        dummyTapHandler.check_call('load_table', parameters)
        # test with parameters
        dummyTapHandler.reset()
        parameters = {}
        parameters['table'] = 'table'
        parameters['verbose'] = True
        tap.load_table('table', verbose=True)
        dummyTapHandler.check_call('load_table', parameters)


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
