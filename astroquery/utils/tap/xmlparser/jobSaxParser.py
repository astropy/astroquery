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

UWS_JOBID = "uws:jobid"
UWS_RUNID = "uws:runid"
UWS_OWNERID = "uws:ownerid"
UWS_PHASE = "uws:phase"
UWS_QUOTE = "uws:quote"
UWS_START_TIME = "uws:starttime"
UWS_END_TIME = "uws:endtime"
UWS_CREATION_TIME = "uws:creationtime"
UWS_EXECUTION_DURATION = "uws:executionduration"
UWS_DESTRUCTION = "uws:destruction"
UWS_LOCATIONID = "uws:locationid"
UWS_NAME = "uws:name"
UWS_PARAMETER = "uws:parameter"

VALID_ITEMS = [UWS_JOBID, UWS_RUNID, UWS_OWNERID, UWS_PHASE, UWS_QUOTE,
               UWS_START_TIME, UWS_END_TIME, UWS_CREATION_TIME,
               UWS_EXECUTION_DURATION, UWS_DESTRUCTION, UWS_LOCATIONID,
               UWS_NAME, UWS_PARAMETER]


class JobSaxParser(xml.sax.ContentHandler):
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

    def __check_valid_item_id(self, name):
        for idTmp in VALID_ITEMS:
            if self.__check_item_id(idTmp, name):
                return True
        return False

    def __start_reading_data(self):
        self.__concatData = True
        del self.__charBuffer[:]

    def __stop_reading_data(self):
        self.__concatData = False

    def parseData(self, data):
        # self.__job = Job(True)
        xml.sax.parse(data, self)
        return self.__jobs

    def startElement(self, name, attrs):
        if self.__check_item_id(UWS_JOBID, name):
            self.__job = Job(self.__async)
            self.__jobs.append(self.__job)
            self.__start_reading_data()
        elif self.__check_valid_item_id(name):
            self.__start_reading_data()
            if self.__check_item_id(UWS_PARAMETER, name):
                self.__paramKey = attrs.get("id")
        else:
            self.__stop_reading_data()

    def endElement(self, name):
        if self.__check_valid_item_id(name):
            value = self.__create_string_from_buffer()
            self.__populate_job_value(value, name)
            self.__stop_reading_data()
        else:
            self.__stop_reading_data()

    def characters(self, content):
        if self.__concatData:
            self.__charBuffer.append(content)

    def __populate_job_value(self, value, name):
        nameLower = name.lower()
        if UWS_JOBID == nameLower:
            self.__job.jobid = value
        elif UWS_RUNID == nameLower:
            self.__job.runid = value
        elif UWS_OWNERID == nameLower:
            self.__job.ownerid = value
        elif UWS_PHASE == nameLower:
            print("phase was set")
            self.__job._phase = value
        elif UWS_QUOTE == nameLower:
            self.__job.quote = value
        elif UWS_START_TIME == nameLower:
            self.__job.startTime = value
        elif UWS_END_TIME == nameLower:
            self.__job.endTime = value
        elif UWS_CREATION_TIME == nameLower:
            self.__job.creationTime = value
        elif UWS_LOCATIONID == nameLower:
            self.__job.locationID = value
        elif UWS_NAME == nameLower:
            self.__job.name = value
        elif UWS_EXECUTION_DURATION == nameLower:
            self.__job.executionDuration = value
        elif UWS_DESTRUCTION == nameLower:
            self.__job.destruction = value
        elif UWS_PARAMETER == nameLower:
            self.__job.parameters[self.__paramKey] = value
