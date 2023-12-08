# Licensed under a 3-clause BSD style license - see LICENSE.rst

import json
from functools import partial
from io import BytesIO


# The MockResponse class is currently relied upon in code and thus
# temporarily got moved here to avoid adding pytest as a
# mandatory dependency


class MockResponse:
    """
    A mocked/non-remote version of `astroquery.query.AstroResponse`
    """

    def __init__(self, content=None, *, url=None, headers=None, content_type=None,
                 stream=False, auth=None, status_code=200, verify=True,
                 allow_redirects=True, json=None):
        assert content is None or hasattr(content, 'decode')
        self.content = content
        self.raw = content
        self.headers = headers or {}
        if content_type is not None:
            self.headers.update({'Content-Type': content_type})
        self.url = url
        self.auth = auth
        self.status_code = status_code

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def iter_lines(self):
        content = self.content.split(b"\n")
        for line in content:
            yield line

    def iter_content(self, chunk_size):
        stream = BytesIO(self.content)
        return iter(partial(stream.read, chunk_size), b'')

    def raise_for_status(self):
        pass

    def json(self):
        try:
            return json.loads(self.content)
        except TypeError:
            return json.loads(self.content.decode('utf-8'))

    @property
    def text(self):
        return self.content.decode(errors='replace')
