from astroquery.esasky import ESASky
import astropy.units as u
from astropy.coordinates import SkyCoord

ra = 265.05 * u.degree
dec = 69.0 * u.degree
coordinates = SkyCoord(ra, dec, frame='icrs', unit='deg')

esasky = ESASky()
print(esasky.query_region_maps("m51", 1*u.arcmin, "all"))
print(esasky.query_region_maps(coordinates, 1*u.arcmin, "all"))
print(esasky.query_region_maps("m51", 1*u.arcmin, "INTEGRAL"))
