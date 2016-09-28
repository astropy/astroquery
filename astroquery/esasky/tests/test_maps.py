from astroquery.esasky import ESASky
import astropy.units as u
from astropy.coordinates import SkyCoord

from astropy.table import Table

ra = 265.05 * u.degree
dec = 69.0 * u.degree
coordinates = SkyCoord(ra, dec, frame='icrs', unit='deg')

esasky = ESASky()

result = esasky.query_region_maps("Abell 1689", 100*u.arcmin, ['HST', 'Herschel'])
print(result)
for key in result.keys():
    result[key].pprint(100, 1000)

name = "all"
result = esasky.query_region_maps(coordinates, "14'", name)
print(result)
result = esasky.query_region_maps("M51", 20 * u.arcmin, name)
print(result)
 
maps = esasky.get_maps(result)
print(maps)
