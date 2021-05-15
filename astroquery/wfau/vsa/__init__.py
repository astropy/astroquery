# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
VSA Image and Catalog Query Tool
--------------------------------
.. topic:: Revision History

    Refactored using common API as a part of Google Summer of Code 2013.
    Modified for VSA by @eztean

    :Originally contributed by:

        Thomas Robitalle (thomas.robitaille@gmail.com)

        Adam Ginsburg (adam.g.ginsburg@gmail.com)
"""
from astropy import config as _config


class Conf(_config.ConfigNamespace):
    """
    Configuration parameters for `astroquery.vsa`.
    """
    server = _config.ConfigItem(
        ['http://horus.roe.ac.uk:8080/vdfs/'],
        'Name of the VSA mirror to use')

    timeout = _config.ConfigItem(
        30,
        'Time limit for connecting to VSA server.')


conf = Conf()

from .core import Vsa, VsaClass, clean_catalog

__all__ = ['Vsa', 'VsaClass', 'clean_catalog',
           'Conf', 'conf',
           ]
