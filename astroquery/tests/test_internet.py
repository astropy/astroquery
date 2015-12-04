# Licensed under a 3-clause BSD style license - see LICENSE.rst
from astropy.tests.helper import remote_data
import requests


@remote_data
def test_net_connection():
    R = requests.post('http://httpbin.org/post',
                      headers={'User-Agent': 'astropy:astroquery.0.1.dev'})
    R.raise_for_status()
