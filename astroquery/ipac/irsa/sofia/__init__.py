# Licensed under a 3-clause BSD style license - see LICENSE.rst

"""
SOFIA Archive
-------------
"""

from astropy import config as _config


class Conf(_config.ConfigNamespace):
    server = _config.ConfigItem(
        ['https://irsa.ipac.caltech.edu',
         ],
        'IRSA server URL.')

    timeout = _config.ConfigItem(
        30,
        'Time limit for connecting to the IRSA server.')


conf = Conf()

from .core import SOFIA, SOFIAClass

__all__ = ['SOFIA', 'SOFIAClass',
           'Conf', 'conf',
           ]
