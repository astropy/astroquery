# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
Access to the Open Exoplanet Catalogue.
Hanno Rein 2013

https://github.com/hannorein/open_exoplanet_catalogue
https://github.com/hannorein/oec_meta
http://openexoplanetcatalogue.com
"""
from astropy.config import ConfigurationItem

OEC_SERVER = ConfigurationItem('open_exoplanet_catalogue_server', ['https://raw.github.com/hannorein/open_exoplanet_catalogue/master/','http://www.openexoplanetcatalogue.com/open_exoplanet_catalogue/'],'URL of Open Exoplanet Catalogue repository.')
OEC_META_SERVER = ConfigurationItem('open_exoplanet_catalogue_meta_server', ['https://raw.github.com/hannorein/oec_meta/master/','http://www.openexoplanetcatalogue.com/oec_meta/'],'URL of Open Exoplanet Catalogue repository.')

from .oec_query import *
