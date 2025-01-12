# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
CDMS catalog
------------
Cologne Database for Molecular Spectroscopy query tool


"""
from astropy import config as _config


class Conf(_config.ConfigNamespace):
    """
    Configuration parameters for `astroquery.linelists.cdms`.
    """
    server = _config.ConfigItem(
        'https://cdms.astro.uni-koeln.de/',
        'CDMS Search and Conversion Form URL.')

    search = _config.ConfigItem(
        'https://cdms.astro.uni-koeln.de/cgi-bin/cdmssearch',
        'CDMS Search and Conversion Form URL.')

    catfile_url = _config.ConfigItem(
        'https://cdms.astro.uni-koeln.de/classic/entries/partition_function.html',
        'CDMS partition function table listing all available molecules.')

    catfile_url2 = _config.ConfigItem(
        'https://cdms.astro.uni-koeln.de/classic/predictions/catalog/catdir.html',
        'CDMS catalog table listing all available molecules (with different names from partition function).')

    classic_server = _config.ConfigItem(
        'https://cdms.astro.uni-koeln.de/classic',
        'CDMS Classic Molecule List server.')

    timeout = _config.ConfigItem(
        60,
        'Time limit for connecting to the CDMS server.')


conf = Conf()

from .core import CDMS, CDMSClass

__all__ = ['CDMS', 'CDMSClass',
           'Conf', 'conf',
           ]
