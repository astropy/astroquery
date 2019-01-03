# Licensed under a 3-clause BSD style license - see LICENSE.rst

"""
HiGal cutout service
--------------------

:author: Adam Ginsburg <adam.g.ginsburg@gmail.com>
"""

# Make the URL of the server, timeout and other items configurable
# See <http://docs.astropy.org/en/latest/config/index.html#developer-usage>
# for docs and examples on how to do this
# Below is a common use case
from astropy import config as _config


class Conf(_config.ConfigNamespace):
    """
    Configuration parameters for `astroquery.higal`.
    """
    server = _config.ConfigItem(
        ['https://tools.ssdc.asi.it/',
         ],
        'Name of the higal server to use.')

    timeout = _config.ConfigItem(
        30,
        'Time limit for connecting to template_module server.')


conf = Conf()

# Now import your public class
# Should probably have the same name as your module
from .core import HiGal, HiGalClass

__all__ = ['HiGal', 'HiGalClass',
           'Conf', 'conf',
           ]
