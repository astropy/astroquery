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
        self.__attributes = attrs
        self.id = attrs.getValue("shareTo")
        self.type = attrs.getValue("shareType")
        self.mode = attrs.getValue("shareMode")

    def __str__(self):
        return ("Shared to item: " + str(self.id) +
                "\n\tType: " + str(self.type) +
                "\n\tMode: " + str(self.mode))
