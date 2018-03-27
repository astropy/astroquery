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


PARAMETER_JOB_ID = 'jobid'
PARAMETER_JOB_NAME = 'jobname'
PARAMETER_PHASE_ID = 'phaseid'
PARAMETER_QUERY = 'query'
PARAMETER_START_TIME_INIT = 'start_time_init'
PARAMETER_END_TIME_INIT = 'end_time_init'
PARAMETER_START_TIME_LIMIT = 'start_time_limit'
PARAMETER_END_TIME_LIMIT = 'end_time_limit'


class Filter(object):

    def __init__(self):
        self.__internal_init()

    def __internal_init(self):
        self.__filters = {}
        self.__order = None
        self.__offset = None
        self.__limit = None
        self.__metadataOnly = True

    def add_filter(self, name, value):
        self.__filters[name] = value

    def set_order(self, order):
        self.__order = order

    def get_order(self):
        return self.__order

    def set_offset(self, offset):
        self.__offset = offset

    def get_offset(self):
        return self.__offset

    def set_limit(self, limit):
        self.__limit = limit

    def get_limit(self, limit):
        return self.__limit

    def get_filters(self):
        return self.__filters

    def has_order(self):
        return self.__order is not None

    def has_offset(self):
        return self.__offset is not None

    def has_limit(self):
        return self.__limit is not None

    def set_metadata_only(self, metadataOnly):
        self.__metadataOnly = metadataOnly

    def get_metadata_only(self, metadataOnly):
        return self.__metadataOnly

    def create_url_data_request(self):
         # jobs/list?[&session=][&limit=][&offset=][&order=][&metadata_only=true|false]
        data = self.__filters.copy()
        data["metadata_only"] = self.__metadataOnly
        if self.__offset is not None:
            data["offset"] = self.__offset
        if self.__limit is not None:
            data["limit"] = self.__limit
        if self.__order is not None:
            data["order"] = self.__order
        return data
