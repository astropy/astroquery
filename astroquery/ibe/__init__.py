# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
IRSA Image Server program interface (IBE) Query Tool
====================================================

This module contains various methods for querying the
IRSA Image Server program interface (IBE).
"""
from astropy import config as _config


class Conf(_config.ConfigNamespace):
    """
    Configuration parameters for `astroquery.ibe`.
    """

    server = _config.ConfigItem(
        'http://irsa.ipac.caltech.edu/ibe/',
        'Name of the IBE server to use.')
    mission = _config.ConfigItem(
        'ptf',
        ('Default mission. See, for example, '
         'http://irsa.ipac.caltech.edu/ibe/search/ for options.'))

    dataset = _config.ConfigItem(
        'images',
        ('Default data set. See, for example, '
         'http://irsa.ipac.caltech.edu/ibe/search/ptf for options.'))
    table = _config.ConfigItem(
        'level1',
        ('Default table. See, for example, '
         'http://irsa.ipac.caltech.edu/ibe/search/ptf/images for options.'))
    timeout = _config.ConfigItem(
        60,
        'Time limit for connecting to the IRSA server.')

conf = Conf()


from .core import Ibe, IbeClass

__all__ = ['Ibe', 'IbeClass',
           'Conf', 'conf',
           ]
