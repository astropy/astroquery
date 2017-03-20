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


class TapTableMeta(object):
    """TAP table metadata object
    """

    def __init__(self):
        """Constructor
        """
        self.__internal_init()

    def __internal_init(self):
        self.__columns = []
        self.__name = None
        self.__schema = None
        self.__description = None

    def get_schema(self):
        """Returns the TAP table schema name

        Returns
        -------
        The TAP table schema name
        """
        return self.__schema

    def set_schema(self, schema):
        """Sets the TAP table schema name

        Parameters
        ----------
        schema : str, mandatory
            TAP table schema name
        """
        self.__schema = schema

    def get_name(self):
        """Returns the TAP table name

        Returns
        -------
        The TAP table name
        """
        return self.__name

    def set_name(self, name):
        """Sets the TAP table name

        Parameters
        ----------
        name : str, mandatory
            TAP table name
        """
        self.__name = name

    def get_description(self):
        """Returns the TAP table description

        Returns
        -------
        The TAP table description
        """
        return self.__description

    def set_description(self, description):
        """Sets the TAP table description

        Parameters
        ----------
        description : str, mandatory
            TAP table description
        """
        self.__description = description

    def get_qualified_name(self):
        """Returns the qualified TAP table name. I.e. schema+table

        Returns
        -------
        The the qualified TAP table name (schema+table)
        """
        return self.__schema + "." + self.__name

    def get_columns(self):
        """Returns the TAP table columns

        Returns
        -------
        The TAP table columns (a list)
        """
        return self.__columns

    def add_column(self, tap_column):
        """Adds a table TAP column

        Parameters
        ----------
        tap_column : TAP Column object, mandatory
            table TAP column
        """
        self.__columns.append(tap_column)

    def __str__(self):
        return "TAP Table name: " + str(self.get_qualified_name()) + \
            "\nDescription: " + str(self.get_description()) + \
            "\nNum. columns: " + str(len(self.get_columns()))
