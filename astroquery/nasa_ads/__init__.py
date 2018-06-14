# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
SAO/NASA ADS Query Tool
-----------------------------------

:Author: Magnus Vilhelm Persson (magnusp@vilhelm.nu)

"""

from astropy import config as _config


class Conf(_config.ConfigNamespace):
    """
    Configuration parameters for `astroquery.nasa_ads`.
    """

    server = _config.ConfigItem(
        'https://api.adsabs.harvard.edu',
        'SAO/NASA ADS main server.')

    simple_path = _config.ConfigItem(
        '/v1/search/query?',
        'Path for simple query (return JSON)')
    timeout = _config.ConfigItem(
        120,
        'Time limit for connecting to ADS server')


conf = Conf()


conf.adsfields = ['bibcode', 'title', 'author', 'aff', 'pub',
                  'volume', 'pubdate', 'page', 'citations',
                  'abstract', 'doi', 'eid']
conf.sort = 'date desc'
conf.nrows = 10
conf.nstart = 0

conf.token = None

from .core import ADSClass, ADS

__all__ = ['ADSClass', 'ADS',
           'Conf', 'conf']
