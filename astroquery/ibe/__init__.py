# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
IRSA Image Server program interface (IBE) Query Tool
====================================================

The ``astroquery.ibe`` module is deprecated and will be removed in a future
release of Astroquery. IRSA no longer supports the IBE interface. To access
IRSA datasets programatically, users encouraged to use the TAP protocol
(http://irsa.ipac.caltech.edu/docs/program_interface/TAP.html) via PyVO
(https://pyvo.readthedocs.io/en/latest/dal/index.html#table-access-protocol).
"""
import warnings
from astropy.utils.exceptions import AstropyDeprecationWarning

warnings.warn(__doc__.partition('\n\n')[2].strip().replace('\n', ' '),
              AstropyDeprecationWarning)
