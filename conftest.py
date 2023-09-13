# Licensed under a 3-clause BSD style license - see LICENSE.rst

import numpy as np
from astropy.utils import minversion

from pytest_astropy_header.display import (PYTEST_HEADER_MODULES,
                                           TESTED_VERSIONS)


# Keep this until we require numpy to be >=2.0
if minversion(np, "2.0.0.dev0+git20230726"):
    np.set_printoptions(legacy="1.25")


def pytest_configure(config):
    config.option.astropy_header = True

    PYTEST_HEADER_MODULES['Astropy'] = 'astropy'
    PYTEST_HEADER_MODULES['regions'] = 'regions'
    PYTEST_HEADER_MODULES['pyVO'] = 'pyvo'
    PYTEST_HEADER_MODULES['mocpy'] = 'mocpy'
    PYTEST_HEADER_MODULES['astropy-healpix'] = 'astropy_healpix'
    PYTEST_HEADER_MODULES['vamdclib'] = 'vamdclib'

    # keyring doesn't provide __version__ any more
    # PYTEST_HEADER_MODULES['keyring'] = 'keyring'

    # add '_testrun' to the version name so that the user-agent indicates that
    # it's being run in a test
    from astroquery import version
    version.version += '_testrun'

    TESTED_VERSIONS['astroquery'] = version.version
    TESTED_VERSIONS['astropy_helpers'] = version.astropy_helpers_version
