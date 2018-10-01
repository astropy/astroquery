# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
=============
TAP plus
=============

@author: Javier Durtan
@contact: javier.duran@sciops.esa.int

European Space Astronomy Centre (ESAC)
European Space Agency (ESA)

Created on 28 sep. 2018


"""


class TapUser(object):
    """TAP user object
    """

    def __init__(self, attrs):
        """Constructor
        """
        self.__attributes = attrs
        self.set_id(attrs.getValue("id"))
        self.set_name(attrs.getValue("name"))
        self.__internal_init()

    def __internal_init(self):
        pass

    def get_id(self):
        """Returns group id

        Returns
        -------
        The group id
        """
        return self.__id

    def set_id(self, ident):
        """Sets group id

        Parameters
        ----------
        user : str, mandatory
            id to be set
        """
        self.__id = ident
        
    def get_name(self):
        """Returns user name

        Returns
        -------
        The user name
        """
        return self.__name

    def set_name(self, name):
        """Sets user name

        Parameters
        ----------
        user : str, mandatory
            user name
        """
        self.__name = name

    def __str__(self):
        return "User: " + str(self.get_id()) + \
            "\n\tName: " + str(self.get_name())
