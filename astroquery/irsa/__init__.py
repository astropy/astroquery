# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
This module contains various methods for querying the IRSA Catalog Query Service(CatQuery)
"""
from astropy.config import ConfigurationItem

IRSA_SERVER = ConfigurationItem('irsa_server', ['http://irsa.ipac.caltech.edu/cgi-bin/Gator/nph-query'],
                               'Name of the IRSA mirror to use.')
GATOR_LIST_CATALOGS = ConfigurationItem('gator_list_catalogs', ['http://irsa.ipac.caltech.edu/cgi-bin/Gator/nph-scan'],
                                        'URL from which to list all the public catalogs in IRSA.')
ROW_LIMIT = ConfigurationItem('row_limit', 500, 'maximum number of rows to retrieve in result')
TIMEOUT = ConfigurationItem('timeout', 60, 'time limit for connecting to the IRSA server')

from .core import Irsa

__all__ = ['Irsa']
