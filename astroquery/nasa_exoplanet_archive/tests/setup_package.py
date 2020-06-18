# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import absolute_import

import os


def get_package_data():
    return {"astroquery.nasa_exoplanet_archive.tests": [os.path.join("data", "*.json"),
                                                        os.path.join("data", "*.txt")]}
