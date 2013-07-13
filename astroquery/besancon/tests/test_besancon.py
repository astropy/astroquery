# Licensed under a 3-clause BSD style license - see LICENSE.rst

from ... import besancon
import os
from astropy.tests.helper import pytest  # import this since the user may not have pytest installed
import astropy.io.ascii as asciitable
from astropy.io.ascii.tests.common import assert_equal

# SKIP - don't run tests because Besancon folks don't want them (based on the fact that your@email.net is now rejected)
# def test_besancon_reader():
#     #assert os.path.exists('besancon_test.txt')
#     B = asciitable.read('t/besancon_test.txt',Reader=besancon.BesanconFixed,guess=False)
#     assert_equal(len(B),12)
# 
# def test_basic():
#     besancon_model = besancon.request_besancon('astropy.astroquery@gmail.com',10.5,0.0,rsup=0.5)
#     B = asciitable.read(besancon_model,Reader=besancon.BesanconFixed,guess=False)
#     B.pprint()

class TestCase(object):
    def data(self, filename):
        data_dir = os.path.join(os.path.dirname(__file__), 'data')
        return os.path.join(data_dir, filename)

class TestBesancon(TestCase):

    def test_offline(self):
        besancon_model = self.data('besancon_test.txt')
        B = asciitable.read(besancon_model,Reader=besancon.BesanconFixed,guess=False) 
        B.pprint()
        assert_equal(len(B),13)
        assert_equal(len(B.columns),18)
        assert_equal(repr(B.columns),"<TableColumns names=('Dist','Mv','CL','Typ','LTef','logg','Age','Mass','J-H','H-K','J-K','V-K','V','[Fe/H]','l','b','Av','Mbol')>")
