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
import os

from astroquery.utils.tap.conn.tapconn import TapConn
from astroquery.utils.tap.conn.tests.DummyConn import DummyConn


def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)


def test_get():
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
    hostUrl = f"{host}:{connPort}/{serverContext}/{tapContext}/"
    assert tap.get_host_url() == hostUrl
    hostUrlSecure = f"{host}:{connPortSsl}/{serverContext}/{tapContext}/"
    assert tap.get_host_url_secure() == hostUrlSecure
    # GET
    subContext = "testSubContextGet"
    context = f"/{serverContext}/{tapContext}/{subContext}"
    r = tap.execute_tapget(subcontext=subContext, verbose=False)
    assert r.status == 222
    assert r.get_method() == 'GET'
    assert r.get_context() == context
    assert r.get_body() is None


def test_post():
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
    hostUrl = f"{host}:{connPort}/{serverContext}/{tapContext}/"
    assert tap.get_host_url() == hostUrl
    hostUrlSecure = f"{host}:{connPortSsl}/{serverContext}/{tapContext}/"
    assert tap.get_host_url_secure() == hostUrlSecure
    # GET
    subContext = "testSubContextGet"
    context = f"/{serverContext}/{tapContext}/{subContext}"
    data = "postData"
    r = tap.execute_tappost(subcontext=subContext, data=data, verbose=False)
    assert r.status == 111
    assert r.get_method() == 'POST'
    assert r.get_context() == context
    assert r.get_body() == data


def test_login():
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
    hostUrl = f"{host}:{connPort}/{serverContext}/{tapContext}/"
    assert tap.get_host_url() == hostUrl
    hostUrlSecure = f"{host}:{connPortSsl}/{serverContext}/{tapContext}/"
    assert tap.get_host_url_secure() == hostUrlSecure
    # POST SECURE
    subContext = "testSubContextPost"
    context = f"/{serverContext}/{subContext}"
    data = "testData"
    r = tap.execute_secure(subcontext=subContext, data=data, verbose=False)
    assert r.status == 333
    assert r.get_method() == 'POST'
    assert r.get_context() == context
    assert r.get_body() == data


def test_find_header():
    host = "testHost"
    tap = TapConn(ishttps=False, host=host)

    headers = [('Date', 'Sat, 12 Apr 2025 05:10:47 GMT'),
               ('Server', 'Apache/2.4.6 (Red Hat Enterprise Linux) OpenSSL/1.0.2k-fips mod_jk/1.2.43'),
               ('Set-Cookie', 'JSESSIONID=E677B51BA5C4837347D1E17D4E36647E; Path=/data-server; Secure; HttpOnly'),
               ('X-Content-Type-Options', 'nosniff'), ('X-XSS-Protection', '0'),
               ('Cache-Control', 'no-cache, no-store, max-age=0, must-revalidate'), ('Pragma', 'no-cache'),
               ('Expires', '0'), ('X-Frame-Options', 'SAMEORIGIN'),
               ('Set-Cookie', 'SESSION=ZjQ3MjIzMDAt; Path=/data-server; Secure; HttpOnly; SameSite=Lax'),
               ('Transfer-Encoding', 'chunked'), ('Content-Type', 'text/plain; charset=UTF-8')]
    key = 'Set-Cookie'
    result = tap.find_header(headers, key)

    assert (result == "JSESSIONID=E677B51BA5C4837347D1E17D4E36647E; Path=/data-server; Secure; HttpOnly")


def test_find_all_headers():
    host = "testHost"
    tap = TapConn(ishttps=False, host=host)

    headers = [('Date', 'Sat, 12 Apr 2025 05:10:47 GMT'),
               ('Server', 'Apache/2.4.6 (Red Hat Enterprise Linux) OpenSSL/1.0.2k-fips mod_jk/1.2.43'),
               ('Set-Cookie', 'JSESSIONID=E677B51BA5C4837347D1E17D4E36647E; Path=/data-server; Secure; HttpOnly'),
               ('X-Content-Type-Options', 'nosniff'), ('X-XSS-Protection', '0'),
               ('Cache-Control', 'no-cache, no-store, max-age=0, must-revalidate'), ('Pragma', 'no-cache'),
               ('Expires', '0'), ('X-Frame-Options', 'SAMEORIGIN'),
               ('Set-Cookie', 'SESSION=ZjQ3MjIzMDAtNjNiYy00Mj; Path=/data-server; Secure; HttpOnly; SameSite=Lax'),
               ('Transfer-Encoding', 'chunked'), ('Content-Type', 'text/plain; charset=UTF-8')]
    key = 'Set-Cookie'
    result = tap.find_all_headers(headers, key)

    assert (result[0] == "JSESSIONID=E677B51BA5C4837347D1E17D4E36647E; Path=/data-server; Secure; HttpOnly")
    assert (result[1] == "SESSION=ZjQ3MjIzMDAtNjNiYy00Mj; Path=/data-server; Secure; HttpOnly; SameSite=Lax")


def test_get_file_from_header():
    host = "testHost"
    tap = TapConn(ishttps=False, host=host)

    headers = [('Date', 'Sat, 12 Apr 2025 05:10:47 GMT'),
               ('Server', 'Apache/2.4.6 (Red Hat Enterprise Linux) OpenSSL/1.0.2k-fips mod_jk/1.2.43'),
               ('Set-Cookie', 'JSESSIONID=E677B51BA5C4837347D1E17D4E36647E; Path=/data-server; Secure; HttpOnly'),
               ('X-Content-Type-Options', 'nosniff'), ('X-XSS-Protection', '0'),
               ('Cache-Control', 'no-cache, no-store, max-age=0, must-revalidate'), ('Pragma', 'no-cache'),
               ('Expires', '0'), ('X-Frame-Options', 'SAMEORIGIN'),
               ('Set-Cookie', 'SESSION=ZjQ3MjIzMDAtNjNiYy00Mj; Path=/data-server; Secure; HttpOnly; SameSite=Lax'),
               ('Transfer-Encoding', 'chunked'), ('Content-Type', 'text/plain; charset=UTF-8'),
               ('Content-Disposition', 'filename="my_file.vot.gz"'), ('Content-Encoding', "gzip")]

    result = tap.get_file_from_header(headers)

    assert (result == "my_file.vot.gz")
