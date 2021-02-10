# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
HEASARC
-------

The High Energy Astrophysics Science Archive Research Center (HEASARC)
is the primary archive for NASA's (and other space agencies') missions.

The initial version of this was coded in a sprint at the
"Python in astronomy" workshop in April 2015 by Jean-Christophe Leyder,
Abigail Stevens, Antonio Martin-Carrillo and Christoph Deil.
"""
from astropy import config as _config


class Conf(_config.ConfigNamespace):
    """
    Configuration parameters for `astroquery.heasarc`.
    """

    server = _config.ConfigItem(
        ['https://heasarc.gsfc.nasa.gov/db-perl/W3Browse/w3query.pl',
         'https://www.isdc.unige.ch/browse/w3query.pl'],
        'Name of the HEASARC server used to query available missions.')

    timeout = _config.ConfigItem(
        30,
        'Time limit for connecting to HEASARC server.')


conf = Conf()

from .core import Heasarc, HeasarcClass

__all__ = ['Heasarc', 'HeasarcClass',
           'Conf', 'conf',
           ]
