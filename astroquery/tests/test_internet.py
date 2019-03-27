# Licensed under a 3-clause BSD style license - see LICENSE.rst
from astropy.tests.helper import remote_data
import requests
import os

from .. import version

IS_CI = os.environ.get('TRAVIS', False) or os.environ.get('APPVEYOR', False) == 'True'


@remote_data
def test_net_connection():
    R = requests.post('http://httpbin.org/post',
                      headers={'User-Agent':
                      'astropy:astroquery-ci-tests.{0}'
                      .format(version.version)})
    R.raise_for_status()
