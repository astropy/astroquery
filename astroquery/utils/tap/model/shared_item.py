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


class TapSharedItem(object):
    """TAP shared item object
    """

    def __init__(self, attrs):
        """Constructor
        """
        self.__internal_init()
        self.__attributes = attrs
        self.set_id(attrs.getValue("id"))
        self.set_type(attrs.getValue("type"))

    def __internal_init(self):
        self.__shared_to_items = []

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

    def get_title(self):
        """Returns title

        Returns
        -------
        Title
        """
        return self.__title

    def set_title(self, t):
        """Sets type

        Parameters
        ----------
        user : str, mandatory
            type
        """
        self.__title = t

    def get_description(self):
        """Returns title

        Returns
        -------
        Description
        """
        return self.__description

    def set_description(self, d):
        """Sets type

        Parameters
        ----------
        user : str, mandatory
            type
        """
        self.__description = d

    def get_shared_to_items_list(self):
        """Returns groups in which this item is shared

        Returns
        -------
        groups in which this item is shared
        """
        return self.__shared_to_items

    def add_shared_to_items_list(self, group):
        """Adds a group in which this item is shared

        Parameters
        ----------
        group : str, mandatory
            group id in which this item is shared
        """
        self.__shared_to_items.append(group)

    def __str__(self):
        shared_to = ""
        for u in self.get_shared_to_items_list():
            shared_to = shared_to + "\n\t\t" + str(u)

        return ("Shared item: " + str(self.get_id()) +
            "\n\tType: " + str(self.get_type()) +
            "\n\tTitle: " + str(self.get_title()) +
            "\n\tDescription: " + str(self.get_description()) +
            "\n\tShared to: " + str(shared_to))
