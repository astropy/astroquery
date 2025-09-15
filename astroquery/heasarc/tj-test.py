import sys
sys.path.insert(0, "/Users/tjaffe/space/sw/heasarc/trjaffe/astroquery")
import astropy.coordinates as coord
from astroquery.heasarc import Heasarc
from astroquery.heasarc import Heasarc, HeasarcClass

coords = coord.SkyCoord(217.0,-31.7, frame='icrs', unit='deg')

#  Need to use the class to call one of its static functions
vec = HeasarcClass._get_vec("217.0","-31.7")
print(f"Vector result is {vec}")
print("----------------")
print("----------------")

result = Heasarc.query_all(coords,get_query_payload=True)
print(result)

exit()

result = Heasarc.query_all(coords)
print(result[0:10])

print("----------------")
print("----------------Getting top result")
print("")
result = Heasarc.query_region(coords,catalog=result['table_name'][0])
print(result)

print("----------------")
print("----------------All columns")
print("")

print(result.columns)
