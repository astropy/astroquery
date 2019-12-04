# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
================
JWST Data Access
================

@author: Raul Gutierrez-Sanchez
@contact: raul.gutierrez@sciops.esa.int

European Space Astronomy Centre (ESAC)
European Space Agency (ESA)

Created on 02 nov. 2018


"""

from astropy.utils import data

__all__ = ['JwstDataHandler']


class JwstDataHandler(object):
    def __init__(self, base_url=None):
        if base_url is None:
            self.base_url = "http://jwstdummydata.com"
        else:
            self.base_url = base_url
            
    def download_file(self, url):
        return data.download_file(url, cache=True )
    
    def clear_download_cache(self):
        data.clear_download_cache()
