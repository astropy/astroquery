# Licensed under a 3-clause BSD style license - see LICENSE.rst
from ... import sdss
from astropy import coordinates

# Test Case: A Seyfert 1 galaxy
coords = coordinates.ICRSCoordinates('0h8m05.63s +14d50m23.3s')


def test_sdss_spectrum():
    xid = sdss.core.SDSS.query_region(coords, spectro=True)
    sp = sdss.core.SDSS.get_spectra(xid)
    
def test_sdss_image():
    xid = sdss.core.SDSS.query_region(coords)
    img = sdss.core.SDSS.get_images(xid)
    
def test_sdss_template():
    template = sdss.core.SDSS.get_spectral_template('qso')
