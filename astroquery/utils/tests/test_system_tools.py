# Licensed under a 3-clause BSD style license - see LICENSE.rst

try:
    import gzip

    HAS_GZIP = True
except ImportError:
    HAS_GZIP = False

import shutil
import os
from os.path import exists
import tempfile

import pytest

from ..system_tools import gunzip


@pytest.mark.skipif("not HAS_GZIP")
def test_gunzip():

    temp_dir = tempfile.mkdtemp()
    filename = f"{temp_dir}{os.sep}test_gunzip.txt.gz"
    unziped_filename = filename.rsplit(".", 1)[0]

    # First create a gzip file
    content = b"Bla"
    with gzip.open(filename, "wb") as f:
        f.write(content)

    try:
        # Then test our gunzip command works and creates an unziped file
        gunzip(filename)
        assert exists(unziped_filename)

        # Check content is the same
        with open(unziped_filename, "rb") as f:
            new_content = f.read()
        assert new_content == content

    finally:
        # Clean
        shutil.rmtree(temp_dir)
