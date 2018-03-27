# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
Besancon Query Tool
-------------------
A tool to query the Besancon model of the galaxy
http://model.obs-besancon.fr/

:Author: Adam Ginsburg (adam.g.ginsburg@gmail.com)
"""
from astropy import config as _config


class Conf(_config.ConfigNamespace):
    """
    Configuration parameters for `astroquery.besancon`.
    """

    download_url = _config.ConfigItem(
        ['ftp://sasftp.obs-besancon.fr/modele/modele2003/',
         'ftp://sasftp.obs-besancon.fr/modele/',
         ],
        'Besancon download URL.  Changed to modele2003 in 2013.')
    model_form = _config.ConfigItem(
        ['http://model.obs-besancon.fr/modele_form.php'],
        'Besancon model form URL')
    ping_delay = _config.ConfigItem(
        30.0,
        'Amount of time before pinging the Besancon server to see if the '
        'file is ready.  Minimum 30s.')
    timeout = _config.ConfigItem(
        30.0,
        'Timeout for Besancon query')


conf = Conf()

from .core import (Besancon, BesanconClass, parse_besancon_model_string,
                   parse_besancon_model_file)

__all__ = ['Besancon', 'BesanconClass',
           'parse_besancon_model_file',
           'parse_besancon_model_string',
           'Conf', 'conf',
           ]
