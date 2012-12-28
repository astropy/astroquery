from astroquery import besancon
import asciitable
import pytest
import os

from astropy.io.ascii.tests.common import (raises,
                     assert_equal, assert_almost_equal, assert_true,
                     setup_function, teardown_function, has_isnan)

def test_besancon_reader():
    #assert os.path.exists('besancon_test.txt')
    B = asciitable.read('t/besancon_test.txt',Reader=besancon.BesanconFixed,guess=False)
    assert_equal(len(B),12)

def test_basic():
    besancon_model = besancon.request_besancon('your@email.net',10.5,0.0)
    B = asciitable.read(besancon_model,Reader=besancon.BesanconFixed,guess=False)
    B.pprint()


