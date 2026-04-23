# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
JPL Spectral Catalog
--------------------

"""
from astropy import config as _config


class Conf(_config.ConfigNamespace):
    """
    Configuration parameters for `astroquery.linelists.jplspec`.
    """
    server = _config.ConfigItem(
        'https://spec.jpl.nasa.gov/cgi-bin/catform',
        'JPL Spectral Catalog URL.')

    ftp_cat_server = _config.ConfigItem(
        ['https://spec.jpl.nasa.gov/ftp/pub/catalog/',
         'https://web.archive.org/web/20250630185813/https://spec.jpl.nasa.gov/ftp/pub/catalog/'],
        'JPL FTP Catalog URL'
    )

    timeout = _config.ConfigItem(
        60,
        'Time limit for connecting to JPL server.')


conf = Conf()

from .core import JPLSpec, JPLSpecClass

__all__ = ['JPLSpec', 'JPLSpecClass',
           'Conf', 'conf',
           ]
