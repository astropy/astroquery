from astroquery import nist
import pytest

def test_basic():
    Q = nist.NISTAtomicLinesQuery()
    Q.query_line('H I',4000,7000,wavelength_unit='A',energy_level_unit='eV')
