# Licensed under a 3-clause BSD style license - see LICENSE.rst
import os
from pathlib import Path

from astropy.utils import minversion
import numpy as np
import pytest
# this contains imports plugins that configure py.test for astropy tests.
# by importing them here in conftest.py they are discoverable by py.test
# no matter how it is invoked within the source tree.

from pytest_astropy_header.display import (PYTEST_HEADER_MODULES,
                                           TESTED_VERSIONS)


# Keep this until we require numpy to be >=2.0
if minversion(np, "2.0.0.dev0+git20230726"):
    np.set_printoptions(legacy="1.25")


def pytest_configure(config):
    config.option.astropy_header = True


# Add astropy to test header information and remove unused packages.
# Pytest header customisation was introduced in astropy 1.0.

try:
    PYTEST_HEADER_MODULES['Astropy'] = 'astropy'
    PYTEST_HEADER_MODULES['regions'] = 'regions'
    PYTEST_HEADER_MODULES['pyVO'] = 'pyvo'
    PYTEST_HEADER_MODULES['mocpy'] = 'mocpy'
    PYTEST_HEADER_MODULES['astropy-healpix'] = 'astropy_healpix'
    PYTEST_HEADER_MODULES['vamdclib'] = 'vamdclib'

    # keyring doesn't provide __version__ any more
    # PYTEST_HEADER_MODULES['keyring'] = 'keyring'
    del PYTEST_HEADER_MODULES['h5py']
    del PYTEST_HEADER_MODULES['Scipy']
    del PYTEST_HEADER_MODULES['Pandas']
except (NameError, KeyError):
    pass

# add '_testrun' to the version name so that the user-agent indicates that
# it's being run in a test
from . import version
version.version += '_testrun'


# This is to figure out the affiliated package version, rather than
# using Astropy's
from .version import version, astropy_helpers_version


packagename = os.path.basename(os.path.dirname(__file__))
TESTED_VERSIONS[packagename] = version
TESTED_VERSIONS['astropy_helpers'] = astropy_helpers_version


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
