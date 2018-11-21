from astropy import coordinates
from astroquery.simbad import Simbad

customSimbad = Simbad()

# We've seen errors where ra_prec was NAN, but it's an int: that's a problem
# this is a workaround we adapted
customSimbad.add_votable_fields('ra(d)', 'dec(d)')
customSimbad.remove_votable_fields('coordinates')

C = coordinates.SkyCoord(0, 0, unit=('deg', 'deg'), frame='icrs')

result = customSimbad.query_region(C, radius='2 degrees')

result[:5].pprint()
"""
    MAIN_ID        RA_d       DEC_d
 ------------- ----------- ------------
 ALFALFA 5-186  0.00000000   0.00000000
 ALFALFA 5-188  0.00000000   0.00000000
 ALFALFA 5-206  0.00000000   0.00000000
 ALFALFA 5-241  0.00000000   0.00000000
 ALFALFA 5-293  0.00000000   0.00000000
"""
