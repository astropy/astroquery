# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""Test `astroquery.utils.system_tools`.

"""

# STDLIB
import gzip
import os
from os.path import exists

# THIRD-PARTY
import pytest

# LOCAL
from ..system_tools import gunzip

def test_gunzip():
    filename = 'test_system_tools.txt.gz'
    unziped_filename = filename.rsplit(".", 1)[0]
    for f in [filename, unziped_filename]:
        if exists(f):
            os.remove(f)
            
    # First create a gzip file
    content = b"Bla"
    with gzip.open(filename, 'wb') as f:
        f.write(content)
    
    # Then test our gunzip command works and creates an unziped file
    gunzip(filename)
    assert exists(unziped_filename)

    # Check content is the same
    with open(unziped_filename, 'rb') as f:
        new_content = f.read()
    assert new_content == content

    # Clean
    for f in [filename, unziped_filename]:
        if exists(f):
            os.remove(f)
