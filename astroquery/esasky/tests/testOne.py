#
from astroquery.esasky import ESASky
#import json
#from astropy.table import Table
import zlib
import io
import os
import tarfile
#from astropy.io import ascii
from astropy.io import votable
from astropy.io import fits
import urllib.request
import tempfile

ea = ESASky()
#result = ea.query_object_async('PCCS2 857 G104.80+68.56', catalog='mv_pcss_catalog_hfi_fdw', limit=100, get_query_payload=False)
#result = ea.query_herschel_metadata(1342254493, get_query_payload=False)
# PMODE with PACS + SPIRE with the same OBSID
obsid = 1342231852
instrument = 'PACS'
#instrument = 'SPIRE'
result = ea.query_herschel_observations(obsid, get_query_payload=False)
# result.content is a gzipped VOTable
output = zlib.decompress(result.content, 16+zlib.MAX_WBITS)
f = io.BytesIO(output)
tx = votable.parse(f)
# this is a VOTableFile object
tbl = tx.get_first_table()
tomm = tbl.to_table(use_names_over_ids=True)
#
postcard_urls = tbl.array["postcard_url"].data
product_urls = tbl.array["product_url"].data
for urls in postcard_urls:
    urls_decoded = urls.decode('utf-8')
    if (instrument in urls_decoded): 
        postcard_url = urls_decoded
#print (postcard_url)
for urls in product_urls:
    urls_decoded = urls.decode('utf-8')
    if (instrument in urls_decoded): 
        product_url = urls_decoded
#print (product_url)
#
# now try to submit a requets to retrieve the data
#
#with urllib.request.urlopen(postcard_url) as response:
#            r = response.read()

tar_file = tempfile.NamedTemporaryFile()

with tempfile.TemporaryDirectory() as tmp_dir:
    with urllib.request.urlopen(product_url) as response:
        tar_file.write(response.read())    

    fitsOut = dict()            
    
    with tarfile.open(tar_file.name,'r') as tar:
        for member in tar.getmembers():
            print (member.name)
            if ('hspire' in member.name or 'hpacs' in member.name):
                f=tar.extract(member,path=tmp_dir)
                if ('hspireplw' in member.name):
                    array = '500'
                elif ('hspirepmw' in member.name):
                    array = '350'
                elif ('hspirepsw' in member.name):
                    array = '250'
                elif ('hpppmapb' in member.name):
                    array = 'blue'
                elif ('hpppmapr' in member.name):
                    array = 'red'
                else:
                    array = 'unknown'
                fitsFile = os.path.join(tmp_dir, member.name)
                fitsOut[array] = fits.open(fitsFile)
print (fitsOut)   
tar_file.close()

#votable = parse(tt.read())
#print (result.content)
#print (result.text)
# a = json.loads(result.text)
# metaa = a["metadata"]
# dataa = a["data"]
# print (dataa)
# b = dict()
# for i,imeta in enumerate(metaa):
#     cx = imeta["name"]
#     #print (i,cx)
#     b[cx] = dataone[i]
#     dd.append(dataone[i])
#     lx = len(str(dataone[i]))
#     dtp.append('S%i'%lx)
# #
# t = Table(names=nm,dtype=dtp)
# t.add_row(dd)
# print (t)
# ascii.write(t,'/Users/ivaltchanov/Tmp/test_table.csv',delimiter=",")
#import bs4
#htmldoc = bs4.BeautifulSoup(result.content)
#print (htmldoc)
#print (result)
#params = {'QUERY': "SELECT TOP 100 * FROM mv_pcss_catalog_hfi_fdw WHERE name='PCCS2 857 G104.80+68.56';", \
#    'FORMAT': 'VOT', 'REQUEST': 'doQuery', 'LANG': 'ADQL'}
#tt = ea._request('GET',ea.URL,params=params)
#tt.content
#
# # get the available TAP catalogs in ESASky
# urlcats = 'http://ammidev.n1data.lan:8080/esasky-tap/catalogs'
# with urllib.request.urlopen(urlcats) as response:
#     r = response.read().decode('utf-8')
# # this is a json bytes output that's why it needs decoding to string 
# a = json.loads(r)
# tmp = a["catalogs"]
# ncats = len(tmp)
# catsList = []
# for i in range(ncats):
#     catsList.append(tmp[i]["tapTable"])
# #
# # get the available TAP maps in ESASky
# #
# urlobs = 'http://ammidev.n1data.lan:8080/esasky-tap/observations'
# with urllib.request.urlopen(urlobs) as response:
#     r = response.read().decode('utf-8')
# # this is a json bytes output that's why it needs decoding to string 
# b = json.loads(r)
# tmp = a["observations"]
# nobs = len(tmp)
# obsList = []
# for i in range(nobs):
#     obsList.append(tmp[i]["tapTable"])
# 
#     def get_esasky_tables(self):
#         """
#         A method to return the available ESASky tables and their respective column names and types.
#         """
#         urlTables = self.URL + '/tables'
#         with urllib.request.urlopen(urlTables) as response:
#             r = response.read()
#         # create the XML tree
#         root = ET.fromstring(r)
#         #
#         cat = dict()
#         # iterate on all table elements
#         for child in root.iter('table'):
#             if (child.attrib.get('type') == 'base_table'):
#                 catname = child.find('name').text
#                 cat[catname] = {'column': [], 'type': []}
#                 # now get each catalog column
#                 for subnode in child.findall("column"):
#                     cat[catname]['column'].append(subnode.find('name').text)
#                     cat[catname]['type'].append(subnode.find('dataType').text)
#         return cat
