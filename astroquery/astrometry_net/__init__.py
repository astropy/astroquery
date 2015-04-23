# Licensed under a 3-clause BSD style license - see LICENSE.rst

"""
<Put Your Tool Name Here>
-------------------------

:author: <your name> (<your email>)
"""

# Make the URL of the server, timeout and other items configurable
# See <http://docs.astropy.org/en/latest/config/index.html#developer-usage>
# for docs and examples on how to do this
# Below is a common use case

from astropy.config import ConfigurationItem
from astropy import config as _config

# Set the server mirrors to query
SERVER = ConfigurationItem('server',
                           ['http://dummy_server_mirror_1',
                            'http://dummy_server_mirror_2',
                            'http://dummy_server_mirror_n'],
                           'put a brief description of the item here')

# Set the timeout for connecting to the server in seconds, here we set it to 30s
TIMEOUT = ConfigurationItem('timeout', 30, 'default timeout for connecting to server')

class Conf(_config.ConfigNamespace):
    """ Configuration parameters for `astroquery.astrometry_net` """

    api_key = _config.ConfigItem(
        '',
        "The Astrometry.net API key."
        )

conf = Conf()

# Now import your public class
# Should probably have the same name as your module

from .core import AstrometryNet, AstrometryNetClass

__all__ = ['AstrometryNet', 'AstrometryNetClass']
