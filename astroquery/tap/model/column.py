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

class Column(object):
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
        """Returns the column name

        Returns
        -------
        The column name
        """
        return self.__name
    
    def set_name(self, name):
        """Sets the column name
        
        Parameters
        ----------
        name : str, mandatory
            column name
        """
        self.__name = name
    
    def get_description(self):
        """Returns the column description

        Returns
        -------
        The column description
        """
        return self.__description
    
    def set_description(self, description):
        """Sets the column description
        
        Parameters
        ----------
        description : str, mandatory
            column description
        """
        self.__description = description
    
    def get_unit(self):
        """Returns the column unit

        Returns
        -------
        The column unit
        """
        return self.__unit
    
    def set_unit(self, unit):
        """Sets the column unit
        
        Parameters
        ----------
        description : str, mandatory
            column unit
        """
        self.__unit = unit
    
    def get_ucd(self):
        """Returns the column ucd

        Returns
        -------
        The column ucd
        """
        return self.__ucd
    
    def set_ucd(self, ucd):
        """Sets the column ucd
        
        Parameters
        ----------
        description : str, mandatory
            column ucd
        """
        self.__ucd = ucd
    
    def get_utype(self):
        """Returns the column utype

        Returns
        -------
        The column utype
        """
        return self.__utype
    
    def set_utype(self, utype):
        """Sets the column utype
        
        Parameters
        ----------
        description : str, mandatory
            column utype
        """
        self.__utype = utype
    
    def get_data_type(self):
        """Returns the column data type

        Returns
        -------
        The column data type
        """
        return self.__datatype
    
    def set_data_type(self, dataType):
        """Sets the column data type
        
        Parameters
        ----------
        description : str, mandatory
            column data type
        """
        self.__datatype = dataType
    
    def get_array_size(self):
        """Returns the column data array size

        Returns
        -------
        The column data array size
        """
        return self.__arraysize
    
    def set_array_size(self, arraySize):
        """Sets the column data array size
        
        Parameters
        ----------
        description : str, mandatory
            column data array size
        """
        self.__arraysize = arraySize
    
    def get_flag(self):
        """Returns the column flag (TAP+)

        Returns
        -------
        The column flag
        """
        return self.__flag
    
    def set_flag(self, flag):
        """Sets the column flag (TAP+)
        
        Parameters
        ----------
        description : str, mandatory
            column flag
        """
        self.__flag = flag
    
    def __str__(self):
        return "Column name: " + str(self.__name) + \
            "\nDescription: " + str(self.__description) + \
            "\nUnit: " + str(self.__unit) + \
            "\nUcd: " + str(self.__ucd) + \
            "\nUtype: " + str(self.__utype) + \
            "\nDataType: " + str(self.__datatype) + \
            "\nArraySize: " + str(self.__arraysize) + \
            "\nFlag: " + str(self.__flag)
        
