from ... import alfalfa
from astropy import coordinates

# Test Case: A Seyfert 1 galaxy
coords = coordinates.ICRSCoordinates('0h8m05.63s +14d50m23.3s')

def test_alfalfa_catalog():
    cat = alfalfa.core.ALFALFA.get_catalog()

def test_alfalfa_crossID():
    agc = alfalfa.core.ALFALFA.query_region(coords, optical_counterpart=True)
    global AGC
    AGC = agc

def test_alfalfa_spectrum():
    sp = alfalfa.core.ALFALFA.get_spectra(AGC)

if __name__ == '__main__':
    test_alfalfa_catalog()
    test_alfalfa_crossID()
    test_alfalfa_spectrum()
    