#!/usr/bin/env python
# Licensed under a 3-clause BSD style license - see LICENSE.rst

import glob
import os
import sys

# Workaround for https://github.com/pypa/pip/issues/6163
sys.path.insert(0, os.path.dirname(__file__))

import ah_bootstrap
from setuptools import setup

import builtins

builtins._ASTROPY_SETUP_ = True

from astropy_helpers.git_helpers import get_git_devstr
from astropy_helpers.version_helpers import generate_version_py
from astropy_helpers.distutils_helpers import is_distutils_display_option

from setuptools.config import read_configuration

setup()
