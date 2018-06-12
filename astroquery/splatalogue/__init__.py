# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
Splatalogue Catalog Query Tool
-----------------------------------

:Author: Adam Ginsburg (adam.g.ginsburg@gmail.com)

:Originally contributed by:

     Magnus Vilhelm Persson (magnusp@vilhelm.nu)
"""
from astropy import config as _config


class Conf(_config.ConfigNamespace):
    """
    Configuration parameters for `astroquery.splatalogue`.
    """
    slap_url = _config.ConfigItem(
        'https://find.nrao.edu/splata-slap/slap',
        'Splatalogue SLAP interface URL (not used).')
    query_url = _config.ConfigItem(
        'https://www.cv.nrao.edu/php/splat/c_export.php',
        'Splatalogue web interface URL.')
    timeout = _config.ConfigItem(
        60,
        'Time limit for connecting to Splatalogue server.')
    lines_limit = _config.ConfigItem(
        1000,
        'Limit to number of lines exported.')


conf = Conf()

from . import load_species_table
from . import utils
from .core import Splatalogue, SplatalogueClass

__all__ = ['Splatalogue', 'SplatalogueClass',
           'Conf', 'conf',
           ]
