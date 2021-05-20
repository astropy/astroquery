# Licensed under a 3-clause BSD style license - see LICENSE.rst

__all__ = ['__version__', '__githash__']

# this indicates whether or not we are in the package's setup.py
try:
    _ASTROPY_SETUP_
except NameError:
    from sys import version_info
    if version_info[0] >= 3:
        import builtins
    else:
        import __builtin__ as builtins
    builtins._ASTROPY_SETUP_ = False

try:
    from .version import version as __version__
except ImportError:
    __version__ = ''
try:
    from .version import githash as __githash__
except ImportError:
    __githash__ = ''


if not _ASTROPY_SETUP_:  # noqa
    import os

    # Create the test function for self test
    from astropy.tests.runner import TestRunner
    test = TestRunner.make_test_runner_in(os.path.dirname(__file__))
    test.__test__ = False
    __all__ += ['test']
