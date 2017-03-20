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


from astroquery.utils.tap.model.job import Job
from astroquery.utils.tap.xmlparser import utils as Utils

READING_JOB = 10
READING_PHASE = 20

UWS_JOBREF = "uws:jobref"
UWS_PHASE = "uws:phase"


class JobListSaxParser(xml.sax.ContentHandler):
    '''
    classdocs
    '''

    def __init__(self, async_job=False):
        '''
        Constructor
        '''
        self.__internal_init()
        self.__async = async_job

    def __internal_init(self):
        self.__concatData = False
        self.__charBuffer = []
        self.__job = None
        self.__jobs = []
        self.__status = 0
        self.__paramKey = None
        self.__async = False

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
        self.__status = READING_JOB
        xml.sax.parse(data, self)
        return self.__jobs

    def startElement(self, name, attrs):
        if self.__status == READING_JOB:
            self.__reading_job(name, attrs)
        elif self.__status == READING_PHASE:
            self.__reading_phase(name, attrs)

    def endElement(self, name):
        if self.__status == READING_JOB:
            self.__end_job(name)
        elif self.__status == READING_PHASE:
            self.__end_phase(name)

    def characters(self, content):
        if self.__concatData:
            self.__charBuffer.append(content)

    def __reading_job(self, name, attrs):
        if self.__check_item_id(UWS_JOBREF, name):
            self.__job = Job(self.__async)
            self.__job.set_jobid(attrs.get("id"))
            self.__status = READING_PHASE

    def __end_job(self, name):
        if self.__check_item_id(UWS_JOBREF, name):
            self.__jobs.append(self.__job)

    def __reading_phase(self, name, attrs):
        if self.__check_item_id(UWS_PHASE, name):
            self.__start_reading_data()

    def __end_phase(self, name):
        if self.__check_item_id(UWS_PHASE, name):
            self.__job.set_phase(self.__create_string_from_buffer())
            self.__status = READING_JOB
