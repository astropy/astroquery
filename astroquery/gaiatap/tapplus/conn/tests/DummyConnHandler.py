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
from gaiatap.tapplus import taputils

try:
    #python 3
    from urllib.parse import urlencode as urlEncode
except ImportError:
    #python 2
    from urllib import urlencode as urlEncode
    
class DummyConnHandler:
    
    def __init__(self):
        self.request = None
        self.data = None
        self.fileExt = ".ext"
        self.defaultResponse = None
        self.responses = {}
        self.errorFileOutput = None
        self.errorReceivedResponse = None
        pass
    
    def setDefaultResponse(self, defaultResponse):
        self.defaultResponse = defaultResponse
        pass
    
    def getDefaultResponse(self):
        return self.defaultResponse
    
    def getLastRequest(self):
        return self.request
    
    def getLastData(self):
        return self.data
    
    def getErrorFileOutput(self):
        return self.errorFileOutput
    
    def getErrorReceivedResponse(self):
        return self.errorReceivedResponse
    
    def setResponse(self, request, response):
        self.responses[str(request)] = response
        pass
    
    def execute_get(self, request):
        self.request = request
        return self.__getResponse(request)
    
    def execute_post(self, subcontext, data):
        self.data = data
        sortedKey = self.__createSortedDictKey(data)
        if subcontext.find('?') == -1:
            self.request = subcontext + "?" + sortedKey
        else:
            if subcontext.endswith('?'):
                self.request = subcontext + sortedKey
            else:
                self.request = subcontext + "&" + sortedKey
        return self.__getResponse(self.request)
    
    def dump_to_file(self, fileOutput, response):
        self.errorFileOutput = fileOutput
        self.errorReceivedResponse = response
        print ("DummyConnHandler - dump to file: file: '%s', response status: %s, response msg: %s", (str(fileOutput), str(response.status), str(response.reason)))
        pass
    
    def __getResponse(self, responseid):
        try:
            return self.responses[str(responseid)]
        except KeyError as e:
            if self.defaultResponse is not None:
                return self.defaultResponse
            else:
                print ("\nNot found response for key\n\t'"+str(responseid)+"'")
                print ("Available keys: ")
                if self.responses is None:
                    print ("\tNone available")
                else:
                    for k in self.responses.keys():
                        print ("\t'"+str(k)+"'")
                        #if (str(k) == str(responseid)):
                        #    print ("\t\tfound")
                        #else:
                        #    l1 = len(k)
                        #    l2 = len(responseid)
                        #    if l1 == l2:
                        #        for i in range(0,l1):
                        #            print("'"+str(k[i])+"' - '"+str(responseid[i])+"'")
                        #            if str(k[i]) != str(responseid[i]):
                        #                print ("not equals")
                raise (e)
    
    def __createSortedDictKey(self, data):
        dictTmp = {}
        items = data.split('&')
        for i in (items):
            subItems = i.split('=')
            dictTmp[subItems[0]] = subItems[1]
            pass
        #sort dict
        return taputils.tapUtilCreateSortedDictKey(dictTmp)
    
    def check_launch_response_status(self, response, debug, expected_response_status):
        isError = False
        if response.status != expected_response_status:
            if debug:
                print ("ERROR: " + str(response.status) + ": " + str(response.reason))
            isError = True
        return isError
    
    def url_encode(self, data):
        return urlEncode(data)
    
    def get_suitable_extension(self, headers):
        return self.fileExt
    
    def set_suitable_extension(self, ext):
        self.fileExt = ext
    
    def find_header(self, headers, key):
        return taputils.tapUtilFindHeader(headers, key)
    
    pass
        