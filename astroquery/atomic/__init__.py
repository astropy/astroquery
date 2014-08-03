from astropy.config import ConfigurationItem

ATOMIC_LINE_LIST_URL = ConfigurationItem(
    'atomic_line_list',
    'http://www.pa.uky.edu/~peter/atomic/',
    'Atomic Line List URL')
TIMEOUT = ConfigurationItem(
    'timeout',
    60,
    'time limit for connecting to the Atomic Line List server')

from .core import AtomicLineList, AtomicLineListClass

__all__ = ['AtomicLineList', 'AtomicLineListClass']