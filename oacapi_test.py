import astropy.coordinates as coord
import astropy.units as u
from astroquery.oac import OAC


ra = 197.45037
dec = -23.38148

test_coords = coord.SkyCoord(ra=ra, dec=dec, unit=(u.deg, u.deg))

test_radius = 10*u.arcsec
test_height = 10*u.arcsec
test_width = 10*u.arcsec

test_time = 57740
spectra = OAC.get_spectra("SN2014J")
print (spectra.keys())
print (spectra["SN2014J"].keys())
print (spectra["SN2014J"]["spectra"][0][0])
print (spectra["SN2014J"]["spectra"][0][1][0])
