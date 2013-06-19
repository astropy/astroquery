from ... import sdss

# Test Case: A Seyfert 1 galaxy
RA = '0h8m05.63s'
DEC = '14d50m23.3s'

def test_sdss_spectrum():
    xid = sdss.crossID(ra=RA, dec=DEC)
    sp = sdss.get_spectrum(crossID=xid[0])
    
def test_sdss_image():
    xid = sdss.crossID(ra=RA, dec=DEC)
    img = sdss.get_image(crossID=xid[0])
    
def test_sdss_template():
    template = sdss.get_spectral_template('qso')
