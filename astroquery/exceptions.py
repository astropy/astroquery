# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
Custom exceptions used in the astroquery query classes
"""

from astropy.utils.exceptions import AstropyWarning

__all__ = ['TimeoutError', 'InvalidQueryError', 'RemoteServiceError',
           'TableParseError', 'LoginError', 'ResolverError',
           'NoResultsWarning', 'LargeQueryWarning', 'InputWarning',
           'AuthenticationWarning', 'MaxResultsWarning']


class TimeoutError(Exception):

    """
    Raised on failure to establish connection with server
    within a particular time limit
    """
    pass


class InvalidQueryError(Exception):
    """
    Errors related to invalid queries.
    """
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


class ResolverError(Exception):
    """
    Errors due to failing to resolve an object name/id to a specific
    sky coordinate.
    """
    pass


class NoResultsWarning(AstropyWarning):
    """
    Astroquery warning class to be issued when a query returns no result.
    """
    pass


class LargeQueryWarning(AstropyWarning):
    """
    Astroquery warning class to be issued when a query is larger than
    recommended for a given service.
    """
    pass


class InputWarning(AstropyWarning):
    """
    Astroquery warning class to be issued when use input is incorrect
    in some way but doesn't prevent the function from running.
    """
    pass


class AuthenticationWarning(AstropyWarning):
    """
    Astroquery warning class to be issued when there are problems with
    user authentication.
    """


class MaxResultsWarning(AstropyWarning):
    """
    Astroquery warning class to be issued when the maximum allowed
    results are returned.
    """
    pass
