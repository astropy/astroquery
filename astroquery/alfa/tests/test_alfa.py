from astroquery import alfa

# Test Case: A Seyfert 1 galaxy
RA = '0h8m05.63s'
DEC = '14d50m23.3s'

def test_alfa_catalog():
    cat = alfa.get_catalog()

def test_alfa_spectrum():
    sp = alfa.get_spectrum(ra=RA, dec=DEC, counterpart=True)

if __name__ == '__main__':
    test_alfa_catalog()
    test_alfa_spectrum()
    