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

import requests


class DummyConnHandler:

    def __init__(self):
        self.request = None
        self.data = None
        self.fileExt = ".ext"
        self.defaultResponse = None
        self.responses = {}
        self.contentType = None
        self.verbose = None
        self.query = None
        self.fileOutput = None

    def set_default_response(self, defaultResponse):
        self.defaultResponse = defaultResponse

    def get_default_response(self):
        return self.defaultResponse

    def set_response(self, request, response):
        self.responses[str(request)] = response

    def execute_tapget(self, request=None, verbose=False):
        return self.__execute_get(request, verbose)

    def execute_dataget(self, query, verbose=False):
        return self.__execute_get(query)

    def execute_datalinkget(self, subcontext, query, verbose=False):
        self.query = query
        return self.__execute_get(subcontext, verbose)

    def __execute_get(self, request, verbose):
        self.request = request
        self.verbose = verbose
        return self.__get_response(request)

    def execute_tappost(self, subcontext=None, data=None,
                        content_type=None, verbose=False):
        return self.__execute_post(subcontext, data, content_type, verbose)

    def execute_datapost(self, data=None, content_type=None, verbose=False):
        return self.__execute_post("", data, content_type, verbose)

    def execute_datalinkpost(self, subcontext=None, data=None,
                             content_type=None, verbose=False):
        return self.__execute_post(subcontext, data, content_type, verbose)

    def __execute_post(self, subcontext=None, data=None,
                       content_type=None, verbose=False):
        self.data = data
        self.contentType = content_type
        self.verbose = verbose
        sortedKey = self.__create_sorted_dict_key(data)
        if subcontext.find('?') == -1:
            self.request = f"{subcontext}?{sortedKey}"
        else:
            if subcontext.endswith('?'):
                self.request = f"{subcontext}{sortedKey}"
            else:
                self.request = f"{subcontext}&{sortedKey}"
        return self.__get_response(self.request)

    def dump_to_file(self, fileOutput, response):
        print(f"DummyConnHandler - dump to file: file: '{fileOutput}', \
        response status: {response.status}, response msg: {response.reason}")

    def __get_response(self, responseid):
        try:
            return self.responses[str(responseid)]
        except KeyError as e:
            if self.defaultResponse is not None:
                return self.defaultResponse
            else:
                print(f"\nNot found response for key\n\t'{responseid}'")
                print("Available keys: ")
                if self.responses is None:
                    print("\tNone available")
                else:
                    for k in self.responses.keys():
                        print(f"\t'{k}'")
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
                                     expected_response_status,
                                     raise_exception=True):
        isError = False
        if response.status != expected_response_status:
            if debug:
                print(f"ERROR: {response.status}: {response.reason}")
            isError = True
        if isError and raise_exception:
            errMsg = taputils.get_http_response_error(response)
            print(response.status, errMsg)
            raise requests.exceptions.HTTPError(errMsg)
        else:
            return isError

    def get_suitable_extension(self, headers):
        return self.fileExt

    def get_suitable_extension_by_format(self, output_format):
        return self.fileExt

    def get_file_from_header(self, headers):
        return self.fileOutput

    def find_header(self, headers, key):
        return taputils.taputil_find_header(headers, key)

    def execute_table_edit(self, data,
                           content_type="application/x-www-form-urlencoded",
                           verbose=False):
        return self.__execute_post(subcontext="tableEdit", data=data,
                                   content_type=content_type, verbose=verbose)

    def execute_table_tool(self, data,
                           content_type="application/x-www-form-urlencoded",
                           verbose=False):
        return self.__execute_post(subcontext="TableTool", data=data,
                                   content_type=content_type, verbose=verbose)

    def execute_secure(self, subcontext=None, data=None, verbose=False):
        return self.__execute_post(subcontext=subcontext, data=data, verbose=verbose)

    def get_host_url(self):
        return "my fake object"
