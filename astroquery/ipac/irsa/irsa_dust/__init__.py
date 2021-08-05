# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
IRSA Galactic Dust Reddening and Extinction Query Tool
======================================================

.. topic:: Revision History

    Refactored using common API as a part of Google Summer of Code 2013.

    :Originally contributed by: David Shiga (dshiga.dev@gmail.com)
"""
from astropy import config as _config


class Conf(_config.ConfigNamespace):
    """
    Configuration parameters for `astroquery.irsa_dust`.
    """
    # maintain a list of URLs in case the user wants to append a mirror
    server = _config.ConfigItem(
        ['https://irsa.ipac.caltech.edu/cgi-bin/DUST/nph-dust'],
        'Name of the irsa_dust server to use.')
    timeout = _config.ConfigItem(
        30,
        'Default timeout for connecting to server.')


conf = Conf()


from .core import IrsaDust, IrsaDustClass

__all__ = ['IrsaDust', 'IrsaDustClass',
           'Conf', 'conf',
           ]
