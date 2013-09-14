# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
Besancon Query Tool
-------------------
A tool to query the Besancon model of the galaxy
http://model.obs-besancon.fr/

:Author: Adam Ginsburg (adam.g.ginsburg@gmail.com)
"""
from astropy.config import ConfigurationItem
# maintain a list of URLs in case the user wants to append a mirror
BESANCON_DOWNLOAD_URL = ConfigurationItem('besancon_download_url',[
                                    'ftp://sasftp.obs-besancon.fr/modele/modele2003/',
                                    'ftp://sasftp.obs-besancon.fr/modele/',
                                    ],
    'Besancon download URL.  Changed to modele2003 in 2013.')

BESANCON_MODEL_FORM = ConfigurationItem('besancon_model_Form',
                            ["http://model.obs-besancon.fr/modele_form.php"],
                            "Besancon model form URL")

BESANCON_PING_DELAY = ConfigurationItem('besancon_ping_delay', 30.0,
                                        "Amount of time before pinging the Besancon server to see if the file is ready.  Minimum 30s.",
                                        cfgtype="float(min=30.0)")

BESANCON_TIMEOUT = ConfigurationItem('besancon_timeout', 30.0,
                                        "Timeout for Besancon query")

from .core import Besancon
from .reader import BesanconFixed,BesanconFixedWidthHeader,BesanconFixedWidthData

__all__ = ['Besancon','BesanconFixed','BesanconFixedWidthHeader','BesanconFixedWidthData']
