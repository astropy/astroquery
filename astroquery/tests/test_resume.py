import string
import os
import requests

import pytest
from .. import query

ACTIVE_HTTPBIN = os.getenv('ACTIVE_HTTPBIN') is not None


@pytest.mark.skipif('not ACTIVE_HTTPBIN')
def test_resume(length=2048, partial_length=1024, qu=None):
    # Test that a resumed query will finish

    # 'range' will return abcd...xyz repeating
    target_url = 'http://127.0.0.1:5000/range/{0}'.format(length)

    # simple check: make sure the server does what's expected
    assert len(requests.get(target_url).content) == length

    if qu is None:
        qu = query.BaseQuery()

    result_1 = qu._request('GET', target_url, save=True)
    # now the full file is written, so we have to delete parts of it

    with open(result_1, 'rb') as fh:
        data = fh.read()
    with open(result_1, 'wb') as fh:
        # overwrite with a partial file
        fh.write(data[:partial_length])
    with open(result_1, 'rb') as fh:
        data = fh.read()
        assert len(data) == partial_length

    result_2, response = qu._request('GET', target_url, save=True, continuation=True,
                                     return_response_on_save=True)

    assert 'content-range' in response.headers
    assert response.headers['content-range'] == 'bytes {0}-{1}/{2}'.format(
        partial_length, length-1, length
    )

    with open(result_2, 'rb') as fh:
        data = fh.read()
    assert len(data) == length
    assert data == (string.ascii_lowercase*(length//26+1))[:length].encode('ascii')


@pytest.mark.skipif('not ACTIVE_HTTPBIN')
def test_resume_consecutive():
    # Test that consecutive resumed queries request the correct content range and finish
    qu = query.BaseQuery()

    test_resume(length=2048, partial_length=1024, qu=qu)
    test_resume(length=2048, partial_length=512, qu=qu)
