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


# Set the bibtex entry to the article referenced in CITATION.
def _get_bibtex():
    citation_file = os.path.join(os.path.dirname(__file__), 'CITATION')

    with open(citation_file, 'r') as citation:
        refs = citation.read().split('@ARTICLE')[1:]
        if len(refs) == 0: return ''
        bibtexreference = "@ARTICLE{0}".format(refs[0])
    return bibtexreference


__citation__ = __bibtex__ = _get_bibtex()
