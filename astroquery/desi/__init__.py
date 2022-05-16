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
    Configuration parameters for `astroquery.desi`.
    """
    legacysurvey_service_url = _config.ConfigItem(
        ['https://www.legacysurvey.org/viewer/fits-cutout',
         ],
        'url for the LegacySurvey service')

    tap_service_url = _config.ConfigItem(
        ['https://datalab.noirlab.edu/tap',
         ],
        'url for the TAP service')


conf = Conf()

# Now import your public class
# Should probably have the same name as your module
from .core import DESILegacySurvey, DESILegacySurveyClass

__all__ = ['DESILegacySurvey', 'DESILegacySurveyClass',
           'Conf', 'conf',
           ]
