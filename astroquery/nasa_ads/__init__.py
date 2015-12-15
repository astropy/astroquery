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
        'http://adswww.harvard.edu',
        'SAO/NASA ADS main server.')

    mirrors = _config.ConfigItem(
        ['http://cdsads.u-strasbg.fr',
         'http://ukads.nottingham.ac.uk',
         'http://esoads.eso.org',
         'http://ads.ari.uni-heidelberg.de',
         'http://ads.inasan.ru',
         'http://ads.mao.kiev.ua',
         'http://ads.astro.puc.cl',
         'http://ads.nao.ac.jp',
         'http://ads.bao.ac.cn',
         'http://ads.iucaa.ernet.in',
         'http://ads.arsip.lipi.go.id',
         'http://saaoads.chpc.ac.za',
         'http://ads.on.br'],
        'SAO/NASA ADS mirrors around the world')
    advanced_path = _config.ConfigItem(
        '/cgi-bin/nph-abs_connect',
        'Path for advanced query (unconfirmed)')
    simple_path = _config.ConfigItem(
        '/cgi-bin/basic_connect',
        'Path for simple query (return XML)')
    timeout = _config.ConfigItem(
        120,
        'Time limit for connecting to ADS server')

conf = Conf()


conf.adsfields = ['bibcode', 'title', 'author', 'affiliation', 'journal',
                  'volume', 'pubdate', 'page', 'lastpage', 'keywords',
                  'keyword', 'origin', 'copyright', 'link', 'name', 'url',
                  'count', 'score', 'citations', 'abstract', 'doi', 'eprintid']

from .core import ADSClass, ADS

__all__ = ['ADSClass', 'ADS',
           'Conf', 'conf']
