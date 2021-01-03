# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
=============
TAP plus
=============

@author: Juan Carlos Segovia
@contact: juan.carlos.segovia@sciops.esa.int

European Space Astronomy Centre (ESAC)
European Space Agency (ESA)

Created on 30 jun. 2016


"""


class TapColumn:
    """TAP column object
    """

    def __init__(self, flags):
        """
        Constructor
        """
        self.name = None
        self.description = None
        self.unit = None
        self.ucd = None
        self.utype = None
        self.datatype = None
        self.arraysize = None
        self.flag = None
        self.flags = flags

    def __str__(self):
        return f"TAP Column name: {self.name}" \
            f"\nDescription: {self.description}" \
            f"\nUnit: {self.unit}" \
            f"\nUcd: {self.ucd}" \
            f"\nUtype: {self.utype}" \
            f"\nDataType: {self.datatype}" \
            f"\nArraySize: {self.arraysize}" \
            f"\nFlag: {self.flag}" \
            f"\nFlags: {self.flags}"
