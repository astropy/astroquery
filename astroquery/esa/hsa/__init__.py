# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
HSA
-------

The Herschel Science Archive (HSA) is the ESA's archive for the
Herschel mission.
"""
from astropy import config as _config


class Conf(_config.ConfigNamespace):
    """
    Configuration parameters for `astroquery.esa.hsa`.
    """
    DATA_ACTION = _config.ConfigItem("http://archives.esac.esa.int/hsa/whsa-tap-server/data?",
                                     "Main url for retrieving HSA Data Archive files")

    METADATA_ACTION = _config.ConfigItem("http://archives.esac.esa.int/hsa/whsa-tap-server/tap",
                                         "Main url for retrieving HSA Data Archive metadata")

    TIMEOUT = 60


conf = Conf()

from .core import HSA, HSAClass

__all__ = ['HSA', 'HSAClass', 'Conf', 'conf']
