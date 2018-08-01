from astroquery.vizier import Vizier
from astropy import coordinates
from astropy import units as u

v = Vizier(keywords=['stars:white_dwarf'])

c = coordinates.SkyCoord(0, 0, unit=('deg', 'deg'), frame='icrs')
result = v.query_region(c, radius=2*u.deg)

print(len(result))
# 44

result[0].pprint()
"""
   LP    Rem Name  RA1950   DE1950  Rmag l_Pmag Pmag u_Pmag spClass     pm    pmPA  _RA.icrs   _DE.icrs
                  "h:m:s"  "d:m:s"  mag         mag                 arcs / yr deg              "d:m:s"
-------- --- ---- -------- -------- ---- ------ ---- ------ ------- --------- ---- ---------- ---------
584-0063          00 03 23 +00 01.8 18.1        18.3              f     0.219   93 00 05 56.8 +00 18 41
643-0083          23 50 40 +00 33.4 15.9        17.0              k     0.197   93 23 53 13.7 +00 50 15
584-0030          23 54 05 -01 32.3 16.6        17.7              k     0.199  193 23 56 38.8 -01 15 26
"""
