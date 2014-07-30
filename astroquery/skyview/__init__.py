# Licensed under a 3-clause BSD style license - see LICENSE.rst
from astropy import config as _config


class Conf(_config.ConfigNamespace):
    """
    Configuration parameters for `astroquery.skyview`.
    """
    url = _config.ConfigItem(
        'http://skyview.gsfc.nasa.gov/current/cgi/basicform.pl',
        'SkyView URL')


conf = Conf()

from .core import SkyView, SkyViewClass

__all__ = ['SkyView', 'SkyViewClass',
           'Conf', 'conf',
           ]
