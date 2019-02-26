# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
THOR Image Query Tool
---------------------
.. topic:: Revision History

    :Originally contributed by:

        Adam Ginsburg (adam.g.ginsburg@gmail.com)

"""
from astropy import config as _config


class Conf(_config.ConfigNamespace):
    """
    Configuration parameters for `astroquery.magpis`.
    """
    server = _config.ConfigItem(
        ['http://astro.kent.ac.uk'],
        'Name of the THOR server.')
    timeout = _config.ConfigItem(
        60,
        'Time limit for connecting to THOR server.')


conf = Conf()

from .core import Thor, ThorClass

__all__ = ['Thor', 'ThorClass',
           'Conf', 'conf',
           ]
