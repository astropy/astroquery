# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
VizieR Query Tool
-----------------

:Author: Julien Woillez (jwoillez@gmail.com)

This package is for querying the VizieR service, primarily hosted at:
http://vizier.u-strasbg.fr

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

    server = _config.ConfigItem(
        ['vizier.u-strasbg.fr',
         'vizier.nao.ac.jp',
         'vizier.hia.nrc.ca',
         'vizier.ast.cam.ac.uk',
         'vizier.cfa.harvard.edu',
         'www.ukirt.jach.hawaii.edu',
         'vizier.iucaa.ernet.in',
         'vizier.china-vo.org',
         ],
        'Name of the VizieR mirror to use.')

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
