from astroquery.astrocats import OACAPI

'''# Test object query
photometry = OACAPI.query_object(object_name='GW170817')
print(photometry[:5])
'''

# Test region query
import astropy.units as u
import astropy.coordinates as coord

ra = 197.45037
dec = -23.38148


test_coords = coord.SkyCoord(ra = ra, dec = dec, unit = (u.deg, u.deg))

test_table = OACAPI.query_region(coordinates = test_coords,
                                 width =  10,
                                 height = 10,
                                 get_query_payload=False,
                                 verbose=True)

print(test_table[:5])