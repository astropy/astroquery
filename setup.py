#!/usr/bin/env python
# Licensed under a 3-clause BSD style license - see LICENSE.rst

import os
import sys

# Workaround for https://github.com/pypa/pip/issues/6163
sys.path.insert(0, os.path.dirname(__file__))

import ah_bootstrap

import builtins

builtins._ASTROPY_SETUP_ = True

from astropy_helpers.setup_helpers import setup

setup()
