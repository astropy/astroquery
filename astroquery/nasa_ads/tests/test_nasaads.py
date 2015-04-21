from ... import nasa_ads
from astropy.tests.helper import pytest

def test_simple():
    x = nasa_ads.ADS.query_simple('^Persson Origin of water around deeply embedded low-mass protostars')
    assert x[-1]['authors'][0] == 'Persson, M. V.'
