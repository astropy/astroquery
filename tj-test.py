import sys
sys.path.insert(0, "/Users/tjaffe/space/sw/heasarc/trjaffe/astroquery")
import astropy.coordinates as coord
from astroquery.utils import commons, parse_coordinates
from astroquery.heasarc import Heasarc
from astroquery.heasarc import Heasarc, HeasarcClass
from astropy.time import Time

coords = coord.SkyCoord(217.0, -31.7, frame='icrs', unit='deg')
coords_str = "217.0,-31.7"
start_time = Time("2017-01-01")
end_time = Time("2020-01-01")

print("---------------- ")
full_with_strpos = Heasarc.query_all("217.0000 -31.7000", debug=True, start_time="2017-01-01",
                                     end_time="2020-01-01")
print(full_with_strpos)
# exit()


print("---------------- using Time")
# has to be called from a Heasarc instance
print(Heasarc.query_all(coords, start_time=start_time,
                        end_time=end_time, get_query_payload=True))
print("---------------- using string")
print(Heasarc.query_all(coords_str, start_time="2017-01-01",
                        end_time="2020-01-01", get_query_payload=True))
print("---------------- using Time and no coords")
print(Heasarc.query_all(start_time=start_time,
                        end_time=end_time, get_query_payload=True))


print("-------------  'coord.SkyCoord(217.0,-31.7, frame='icrs', unit='deg')''")
print(coords)
print("-------------  parse_coordinates('217.0,-31.7')")
print(parse_coordinates('217.0,-31.7'))

start_time = "2017-01-01"
end_time = "2020-01-02"
print("---------------- using matches")
#  has to be called from the class
print(HeasarcClass._query_matches("217.0", "-31.7", start_time="2017-01-01", end_time="2020-01-01"))
print("---------------- using SkyCoords")
# has to be called from a Heasarc instance
print(Heasarc.query_all(coords, start_time=Time("2017-01-01"), end_time=Time("2017-01-01"), get_query_payload=True))
print("---------------- using string")
print(Heasarc.query_all(coords_str, get_query_payload=True))

print("---------------- using string with more zeros")
print(Heasarc.query_all("217.0000,-31.7000", get_query_payload=True))
exit()


#  Need to use the class to call one of its static functions
vec = HeasarcClass._get_vec("217.0", "-31.7")
print(f"Vector result is {vec}")
print("----------------")

exit()


# result = Heasarc.query_all(coords,times="2017-01-01..2018-01-01")
# result = Heasarc.query_all(times="2017-01-01..2018-01-01")
result = Heasarc.query_all(coords, times=times)


print(result[0:10])
exit()


print("----------------")
print("----------------Getting top result")
print("")
result = Heasarc.query_region(coords, catalog=result['table_name'][0])
print(result)
