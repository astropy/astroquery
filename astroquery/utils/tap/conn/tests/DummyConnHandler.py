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
from astroquery.utils.tap import taputils

from six.moves.urllib.parse import urlencode


class DummyConnHandler(object):

    def __init__(self):
        self.request = None
        self.data = None
        self.fileExt = ".ext"
        self.defaultResponse = None
        self.responses = {}
        self.errorFileOutput = None
        self.errorReceivedResponse = None

    def set_default_response(self, defaultResponse):
        self.defaultResponse = defaultResponse

    def get_default_response(self):
        return self.defaultResponse

    def get_last_request(self):
        return self.request

    def get_last_data(self):
        return self.data

    def get_error_file_output(self):
        return self.errorFileOutput

    def get_error_received_response(self):
        return self.errorReceivedResponse

    def set_response(self, request, response):
        self.responses[str(request)] = response

    def execute_get(self, request):
        self.request = request
        return self.__get_response(request)

    def execute_post(self, subcontext, data):
        self.data = data
        sortedKey = self.__create_sorted_dict_key(data)
        if subcontext.find('?') == -1:
            self.request = subcontext + "?" + sortedKey
        else:
            if subcontext.endswith('?'):
                self.request = subcontext + sortedKey
            else:
                self.request = subcontext + "&" + sortedKey
        return self.__get_response(self.request)

    def dump_to_file(self, fileOutput, response):
        self.errorFileOutput = fileOutput
        self.errorReceivedResponse = response
        print("DummyConnHandler - dump to file: file: '%s', \
        response status: %s, response msg: %s", (
            str(fileOutput),
            str(response.status),
            str(response.reason)))

    def __get_response(self, responseid):
        try:
            return self.responses[str(responseid)]
        except KeyError as e:
            if self.defaultResponse is not None:
                return self.defaultResponse
            else:
                print("\nNot found response for key\n\t'"+str(responseid)+"'")
                print("Available keys: ")
                if self.responses is None:
                    print("\tNone available")
                else:
                    for k in self.responses.keys():
                        print("\t'"+str(k)+"'")
                raise (e)

    def __create_sorted_dict_key(self, data):
        dictTmp = {}
        items = data.split('&')
        for i in (items):
            subItems = i.split('=')
            dictTmp[subItems[0]] = subItems[1]
        # sort dict
        return taputils.taputil_create_sorted_dict_key(dictTmp)

    def check_launch_response_status(self, response, debug,
                                     expected_response_status):
        isError = False
        if response.status != expected_response_status:
            if debug:
                print("ERROR: " + str(response.status) + ": "
                       + str(response.reason))
            isError = True
        return isError

    def url_encode(self, data):
        return urlencode(data)

    def get_suitable_extension(self, headers):
        return self.fileExt

    def set_suitable_extension(self, ext):
        self.fileExt = ext

    def get_suitable_extension_by_format(self, output_format):
        return self.fileExt

    def find_header(self, headers, key):
        return taputils.taputil_find_header(headers, key)
