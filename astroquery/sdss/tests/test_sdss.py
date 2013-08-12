from ... import sdss
from astropy import coordinates

# Test Case: A Seyfert 1 galaxy
coords = coordinates.ICRSCoordinates('0h8m05.63s +14d50m23.3s')

def test_sdss_spectrum():
    xid = sdss.core.SDSS.query_region(coords, spectro=True)
    sp = sdss.get_spectrum(crossID=xid[0])
    
def test_sdss_image():
    xid = sdss.crossID(ra=RA, dec=DEC)
    img = sdss.get_image(crossID=xid[0])
    
def test_sdss_template():
    template = sdss.get_spectral_template('qso')
