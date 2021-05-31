# Licensed under a 3-clause BSD style license - see LICENSE.rst

"""
DESI LegacySurvery

https://www.legacysurvey.org/
-------------------------

:author: Gabriele Barni (Gabriele.Barni@unige.ch)
"""

# Make the URL of the server, timeout and other items configurable
# See <http://docs.astropy.org/en/latest/config/index.html#developer-usage>
# for docs and examples on how to do this
# Below is a common use case
from astropy import config as _config


class Conf(_config.ConfigNamespace):
    """
    Configuration parameters for `astroquery.legacysurvey`.
    """
    server = _config.ConfigItem(
        ['https://portal.nersc.gov/cfs/cosmo/data/legacysurvey/dr9/',
         ],
        'base url')

    timeout = _config.ConfigItem(
        30,
        'Time limit for connecting to template_module server.')


conf = Conf()

# Now import your public class
# Should probably have the same name as your module
from .core import LegacySurvey, LegacySurveyClass

__all__ = ['LegacySurvey', 'LegacySurveyClass',
           'Conf', 'conf',
           ]
