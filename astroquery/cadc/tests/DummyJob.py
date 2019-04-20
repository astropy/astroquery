# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
=============
Cadc TAP plus
=============

"""


class DummyJob(object):

    def __init__(self):
        self.parameters = {}
        self.jobid = '123'
        self.outputFile = 'file.txt'
        self._phase = 'new'
        self.remoteLocation = 'www.host.com/place'
        self.results = 'results'
        self.connHandler = None

    def reset(self):
        self.parameters = {}

    def set_parameter(self, key, value):
        self.parameters[key] = value

    def _Job__responseStatus(self):
        return '200'

    def _Job__responseMsg(self):
        return 'ok'
