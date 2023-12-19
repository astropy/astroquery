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

import http.client as httplib
import mimetypes
import platform
import time
import os
from astroquery.utils.tap.xmlparser import utils
from astroquery.utils.tap import taputils
from astroquery import version

import requests

__all__ = ['TapConn']

CONTENT_TYPE_POST_DEFAULT = "application/x-www-form-urlencoded"


class TapConn:
    """TAP plus connection class
    Provides low level HTTP connection capabilities
    """

    def __init__(self, ishttps,
                 host, *,
                 server_context=None,
                 port=80,
                 sslport=443,
                 connhandler=None,
                 tap_context=None,
                 upload_context=None,
                 table_edit_context=None,
                 data_context=None,
                 datalink_context=None):
        """Constructor

        Parameters
        ----------
        ishttps: bool, mandatory
            'True' is the protocol to use is HTTPS
        host : str, mandatory
            host name
        server_context : str, mandatory
            server context
        tap_context : str, optional
            tap context
        upload_context : str, optional
            upload context
        table_edit_context : str, optional
            table edit context
        data_context : str, optional
            data context
        datalink_context : str, optional
            datalink context
        port : int, optional, default 80
            HTTP port
        sslport : int, optional, default 443
            HTTPS port
        connhandler connection handler object, optional, default None
            HTTP(s) connection hander (creator). If no handler is provided, a
            new one is created.
        """
        self.__interna_init()
        self.__isHttps = ishttps
        self.__connHost = host
        self.__connPort = port
        self.__connPortSsl = sslport
        if server_context is not None:
            if server_context.startswith("/"):
                self.__serverContext = server_context
            else:
                self.__serverContext = f"/{server_context}"
        else:
            self.__serverContext = ""
        self.__tapContext = self.__create_context(tap_context)
        self.__dataContext = self.__create_context(data_context)
        self.__datalinkContext = self.__create_context(datalink_context)
        self.__uploadContext = self.__create_context(upload_context)
        self.__tableEditContext = self.__create_context(table_edit_context)
        if connhandler is None:
            self.__connectionHandler = ConnectionHandler(self.__connHost,
                                                         self.__connPort,
                                                         self.__connPortSsl)
        else:
            self.__connectionHandler = connhandler

    def __create_context(self, context):
        if context is not None and context != "":
            if str(context).startswith("/"):
                return f"{self.__serverContext}{context}"
            else:
                return f"{self.__serverContext}/{context}"
        else:
            return self.__serverContext

    def __interna_init(self):
        self.__connectionHandler = None
        self.__isHttps = False
        self.__connHost = ""
        self.__connPort = 80
        self.__connPortSsl = 443
        self.__serverContext = None
        self.__tapContext = None
        self.__postHeaders = {
            "Content-type": CONTENT_TYPE_POST_DEFAULT,
            "Accept": "text/plain",
            "User-Agent": "astroquery/{vers} Python/{sysver} ({plat})".format(
                vers=version.version, plat=platform.system(), sysver=platform.python_version()),
        }
        self.__getHeaders = {}
        self.__cookie = None
        self.__currentStatus = 0
        self.__currentReason = ""

    def __get_tap_context(self, subContext):
        return f"{self.__tapContext}/{subContext}"

    def __get_data_context(self, encodedData=None):
        if self.__dataContext is None:
            raise ValueError("data_context must be specified at TAP object "
                             + "creation for this action to be performed")
        if encodedData is not None:
            return f"{self.__dataContext}?{encodedData}"
        else:
            return self.__dataContext

    def __get_datalink_context(self, subContext, *, encodedData=None):
        if self.__datalinkContext is None:
            raise ValueError("datalink_context must be specified at TAP "
                             + "object creation for this action to be "
                             + "performed")
        if encodedData is not None:
            return f"{self.__datalinkContext}/{subContext}?{encodedData}"

        else:
            return f"{self.__datalinkContext}/{subContext}"

    def __get_upload_context(self):
        if self.__uploadContext is None:
            raise ValueError("upload_context must be specified at TAP "
                             + "object creation for this action to be "
                             + "performed")
        return self.__uploadContext

    def __get_table_edit_context(self):
        if self.__tableEditContext is None:
            raise ValueError("table_edit_context must be specified at TAP "
                             + "object creation for this action to be "
                             + "performed")
        return self.__tableEditContext

    def __get_server_context(self, subContext):
        return f"{self.__serverContext}/{subContext}"

    def execute_tapget(self, subcontext, *, verbose=False):
        """Executes a TAP GET request
        The connection is done through HTTP or HTTPS depending on the login
        status (logged in -> HTTPS)

        Parameters
        ----------
        subcontext : str, mandatory
            context to be added to host+serverContext+tapContext, usually the
            TAP list name
        verbose : bool, optional, default 'False'
            flag to display information about the process

        Returns
        -------
        An HTTP(s) response object
        """
        if subcontext.startswith("http"):
            # absolute url
            return self.__execute_get(subcontext, verbose=verbose)
        else:
            context = self.__get_tap_context(subcontext)
            return self.__execute_get(context, verbose=verbose)

    def execute_dataget(self, query, *, verbose=False):
        """Executes a data GET request
        The connection is done through HTTP or HTTPS depending on the login
        status (logged in -> HTTPS)

        Parameters
        ----------
        query : str, mandatory
            URL encoded data (query string)
        verbose : bool, optional, default 'False'
            flag to display information about the process

        Returns
        -------
        An HTTP(s) response object
        """
        context = self.__get_data_context(query)
        return self.__execute_get(context, verbose=verbose)

    def execute_datalinkget(self, subcontext, query, *, verbose=False):
        """Executes a datalink GET request
        The connection is done through HTTP or HTTPS depending on the login
        status (logged in -> HTTPS)

        Parameters
        ----------
        subcontext : str, mandatory
            datalink subcontext
        query : str, mandatory
            URL encoded data (query string)
        verbose : bool, optional, default 'False'
            flag to display information about the process

        Returns
        -------
        An HTTP(s) response object
        """
        context = self.__get_datalink_context(subcontext, encodedData=query)
        return self.__execute_get(context, verbose=verbose)

    def __execute_get(self, context, *, verbose=False):
        conn = self.__get_connection(verbose=verbose)
        if verbose:
            print(f"host = {conn.host}:{conn.port}")
            print(f"context = {context}")
        conn.request("GET", context, None, self.__getHeaders)
        response = conn.getresponse()
        self.__currentReason = response.reason
        self.__currentStatus = response.status
        return response

    def execute_tappost(self, subcontext, data,
                        content_type=CONTENT_TYPE_POST_DEFAULT, *,
                        verbose=False):
        """Executes a POST request
        The connection is done through HTTP or HTTPS depending on the login
        status (logged in -> HTTPS)

        Parameters
        ----------
        subcontext : str, mandatory
            context to be added to host+serverContext+tapContext, usually the
            TAP list name
        data : str, mandatory
            POST data
        content_type: str, optional, default: application/x-www-form-urlencoded
            HTTP(s) content-type header value
        verbose : bool, optional, default 'False'
            flag to display information about the process

        Returns
        -------
        An HTTP(s) response object
        """
        context = self.__get_tap_context(subcontext)
        return self.__execute_post(context, data, content_type, verbose=verbose)

    def execute_datapost(self, data,
                         content_type=CONTENT_TYPE_POST_DEFAULT, *,
                         verbose=False):
        """Executes a POST request
        The connection is done through HTTP or HTTPS depending on the login
        status (logged in -> HTTPS)

        Parameters
        ----------
        data : str, mandatory
            POST data
        content_type: str, optional, default: application/x-www-form-urlencoded
            HTTP(s) content-type header value
        verbose : bool, optional, default 'False'
            flag to display information about the process

        Returns
        -------
        An HTTP(s) response object
        """
        context = self.__get_data_context()
        return self.__execute_post(context, data, content_type, verbose=verbose)

    def execute_datalinkpost(self, subcontext, data,
                             content_type=CONTENT_TYPE_POST_DEFAULT, *,
                             verbose=False):
        """Executes a POST request
        The connection is done through HTTP or HTTPS depending on the login
        status (logged in -> HTTPS)

        Parameters
        ----------
        subcontext : str, mandatory
            datalink subcontext (e.g. 'capabilities', 'availability',
            'links', etc.)
        data : str, mandatory
            POST data
        content_type: str, optional, default: application/x-www-form-urlencoded
            HTTP(s) content-type header value
        verbose : bool, optional, default 'False'
            flag to display information about the process

        Returns
        -------
        An HTTP(s) response object
        """
        context = self.__get_datalink_context(subcontext)
        return self.__execute_post(context, data, content_type, verbose=verbose)

    def execute_upload(self, data,
                       content_type=CONTENT_TYPE_POST_DEFAULT, *,
                       verbose=False):
        """Executes a POST upload request
        The connection is done through HTTP or HTTPS depending on the login
        status (logged in -> HTTPS)

        Parameters
        ----------
        data : str, mandatory
            POST data
        content_type: str, optional, default: application/x-www-form-urlencoded
            HTTP(s) content-type header value
        verbose : bool, optional, default 'False'
            flag to display information about the process

        Returns
        -------
        An HTTP(s) response object
        """
        context = self.__get_upload_context()
        return self.__execute_post(context, data, content_type, verbose=verbose)

    def execute_share(self, data, *, verbose=False):
        """Executes a POST upload request
        The connection is done through HTTP or HTTPS depending on the login
        status (logged in -> HTTPS)

        Parameters
        ----------
        data : str, mandatory
            POST data
        content_type: str, optional, default: application/x-www-form-urlencoded
            HTTP(s) content-type header value
        verbose : bool, optional, default 'False'
            flag to display information about the process

        Returns
        -------
        An HTTP(s) response object
        """
        context = self.__get_tap_context("share")
        return self.__execute_post(context,
                                   data,
                                   content_type=CONTENT_TYPE_POST_DEFAULT,
                                   verbose=verbose)

    def execute_table_edit(self, data,
                           content_type=CONTENT_TYPE_POST_DEFAULT, *,
                           verbose=False):
        """Executes a POST upload request
        The connection is done through HTTP or HTTPS depending on the login
        status (logged in -> HTTPS)

        Parameters
        ----------
        data : str, mandatory
            POST data
        content_type: str, optional, default: application/x-www-form-urlencoded
            HTTP(s) content-type header value
        verbose : bool, optional, default 'False'
            flag to display information about the process

        Returns
        -------
        An HTTP(s) response object
        """
        context = self.__get_table_edit_context()
        return self.__execute_post(context, data, content_type, verbose=verbose)

    def execute_table_tool(self, data,
                           content_type=CONTENT_TYPE_POST_DEFAULT, *,
                           verbose=False):
        """Executes a POST upload request
        The connection is done through HTTP or HTTPS depending on the login
        status (logged in -> HTTPS)

        Parameters
        ----------
        data : str, mandatory
            POST data
        content_type: str, optional, default: application/x-www-form-urlencoded
            HTTP(s) content-type header value
        verbose : bool, optional, default 'False'
            flag to display information about the process

        Returns
        -------
        An HTTP(s) response object
        """
        context = self.__get_table_edit_context()
        return self.__execute_post(context, data, content_type, verbose=verbose)

    def __execute_post(self, context, data,
                       content_type=CONTENT_TYPE_POST_DEFAULT, *,
                       verbose=False):
        conn = self.__get_connection(verbose=verbose)
        if verbose:
            print(f"host = {conn.host}:{conn.port}")
            print(f"context = {context}")
            print(f"Content-type = {content_type}")
        self.__postHeaders["Content-type"] = content_type
        conn.request("POST", context, data, self.__postHeaders)
        response = conn.getresponse()
        self.__currentReason = response.reason
        self.__currentStatus = response.status
        return response

    def execute_secure(self, subcontext, data, *, verbose=False):
        """Executes a secure POST request
        The connection is done through HTTPS

        Parameters
        ----------
        subcontext : str, mandatory
            context to be added to host+serverContext+tapContext
        data : str, mandatory
            POST data
        verbose : bool, optional, default 'False'
            flag to display information about the process

        Returns
        -------
        An HTTPS response object
        """
        conn = self.__get_connection_secure(verbose=verbose)
        context = self.__get_server_context(subcontext)
        self.__postHeaders["Content-type"] = CONTENT_TYPE_POST_DEFAULT
        conn.request("POST", context, data, self.__postHeaders)
        response = conn.getresponse()
        self.__currentReason = response.reason
        self.__currentStatus = response.status
        return response

    def get_response_status(self):
        """Returns the latest connection status

        Returns
        -------
        The current (latest) HTTP(s) response status
        """
        return self.__currentStatus

    def get_response_reason(self):
        """Returns the latest connection reason (message)

        Returns
        -------
        The current (latest) HTTP(s) response reason
        """
        return self.__currentReason

    def find_header(self, headers, key):
        """Searches for the specified keyword

        Parameters
        ----------
        headers : HTTP(s) headers object, mandatory
            HTTP(s) response headers
        key : str, mandatory
            header key to be searched for

        Returns
        -------
        The requested header value or None if the header is not found
        """
        return taputils.taputil_find_header(headers, key)

    def dump_to_file(self, output, response):
        """Writes the connection response into the specified output

        Parameters
        ----------
        output : file, mandatory
            output file
        response : HTTP(s) response object, mandatory
            HTTP(s) response object
        """
        with open(output, "wb") as f:
            while True:
                data = response.read(4096)
                if len(data) < 1:
                    break
                f.write(data)
            f.close()

    def get_suitable_extension_by_format(self, output_format):
        """Returns the suitable extension for a file based on the output format

        Parameters
        ----------
        output_format : output format, mandatory

        Returns
        -------
        The suitable file extension based on the output format
        """
        if output_format is None:
            return ".vot"
        ext = ""
        outputFormat = output_format.lower()
        if "vot" in outputFormat:
            ext += ".vot"
        elif "xml" in outputFormat:
            ext += ".xml"
        elif "json" in outputFormat:
            ext += ".json"
        elif "plain" in outputFormat:
            ext += ".txt"
        elif "csv" in outputFormat:
            ext += ".csv"
        elif "ascii" in outputFormat:
            ext += ".ascii"
        return ext

    def get_suitable_extension(self, headers):
        """Returns the suitable extension for a file based on the headers
        received

        Parameters
        ----------
        headers : HTTP(s) response headers object, mandatory
            HTTP(s) response headers

        Returns
        -------
        The suitable file extension based on the HTTP(s) headers
        """
        if headers is None:
            return ""
        ext = ""
        contentType = self.find_header(headers, 'Content-Type')
        if contentType is not None:
            contentType = contentType.lower()
            if "xml" in contentType:
                ext += ".xml"
            elif "json" in contentType:
                ext += ".json"
            elif "plain" in contentType:
                ext += ".txt"
            elif "csv" in contentType:
                ext += ".csv"
            elif "ascii" in contentType:
                ext += ".ascii"
        contentEncoding = self.find_header(headers, 'Content-Encoding')
        if contentEncoding is not None:
            if "gzip" == contentEncoding.lower():
                ext += ".gz"
        return ext

    def get_file_from_header(self, headers):
        """Returns the file name returned in header Content-Disposition
        Usually, that header contains the following:
        Content-Disposition: attachment;filename="1591707060129DEV-aandres1591707060227.tar.gz"
        This method returns the value of 'filename'

        Parameters
        ----------
        headers: HTTP response headers list

        Returns
        -------
        The value of 'filename' in Content-Disposition header
        """
        content_disposition = self.find_header(headers, 'Content-Disposition')
        if content_disposition is not None:
            p = content_disposition.find('filename="')
            if p >= 0:
                filename = os.path.basename(content_disposition[p+10:len(content_disposition)-1])
                content_encoding = self.find_header(headers, 'Content-Encoding')

                if content_encoding is not None:
                    if not (filename.endswith('.gz') or filename.endswith('.zip')):
                        if "gzip" == content_encoding.lower():
                            filename += ".gz"
                        elif "zip" == content_encoding.lower():
                            filename += ".zip"

                return filename
        return None

    def set_cookie(self, cookie):
        """Sets the login cookie
        When a cookie is set, GET and POST requests are done using HTTPS

        Parameters
        ----------
        cookie : str, mandatory
            login cookie
        """
        self.__cookie = cookie
        self.__postHeaders['Cookie'] = cookie
        self.__getHeaders['Cookie'] = cookie

    def unset_cookie(self):
        """Removes the login cookie
        When a cookie is not set, GET and POST requests are done using HTTP
        """
        self.__cookie = None
        self.__postHeaders.pop('Cookie')
        self.__getHeaders.pop('Cookie')

    def get_host_url(self):
        """Returns the host+port+serverContext

        Returns
        -------
        A string composed of: 'host:port/server_context'
        """
        return f'{self.__connHost}:{self.__connPort}{self.__get_tap_context("")}'

    def get_host_url_secure(self):
        """Returns the host+portSsl+serverContext

        Returns
        -------
        A string composed of: 'host:portSsl/server_context'
        """
        return f'{self.__connHost}:{self.__connPortSsl}{self.__get_tap_context("")}'

    def check_launch_response_status(self, response, debug,
                                     expected_response_status, *,
                                     raise_exception=True):
        """Checks the response status code
        Returns True if the response status code is the
        expected_response_status argument

        Parameters
        ----------
        response : HTTP(s) response object, mandatory
            HTTP(s) response
        debug : bool, mandatory
            flag to display information about the process
        expected_response_status : int, mandatory
            expected response status code
        raise_exception : boolean, optional, default True
            if 'True' and the response status is not the
            expected one, an exception is raised.

        Returns
        -------
        'True' if the HTTP(s) response status is the provided
        'expected_response_status' argument
        """
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

    def __get_connection(self, *, verbose=False):
        return self.__connectionHandler.get_connection(ishttps=self.__isHttps,
                                                       cookie=self.__cookie,
                                                       verbose=verbose)

    def __get_connection_secure(self, *, verbose=False):
        return self.__connectionHandler.get_connection_secure(verbose=verbose)

    def encode_multipart(self, fields, files):
        """Encodes a multipart form request

        Parameters
        ----------
        fields : dictionary, mandatory
            dictionary with keywords and values
        files : array with key, filename and value, mandatory
            array with key, filename, value

        Returns
        -------
        The suitable content-type and the body for the request
        """
        timeMillis = int(round(time.time() * 1000))
        boundary = f'==={timeMillis}==='
        CRLF = '\r\n'
        multiparItems = []
        for key in fields:
            multiparItems.append(f'--{boundary}{CRLF}')
            multiparItems.append(
                f'Content-Disposition: form-data; name="{key}"{CRLF}')
            multiparItems.append(CRLF)
            multiparItems.append(f'{fields[key]}{CRLF}')
        for (key, filename, value) in files:
            multiparItems.append(f'--{boundary}{CRLF}')
            multiparItems.append(
                f'Content-Disposition: form-data; name="{key}"; filename="{filename}"{CRLF}')
            multiparItems.append(
                f'Content-Type: {mimetypes.guess_extension(filename)}{CRLF}')
            multiparItems.append(CRLF)
            multiparItems.append(value)
            multiparItems.append(CRLF)
        multiparItems.append(f'--{boundary}--{CRLF}')
        multiparItems.append(CRLF)
        body = utils.util_create_string_from_buffer(multiparItems)
        contentType = f'multipart/form-data; boundary={boundary}'
        return contentType, body.encode('utf-8')

    def __str__(self):
        return f"\tHost: {self.__connHost}\n\tUse HTTPS: {self.__isHttps}" \
            f"\n\tPort: {self.__connPort}\n\tSSL Port: {self.__connPortSsl}"


class ConnectionHandler:
    def __init__(self, host, port, sslport):
        self.__connHost = host
        self.__connPort = port
        self.__connPortSsl = sslport

    def get_connection(self, *, ishttps=False, cookie=None, verbose=False):
        if (ishttps) or (cookie is not None):
            if verbose:
                print("------>https")
            return self.get_connection_secure(verbose)
        else:
            if verbose:
                print("------>http")
            return httplib.HTTPConnection(self.__connHost, self.__connPort)

    def get_connection_secure(self, verbose):
        return httplib.HTTPSConnection(self.__connHost, self.__connPortSsl)
