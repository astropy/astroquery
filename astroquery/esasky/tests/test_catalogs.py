from astroquery.esasky import ESASky
import astropy.units as u
from astropy.coordinates import SkyCoord

ra = 265.05 * u.degree
dec = 69.0 * u.degree
coordinates = SkyCoord(ra, dec, frame='icrs', unit='deg')

# result = esasky.list_catalogs()
# assert (len(result) == 13)
# assert (len(result) != 13)
result = ESASky.query_region_catalogs("Abell 1689", 30*u.arcmin, ["Gaia DR1 TGAS", "XMM-SLEW", "HSC"])
print(result)
    
print(ESASky.query_region_catalogs(coordinates, 10*u.arcmin, "all"))
print(ESASky.query_region_catalogs(coordinates, 1*u.arcmin, "XMM-SLEW"))
print(ESASky.query_region_catalogs("m81", 1*u.arcmin, "INTEGRAL"))

