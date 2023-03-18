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
