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
from astroquery.utils.tap.conn.tests.DummyResponse import DummyResponse


class DummyConn:
    '''
    classdocs
    '''

    def __init__(self, name=None):
        self.response = DummyResponse()
        self.name = name
        self.httpConn = DummyHttpConn(self.response)
        self.cookie = None
        self.ishttps = False

    def request(self, method, context, body, headers):
        self.response.set_data(method, context, body, headers)

    def getresponse(self):
        return self.response

    def get_connection(self, ishttps=False, cookie=None, verbose=False):
        self.ishttps = ishttps
        self.cookie = cookie
        return self.httpConn

    def get_connection_secure(self, verbose):
        return self.httpConn

    def __str__(self):
        return self.name


class DummyHttpConn:

    def __init__(self, response):
        self.response = response
        self.reqmethod = None
        self.requrl = None
        self.reqbody = None
        self.reqheaders = None

    def request(self, method, url, body=None, headers=None):
        self.reqmethod = method
        self.requrl = url
        self.reqbody = body
        self.reqheaders = headers
        self.response.set_data(method, url, body, headers)
        return self.response

    def getresponse(self):
        return self.response
