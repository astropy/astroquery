# Licensed under a 3-clause BSD style license - see LICENSE.rst

"""
This module defines custom exceptions used in the astroquery
query classes
"""

__all__ = ['TimeoutError', 'InvalidQueryError']

class TimeoutError(Exception):
    """
    Raised on failure to establish connection with server
    within a particular time limit
    """
    pass


class InvalidQueryError(Exception):
    pass
