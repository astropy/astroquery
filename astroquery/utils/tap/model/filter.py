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


class Filter:

    def __init__(self):
        self.filters = {}
        self.order = None
        self.offset = None
        self.limit = None
        self.metadataOnly = True

    def add_filter(self, name, value):
        self.filters[name] = value

    def has_order(self):
        return self.order is not None

    def has_offset(self):
        return self.offset is not None

    def has_limit(self):
        return self.limit is not None

    def create_url_data_request(self):
        # jobs/list?[&session=][&limit=][&offset=][&order=][&metadata_only=true|false]
        data = self.filters.copy()
        data["metadata_only"] = self.metadataOnly
        if self.offset is not None:
            data["offset"] = self.offset
        if self.limit is not None:
            data["limit"] = self.limit
        if self.order is not None:
            data["order"] = self.order
        return data
