# Licensed under a 3-clause BSD style license - see LICENSE.rst

# Keep the project level fixtures in this file, keeping them in root level
# conftest causes issues with pytest 9.1+

import os
from pathlib import Path

import pytest


@pytest.fixture(scope='function')
def tmp_cwd(tmp_path):
    """Perform test in a pristine temporary working directory."""
    old_dir = Path.cwd()
    os.chdir(tmp_path)
    try:
        yield tmp_path
    finally:
        os.chdir(old_dir)
