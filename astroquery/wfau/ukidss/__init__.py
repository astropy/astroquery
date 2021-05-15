# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
UKIDSS Image and Catalog Query Tool
-----------------------------------
.. topic:: Revision History

    Refactored using common API as a part of Google Summer of Code 2013.

    :Originally contributed by:

        Thomas Robitalle (thomas.robitaille@gmail.com)

        Adam Ginsburg (adam.g.ginsburg@gmail.com)
"""
from astropy import config as _config


class Conf(_config.ConfigNamespace):
    """
    Configuration parameters for `astroquery.ukidss`.
    """
    server = _config.ConfigItem(
        ['http://surveys.roe.ac.uk:8080/wsa/'],
        'Name of the UKIDSS mirror to use.')

    timeout = _config.ConfigItem(
        30,
        'Time limit for connecting to UKIDSS server.')


conf = Conf()

from .core import Ukidss, UkidssClass, clean_catalog

__all__ = ['Ukidss', 'UkidssClass', 'clean_catalog',
           'Conf', 'conf',
           ]
