# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
=============
TAP plus
=============

"""

from astroquery.cadc.cadctap.job import JobCadc
from astroquery.utils.tap.xmlparser.jobSaxParser import JobSaxParser

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
UWS_MESSAGE = "uws:message"

VALID_ITEMS = [UWS_JOBID, UWS_RUNID, UWS_OWNERID, UWS_PHASE, UWS_QUOTE,
               UWS_START_TIME, UWS_END_TIME, UWS_CREATION_TIME,
               UWS_EXECUTION_DURATION, UWS_DESTRUCTION, UWS_LOCATIONID,
               UWS_NAME, UWS_PARAMETER, UWS_MESSAGE]


class JobSaxParserCadc(JobSaxParser):
    '''
    classdocs
    Reason for change
    -----------------
    Return JobCadc insteasd of Job object
    '''
    def __init__(self, async_job=False):
        JobSaxParser.__init__(self, async_job=async_job)

    def _JobSaxParser__check_valid_item_id(self, name):
        """
        Reason for change
        -----------------
        It needs to find the UWS_MESSAGE in this VAULID_ITEMS
        """
        for idTmp in VALID_ITEMS:
            if self._JobSaxParser__check_item_id(idTmp, name):
                return True
        return False

    def startElement(self, name, attrs):
        """
        Reason for change
        -----------------
        Return a JobCadc object instead of Job object
        """
        if self._JobSaxParser__check_item_id(UWS_JOBID, name):
            self._JobSaxParser__job = JobCadc(self._JobSaxParser__async)
            self._JobSaxParser__jobs.append(self._JobSaxParser__job)
            self._JobSaxParser__start_reading_data()
        elif self._JobSaxParser__check_valid_item_id(name):
            self._JobSaxParser__start_reading_data()
            if self._JobSaxParser__check_item_id(UWS_PARAMETER, name):
                self._JobSaxParser__paramKey = attrs.get("id")
        else:
            self._JobSaxParser__stop_reading_data()

    def _JobSaxParser__populate_job_value(self, value, name):
        """
        Reason for change
        -----------------
        Add the errmessage when there is an error in the job
        """
        nameLower = name.lower()
        if UWS_JOBID == nameLower:
            self._JobSaxParser__job.jobid = value
        elif UWS_RUNID == nameLower:
            self._JobSaxParser__job.runid = value
        elif UWS_OWNERID == nameLower:
            self._JobSaxParser__job.ownerid = value
        elif UWS_PHASE == nameLower:
            self._JobSaxParser__job._phase = value
        elif UWS_QUOTE == nameLower:
            self._JobSaxParser__job.quote = value
        elif UWS_START_TIME == nameLower:
            self._JobSaxParser__job.startTime = value
        elif UWS_END_TIME == nameLower:
            self._JobSaxParser__job.endTime = value
        elif UWS_CREATION_TIME == nameLower:
            self._JobSaxParser__job.creationTime = value
        elif UWS_LOCATIONID == nameLower:
            self._JobSaxParser__job.locationID = value
        elif UWS_NAME == nameLower:
            self._JobSaxParser__job.name = value
        elif UWS_EXECUTION_DURATION == nameLower:
            self._JobSaxParser__job.executionDuration = value
        elif UWS_DESTRUCTION == nameLower:
            self._JobSaxParser__job.destruction = value
        elif UWS_PARAMETER == nameLower:
            self._JobSaxParser__job.parameters[
                self._JobSaxParser__paramKey
            ] = value
        elif UWS_MESSAGE == nameLower:
            self._JobSaxParser__job.errmessage = value
