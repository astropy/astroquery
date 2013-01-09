from astroquery import nist

def test_html():
    Q = nist.NISTAtomicLinesQuery()
    Q.query_line_html('H I',4000,7000,wavelength_unit='A',energy_level_unit='eV')

def test_ascii():
    Q = nist.NISTAtomicLinesQuery()
    Q.query_line_ascii('H I',4000,7000,wavelength_unit='A',energy_level_unit='eV')
