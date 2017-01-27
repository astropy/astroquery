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
from astroquery.gaiatap.tapplus.model.job import Job
from astroquery.gaiatap.tapplus.xmlparser import utils as Utils

READING_JOB = 10
READING_PHASE = 20

UWS_JOBREF = "uws:jobref"
UWS_PHASE = "uws:phase"

class JobListSaxParser(xml.sax.ContentHandler):
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
    
    def _startReadingData(self):
        self.__concatData = True
        del self.__charBuffer[:]
        pass
    
    def _stopReadingData(self):
        self.__concatData = False
        pass
    
    def parseData(self, data):
        self.__status = READING_JOB
        xml.sax.parse(data, self)
        return self.__jobs

    def startElement(self, name, attrs):
        if self.__status == READING_JOB:
            self._readingJob(name, attrs)
        elif self.__status == READING_PHASE:
            self._readingPhase(name, attrs)
        pass
    
    def endElement(self, name):
        if self.__status == READING_JOB:
            self._endJob(name)
        elif self.__status == READING_PHASE:
            self._endPhase(name)
        pass
    
    def characters(self, content):
        if self.__concatData:
            self.__charBuffer.append(content)
        pass
    
    def _readingJob(self, name, attrs):
        if self._checkItemId(UWS_JOBREF, name):
            self.__job = Job(self.__async)
            self.__job.set_jobid(attrs.get("id"))
            self.__status = READING_PHASE
        pass
    
    def _endJob(self, name):
        if self._checkItemId(UWS_JOBREF, name):
            self.__jobs.append(self.__job)
        pass
    
    def _readingPhase(self, name, attrs):
        if self._checkItemId(UWS_PHASE, name):
            self._startReadingData()
        pass
    
    def _endPhase(self, name):
        if self._checkItemId(UWS_PHASE, name):
            self.__job.set_phase(self._createStringFromBuffer())
            self.__status = READING_JOB
        pass
    
    
    
    

