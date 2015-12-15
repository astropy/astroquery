# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
Access to Fermi Gamma-ray Space Telescope data.

http://fermi.gsfc.nasa.gov
http://fermi.gsfc.nasa.gov/ssc/data/
"""
from astropy import config as _config


class Conf(_config.ConfigNamespace):
    """
    Configuration parameters for `astroquery.fermi`.
    """

    url = _config.ConfigItem(
        'http://fermi.gsfc.nasa.gov/cgi-bin/ssc/LAT/LATDataQuery.cgi',
        'Fermi query URL.')
    timeout = _config.ConfigItem(
        60,
        'Time limit for connecting to Fermi server.')
    retrieval_timeout = _config.ConfigItem(
        120,
        'Time limit for retrieving a data file once it has been located.')

conf = Conf()

from .core import *

__all__ = ['FermiLAT', 'FermiLATClass',
           'GetFermilatDatafile', 'get_fermilat_datafile',
           'Conf', 'conf',
           ]

import warnings
warnings.warn("Experimental: Fermi-LAT has not yet been refactored to have "
              "its API match the rest of astroquery.")
