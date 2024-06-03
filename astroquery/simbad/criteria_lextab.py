# -*- coding: utf-8 -*-
# Licensed under a 3-clause BSD style license - see LICENSE.rst

# This file was automatically generated from ply. To re-generate this file,
# remove it from this folder, then build astropy and run the tests in-place:
#
#   python setup.py build_ext --inplace
#   pytest astroquery/simbad
#
# You can then commit the changes to this file.

# criteria_lextab.py. This file automatically created by PLY (version 3.11). Don't edit!
_tabversion   = '3.10'
_lextokens    = set(('BINARY_OPERATOR', 'COLUMN', 'IN', 'LIKE', 'LIST', 'NOTLIKE', 'NUMBER', 'REGION', 'STRING'))
_lexreflags   = 34
_lexliterals  = '&\\|\\(\\)'
_lexstateinfo = {'INITIAL': 'inclusive'}
_lexstatere   = {'INITIAL': [("(?P<t_IN>in\\b)|(?P<t_LIST>\\( *'[^\\)]*\\))|(?P<t_BINARY_OPERATOR>>=|<=|!=|>|<|=)|(?P<t_LIKE>~|∼)|(?P<t_NOTLIKE>!~|!∼)|(?P<t_STRING>'[^']*')|(?P<t_REGION>region\\([^\\)]*\\))|(?P<t_COLUMN>[a-zA-Z_*][a-zA-Z_0-9*]*)|(?P<t_NUMBER>\\d*\\.?\\d+)", [None, ('t_IN', 'IN'), ('t_LIST', 'LIST'), ('t_BINARY_OPERATOR', 'BINARY_OPERATOR'), ('t_LIKE', 'LIKE'), ('t_NOTLIKE', 'NOTLIKE'), ('t_STRING', 'STRING'), ('t_REGION', 'REGION'), ('t_COLUMN', 'COLUMN'), (None, 'NUMBER')])]}
_lexstateignore = {'INITIAL': ', \t\n'}
_lexstateerrorf = {'INITIAL': 't_error'}
_lexstateeoff = {}
