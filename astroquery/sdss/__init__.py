# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
SDSS Spectra/Image/SpectralTemplate Archive Query Tool
------------------------------------------------------
"""
from astropy import config as _config


class Conf(_config.ConfigNamespace):
    """
    Configuration parameters for `astroquery.sdss`.
    """
    skyserver_baseurl = _config.ConfigItem(
        'https://skyserver.sdss.org',
        'Base URL for catalog-related queries like SQL and Cross-ID.')
    sas_baseurl = _config.ConfigItem(
        'https://data.sdss.org/sas',
        'Base URL for downloading data products like spectra and images.')
    timeout = _config.ConfigItem(
        60,
        'Time limit for connecting to SDSS server.')
    default_release = _config.ConfigItem(17, 'Default SDSS data release.')


conf = Conf()


from .core import SDSS, SDSSClass


__all__ = ['SDSS', 'SDSSClass', 'Conf', 'conf']
