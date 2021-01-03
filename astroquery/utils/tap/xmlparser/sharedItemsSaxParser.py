# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
=============
TAP plus
=============

@author: Javier Duran
@contact: javier.duran@sciops.esa.int

European Space Astronomy Centre (ESAC)
European Space Agency (ESA)

Created on 28 sep. 2018


"""

import xml.sax

from astroquery.utils.tap.xmlparser import utils as Utils
from astroquery.utils.tap.model.shared_item import TapSharedItem
from astroquery.utils.tap.model.shared_to_item import TapSharedToItem

READING_ITEM = 10
READING_SHAREDTO = 20


class SharedItemsSaxParser(xml.sax.ContentHandler):
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
        self.__shared_items = []
        self.__shared_to_items = []
        self.__currentItem = None

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
        #  print(str(data))
        self.__status = READING_ITEM
        del self.__shared_items[:]
        xml.sax.parse(data, self)
        return self.__shared_items

    def startElement(self, name, attrs):
        #  print("startElement = " + str(name) + " " + str(attrs))
        if self.__status == READING_ITEM:
            self.__reading_item(name, attrs)
        elif self.__status == READING_SHAREDTO:
            self.__reading_shared_to(name, attrs)

    def endElement(self, name):
        #  print("endElement = " + str(name))
        if self.__status == READING_ITEM:
            self.__end_item(name)
        elif self.__status == READING_SHAREDTO:
            self.__end_shared_to(name)

    def __reading_item(self, name, attrs):
        if self.__check_item_id("sharedItem", name):
            self.__currentItem = TapSharedItem(attrs)
            self.__shared_items.append(self.__currentItem)
        if self.__check_item_id("title", name):
            self.__start_reading_data()
        if self.__check_item_id("description", name):
            self.__start_reading_data()
        if self.__check_item_id("sharedToItems", name):
            self.__status = READING_SHAREDTO

    def __end_item(self, name):
        if self.__check_item_id("title", name):
            self.__currentItem.title = str(self.__create_string_from_buffer())
            self.__stop_reading_data()
        if self.__check_item_id("description", name):
            self.__currentItem.description = str(self.__create_string_from_buffer())
            self.__stop_reading_data()

    def __reading_shared_to(self, name, attrs):
        if self.__check_item_id("sharedToItem", name):
            self.__currentItem.shared_to_items.append(TapSharedToItem(attrs))

    def __end_shared_to(self, name):
        if self.__check_item_id("sharedToItems", name):
            self.__status = READING_ITEM

    def characters(self, content):
        if self.__concatData:
            self.__charBuffer.append(content)

    def __show_attributes(self, attrs):
        return str(attrs.getNames())

    def __nothing(self, name, attrs):
        pass

    def get_item(self, ident):
        if id is None:
            raise ValueError("id must be defined")
        item = None
        for g in self.__shared_items:
            if g.id == str(ident):
                item = g
                break
        return item

    def get_shared_items(self):
        return self.__shared_items
