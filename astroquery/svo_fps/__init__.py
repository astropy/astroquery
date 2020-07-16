"""
SVO FPS query tool
==================

Access to the Spanish Virtual Observatory (SVO) Filter Profile Service (FPS).
"""
from astropy import config as _config


class Conf(_config.ConfigNamespace):
    """
    Configuration parameters for `astroquery.svo_fps`.
    """
    base_url = _config.ConfigItem(
        ['http://svo2.cab.inta-csic.es/theory/fps/fps.php'],
        'SVO FPS base query URL')

    timeout = _config.ConfigItem(
        60,
        'Time limit for connecting to SVO FPS server.')


conf = Conf()

from .core import SvoFps, SvoFpsClass

__all__ = ["SvoFps", "SvoFpsClass", "Conf", "conf"]
