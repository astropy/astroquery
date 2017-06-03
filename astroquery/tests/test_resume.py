import string
import os
import requests

import pytest
from .. import query

ACTIVE_HTTPBIN = os.getenv('ACTIVE_HTTPBIN') is not None


@pytest.mark.skipif('not ACTIVE_HTTPBIN')
def test_resume():
    # Test that a resumed query will finish

    length = 2048

    # 'range' will return abcd...xyz repeating
    target_url = 'http://127.0.0.1:5000/range/{0}'.format(length)

    # simple check: make sure the server does what's expected
    assert len(requests.get(target_url).content) == length

    qu = query.BaseQuery()

    result_1 = qu._request('GET', target_url, save=True)
    # now the full file is written, so we have to delete parts of it

    with open(result_1, 'rb') as fh:
        data = fh.read()
    with open(result_1, 'wb') as fh:
        # overwrite with a partial file
        fh.write(data[:1024])
    with open(result_1, 'rb') as fh:
        data = fh.read()
        assert len(data) == 1024

    result_2 = qu._request('GET', target_url, save=True, continuation=True)

    assert 'range' in qu._session.headers
    assert qu._session.headers['range'] == 'bytes={0}-{1}'.format(1024, length-1)

    with open(result_2, 'rb') as fh:
        data = fh.read()
    assert len(data) == length
    assert data == (string.ascii_lowercase*80)[:length].encode('ascii')
