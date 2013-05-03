# Licensed under a 3-clause BSD style license - see LICENSE.rst
from ... import splatalogue

try:
    import mechanize

    def test_simple():
        splatalogue.search()
except ImportError:
    pass
