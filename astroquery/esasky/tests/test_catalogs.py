from astroquery.esasky import ESASky
import astropy.units as u
from astropy.coordinates import SkyCoord

ra = 265.05 * u.degree
dec = 69.0 * u.degree
coordinates = SkyCoord(ra, dec, frame='icrs', unit='deg')

esasky = ESASky()
print(esasky._get_catalog_tap_table_list())
print(esasky._get_catalogs_json())
print(esasky.query_region_catalogs(coordinates, 1*u.arcmin, "all"))
print(esasky.query_region_catalogs(coordinates, 1*u.arcmin, "XMM-SLEW"))
print(esasky.query_region_catalogs("m81", 1*u.arcmin, "INTEGRAL"))

