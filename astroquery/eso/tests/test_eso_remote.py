# Licensed under a 3-clause BSD style license - see LICENSE.rst
import os
from astropy.tests.helper import pytest, remote_data
from ...eso import Eso

CACHE_PATH = os.path.join(os.path.dirname(__file__), 'data')

try:
    import keyring
    HAS_KEYRING = True
except ImportError:
    HAS_KEYRING = False


@pytest.mark.skipif('not HAS_KEYRING')
@remote_data
class TestEso:
    def test_SgrAstar():
        eso = Eso()
        eso.cache_location = CACHE_PATH

        instruments = eso.list_instruments()
        result_i = eso.query_instrument(instruments[0], target='Sgr A*')

        surveys = eso.list_surveys()
        result_s = eso.query_survey(surveys[0], target='Sgr A*')

        assert result_i is not None
        assert result_s is not None

    def test_empty_return():
        # test for empty return with an object from the North
        eso = Eso()
        surveys = eso.list_surveys()
        result_s = eso.query_survey(surveys[0], target='M51')

        assert result_s is None
