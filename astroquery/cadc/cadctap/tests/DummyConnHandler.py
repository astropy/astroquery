# Licensed under a 3-clause BSD style license - see LICENSE.rst

from astroquery.utils.tap.conn.tests.DummyConnHandler import DummyConnHandler


class DummyConnHandlerCadc(DummyConnHandler):

    def __init__(self):
        super(DummyConnHandlerCadc, self).__init__()
        self.cookie = None
        self._TapConn__connectionHandler = ConnectionHandlerCadc()

    def encode_multipart(self, args, files):
        return 'contentType', self.url_encode(args)

    def execute_get_other(self, request):
        self.request = request
        return self._DummyConnHandler__get_response(request)

    def execute_post(self, subcontext, data, contentType=None):
        self.data = data
        sortedKey = self._DummyConnHandler__create_sorted_dict_key(data)
        if subcontext.find('?') == -1:
            self.request = subcontext + "?" + sortedKey
        else:
            if subcontext.endswith('?'):
                self.request = subcontext + sortedKey
            else:
                self.request = subcontext + "&" + sortedKey
        return self._DummyConnHandler__get_response(self.request)

    def execute_post_other(self, location, data, contentType=None):
        self.data = data
        sortedKey = self._DummyConnHandler__create_sorted_dict_key(data)
        if location.find('?') == -1:
            self.request = location + "?" + sortedKey
        else:
            if location.endswith('?'):
                self.request = location + sortedKey
            else:
                self.request = location + "&" + sortedKey
        return self._DummyConnHandler__get_response(self.request)

    def set_cookie(self, cookie):
        self.cookie = cookie

    def cookies_set(self):
        return self.cookie is not None


class ConnectionHandlerCadc(object):
    def __init__(self):
        self.__certificate = None
