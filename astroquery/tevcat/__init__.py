# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""Get TeVCat as a table.

TeVCat is a TeV gamma-ray source catalog that is continually updated.

The data can be browsed on the html pages at http://tevcat.uchicago.edu/
but currently there is no download link for the catalog in CSV or FITS format.

However all data on the website is contained in a JSON object
which is easy to extract and process from Python.
This is what we do here, we implement the `astroquery.tevcat.get_tevcat` function
which converts the JSON data to an `~astropy.table.Table` object
and nicely formats it so that columns have correct data types,
units and descriptions.

For missing values we use the empty string, ``NaN`` and ``-99``.
"""

from astropy.config import ConfigurationItem
TEVCAT_SERVER = ConfigurationItem('tevcat_server',
                                  'http://tevcat.uchicago.edu/',
                                  'TeVCat server URL')

TEVCAT_TIMEOUT = ConfigurationItem('tevcat_timeout',
                                   60,
                                   'Timeout for connecting to TeVCat server')

from .core import get_tevcat

__all__ = ['get_tevcat']
