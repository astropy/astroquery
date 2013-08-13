# Licensed under a 3-clause BSD style license - see LICENSE.rst
from astroquery import alfalfa

# Test Case: A Seyfert 1 galaxy
RA = '0h8m05.63s'
DEC = '14d50m23.3s'


def test_alfalfa_catalog():
    cat = alfalfa.get_catalog()


def test_alfalfa_crossID():
    agc = alfalfa.crossID(ra=RA, dec=DEC, optical_counterpart=True)
    global AGC
    AGC = agc


def test_alfalfa_spectrum():
    sp = alfalfa.get_spectrum(AGC)

if __name__ == '__main__':
    test_alfalfa_catalog()
    test_alfalfa_crossID()
    test_alfalfa_spectrum()
