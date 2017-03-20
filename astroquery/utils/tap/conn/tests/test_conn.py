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
import unittest
import os

from astroquery.utils.tap.conn.tapconn import TapConn
from astroquery.utils.tap.conn.tests.DummyConn import DummyConn


def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)


class ConnTest(unittest.TestCase):

    def test_get(self):
        conn = DummyConn("http")
        conn.response.status = 222
        host = "testHost"
        serverContext = "testServerContext"
        tapContext = "testTapContext"
        connPort = 90
        connPortSsl = 943
        # TapConn
        tap = TapConn(ishttps=False,
                      host=host,
                      server_context=serverContext,
                      tap_context=tapContext,
                      port=connPort,
                      sslport=connPortSsl,
                      connhandler=conn)
        hostUrl = host + ":" + str(connPort) + "/" + serverContext + "/" \
            + tapContext + "/"
        assert tap.get_host_url() == hostUrl, \
            "Tap host. Expected %s, found %s" % (hostUrl, tap.get_host_url())
        hostUrlSecure = host + ":" + str(connPortSsl) + "/" + serverContext \
            + "/" + tapContext + "/"
        assert tap.get_host_url_secure() == hostUrlSecure, \
            "Tap host secure. Expected %s, found %s" % (hostUrlSecure,
                                                        tap.get_host_url_secure())
        # GET
        subContext = "testSubContextGet"
        context = "/" + serverContext + "/" + tapContext + "/" + subContext
        r = tap.execute_get(subcontext=subContext)
        assert r.status == 222, \
            "Status code, expected: %d, found: %d" % (222, r.status)
        assert r.get_method() == 'GET', \
            "Request method. Expected %s, found %s" % ('GET', r.get_method())
        assert r.get_context() == context, \
            "Request context. Expected %s, found %s" % (context, r.get_context())
        assert r.get_body() is None, \
            "Request body. Expected %s, found %s" % ('None', str(r.get_body()))

    def test_post(self):
        conn = DummyConn('http')
        conn.response.status = 111
        host = "testHost"
        serverContext = "testServerContext"
        tapContext = "testTapContext"
        connPort = 90
        connPortSsl = 943
        # TapConn
        tap = TapConn(ishttps=False,
                      host=host,
                      server_context=serverContext,
                      tap_context=tapContext,
                      port=connPort,
                      sslport=connPortSsl,
                      connhandler=conn)
        hostUrl = host + ":" + str(connPort) + "/" + serverContext + "/" \
            + tapContext + "/"
        assert tap.get_host_url() == hostUrl, \
            "Tap host. Expected %s, found %s" % (hostUrl, tap.get_host_url())
        hostUrlSecure = host + ":" + str(connPortSsl) + "/" + serverContext \
            + "/" + tapContext + "/"
        assert tap.get_host_url_secure() == hostUrlSecure, \
            "Tap host secure. Expected %s, found %s" % (hostUrlSecure,
                                                        tap.get_host_url_secure())
        # GET
        subContext = "testSubContextGet"
        context = "/" + serverContext + "/" + tapContext + "/" + subContext
        data = "postData"
        r = tap.execute_post(subcontext=subContext, data=data)
        assert r.status == 111, \
            "Status code, expected: %d, found: %d" % (111, r.status)
        assert r.get_method() == 'POST', \
            "Request method. Expected %s, found %s" % ('POST', r.get_method())
        assert r.get_context() == context, \
            "Request context. Expected %s, found %s" % (context, r.get_context())
        assert r.get_body() == data, \
            "Request body. Expected %s, found %s" % (data, str(r.get_body()))

    def test_login(self):
        connSecure = DummyConn("https")
        connSecure.response.status = 333
        host = "testHost"
        serverContext = "testServerContext"
        tapContext = "testTapContext"
        connPort = 90
        connPortSsl = 943
        # TapConn
        tap = TapConn(ishttps=False,
                      host=host,
                      server_context=serverContext,
                      tap_context=tapContext,
                      port=connPort,
                      sslport=connPortSsl,
                      connhandler=connSecure)
        hostUrl = host + ":" + str(connPort) + "/" + serverContext + "/" \
            + tapContext + "/"
        assert tap.get_host_url() == hostUrl, \
            "Tap host. Expected %s, found %s" % (hostUrl, tap.get_host_url())
        hostUrlSecure = host + ":" + str(connPortSsl) + "/" + serverContext \
            + "/" + tapContext + "/"
        assert tap.get_host_url_secure() == hostUrlSecure, \
            "Tap host secure. Expected %s, found %s" % (hostUrlSecure,
                                                        tap.get_host_url_secure())
        # POST SECURE
        subContext = "testSubContextPost"
        context = "/" + serverContext + "/" + subContext
        data = "testData"
        r = tap.execute_secure(subcontext=subContext, data=data)
        assert r.status == 333, \
            "Status code, expected: %d, found: %d" % (333, r.status)
        assert r.get_method() == 'POST', \
            "Request method. Expected %s, found %s" % ('POST', r.get_method())
        assert r.get_context() == context, \
            "Request context. Expected %s, found %s" % (context, r.get_context())
        assert r.get_body() == data, \
            "Request body. Expected %s, found %s" % (data, str(r.get_body()))
