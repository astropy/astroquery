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


class TapUser:
    """TAP user object
    """

    def __init__(self, attrs):
        """Constructor
        """
        self.attributes = attrs
        self.id = attrs.getValue("id")
        self.name = attrs.getValue("name")

    def __str__(self):
        return f"User: {self.id}" \
            f"\n\tName: {self.name}"
