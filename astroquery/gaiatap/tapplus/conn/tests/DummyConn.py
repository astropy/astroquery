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
from astroquery.gaiatap.tapplus.conn.tests.DummyResponse import DummyResponse

class DummyConn(object):
    '''
    classdocs
    '''

    def __init__(self, name=None):
        self.response = DummyResponse()
        self.name = name
        pass
    
    def request(self, method, context, body, headers):
        self.response.set_data(method, context, body, headers)
        pass
    
    def getresponse(self):
        return self.response
    
    def __str__(self):
        return self.name
    
    pass
