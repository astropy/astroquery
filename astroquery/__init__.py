# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
Accessing Online Astronomical Data.

Astroquery is an astropy affiliated package that contains a collection of tools
to access online Astronomical data. Each web service has its own sub-package.
"""

# Affiliated packages may add whatever they like to this file, but
# should keep this content at the top.
# ----------------------------------------------------------------------------
from ._astropy_init import *
# ----------------------------------------------------------------------------

# For egg_info test builds to pass, put package imports here.
#if not _ASTROPY_SETUP_:
#    from astroquery import *


# This is to monkey-patch around a config system bug in astropy 1.0.1.
# REMOVEME: when astropy 1.0.1 support is no longer needed
if not _ASTROPY_SETUP_:
    import astropy
    if astropy.__version__ == '1.0.1':
        from astropy.config import configuration

        _existing_ConfigItem__init__ = configuration.ConfigItem.__init__

        def _monkey_patch_1_0_1_ConfigItem__init__(
                self, defaultvalue='', description=None, cfgtype=None,
                module=None, aliases=None):
            if module is None:
                from astropy.utils import find_current_module
                module = find_current_module(2)
                if module is None:
                    msg1 = 'Cannot automatically determine get_config module, '
                    msg2 = 'because it is not called from inside a valid module'
                    raise RuntimeError(msg1 + msg2)
                else:
                    module = module.__name__

            return _existing_ConfigItem__init__(
                self,
                defaultvalue=defaultvalue,
                description=description,
                cfgtype=cfgtype,
                module=module,
                aliases=aliases)

        # Don't apply the same monkey patch twice
        if (configuration.ConfigItem.__init__.__name__ !=
            '_monkey_patch_1_0_1_ConfigItem__init__'):
            configuration.ConfigItem.__init__ = _monkey_patch_1_0_1_ConfigItem__init__
