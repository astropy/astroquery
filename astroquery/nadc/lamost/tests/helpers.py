# Licensed under a 3-clause BSD style license - see LICENSE.rst

import json
from pathlib import Path
from unittest.mock import Mock

from requests import Request, Response


DATA = Path(__file__).parent / 'data'

LAMOST_TOKEN_ENV_VARS = (
    "ASTROQUERY_LAMOST_TOKEN",
    "ASTROQUERY_NADC_LAMOST_TOKEN",
    "NADC_LAMOST_TOKEN",
    "CHINAVO_LAMOST_TOKEN",
    "ASTROQUERY_LAMOST_ACCESS_TOKEN",
    "ASTROQUERY_NADC_LAMOST_ACCESS_TOKEN",
    "NADC_LAMOST_ACCESS_TOKEN",
    "CHINAVO_LAMOST_ACCESS_TOKEN",
)


def _home_env_values(path):
    path = Path(path)
    return {
        'HOME': str(path),
        'USERPROFILE': str(path),
        'HOMEDRIVE': path.drive,
        'HOMEPATH': str(path)[len(path.drive):] if path.drive else str(path),
    }


def set_mock_home(monkeypatch, path):
    """
    Set all common home-directory environment variables to a temporary path.
    """
    for name, value in _home_env_values(path).items():
        monkeypatch.setenv(name, value)


def create_mock_response(content=None, status_code=200, content_type='text/plain',
                         headers=None, json_data=None, url='https://example.invalid/lamost'):
    """
    Create a mock HTTP response object compatible with requests.Response.
    """
    response_headers = {
        'Content-Type': content_type
    }
    if headers:
        response_headers.update(headers)

    if json_data is not None:
        content = json.dumps(json_data).encode('utf-8')
        response_headers['Content-Type'] = 'application/json'

    response = Response()
    response.status_code = status_code
    response.headers.update(response_headers)
    response._content = content.encode('utf-8') if isinstance(content, str) else content or b''
    response._content_consumed = True
    response.request = Request('GET', url).prepare()
    response.url = response.request.url
    response.reason = 'mock response'
    response.close = Mock(wraps=response.close)

    return response
