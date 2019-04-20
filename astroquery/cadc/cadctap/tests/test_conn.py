# Licensed under a 3-clause BSD style license - see LICENSE.rst

import unittest
import os

from astroquery.cadc.cadctap.tapconn import TapConnCadc
from astroquery.utils.tap.conn.tests.DummyConn import DummyConn


def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)


class ConnTestCadc(unittest.TestCase):

    def test_get_other(self):
        conn = DummyConn("http")
        conn.response.status = 222
        host = "testHost"
        serverContext = "testServerContext"
        tapContext = "testTapContext"
        connPort = 90
        connPortSsl = 943
        # TapConn
        tap = TapConnCadc(ishttps=False,
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
            "Tap host secure. Expected %s, found %s" % (
                hostUrlSecure,
                tap.get_host_url_secure())
        # GET
        location = "http://host.ca/tap"
        r = tap.execute_get_other(location)
        assert r.status == 222, \
            "Status code, expected: %d, found: %d" % (222, r.status)
        assert r.get_method() == 'GET', \
            "Request method. Expected %s, found %s" % ('GET', r.get_method())
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
        tap = TapConnCadc(ishttps=False,
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
            "Tap host secure. Expected %s, found %s" % (
                hostUrlSecure,
                tap.get_host_url_secure())
        # GET
        location = "http://test.ca/tap"
        data = "postData"
        r = tap.execute_post_other(location, data=data)
        assert r.status == 111, \
            "Status code, expected: %d, found: %d" % (111, r.status)
        assert r.get_method() == 'POST', \
            "Request method. Expected %s, found %s" % ('POST', r.get_method())
        assert r.get_body() == data, \
            "Request body. Expected %s, found %s" % (data, str(r.get_body()))


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
