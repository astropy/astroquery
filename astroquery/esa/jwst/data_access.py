# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
=================
eJWST Data Access
=================

European Space Astronomy Centre (ESAC)
European Space Agency (ESA)

"""

from astropy.utils import data

__all__ = ['JwstDataHandler']


class JwstDataHandler:
    def __init__(self, base_url=None):
        if base_url is None:
            self.base_url = "http://jwstdummydata.com"
        else:
            self.base_url = base_url

    def download_file(self, url):
        return data.download_file(url, cache=True)

    def clear_download_cache(self):
        data.clear_download_cache()
