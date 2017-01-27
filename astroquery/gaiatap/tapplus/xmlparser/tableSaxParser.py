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

import xml.sax

from astroquery.gaiatap.tapplus.model.table import Table
from astroquery.gaiatap.tapplus.model.column import Column
from astroquery.gaiatap.tapplus.xmlparser import utils as Utils

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
        self.__internalInit()
        pass
    
    def __internalInit(self):
        self.__concatData = False
        self.__charBuffer = []
        self.__tables = []
        self.__status = 0
        self.__currentSchemaName = None
        self.__currentTable = None
        self.__currentColumn = None
        pass
        
    def _createStringFromBuffer(self):
        return Utils.utilCreateStringFromBuffer(self.__charBuffer)
        
    def _checkItemId(self, itemId, tmpValue):
        if str(itemId).lower() == str(tmpValue).lower():
            return True
        return False 
    
    def _startReadingData(self):
        self.__concatData = True
        del self.__charBuffer[:]
        pass
    
    def _stopReadingData(self):
        self.__concatData = False
        pass
    
    def parseData(self, data):
        del self.__tables[:]
        self.__status = READING_SCHEMA
        xml.sax.parse(data, self)
        return self.__tables

    def startElement(self, name, attrs):
        if self.__status == READING_SCHEMA:
            self._readingSchema(name, attrs)
        elif self.__status == READING_TABLE:
            self._readingTable(name, attrs)
        elif self.__status == READING_TABLE_COLUMN:
            self._readingTableColumn(name, attrs)
        pass
    
    def endElement(self, name):
        if self.__status == READING_SCHEMA:
            self._endSchema(name)
        elif self.__status == READING_TABLE:
            self._endTable(name)
        elif self.__status == READING_TABLE_COLUMN:
            self._endTableColumn(name)
        pass
    
    def characters(self, content):
        if self.__concatData:
            self.__charBuffer.append(content)
        pass
    
    def _readingSchema(self, name, attrs):
        if self._checkItemId("name", name):
            self._startReadingData()
        if self._checkItemId("table", name):
            self.__status = READING_TABLE
            self.__currentTable = Table()
            self.__currentTable.set_schema(self.__currentSchemaName)
        pass
    
    def _endSchema(self, name):
        if self._checkItemId("name", name):
            self.__currentSchemaName = self._createStringFromBuffer()
            self._stopReadingData()
        pass
    
    def _readingTable(self, name, attrs):
        if self._checkItemId("name", name):
            self._startReadingData()
        elif self._checkItemId("description", name):
            self._startReadingData()
        elif self._checkItemId("column", name):
            self.__status = READING_TABLE_COLUMN
            self.__currentColumn = Column()
        pass
    
    def _endTable(self, name):
        if self._checkItemId("name", name):
            self._stopReadingData()
            self.__currentTable.set_name(self._createStringFromBuffer())
        elif self._checkItemId("description", name):
            self._stopReadingData()
            self.__currentTable.set_description(self._createStringFromBuffer())
        elif self._checkItemId("table", name):
            self.__tables.append(self.__currentTable)
            self.__status = READING_SCHEMA
        pass
    
    def _readingTableColumn(self, name, attrs):
        if self._checkItemId("name", name):
            self._startReadingData()
        elif self._checkItemId("description", name):
            self._startReadingData()
        elif self._checkItemId("unit", name):
            self._startReadingData()
        elif self._checkItemId("ucd", name):
            self._startReadingData()
        elif self._checkItemId("utype", name):
            self._startReadingData()
        elif self._checkItemId("datatype", name):
            self._startReadingData()
        elif self._checkItemId("flag", name):
            self._startReadingData()
        pass
    
    def _endTableColumn(self, name):
        if self._checkItemId("name", name):
            self.__currentColumn.set_name(self._createStringFromBuffer())
            self._stopReadingData()
        elif self._checkItemId("description", name):
            self.__currentColumn.set_description(self._createStringFromBuffer())
            self._stopReadingData()
        elif self._checkItemId("unit", name):
            self.__currentColumn.set_unit(self._createStringFromBuffer())
            self._stopReadingData()
        elif self._checkItemId("ucd", name):
            self.__currentColumn.set_ucd(self._createStringFromBuffer())
            self._stopReadingData()
        elif self._checkItemId("utype", name):
            self.__currentColumn.set_utype(self._createStringFromBuffer())
            self._stopReadingData()
        elif self._checkItemId("datatype", name):
            self.__currentColumn.set_data_type(self._createStringFromBuffer())
            self._stopReadingData()
        elif self._checkItemId("flag", name):
            self.__currentColumn.set_flag(self._createStringFromBuffer())
            self._stopReadingData()
        if self._checkItemId("column", name):
            self.__status = READING_TABLE
            self.__currentTable.add_column(self.__currentColumn)
        pass
    
    def _nothing(self, name, attrs):
        pass
    
    def getTable(self):
        if len(self.__tables) < 1:
            return None
        return self.__tables[0]
    
    def getTables(self):
        return self.__tables
    

