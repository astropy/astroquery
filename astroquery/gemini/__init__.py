
from astropy import config as _config


class Conf(_config.ConfigNamespace):
    """
    Configuration parameters for `astroquery.template_module`.
    """
    server = _config.ConfigItem(
        ['https://archive.gemini.edu', ],
        'Name of the template_module server to use.'
        )
    timeout = _config.ConfigItem(
        30,
        'Time limit for connecting to template_module server.'
        )


conf = Conf()

from .core import ObservationsClass, Observations

__all__ = ['Observations', 'ObservationsClass', 'conf']
