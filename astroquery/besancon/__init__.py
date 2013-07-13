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

from .core import *
from .reader import *

