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


class TapSharedItem:
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
        for item in self.shared_to_items:
            shared_to = f"{shared_to}\n\t\t{item}"

        return f"Shared item: {self.id}" \
            f"\n\tType: {self.type}" \
            f"\n\tTitle: {self.title}" \
            f"\n\tDescription: {self.description}" \
            f"\n\tShared to: {shared_to}"
