# Licensed under a 3-clause BSD style license - see LICENSE.rst
from astropy import config as _config


class Conf(_config.ConfigNamespace):
    """
    Configuration parameters for `astroquery.xmatch`.
    """
    url = _config.ConfigItem(
        'http://cdsxmatch.u-strasbg.fr/xmatch/api/v1/sync',
        'xMatch URL')

    timeout = _config.ConfigItem(
        60,
        'time limit for connecting to xMatch server')


conf = Conf()


from .core import XMatch, XMatchClass

__all__ = ['XMatch', 'XMatchClass',
           'Conf', 'conf',
           ]
