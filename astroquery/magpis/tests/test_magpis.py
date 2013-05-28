# Licensed under a 3-clause BSD style license - see LICENSE.rst
from astroquery import magpis

def test_get_file():
    fitsfile = magpis.get_magpis_image_gal(10.5,0.0,overwrite=True)
