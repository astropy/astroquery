# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
Accessing Online Astronomical Data.

Astroquery is an astropy affiliated package that contains a collection of tools
to access online Astronomical data. Each web service has its own sub-package.
"""

# Affiliated packages may add whatever they like to this file, but
# should keep this content at the top.
# ----------------------------------------------------------------------------
from ._astropy_init import __version__, __githash__, test
# ----------------------------------------------------------------------------

import os
import logging

from .logger import _init_log
from astropy import config as _config

__all__ = ["__version__", "__githash__", "__citation__", "__bibtex__", "test", "log"]


# Set the bibtex entry to the article referenced in CITATION.
def _get_bibtex():
    citation_file = os.path.join(os.path.dirname(__file__), 'CITATION')

    with open(citation_file, 'r') as citation:
        refs = citation.read().split('@ARTICLE')[1:]
        if len(refs) == 0: return ''
        bibtexreference = "@ARTICLE{0}".format(refs[0])
    return bibtexreference


__citation__ = __bibtex__ = _get_bibtex()


# Setup logging for astroquery
logging.addLevelName(5, "TRACE")
log = logging.getLogger()
log = _init_log()

# Set up cache configuration
class Conf(_config.ConfigNamespace):
    
    default_cache_timeout = _config.ConfigItem(
          60.0*60.0*24.0,
          'Astroquery-wide default cache timeout (seconds).'
          )

conf = Conf()
