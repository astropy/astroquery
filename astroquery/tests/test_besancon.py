from astroquery import besancon
import asciitable
from astropy.io.ascii.tests.common import assert_equal

def test_besancon_reader():
    #assert os.path.exists('besancon_test.txt')
    B = asciitable.read('t/besancon_test.txt',Reader=besancon.BesanconFixed,guess=False)
    assert_equal(len(B),12)

def test_basic():
    besancon_model = besancon.request_besancon('your@email.net',10.5,0.0)
    B = asciitable.read(besancon_model,Reader=besancon.BesanconFixed,guess=False)
    B.pprint()


