from astropy import config as _config


class Conf(_config.ConfigNamespace):
    """
    Configuration parameters for `astroquery.atomic`.
    """
    url = _config.ConfigItem(
        'http://www.pa.uky.edu/~peter/atomic/',
        'Atomic Line List URL')

    timeout = _config.ConfigItem(
        60, 'time limit for connecting to the Atomic Line List server')


conf = Conf()

from .core import AtomicLineList, AtomicLineListClass

__all__ = ['AtomicLineList', 'AtomicLineListClass', 'conf']
