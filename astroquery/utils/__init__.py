# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
Common non-package specific utility
functions that will ultimately be merged into `astropy.utils`.
"""
from .progressbar import chunk_report, chunk_read
from .class_or_instance import class_or_instance
from .commons import (parse_coordinates, TableList, suppress_vo_warnings,
                      validate_email,
                      ASTROPY_LT_5_1, ASTROPY_LT_6_0)
from .process_asyncs import async_to_sync
from .docstr_chompers import prepend_docstr_nosections
from .cleanup_downloads import cleanup_saved_downloads


__all__ = ['chunk_report', 'chunk_read',
           'class_or_instance',
           'parse_coordinates',
           'TableList',
           'suppress_vo_warnings',
           'validate_email',
           'ASTROPY_LT_5_1',
           'ASTROPY_LT_6_0',
           "async_to_sync",
           "prepend_docstr_nosections",
           "cleanup_saved_downloads"]
