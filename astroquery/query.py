# Licensed under a 3-clause BSD style license - see LICENSE.rst

import abc

__all__ = ['BaseQuery']


class BaseQuery(object):

    """
    This is the base class for all the query classes in astroquery. It
    is implemented as an abstract class and must not be directly instantiated.
    """

    __metaclass__ = abc.ABCMeta


class QueryWithLogin(BaseQuery):

    """
    This is the base class for all the query classes which are required to
    have a login to access the data.
    """
    @abc.abstractmethod
    def login(self, **kwargs):
        """
        login to non-public data as a known user

        Parameters
        ----------
        Keyword arguments that can be used to create
        the data payload(dict) sent via `requests.post`
        """
        pass
