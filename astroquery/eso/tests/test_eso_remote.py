# Licensed under a 3-clause BSD style license - see LICENSE.rst
import os
from astropy.tests.helper import remote_data
from ...eso import Eso

CACHE_PATH = os.path.join(os.path.dirname(__file__), 'data')

def test_SgrAstar():

    eso = Eso()
    eso.cache_location = CACHE_PATH
    instruments = eso.list_instruments()
    result = eso.query_instrument(instruments[0], target='Sgr A*')
    
