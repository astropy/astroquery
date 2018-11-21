# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
JPL Spectral Catalog
--------------------


:author: Giannina Guzman (gguzman2@villanova.edu)
:author: Miguel de Val-Borro (miguel.deval@gmail.com)

"""
from astropy import config as _config


class Conf(_config.ConfigNamespace):
    """
    Configuration parameters for `astroquery.jplspec`.
    """
    server = _config.ConfigItem(
        'https://spec.jpl.nasa.gov/cgi-bin/catform',
        'JPL Spectral Catalog URL.')

    timeout = _config.ConfigItem(
        60,
        'Time limit for connecting to JPL server.')


conf = Conf()

from .core import JPLSpec, JPLSpecClass

__all__ = ['JPLSpec', 'JPLSpecClass',
           'Conf', 'conf',
           ]
