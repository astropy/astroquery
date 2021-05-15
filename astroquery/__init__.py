# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
Accessing Online Astronomical Data.

Astroquery is an astropy affiliated package that contains a collection of tools
to access online Astronomical data. Each web service has its own sub-package.
"""

# Affiliated packages may add whatever they like to this file, but
# should keep this content at the top.
# ----------------------------------------------------------------------------
from ._astropy_init import *
# ----------------------------------------------------------------------------

import os
import logging

from .logger import _init_log


# Set the bibtex entry to the article referenced in CITATION.
def _get_bibtex():
    citation_file = os.path.join(os.path.dirname(__file__), 'CITATION')

    with open(citation_file, 'r') as citation:
        refs = citation.read().split('@ARTICLE')[1:]
        if len(refs) == 0: return ''
        bibtexreference = "@ARTICLE{0}".format(refs[0])
    return bibtexreference


__citation__ = __bibtex__ = _get_bibtex()


try:
    from .version import version as __version__
except ImportError:
    # TODO: Issue a warning using the logging framework
    __version__ = ''
try:
    from .version import githash as __githash__
except ImportError:
    # TODO: Issue a warning using the logging framework
    __githash__ = ''


# Setup logging for astroquery
logging.addLevelName(5, "TRACE")
log = logging.getLogger()
log = _init_log()

# backward compatibility: retain the flat namespace as of May 2019 at least
# until we deprecate it

# categories of data type
from atomic_molecular_databases import atomic, hitran, jplspec, nist, splatalogue, vamdc
from simulations import besancon, cosmosim
from observatory_archives import alma, fermi, gaia, lcogt, nrao
from image_cutout_services import skyview, magpis

# institutes with multiple submodules
from wfau import vsa, ukidss
from cds import simbad, vizier, xmatch
from ipac import ibe, irsa, irsa_dust, sha, ned
from esa import esasky, gaia
# hubble is not importable alone b/c there are several
import esa.hubble

from exoplanets import open_exoplanet_catalogue, exoplanet_orbit_database, nasa_exoplanet_archive
from solarsystem import jplsbdb, jplhorizons, mpc

from surveys import alfalfa, nvas, gama, ogle, sdss
