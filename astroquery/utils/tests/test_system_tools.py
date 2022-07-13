# Licensed under a 3-clause BSD style license - see LICENSE.rst

import gzip

from ..system_tools import gunzip


def test_gunzip(tmp_path):
    filename = tmp_path / 'test_gunzip.txt.gz'
    # First create a gzip file
    content = b"Bla"
    with gzip.open(filename, "wb") as f:
        f.write(content)
    # Then test our gunzip command works
    gunzip(str(filename))
    with open(filename.with_suffix(''), "rb") as f:
        new_content = f.read()
    assert new_content == content
