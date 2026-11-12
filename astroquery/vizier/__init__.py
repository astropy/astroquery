# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
VizieR Query Tool
-----------------

This package is for querying the VizieR service, primarily hosted at:
https://vizier.cds.unistra.fr

Note: If the access to catalogues with VizieR was helpful for your research
work, the following acknowledgment would be appreciated::

  This research has made use of the VizieR catalogue access tool, CDS,
  Strasbourg, France.  The original description of the VizieR service was
  published in A&AS 143, 23
"""
from astropy import config as _config


class Conf(_config.ConfigNamespace):
    """
    Configuration parameters for `astroquery.vizier`.
    """

    # the first item is the default
    servers_list = ['vizier.cds.unistra.fr',
                    'vizier.idia.ac.za',
                    'vizier.cfa.harvard.edu',
                    'vizier.nao.ac.jp',
                    'vizier.iucaa.ernet.in',
                    'vizier.china-vo.org',
                    ]

    server = _config.ConfigItem(
        servers_list,
        'Name of the VizieR mirror to use.',
        aliases=['astroquery.vizier.vizier_server'])

    timeout = _config.ConfigItem(
        60,
        'Default timeout for connecting to server',
        aliases=['astropy.coordinates.name_resolve.name_resolve_timeout'])

    row_limit = _config.ConfigItem(
        50,
        'Maximum number of rows that will be fetched from the result '
        '(set to -1 for unlimited).')


conf = Conf()

from .core import Vizier, VizierClass

__all__ = ['Vizier', 'VizierClass',
           'Conf', 'conf',
           ]
