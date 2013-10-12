#!/usr/bin/env python
# Licensed under a 3-clause BSD style license - see LICENSE.rst

import glob
import os
import sys

import setuptools_bootstrap
from setuptools import setup

#A dirty hack to get around some early import/configurations ambiguities
if sys.version_info[0] >= 3:
    import builtins
else:
    import __builtin__ as builtins
builtins._ASTROPY_SETUP_ = True

# Set affiliated package-specific settings
PACKAGENAME = 'packagename'
DESCRIPTION = 'Astropy affiliated package'
LONG_DESCRIPTION = ''
AUTHOR = ''
AUTHOR_EMAIL = ''
LICENSE = 'BSD'
URL = 'http://astropy.org'

# VERSION should be PEP386 compatible (http://www.python.org/dev/peps/pep-0386)
VERSION = '0.0.dev'

# Indicates if this version is a release version
RELEASE = 'dev' not in VERSION

metadata = dict(
    name=PACKAGENAME,
    package_data={},
    version=VERSION,
    description=DESCRIPTION,
    requires=['astropy'],
    install_requires=['astropy'],
    provides=[PACKAGENAME],
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    license=LICENSE,
    url=URL,
    long_description=LONG_DESCRIPTION,
    zip_safe=False,
    use_2to3=True
)

# Treat everything in scripts except README.rst as a script to be installed
metadata['scripts'] = [fname for fname in glob.glob(os.path.join('scripts', '*'))
                       if os.path.basename(fname) != 'README.rst']

# Add the project-global data
metadata['package_data'][PACKAGENAME] = ['data/*']

if len(sys.argv) >= 2 and sys.argv[1] == 'egg_info':

    # TODO: if we have a copy of get_git_devstr in the package template we can
    # set the proper version here.

    pass

else:

    from astropy.setup_helpers import register_commands, adjust_compiler, get_debug_option
    from astropy.version_helpers import get_git_devstr, generate_version_py

    if not RELEASE:
        VERSION += get_git_devstr(False)

    # Populate the dict of setup command overrides; this should be done before
    # invoking any other functionality from distutils since it can potentially
    # modify distutils' behavior.
    metadata['cmdclass'] = register_commands(PACKAGENAME, VERSION, RELEASE)

    # Adjust the compiler in case the default on this platform is to use a
    # broken one.
    adjust_compiler(PACKAGENAME)

    # Freeze build information in version.py
    generate_version_py(PACKAGENAME, VERSION, RELEASE, get_debug_option())

    try:

        from astropy.setup_helpers import get_package_info

        # Get configuration information from all of the various subpackages.
        # See the docstring for setup_helpers.update_package_files for more
        # details.
        metadata.update(get_package_info(PACKAGENAME))

    except ImportError: # compatibility with Astropy 0.2 - can be removed in cases
                        # where Astropy 0.2 is no longer supported

        from setuptools import find_packages
        from astropy.setup_helpers import filter_packages, update_package_files

        # Use the find_packages tool to locate all packages and modules
        metadata['packages'] = filter_packages(find_packages())

        # Additional C extensions that are not Cython-based should be added here.
        metadata['ext_modules'] = []

        # A dictionary to keep track of extra packagedir mappings
        metadata['package_dir'] = {}

        # Update extensions, package_data, packagenames and package_dirs from
        # any sub-packages that define their own extension modules and package
        # data.  See the docstring for setup_helpers.update_package_files for
        # more details.
        update_package_files(PACKAGENAME, metadata['ext_modules'],
                             metadata['package_data'], metadata['packages'],
                             metadata['package_dir'])

setup(**metadata)
