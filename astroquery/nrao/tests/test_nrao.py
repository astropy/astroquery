# Licensed under a 3-clause BSD style license - see LICENSE.rst
from ... import nrao

def test_get_image():
    fitsfile = nrao.get_nrao_image(49.489,-0.37,overwrite=True)
