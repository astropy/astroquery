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
        self.attributes = attrs
        self.id = attrs.getValue("id")
        self.owner = attrs.getValue("owner")
        self.users = []
        self.title = None
        self.description = None

    def __str__(self):
        users = ""
        for u in self.users:
            users = users + "\n\t\t" + u.name + "(" + u.id + ")"
        return "Group: " + str(self.title) + \
            "\n\tDescription: " + str(self.description) + \
            "\n\tOwner: " + str(self.owner) + \
            "\n\tUsers: " + users
