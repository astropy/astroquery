from astroquery.esasky import ESASky
import astropy.units as u
from astropy.coordinates import SkyCoord


ra = 265.05 * u.degree
dec = 69.0 * u.degree
coordinates = SkyCoord(ra, dec, frame='icrs', unit='deg')

esasky = ESASky()
# print(esasky.query_region_maps(coordinates, 1*u.arcmin, "all"))

name = "all"
result = esasky.query_region_maps("m31", 14 * u.arcmin, name)
print(result)
 
maps = esasky.get_maps(result)
print(maps)
