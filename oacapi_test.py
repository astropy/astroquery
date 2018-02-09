import astropy.coordinates as coord
import astropy.units as u
from astroquery.oac import OAC

# Test object query
'''photometry = OAC.query_object(event='GW170817', quantity='spectra',
                              attribute=['time', 'data'],
                              argument=None,
                              data_format='json')

print(photometry)'''

# Test Spectra
spectrum = OAC.get_single_spectrum(event="GW170817", time="54773")
print(spectrum)

# Test Coordinates
'''ra = 197.45037
dec = -23.38148

test_coords = coord.SkyCoord(ra=ra, dec=dec, unit=(u.deg, u.deg))

test_table = OAC.query_region(coordinates=test_coords,
                              width=10,
                              height=10,
                              get_query_payload=False,
                              verbose=True)

print(test_table)
'''
