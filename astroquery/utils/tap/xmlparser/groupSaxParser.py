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
from astroquery.utils.tap.model.group import TapGroup
from astroquery.utils.tap.model.user import TapUser

READING_GROUP = 10
READING_USERS = 20


class GroupSaxParser(xml.sax.ContentHandler):
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
        self.__groups = []
        self.__users = []
        self.__currentGroup = None
        self.__currentUser = None

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
        self.__status = READING_GROUP
        del self.__groups[:]
        xml.sax.parse(data, self)
        return self.__groups

    def startElement(self, name, attrs):
        #  print("startElement = " + str(name) + " " + str(attrs))
        if self.__status == READING_GROUP:
            self.__reading_group(name, attrs)
        elif self.__status == READING_USERS:
            self.__reading_users(name, attrs)

    def endElement(self, name):
        #  print("endElement = " + str(name))
        if self.__status == READING_GROUP:
            self.__end_group(name)
        elif self.__status == READING_USERS:
            self.__end_users(name)

    def __reading_group(self, name, attrs):
        if self.__check_item_id("sharedGroup", name):
            self.__currentGroup = TapGroup(attrs)
            self.__groups.append(self.__currentGroup)
        if self.__check_item_id("title", name):
            self.__start_reading_data()
        if self.__check_item_id("description", name):
            self.__start_reading_data()
        if self.__check_item_id("users", name):
            self.__status = READING_USERS

    def __end_group(self, name):
        if self.__check_item_id("title", name):
            self.__currentGroup.title = str(self.__create_string_from_buffer())
            self.__stop_reading_data()
        if self.__check_item_id("description", name):
            self.__currentGroup.description = str(self.__create_string_from_buffer())
            self.__stop_reading_data()

    def __reading_users(self, name, attrs):
        if self.__check_item_id("user", name):
            self.__currentGroup.users.append(TapUser(attrs))

    def __end_users(self, name):
        if self.__check_item_id("users", name):
            self.__status = READING_GROUP

    def characters(self, content):
        if self.__concatData:
            self.__charBuffer.append(content)

    def __show_attributes(self, attrs):
        return str(attrs.getNames())

    def __nothing(self, name, attrs):
        pass

    def get_group(self, ident):
        if id is None:
            raise ValueError("id must be defined")
        group = None
        for g in self.__groups:
            if g.id == str(ident):
                group = g
                break
        return group

    def get_groups(self):
        return self.__groups
