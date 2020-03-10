"""
"""
from astropy import config as _config


class Conf(_config.ConfigNamespace):
    TIMEOUT = _config.ConfigItem(
        30, 'Time limit for connecting to template_module server.')


conf = Conf()

from .core import VoImageQuery  # noqa

__all__ = ['VoImageQuery', 'conf']
