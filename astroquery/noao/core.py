"""\
Provide astroquery API access to OIR Lab Astro Data Archive (natica).

This does DB access through web-services. It allows query against ALL
fields in FITS file headers.  

Also possible but not provided here: query through Elasticsearch DSL.  ES will
be much faster but much more limitted in what can be used in query.  """

# Python library
# External packages
import requests
import astropy.table
# Local packages
from astroquery.utils.class_or_instance import class_or_instance
from astroquery.utils import async_to_sync
import astroquery.query 
from . import conf

__all__ = ['Noao', 'NoaoClass']  # specifies what to import

@async_to_sync
class NoaoClass(astroquery.query.BaseQuery):

    NAT_URL = conf.server
    ADS_URL = f'{NAT_URL}/api/adv_search/fasearch'
    #SIA_URL = f'{NAT_URL}/api/sia/vohdu'  # can match against all HDUs individually
    SIA_URL = f'{NAT_URL}/api/sia/voimg'

    def __init__(self, which='voimg'):
        """ set some parameters """
        if which == 'vohdu':
            self.url = f'{self.NAT_URL}/api/sia/vohdu'
        if which == 'voimg':
            self.url = f'{self.NAT_URL}/api/sia/voimg'
        else:
            self.url = f'{self.NAT_URL}/api/sia/voimg'
            

    @class_or_instance
    def query_region(self, coordinate, radius='1'):
        #response = requests.post(self.ADS_URL, json=search_spec)
        ra,dec = coordinate.to_string('decimal').split()
        size = radius
        url = f'{self.url}?POS={ra},{dec}&SIZE={size}&format=json'
        response = requests.get(url)
        return astropy.table.Table(data=response.json())
        
    def _parse_result(self, result):
        # do something, probably with regexp's
        return astropy.table.Table(tabular_data)

    def _args_to_payload(self, *args):
        # convert arguments to a valid requests payload

        return dict
    
Noao = NoaoClass()
