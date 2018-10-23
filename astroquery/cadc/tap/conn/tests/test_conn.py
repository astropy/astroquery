# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
=============
TAP plus
=============

"""
import unittest
import os
import time

from astroquery.cadc import auth
from astroquery.cadc.tap.conn.tapconn import TapConn
from astroquery.cadc.tap.conn.tests.DummyConn import DummyConn

def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)

class ConnTest(unittest.TestCase):
    def test_get_anon(self):
        anon = auth.AnonAuthMethod()
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
        r = tap.execute_get(subcontext=subContext, authentication=anon)
        assert r.status == 222, \
            "Status code, expected: %d, found: %d" % (222, r.status)
        assert r.get_method() == 'GET', \
            "Request method. Expected %s, found %s" % ('GET', r.get_method())
        assert r.get_context() == context, \
            "Request context. Expected %s, found %s" % (context, r.get_context())
        assert r.get_body() is None, \
            "Request body. Expected %s, found %s" % ('None', str(r.get_body()))

    def test_get_netrc(self):
        netrc = auth.NetrcAuthMethod(filename=data_path('netrc'))
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
        r = tap.execute_get(subcontext=subContext, authentication=netrc)
        assert r.status == 222, \
            "Status code, expected: %d, found: %d" % (222, r.status)
        assert r.get_method() == 'GET', \
            "Request method. Expected %s, found %s" % ('GET', r.get_method())
        assert r.get_context() == context, \
            "Request context. Expected %s, found %s" % (context, r.get_context())
        assert r.get_body() is None, \
            "Request body. Expected %s, found %s" % ('None', str(r.get_body()))

    def test_get_secure(self):
        cert = auth.CertAuthMethod(certificate=data_path('certificate.pem'))
        conn = DummyConn("https")
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
        r = tap.execute_get_secure(subcontext=subContext, authentication=cert)
        assert r.status == 222, \
            "Status code, expected: %d, found: %d" % (222, r.status)
        assert r.get_method() == 'GET', \
            "Request method. Expected %s, found %s" % ('GET', r.get_method())
        assert r.get_context() == context, \
            "Request context. Expected %s, found %s" % (context, r.get_context())
        assert r.get_body() is None, \
            "Request body. Expected %s, found %s" % ('None', str(r.get_body()))

    def test_post_anon(self):
        anon = auth.AnonAuthMethod()
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
        r = tap.execute_post(subcontext=subContext, data=data, authentication=anon)
        assert r.status == 111, \
            "Status code, expected: %d, found: %d" % (111, r.status)
        assert r.get_method() == 'POST', \
            "Request method. Expected %s, found %s" % ('POST', r.get_method())
        assert r.get_context() == context, \
            "Request context. Expected %s, found %s" % (context, r.get_context())
        assert r.get_body() == data, \
            "Request body. Expected %s, found %s" % (data, str(r.get_body()))

    def test_post_netrc(self):
        netrc = auth.NetrcAuthMethod(filename=data_path('netrc'))
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
        r = tap.execute_post(subcontext=subContext, data=data, authentication=netrc)
        assert r.status == 111, \
            "Status code, expected: %d, found: %d" % (111, r.status)
        assert r.get_method() == 'POST', \
            "Request method. Expected %s, found %s" % ('POST', r.get_method())
        assert r.get_context() == context, \
            "Request context. Expected %s, found %s" % (context, r.get_context())
        assert r.get_body() == data, \
            "Request body. Expected %s, found %s" % (data, str(r.get_body()))


    def test_post_secure(self):
        cert = auth.CertAuthMethod(certificate=data_path('certificate.pem'))
        conn = DummyConn('https')
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
        r = tap.execute_post_secure(subcontext=subContext, data=data, authentication=cert)
        assert r.status == 111, \
            "Status code, expected: %d, found: %d" % (111, r.status)
        assert r.get_method() == 'POST', \
            "Request method. Expected %s, found %s" % ('POST', r.get_method())
        assert r.get_context() == context, \
            "Request context. Expected %s, found %s" % (context, r.get_context())
        assert r.get_body() == data, \
            "Request body. Expected %s, found %s" % (data, str(r.get_body()))

    def test_check_launch_response_status(self):
        conn = DummyConn('http')
        conn.response.status = 200
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
        status = tap.check_launch_response_status(conn.response, 
                                                  False,
                                                  200)
        assert status == False, \
            "Status code, expected: %d, found: %d" % (200, conn.response.status)
       
    def test_encode_multipart(self):
        conn = DummyConn('http')
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
        args = {'REQUEST': 'doQuery', 'LANG': 'ADQL', 'FORMAT': 'votable', 'tapclient': 'aqtappy-1.0.1', 'QUERY': 'SELECT  TOP 2000 * FROM tap_upload.test_table_upload', 'UPLOAD': 'test_table_upload,param:test_table_upload'}
        files = [['test_table_upload', 'data/test.txt', 'testing encoding\n']]

        timeMillis = int(round(time.time() * 1000))
        boundary = '***%s***' % str(timeMillis)
        contentType = "multipart/form-data; boundary=" + boundary          
        body = '--' + boundary + '\
        Content-Disposition: form-data; name="REQUEST"\n\
        doQuery\
        --' + boundary + '\
        Content-Disposition: form-data; name="LANG"\n\
        ADQL\
        --' + boundary + '\
        Content-Disposition: form-data; name="FORMAT"\n\
        votable\
        --' + boundary + '\
        Content-Disposition: form-data; name="tapclient"\n\
        aqtappy-1.0.1\
        --' + boundary + '\
        Content-Disposition: form-data; name="QUERY"\n\
        SELECT  TOP 2000 * FROM tap_upload.test_table_upload\
        --' + boundary + '\
        Content-Disposition: form-data; name="UPLOAD"\n\
        test_table_upload,param:test_table_upload\
        --' + boundary + '\
        Content-Disposition: form-data; name="test_table_upload"; filename="data/test.txt"\
        Content-Type: None\n\
        testing encoding\n\
        --' + boundary + '--' 

        timeMillis = timeMillis + 1
        boundary = '***%s***' % str(timeMillis)
        contentTypeSecond = "multipart/form-data; boundary=" + boundary
        bodySecond = '--' + boundary + '\
        Content-Disposition: form-data; name="REQUEST"\n\
        doQuery\
        --' + boundary + '\
        Content-Disposition: form-data; name="LANG"\n\
        ADQL\
        --' + boundary + '\
        Content-Disposition: form-data; name="FORMAT"\n\
        votable\
        --' + boundary + '\
        Content-Disposition: form-data; name="tapclient"\n\
        aqtappy-1.0.1\
        --' + boundary + '\
        Content-Disposition: form-data; name="QUERY"\n\
        SELECT  TOP 2000 * FROM tap_upload.test_table_upload\
        --' + boundary + '\
        Content-Disposition: form-data; name="UPLOAD"\n\
        test_table_upload,param:test_table_upload\
        --' + boundary + '\
        Content-Disposition: form-data; name="test_table_upload"; filename="data/test.txt"\
        Content-Type: None\n\
        testing encoding\n\
        --' + boundary + '--'

        contentTypeTest, bodyTest = tap.encode_multipart(args, files)
        assert contentTypeTest == contentType or contentTypeTest == contentTypeSecond, \
            "ContentType, expected: %s, founds: %s" % (contentType, contentTypeTest)
        sbodyTest = ' '.join(bodyTest.split())
        sbody = ' '.join(body.split())
        sbodySecond = ' '.join(bodySecond.split())
        assert sbodyTest == sbody or sbodyTest == sbodySecond, \
            "Body, expected:\n %s,\n\n\n\n found:\n %s" % (sbody, sbodyTest)

if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
