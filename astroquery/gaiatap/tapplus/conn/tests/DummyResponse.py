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
class DummyResponse(object):
    '''
    classdocs
    '''
    def __init__(self):
        self.reason = ""
        self.status = 0
        self.index = 0
        self.set_data(None, None, None, None)
        pass
    
    def set_status_code(self, status):
        self.status = status
        pass
    
    def set_message(self, reason):
        self.reason = reason
        pass
    
    def set_data(self, method, context, body, headers):
        self.method = method
        self.context = context
        self.body = body
        self.headers = headers
        self.index = 0
        pass
    
    def get_method(self):
        return self.method
    
    def get_context(self):
        return self.context
    
    def get_body(self):
        return self.body
    
    def read(self, size=None):
        v = self.get_body()
        if v == None:
            return None
        else:
            if size is None or size < 0:
                #read all
                return v.encode(encoding='utf_8', errors='strict')
            else:
                bodyLength = len(v)
                if self.index < 0:
                    return ""
                if size >= bodyLength:
                    size = bodyLength - 1
                if size <= 0:
                    return ""
                endPos = self.index + size
                tmp = v[self.index:endPos]
                self.index = endPos
                if endPos >= (bodyLength - 1):
                    self.index = -1
                return tmp.encode(encoding='utf_8', errors='strict')
            pass
        pass
    
    def close(self):
        self.index = 0
        pass
    
    def getheaders(self):
        return self.headers
    
    pass
        