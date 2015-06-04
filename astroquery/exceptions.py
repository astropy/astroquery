# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
Custom exceptions used in the astroquery query classes
"""

from astropy.utils.exceptions import AstropyWarning

__all__ = ['TimeoutError', 'InvalidQueryError', 'RemoteServiceError',
           'TableParseError', 'LoginError', 'NoResultsWarning']


class TimeoutError(Exception):

    """
    Raised on failure to establish connection with server
    within a particular time limit
    """
    pass


class InvalidQueryError(Exception):
    pass


class TableParseError(Exception):
    """
    Errors related to VOTable parsing.
    These should be either submitted as issues to astropy or to the originating
    service.
    """
    pass


class RemoteServiceError(Exception):
    """
    Errors related to the remote service, i.e. if the service returns an error
    page
    """
    pass


class LoginError(Exception):
    """
    Errors due to failed logins.  Should only be raised for services for which
    a login is a prerequisite for the requested action
    """
    pass


class NoResultsWarning(AstropyWarning):
    """
    Astroquery warning class to be issued when a query returns no result.
    """
