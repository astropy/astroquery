# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import print_function

import os

from ... import vamdc


def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)


# finally test the methods using the mock HTTP response
# def test_query_molecule(patch_request):
#    ch3oh = vamdc.core.VamdcClass().query_molecule('CH3OH')
#    assert 'SCDMS-2369983' in ch3oh.data['States']

# similarly fill in tests for each of the methods
# look at tests in existing modules for more examples
