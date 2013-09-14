# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
LAMDA Query Tool
----------------

:Author: Brian Svoboda (svobodb@email.arizona.edu)

This packaged is for querying the Leiden Atomic and Molecular Database (LAMDA)
hosted at: http://home.strw.leidenuniv.nl/~moldata/.

Note:
  If you use the data files from LAMDA in your research work please refer to
  the publication by Schoier, F.L., van der Tak, F.F.S., van Dishoeck E.F.,
  Black, J.H. 2005, A&A 432, 369-379. When individual molecules are considered,
  references to the original papers providing the spectroscopic and collisional
  data are encouraged.
"""
from .core import *

import warnings
warnings.warn("Experimental: LAMDA has not yet been refactored to have its API match the rest of astroquery.")
