# Licensed under a 3-clause BSD style license - see LICENSE.rst
import os
from ...eso import Eso
from astropy.tests.helper import pytest

CACHE_PATH = os.path.join(os.path.dirname(__file__), 'data')

# This test should attempt to access the internet and therefore should fail
@pytest.mark.xfail
def test_SgrAstar():
    # Local caching prevents a remote query here

    eso = Eso()
    # set up local cache path to prevent remote query
    eso.cache_location = CACHE_PATH

    result = eso.query_instrument('amber', target='Sgr A*')
    
    # test that max_results = 50
    assert len(result) == 50

    assert 'GC_IRS7' in result['Object']
