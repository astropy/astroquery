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

from gaiatap.tapplus.model.table import Table
from gaiatap.tapplus.model.column import Column
from gaiatap.tapplus.model.job import Job
from gaiatap.tapplus.xmlparser import utils as Utils

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

VALID_ITEMS = [UWS_JOBID, UWS_RUNID, UWS_OWNERID, UWS_PHASE,UWS_QUOTE,\
               UWS_START_TIME, UWS_END_TIME, UWS_CREATION_TIME, \
               UWS_EXECUTION_DURATION, UWS_DESTRUCTION, UWS_LOCATIONID, UWS_NAME, UWS_PARAMETER]

class JobSaxParser(xml.sax.ContentHandler):
    '''
    classdocs
    '''

    
    def __init__(self, async=False):
        '''
        Constructor
        '''
        self.__internalInit()
        self.__async = async
        pass
    
    def __internalInit(self):
        self.__concatData = False
        self.__charBuffer = []
        self.__job = None
        self.__jobs = []
        self.__status = 0
        self.__paramKey = None
        self.__async = False
        pass
        
    def _createStringFromBuffer(self):
        return Utils.utilCreateStringFromBuffer(self.__charBuffer)
        
    def _checkItemId(self, itemId, tmpValue):
        if str(itemId).lower() == str(tmpValue).lower():
            return True
        return False 
    
    def _checkValidItemId(self, name):
        for id in VALID_ITEMS:
            if self._checkItemId(id, name):
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
        #self.__job = Job(True)
        xml.sax.parse(data, self)
        return self.__jobs

    def startElement(self, name, attrs):
        if self._checkItemId(UWS_JOBID, name):
            self.__job = Job(self.__async)
            self.__jobs.append(self.__job)
            self._startReadingData()
        elif self._checkValidItemId(name):
            self._startReadingData()
            if self._checkItemId(UWS_PARAMETER, name):
                self.__paramKey = attrs.get("id")
        else:
            self._stopReadingData()
        pass
    
    def endElement(self, name):
        if self._checkValidItemId(name):
            value = self._createStringFromBuffer()
            self._populateJobValue(value, name)
            self._stopReadingData()
        else:
            self._stopReadingData()
        pass
    
    def characters(self, content):
        if self.__concatData:
            self.__charBuffer.append(content)
        pass
    
    def _populateJobValue(self, value, name):
        nameLower = name.lower()
        if UWS_JOBID == nameLower:
            self.__job.set_jobid(value)
        elif UWS_RUNID == nameLower:
            self.__job.set_runid(value)
        elif UWS_OWNERID == nameLower:
            self.__job.set_ownerid(value)
        elif UWS_PHASE == nameLower:
            self.__job.set_phase(value)
        elif UWS_QUOTE == nameLower:
            self.__job.set_quote(value)
        elif UWS_START_TIME == nameLower:
            self.__job.set_start_time(value)
        elif UWS_END_TIME == nameLower:
            self.__job.set_end_time(value)
        elif UWS_CREATION_TIME == nameLower:
            self.__job.set_creation_time(value)
        elif UWS_LOCATIONID == nameLower:
            self.__job.set_locationid(value)
        elif UWS_NAME == nameLower:
            self.__job.set_name(value)
        elif UWS_EXECUTION_DURATION == nameLower:
            self.__job.set_execution_duration(value)
        elif UWS_DESTRUCTION == nameLower:
            self.__job.set_destruction(value)
        elif UWS_PARAMETER == nameLower:
            self.__job.set_parameter(self.__paramKey, value)
        pass
    
    
    

