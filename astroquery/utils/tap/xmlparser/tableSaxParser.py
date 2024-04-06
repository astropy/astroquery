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

import xml.sax

from astroquery.utils.tap.model.tapcolumn import TapColumn
from astroquery.utils.tap.model.taptable import TapTableMeta
from astroquery.utils.tap.xmlparser import utils as Utils

READING_SCHEMA = 10
READING_TABLE = 20
READING_TABLE_COLUMN = 30


class TableSaxParser(xml.sax.ContentHandler):
    '''
    classdocs
    '''

    def __init__(self):
        '''
        Constructor
        '''
        self.__internal_init()

    def __internal_init(self):
        self.__concatData = False
        self.__charBuffer = []
        self.__tables = []
        self.__status = 0
        self.__currentSchemaName = None
        self.__currentTable = None
        self.__currentColumn = None

    def __create_string_from_buffer(self):
        return Utils.util_create_string_from_buffer(self.__charBuffer)

    def __check_item_id(self, itemId, tmpValue):
        if str(itemId).lower() == str(tmpValue).lower():
            return True
        return False

    def __start_reading_data(self):
        self.__concatData = True
        del self.__charBuffer[:]

    def __stop_reading_data(self):
        self.__concatData = False

    def parseData(self, data):
        del self.__tables[:]
        self.__status = READING_SCHEMA
        xml.sax.parse(data, self)
        return self.__tables

    def startElement(self, name, attrs):
        if self.__status == READING_SCHEMA:
            self.__reading_schema(name, attrs)
        elif self.__status == READING_TABLE:
            self.__reading_table(name, attrs)
        elif self.__status == READING_TABLE_COLUMN:
            self.__reading_table_column(name, attrs)

    def endElement(self, name):
        if self.__status == READING_SCHEMA:
            self.__end_schema(name)
        elif self.__status == READING_TABLE:
            self.__end_table(name)
        elif self.__status == READING_TABLE_COLUMN:
            self.__end_table_column(name)

    def characters(self, content):
        if self.__concatData:
            self.__charBuffer.append(content)

    def __reading_schema(self, name, attrs):
        if self.__check_item_id("name", name):
            self.__start_reading_data()
        if self.__check_item_id("table", name):
            self.__status = READING_TABLE
            self.__currentTable = TapTableMeta()
            self.__currentTable.schema = self.__currentSchemaName
            if 'esatapplus:size_bytes' in attrs:
                self.__currentTable.size_bytes = int(attrs.getValue('esatapplus:size_bytes'))

    def __end_schema(self, name):
        if self.__check_item_id("name", name):
            self.__currentSchemaName = self.__create_string_from_buffer()
            self.__stop_reading_data()

    def __reading_table(self, name, attrs):
        if self.__check_item_id("name", name):
            self.__start_reading_data()
        elif self.__check_item_id("description", name):
            self.__start_reading_data()
        elif self.__check_item_id("column", name):
            self.__status = READING_TABLE_COLUMN
            self.__currentColumn = TapColumn(attrs.getValue('esatapplus:flags'))

    def __end_table(self, name):
        if self.__check_item_id("name", name):
            self.__stop_reading_data()
            self.__currentTable.name = self.__create_string_from_buffer()
        elif self.__check_item_id("description", name):
            self.__stop_reading_data()
            self.__currentTable.description = self.__create_string_from_buffer()
        elif self.__check_item_id("table", name):
            self.__tables.append(self.__currentTable)
            self.__status = READING_SCHEMA

    def __reading_table_column(self, name, attrs):
        if self.__check_item_id("name", name):
            self.__start_reading_data()
        elif self.__check_item_id("description", name):
            self.__start_reading_data()
        elif self.__check_item_id("unit", name):
            self.__start_reading_data()
        elif self.__check_item_id("ucd", name):
            self.__start_reading_data()
        elif self.__check_item_id("utype", name):
            self.__start_reading_data()
        elif self.__check_item_id("datatype", name):
            self.__start_reading_data()
        elif self.__check_item_id("flag", name):
            self.__start_reading_data()

    def __end_table_column(self, name):
        if self.__check_item_id("name", name):
            self.__currentColumn.name = self.__create_string_from_buffer()
            self.__stop_reading_data()
        elif self.__check_item_id("description", name):
            self.__currentColumn.description = self.__create_string_from_buffer()
            self.__stop_reading_data()
        elif self.__check_item_id("unit", name):
            self.__currentColumn.unit = self.__create_string_from_buffer()
            self.__stop_reading_data()
        elif self.__check_item_id("ucd", name):
            self.__currentColumn.ucd = self.__create_string_from_buffer()
            self.__stop_reading_data()
        elif self.__check_item_id("utype", name):
            self.__currentColumn.utype = self.__create_string_from_buffer()
            self.__stop_reading_data()
        elif self.__check_item_id("datatype", name):
            self.__currentColumn.data_type = self.__create_string_from_buffer()
            self.__stop_reading_data()
        elif self.__check_item_id("flag", name):
            self.__currentColumn.flag = self.__create_string_from_buffer()
            self.__stop_reading_data()
        if self.__check_item_id("column", name):
            self.__status = READING_TABLE
            self.__currentTable.add_column(self.__currentColumn)

    def __show_attributes(self, attrs):
        return str(attrs.getNames())

    def __nothing(self, name, attrs):
        pass

    def get_table(self):
        if len(self.__tables) < 1:
            return None
        return self.__tables[0]

    def get_tables(self):
        return self.__tables
