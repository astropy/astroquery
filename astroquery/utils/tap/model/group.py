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


class TapGroup(object):
    """TAP group object
    """

    def __init__(self, attrs):
        """Constructor
        """
        self.__attributes = attrs
        self.set_id(attrs.getValue("id"))
        self.set_owner(attrs.getValue("owner"))
        self.__internal_init()

    def __internal_init(self):
        self.__users = []
        self.__title = None
        self.__description = None

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
        
    def get_owner(self):
        """Returns group owner

        Returns
        -------
        The group owner
        """
        return self.__owner

    def set_owner(self, owner):
        """Sets group id

        Parameters
        ----------
        user : str, mandatory
            id to be set
        """
        self.__owner = owner
        
    def get_users(self):
        """Returns users of this group

        Returns
        -------
        The list of users of this group
        """
        return self.__users

    def add_user(self, user):
        """Adds a user to the group

        Parameters
        ----------
        user : str, mandatory
            user to be added
        """
        self.__users.__add__(user)

    def get_title(self):
        """Returns the title of the group

        Returns
        -------
        The title of the group
        """
        return self.__title

    def set_title(self, title):
        """Sets the the title of the group

        Parameters
        ----------
        title : str, mandatory
            The title of the group
        """
        self.__title = title

    def get_description(self):
        """Returns the group description

        Returns
        -------
        The group description
        """
        return self.__description

    def set_description(self, description):
        """Sets the group description

        Parameters
        ----------
        description : str, mandatory
            The group description
        """
        self.__description = description

    def __str__(self):
        users = ""
        for u in self.get_users():
            users = users + "\n\t\t" + u.get_name() + "(" + u.get_id() + ")" 
        return "Group: " + str(self.get_title()) + \
            "\n\tDescription: " + str(self.get_description()) + \
            "\n\tOwner: " + str(self.get_owner()) + \
            "\n\tUsers: " + users
