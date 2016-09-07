#
from astroquery.esasky import ESASky
import matplotlib.pyplot as plt

ea = ESASky()
#result = ea.query_object_async('PCCS2 857 G104.80+68.56', catalog='mv_pcss_catalog_hfi_fdw', limit=100, get_query_payload=False)
#result = ea.query_herschel_metadata(1342254493, get_query_payload=False)
# PMODE with PACS + SPIRE with the same OBSID
obsid = 1342231852
instrument = 'PACS'
#instrument = 'SPIRE'
result = ea.query_herschel_observations(obsid, get_query_payload=False)
# result.content is a gzipped VOTable
print (result)
maps = ea.get_herschel_default_maps(result, instrument='SPIRE')

plt.imshow(maps['250']['image'].data)
plt.show()
#

