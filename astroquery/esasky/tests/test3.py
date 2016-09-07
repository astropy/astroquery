#
from astroquery.esasky import ESASky
import matplotlib.pyplot as plt
from astropy.coordinates import SkyCoord
import astropy.units as u

ea = ESASky()
esaskyMaps = ea.get_esasky_obs()
print (esaskyMaps)
esaskyCats = ea.get_esasky_catalogs()
print (esaskyCats)
#
#
ra = 265.05 * u.degree
dec = 69.0 * u.degree
coo= SkyCoord(ra, dec, frame='icrs', unit='deg')
#
obsx = 'mv_hsa_esasky_photo_table_fdw'
result = ea.query_region_obs(coo,radius=0 * u.arcmin,mission=obsx, get_query_payload=False)
print ("Found total of %i observations in %s"%(len(result),obsx))
print ("Listing of the OBSIDS")
print (result['observation_id'])
obsid = int(result['observation_id'][-1])
#
# now get the last one and plot it:
#
print ("Now searching for Herschel observation %i"%obsid)
#
output = ea.query_herschel_observations(obsid, get_query_payload=False)
#
maps = ea.get_herschel_default_maps(output, instrument='SPIRE')
#
#targetName = maps['250'][0].header['OBJECT']
#plt.imshow(maps['250']['image'].data)
#plt.title(targetName)
#plt.show()
#

