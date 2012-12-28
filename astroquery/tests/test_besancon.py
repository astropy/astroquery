from astroquery import besancon
from astropy.io.ascii import besancon as besancon_reader
import asciitable
import pytest

def test_basic():
    besancon_model = besancon.request_besancon('your@email.net',10.5,0.0)
    B = asciitable.read(besancon_model,Reader=besancon_reader.BesanconFixed,guess=False)
    B.pprint()

