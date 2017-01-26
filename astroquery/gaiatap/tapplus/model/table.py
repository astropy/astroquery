# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
=============
Gaia TAP plus
=============

@author: Juan Carlos Segovia
@contact: juan.carlos.segovia@sciops.esa.int

European Space Astronomy Centre (ESAC)
European Space Agency (ESA)

Created on 30 jun. 2016


"""

class Table(object):
    """TAP table object
    """

    def __init__(self):
        """Constructor
        """
        self.__internalInit()
        pass
    
    def __internalInit(self):
        self.__columns = []
        self.__name = None
        self.__schema = None
        self.__description = None
        pass
    
    def get_schema(self):
        """Returns the schema name

        Returns
        -------
        The schema name
        """
        return self.__schema
    
    def set_schema(self, schema):
        """Sets the table schema name
        
        Parameters
        ----------
        schema : str, mandatory
            table schema name
        """
        self.__schema = schema
    
    def get_name(self):
        """Returns the table name

        Returns
        -------
        The table name
        """
        return self.__name
    
    def set_name(self, name):
        """Sets the table name
        
        Parameters
        ----------
        name : str, mandatory
            table name
        """
        self.__name = name
    
    def get_description(self):
        """Returns the table description

        Returns
        -------
        The table description
        """
        return self.__description
    
    def set_description(self, description):
        """Sets the table description
        
        Parameters
        ----------
        description : str, mandatory
            table description
        """
        self.__description = description
    
    def get_qualified_name(self):
        """Returns the qualified table name. I.e. schema+table

        Returns
        -------
        The the qualified table name (schema+table)
        """
        return self.__schema + "." + self.__name
    
    def get_columns(self):
        """Returns the table columns

        Returns
        -------
        The table columns (a list)
        """
        return self.__columns
    
    def add_column(self, column):
        """Adds a table column
        
        Parameters
        ----------
        column : Column object, mandatory
            table column
        """
        self.__columns.append(column)
    
    def __str__(self):
        return "Table name: " + str(self.get_qualified_name()) + \
            "\nDescription: " + str(self.get_description()) + \
            "\nNum. columns: " + str(len(self.get_columns())) 
        pass
    
    pass