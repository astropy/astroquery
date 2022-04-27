# Licensed under a 3-clause BSD style license - see LICENSE.rst

"""
astrometry.net
--------------

:author: Matt Craig (<mattwcraig@gmail.com>)
"""

# Make the URL of the server, timeout and other items configurable
from astropy import config as _config


class Conf(_config.ConfigNamespace):
    """ Configuration parameters for `astroquery.astrometry_net` """

    api_key = _config.ConfigItem(
        '',
        "The Astrometry.net API key."
    )
    server = _config.ConfigItem('https://nova.astrometry.net', 'Name of server')
    timeout = _config.ConfigItem(120,
                                 'Default timeout for connecting to server')


conf = Conf()

# Now import your public class
# Should probably have the same name as your module

from .core import AstrometryNet, AstrometryNetClass

__all__ = ['AstrometryNet', 'AstrometryNetClass']
