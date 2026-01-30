# Licensed under a 3-clause BSD style license - see LICENSE.rst

import os
from pathlib import Path
import sys

from astropy.utils import minversion
import numpy as np
import pytest
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

    del PYTEST_HEADER_MODULES['h5py']
    del PYTEST_HEADER_MODULES['Scipy']
    del PYTEST_HEADER_MODULES['Pandas']

    # keyring doesn't provide __version__ any more
    # PYTEST_HEADER_MODULES['keyring'] = 'keyring'

    # add '_testrun' to the version name so that the user-agent indicates that
    # it's being run in a test
    from astroquery import version
    version.version += '_testrun'

    TESTED_VERSIONS['astroquery'] = version.version
    TESTED_VERSIONS['astropy_helpers'] = version.astropy_helpers_version


def pytest_addoption(parser):
    parser.addoption(
        '--alma-site',
        action='store',
        default='almascience.eso.org',
        help='ALMA site (almascience.nrao.edu, almascience.eso.org or '
             'almascience.nao.ac.jp for example)'
    )


@pytest.fixture(scope='function')
def tmp_cwd(tmp_path):
    """Perform test in a pristine temporary working directory."""
    old_dir = Path.cwd()
    os.chdir(tmp_path)
    try:
        yield tmp_path
    finally:
        os.chdir(old_dir)


def pytest_runtestloop(session):
    if sys.platform == 'win32':
        session.add_marker(pytest.mark.filterwarnings(
        'ignore:OverflowError converting to IntType in column:astropy.utils.exceptions.AstropyWarning'))
