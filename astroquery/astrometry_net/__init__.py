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

from astropy import config as _config


class Conf(_config.ConfigNamespace):
    """ Configuration parameters for `astroquery.astrometry_net` """

    api_key = _config.ConfigItem(
        '',
        "The Astrometry.net API key."
    )
    server = _config.ConfigItem('http://nova.astrometry.net', 'Name of server')
    timeout = _config.ConfigItem(60,
                                 'Default timeout for connecting to server')


conf = Conf()

# Now import your public class
# Should probably have the same name as your module

from .core import AstrometryNet, AstrometryNetClass

__all__ = ['AstrometryNet', 'AstrometryNetClass']
