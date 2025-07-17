# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
NSF NOIRLab Astro Data Archive Query Tool
-----------------------------------------
"""
from astropy import config as _config


class Conf(_config.ConfigNamespace):
    """
    Configuration parameters for `astroquery.noirlab`.
    """
    server = _config.ConfigItem(['https://astroarchive.noirlab.edu',],
                                'Name of the NSF NOIRLab server to use.')
    timeout = _config.ConfigItem(30,
                                 'Time limit for connecting to NSF NOIRLab server.')


conf = Conf()

from .core import NOIRLab, NOIRLabClass  # noqa

__all__ = ['NOIRLab', 'NOIRLabClass',
           'conf', 'Conf']
