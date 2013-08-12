# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
VizieR Query Tool
-----------------

:Author: Julien Woillez (jwoillez@gmail.com)

This package is for querying the VizieR service, primarily hosted at: http://vizier.u-strasbg.fr

Note: If the access to catalogues with VizieR was helpful for your research work, the following
acknowledgment would be appreciated::

  This research has made use of the VizieR catalogue access tool, CDS, Strasbourg, France.
  The original description of the VizieR service was published in A&AS 143, 23
"""
from astropy.config import ConfigurationItem

VIZIER_SERVER = ConfigurationItem('vizier_server', ['vizier.u-strasbg.fr',
                                                    'vizier.nao.ac.jp',
                                                    'vizier.hia.nrc.ca',
                                                    'vizier.ast.cam.ac.uk',
                                                    'vizier.cfa.harvard.edu',
                                                    'www.ukirt.jach.hawaii.edu',
                                                    'vizier.iucaa.ernet.in',
                                                    'vizier.china-vo.org'], 'Name of the VizieR mirror to use.')

VIZIER_TIMEOUT = ConfigurationItem('timeout', 60, 'default timeout for connecting to server')

ROW_LIMIT = ConfigurationItem('row_limit', 50, 'maximum number of rows that will be fetched from the result.')

from .core import Vizier
