# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
CDS MOCServer Query Tool
------------------------

:Author: Matthieu Baumann (matthieu.baumann@astro.unistra.fr)

This package is for querying the CDS MOC service, primarily hosted at:

* https://alasky.unistra.fr/MocServer/query
* https://alaskybis.unistra.fr/MocServer/query (mirror)

Note: If the access to MOCs with the MOCServer tool was helpful for your research
work, the following acknowledgment would be appreciated::

  This research has made use of the MOCServer, a tool developed at CDS, Strasbourg, France aiming at retrieving
  MOCs/meta-data from known data-sets. MOC is an IVOA standard described in the following paper :
  http://www.ivoa.net/documents/MOC/20140602/REC-MOC-1.0-20140602.pdf

.. deprecated:: 0.4.7
"""

# Licensed under a 3-clause BSD style license - see LICENSE.rst
import warnings
from astropy.utils.exceptions import AstropyDeprecationWarning


warnings.warn("The ``cds`` module has been moved to astroquery.mocserver, "
              "and ``CdsClass`` has been renamed to ``MOCServerClass``. "
              "Please update your imports.", AstropyDeprecationWarning, stacklevel=2)


from astroquery.mocserver import MOCServer as cds
from astroquery.mocserver import MOCServerClass as CdsClass
from astroquery.mocserver import conf, Conf

__all__ = ['conf', 'Conf', 'cds', 'CdsClass']
