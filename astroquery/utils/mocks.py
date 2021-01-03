# Licensed under a 3-clause BSD style license - see LICENSE.rst

import json

# The MockResponse class is currently relied upon in code and thus
# temporarily got moved out of testing_tools to avoid adding pytest as a
# mandatory dependency


class MockResponse:
    """
    A mocked/non-remote version of `astroquery.query.AstroResponse`
    """

    def __init__(self, content=None, url=None, headers={}, content_type=None,
                 stream=False, auth=None, status_code=200, verify=True,
                 allow_redirects=True, json=None):
        assert content is None or hasattr(content, 'decode')
        self.content = content
        self.raw = content
        self.headers = headers
        if content_type is not None:
            self.headers.update({'Content-Type': content_type})
        self.url = url
        self.auth = auth
        self.status_code = status_code

    def iter_lines(self):
        c = self.content.split(b"\n")
        for l in c:
            yield l

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
