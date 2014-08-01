# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
Miriade Query Tool
------------------
A tool to query Miriade, The Virtual Observatory Solar System Object
Ephemeris Generator, a web service of the IMCCE
http://vo.imcce.fr/webservices/miriade/

:Author: Julien Woillez (jwoillez@gmail.com) et al.
"""

from astropy import config as _config

class Conf(_config.ConfigNamespace):
    """
    Configuration parameters for `astroquery.miriade`.
    """

    obs_codes_url = _config.ConfigItem(
        'http://www.minorplanetcenter.net/iau/lists/ObsCodes.html',
        'Observatory codes URL from the Minor Planet Center.'
        )
    rts_url = _config.ConfigItem(
        'http://vo.imcce.fr/webservices/miriade/rts_query.php',
        'URL of the Rise Transit Time web service.'
        )

conf = Conf()

from .core import Miriade, MiriadeClass
 
__all__ = ['Miriade', 'MiriadeClass']

