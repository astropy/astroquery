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
        self.attributes = attrs
        self.id = attrs.getValue("id")
        self.type = attrs.getValue("type")
        self.shared_to_items = []

    def __str__(self):
        shared_to = ""
        for u in self.shared_to_items:
            shared_to = shared_to + "\n\t\t" + str(u)

        return ("Shared item: " + str(self.id) +
                "\n\tType: " + str(self.type) +
                "\n\tTitle: " + str(self.title) +
                "\n\tDescription: " + str(self.description) +
                "\n\tShared to: " + str(shared_to))
