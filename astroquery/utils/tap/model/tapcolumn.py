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
        self.__internal_init()

    def __internal_init(self):
        self.__name = None
        self.__description = None
        self.__unit = None
        self.__ucd = None
        self.__utype = None
        self.__datatype = None
        self.__arraysize = None
        self.__flag = None

    def get_name(self):
        """Returns the TAP column name

        Returns
        -------
        The TAP column name
        """
        return self.__name

    def set_name(self, name):
        """Sets the TAP column name

        Parameters
        ----------
        name : str, mandatory
            TAP column name
        """
        self.__name = name

    def get_description(self):
        """Returns the TAP column description

        Returns
        -------
        The TAP column description
        """
        return self.__description

    def set_description(self, description):
        """Sets the TAP column description

        Parameters
        ----------
        description : str, mandatory
            TAP column description
        """
        self.__description = description

    def get_unit(self):
        """Returns the TAP column unit

        Returns
        -------
        The TAP column unit
        """
        return self.__unit

    def set_unit(self, unit):
        """Sets the TAP column unit

        Parameters
        ----------
        description : str, mandatory
            TAP column unit
        """
        self.__unit = unit

    def get_ucd(self):
        """Returns the TAP column ucd

        Returns
        -------
        The TAP column ucd
        """
        return self.__ucd

    def set_ucd(self, ucd):
        """Sets the TAP column ucd

        Parameters
        ----------
        description : str, mandatory
            TAP column ucd
        """
        self.__ucd = ucd

    def get_utype(self):
        """Returns the TAP column utype

        Returns
        -------
        The TAP column utype
        """
        return self.__utype

    def set_utype(self, utype):
        """Sets the TAP column utype

        Parameters
        ----------
        description : str, mandatory
            TAP column utype
        """
        self.__utype = utype

    def get_data_type(self):
        """Returns the TAP column data type

        Returns
        -------
        The TAP column data type
        """
        return self.__datatype

    def set_data_type(self, dataType):
        """Sets the TAP column data type

        Parameters
        ----------
        description : str, mandatory
            TAP column data type
        """
        self.__datatype = dataType

    def get_array_size(self):
        """Returns the TAP column data array size

        Returns
        -------
        The TAP column data array size
        """
        return self.__arraysize

    def set_array_size(self, arraySize):
        """Sets the TAP column data array size

        Parameters
        ----------
        description : str, mandatory
            TAP column data array size
        """
        self.__arraysize = arraySize

    def get_flag(self):
        """Returns the TAP column flag (TAP+)

        Returns
        -------
        The TAP column flag
        """
        return self.__flag

    def set_flag(self, flag):
        """Sets the TAP column flag (TAP+)

        Parameters
        ----------
        description : str, mandatory
            TAP column flag
        """
        self.__flag = flag

    def __str__(self):
        return "TAP Column name: " + str(self.__name) + \
            "\nDescription: " + str(self.__description) + \
            "\nUnit: " + str(self.__unit) + \
            "\nUcd: " + str(self.__ucd) + \
            "\nUtype: " + str(self.__utype) + \
            "\nDataType: " + str(self.__datatype) + \
            "\nArraySize: " + str(self.__arraysize) + \
            "\nFlag: " + str(self.__flag)
