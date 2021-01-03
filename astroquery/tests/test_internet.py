# Licensed under a 3-clause BSD style license - see LICENSE.rst
import pytest
import requests

from .. import version


@pytest.mark.remote_data
def test_net_connection():
    R = requests.post('http://httpbin.org/post',
                      headers={'User-Agent':
                               'astropy:astroquery.{0}'
                               .format(version.version)})
    R.raise_for_status()
