# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
Fetches line spectra from the NIST Atomic Spectra Database.
"""
from astropy import config as _config


class Conf(_config.ConfigNamespace):
    """
    Configuration parameters for `astroquery.nist`.
    """
    server = _config.ConfigItem(
        ['http://physics.nist.gov/cgi-bin/ASD/lines1.pl'],
        'Name of the NIST URL to query.')
    timeout = _config.ConfigItem(
        30,
        'Time limit for connecting to NIST server.')


conf = Conf()

from .core import Nist, NistClass

__all__ = ['Nist', 'NistClass',
           'Conf', 'conf',
           ]
