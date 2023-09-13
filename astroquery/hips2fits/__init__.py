# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
CDS hips2fits Query Tool
------------------------

:Author: Matthieu Baumann (matthieu.baumann@astro.unistra.fr)

This package is for querying the CDS hips2fits service, primarily hosted at:

* https://alasky.cds.unistra.fr/hips-image-services/hips2fits
* https://alaskybis.cds.unistra.fr/hips-image-services/hips2fits (mirror)

Note: If the access to hips2fits was helpful for your research
work, the following acknowledgment would be appreciated::

  This research has made use of the hips2fits, a tool developed at CDS, Strasbourg, France aiming at extracting
  FITS images from HiPS sky maps with respect to a WCS.
"""

from astropy import config as _config


class Conf(_config.ConfigNamespace):
    """
    Configuration parameters for ``astroquery.template_module``.
    """
    server = _config.ConfigItem(
        ["https://alasky.cds.unistra.fr/hips-image-services/hips2fits",
         "https://alaskybis.cds.unistra.fr/hips-image-services/hips2fits"],
        'Name of the template_module server to use.')

    timeout = _config.ConfigItem(
        30,
        'Time limit for connecting to template_module server.')


conf = Conf()

from .core import hips2fits, hips2fitsClass

__all__ = [
    'hips2fits', 'hips2fitsClass',
    'Conf', 'conf',
]
