from astroquery.esasky import ESASky
import astropy.units as u
from astropy.coordinates import SkyCoord

ra = 265.05 * u.degree
dec = 69.0 * u.degree
coordinates = SkyCoord(ra, dec, frame='icrs', unit='deg')

result = ESASky.query_region_maps("Abell 1689", 100*u.arcmin, ['HST', 'Herschel', 'XMM-EPIC'])
for key in result.keys():
    result[key].pprint(100, 1000)

maps = ESASky.get_images("Abell 1689", 100*u.arcmin, ['HST', 'Herschel', 'XMM-EPIC'], '/home/hnorman/workspace')
maps = ESASky.get_maps(result, ["Herschel"], '/home/hnorman/workspace')

name = "all"
result = ESASky.query_region_maps(coordinates, "14'", name)
print(result)
result = ESASky.query_region_maps("M51", 20 * u.arcmin, name)
print(result)
 
maps = ESASky.get_maps(result)
print(maps)
