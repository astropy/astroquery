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


class TapSharedToItem(object):
    """TAP shared to item object
    """

    def __init__(self, attrs):
        """Constructor
        """
        self.__internal_init()
        self.__attributes = attrs
        self.set_id(attrs.getValue("shareTo"))
        self.set_type(attrs.getValue("shareType"))
        self.set_mode(attrs.getValue("shareMode"))

    def __internal_init(self):
        pass

    def get_id(self):
        """Returns id

        Returns
        -------
        id
        """
        return self.__id

    def set_id(self, ident):
        """Sets id

        Parameters
        ----------
        user : str, mandatory
            id to be set
        """
        self.__id = ident

    def get_type(self):
        """Returns type

        Returns
        -------
        Type
        """
        return self.__type

    def set_type(self, t):
        """Sets type

        Parameters
        ----------
        user : str, mandatory
            type
        """
        self.__type = t

    def get_mode(self):
        """Returns mode

        Returns
        -------
        Mode
        """
        return self.__mode

    def set_mode(self, m):
        """Sets mode

        Parameters
        ----------
        user : str, mandatory
            mode
        """
        self.__mode = m

    def __str__(self):
        return ("Shared to item: " + str(self.get_id()) +
                "\n\tType: " + str(self.get_type()) +
                "\n\tMode: " + str(self.get_mode()))
