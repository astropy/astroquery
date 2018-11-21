from astroquery import open_exoplanet_catalogue as oec
from astroquery.open_exoplanet_catalogue import findvalue

cata = oec.get_catalogue()
kepler68b = cata.find(".//planet[name='Kepler-68 b']")
print(findvalue(kepler68b, 'mass'))

"""
0.02105109
"""
