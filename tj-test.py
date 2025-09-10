import sys
sys.path.insert(0, "/Users/tjaffe/space/sw/heasarc/trjaffe/astroquery")
import astropy.coordinates as coord
from astroquery.heasarc import Heasarc
coords = coord.SkyCoord(187.277915, 2.052388, frame='icrs', unit='deg')

result = Heasarc.query_all(coords,get_query_payload=True)
print(result)

result = Heasarc.query_all(coords)
print(result[0:10])


