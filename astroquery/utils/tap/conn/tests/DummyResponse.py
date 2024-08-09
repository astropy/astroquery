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


class DummyResponse:
    '''
    classdocs
    '''

    STATUS_MESSAGES = {200: "OK", 303: "OK", 500: "ERROR"}

    def __init__(self, status_code=None):
        self.zip_bytes = None
        self.reason = ""
        self.set_status_code(status_code)
        self.index = 0
        self.set_data(None, None, None, None)

    def __iter__(self):
        return iter([self.get_body().encode(encoding='UTF-8')])

    def set_status_code(self, status_code):
        self.status = status_code
        self.reason = self.STATUS_MESSAGES.get(status_code)

    def set_data(self, method, context=None, body=None, headers=None):
        self.method = method
        self.context = context
        self.body = body
        self.headers = headers
        self.index = 0

    def get_method(self):
        return self.method

    def get_context(self):
        return self.context

    def get_body(self):
        return self.body

    def read(self, size=None):
        v = self.get_body()
        if v is None:
            return None
        else:

            if v.endswith('zip'):
                if self.zip_bytes is None:
                    with open(v, 'rb') as file:
                        self.zip_bytes = file.read()

            if size is None or size < 0:

                if v.endswith('zip'):
                    return self.zip_bytes

                # read all
                return v.encode(encoding='utf_8', errors='strict')
            else:
                is_zip = False

                if v.endswith('zip'):
                    is_zip = True
                    bodyLength = len(self.zip_bytes)
                    v = self.zip_bytes
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

                if is_zip:
                    return tmp
                else:
                    return tmp.encode(encoding='utf_8', errors='strict')

    def close(self):
        self.index = 0

    def getheaders(self):
        return self.headers
