# Licensed under a 3-clause BSD style license - see LICENSE.rst

"""
ADS Queries
-----------

"""

# Make the URL of the server, timeout and other items configurable
# See <http://docs.astropy.org/en/latest/config/index.html#developer-usage>
# for docs and examples on how to do this
# Below is a common use case
from astropy import config as _config


class Conf(_config.ConfigNamespace):
    """
    Configuration parameters for `astroquery.ads`.
    """
    server = _config.ConfigItem(
        [
         'http://adswww.harvard.edu/',
         'http://cdsads.u-strasbg.fr/',
         'http://ukads.nottingham.ac.uk/',
         'http://esoads.eso.org/',
         'http://ads.ari.uni-heidelberg.de/',
         'http://ads.inasan.ru/',
         'http://ads.mao.kiev.ua/',
         'http://ads.astro.puc.cl/',
         'http://ads.nao.ac.jp/',
         'http://ads.bao.ac.cn/',
         'http://ads.iucaa.ernet.in/',
         'http://ads.arsip.lipi.go.id/',
         'http://saaoads.chpc.ac.za/',
         'http://ads.on.br/',
        ],
        'Name of the ADS server to use.'
        )
    timeout = _config.ConfigItem(
        30,
        'Time limit for connecting to ads server.'
        )

conf = Conf()

# Now import your public class
# Should probably have the same name as your module
from .core import Ads, AdsClass

__all__ = ['Ads', 'AdsClass',
           'Conf', 'conf',
           ]
