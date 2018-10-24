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


class TapColumn(object):
    """TAP column object
    """

    def __init__(self):
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

    def __str__(self):
        return "TAP Column name: " + str(self.name) + \
            "\nDescription: " + str(self.description) + \
            "\nUnit: " + str(self.unit) + \
            "\nUcd: " + str(self.ucd) + \
            "\nUtype: " + str(self.utype) + \
            "\nDataType: " + str(self.datatype) + \
            "\nArraySize: " + str(self.arraysize) + \
            "\nFlag: " + str(self.flag)
