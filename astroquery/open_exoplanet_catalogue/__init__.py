# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
Access to the Open Exoplanet Catalogue.
Hanno Rein 2013

https://github.com/OpenExoplanetCatalogue/open_exoplanet_catalogue
https://github.com/OpenExoplanetCatalogue/oec_meta
https://openexoplanetcatalogue.com
"""
from .oec_query import xml_element_to_dict, findvalue, get_catalogue


__all__ = ['xml_element_to_dict', 'findvalue', 'get_catalogue']
