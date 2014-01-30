from astropy.config import ConfigurationItem

ROW_LIMIT = ConfigurationItem('row_limit', 50, 'maximum number of rows returned (set to -1 for unlimited).')

from .core import Eso, EsoClass

__all__ = ['Eso', 'EsoClass']
