# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
=============
TAP plus
=============

"""
import ssl
import mimetypes
import time

from six.moves import http_client as httplib

from astroquery.utils.tap.xmlparser import utils
from astroquery.utils.tap.conn.tapconn import TapConn
from astroquery.utils.tap.conn.tapconn import ConnectionHandler

__all__ = ['TapConn']

CONTENT_TYPE_POST_DEFAULT = "application/x-www-form-urlencoded"


class TapConnCadc(TapConn):
    """TAP plus connection class
    Provides low level HTTP connection capabilities

    Notes
    -----------------
    Add functions to go to other places
    """
    def __init__(self, ishttps, host, server_context, tap_context=None,
                 port=80, sslport=443, connhandler=None):
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
        port : int, optional, default 80
            HTTP port
        sslport : int, optional, default 443
            HTTPS port
        connhandler connection handler object, optional, default None
            HTTP(s) connection hander (creator). If no handler is provided, a
            new one is created.

        Notes
        -----------------
        Make a ConnectionHandlerCadc instead of the original __init__ creating
        a ConnectionHandler object
        """
        if connhandler is None:
            connhandler = ConnectionHandlerCadc(host,
                                                port,
                                                sslport)
        super(TapConnCadc, self).__init__(ishttps, host, server_context,
                                          tap_context=tap_context, port=port,
                                          sslport=sslport,
                                          connhandler=connhandler)

    def execute_get_other(self, location, verbose=False):
        """Executes a GET request
        The connection is done through HTTP

        Parameters
        ----------
        location : str, mandatory
            URL to send the request to
        verbose : bool, optional, default 'False'
            flag to display information about the process

        Returns
        -------
        An HTTP response object
        Reason for adding
        -----------------
        Don't add a context onto the host url, send to a completly
        different url
        """
        conn = self._TapConn__get_connection(verbose)
        context = location

        conn.request("GET", context, None, self._TapConn__getHeaders)
        response = conn.getresponse()
        self.__currentReason = response.reason
        self.__currentStatus = response.status
        return response

    def execute_post_other(self, location, data,
                           content_type=CONTENT_TYPE_POST_DEFAULT,
                           verbose=False):
        """Executes a POST request
        The connection is done through HTTP or HTTPS depending on the login
        status (logged in -> HTTPS)
        Parameters
        ----------
        location : str, mandatory
            URL to send the request to
        data : str, mandatory
            POST data
        content_type: str, optional,
                      default 'application/x-www-form-urlencoded'
            HTTP(s) content-type header value
        verbose : bool, optional, default 'False'
            flag to display information about the process
        Returns
        -------
        An HTTP(s) response object
        Reason for adding
        -----------------
        Don't add a context onto the host url, send to a completly
        different url
        """
        conn = self._TapConn__get_connection(verbose)
        context = location
        self._TapConn__postHeaders["Content-type"] = content_type
        conn.request("POST", context, data, self._TapConn__postHeaders)
        response = conn.getresponse()
        self.__currentReason = response.reason
        self.__currentStatus = response.status
        return response

    def cookies_set(self):
        """Returns True if the Cookies are in the headers
        Reason for adding
        -----------------
        Check if the cookie is set in the headers
        """
        if 'Cookie' in self._TapConn__postHeaders:
            return True
        else:
            return False

    def encode_multipart(self, fields, files):
        """Encodes a multipart form request (not using '=' in boundary)
        Parameters
        ----------
        fields : dictionary, mandatory
            dictionary with keywords and values
        files : array with key, filename and value, mandatory
            array with key, filename, value
        Returns
        -------
        The suitable content-type and the body for the request

        Notes
        -----------------
        In boundary use * instead of =, async processor complains if it has =
        """
        timeMillis = int(round(time.time() * 1000))
        boundary = '***%s***' % str(timeMillis)
        CRLF = '\r\n'
        multiparItems = []
        for key in fields:
            multiparItems.append('--' + boundary + CRLF)
            multiparItems.append(
                'Content-Disposition: form-data; name="%s"%s' % (key, CRLF))
            multiparItems.append(CRLF)
            multiparItems.append(fields[key]+CRLF)
        for (key, filename, value) in files:
            multiparItems.append('--' + boundary + CRLF)
            multiparItems.append(
                'Content-Disposition: form-data; name="%s"; filename="%s"%s' %
                (key, filename, CRLF))
            multiparItems.append(
                'Content-Type: %s%s' %
                (mimetypes.guess_extension(filename), CRLF))
            multiparItems.append(CRLF)
            multiparItems.append(value)
            multiparItems.append(CRLF)
        multiparItems.append('--' + boundary + '--' + CRLF)
        multiparItems.append(CRLF)
        body = utils.util_create_string_from_buffer(multiparItems)
        contentType = 'multipart/form-data; boundary=%s' % boundary
        return contentType, body


class ConnectionHandlerCadc(ConnectionHandler):
    def __init__(self, host, port, sslport):
        """
        Notes
        -----------------
        Add a certificate variable
        """
        super(ConnectionHandlerCadc, self).__init__(host, port, sslport)
        self.__certificate = None

    def get_connection(self, ishttps=False, cookie=None, verbose=False):
        """
        Notes
        -----------------
        If using certificates get secure not if using cookies
        """
        if self.__certificate is not None:
            if verbose:
                print("------>Cert")
            return self.get_connection_secure(verbose)
        else:
            if verbose:
                print("------>Cookie")
            return httplib.HTTPSConnection(self._ConnectionHandler__connHost,
                                           self._ConnectionHandler__connPort)

    def get_connection_secure(self, verbose):
        """
        Notes
        -----------------
        Add certificate to connection
        """
        # Prepare the certificate
        context = ssl.create_default_context()
        if self.__certificate:
            context.load_cert_chain(self.__certificate)
        return httplib.HTTPSConnection(self._ConnectionHandler__connHost,
                                       self._ConnectionHandler__connPortSsl,
                                       context=context)
