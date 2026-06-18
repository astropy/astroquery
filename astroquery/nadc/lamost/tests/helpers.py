# Licensed under a 3-clause BSD style license - see LICENSE.rst

import json
from pathlib import Path
from unittest.mock import Mock

from requests import HTTPError


LAMOST_TOKEN_ENV_VARS = (
    "ASTROQUERY_LAMOST_TOKEN",
    "ASTROQUERY_NADC_LAMOST_TOKEN",
    "NADC_LAMOST_TOKEN",
    "CHINAVO_LAMOST_TOKEN",
    "ASTROQUERY_LAMOST_ACCESS_TOKEN",
    "ASTROQUERY_NADC_LAMOST_ACCESS_TOKEN",
    "NADC_LAMOST_ACCESS_TOKEN",
    "CHINAVO_LAMOST_ACCESS_TOKEN",
    "ASTROQUERY_NADC_TOKEN",
    "NADC_QUERYDATA_TOKEN",
    "ASTROQUERY_NADC_ACCESS_TOKEN",
    "NADC_QUERYDATA_ACCESS_TOKEN",
    "ASTROQUERY_CHINAVO_TOKEN",
    "CHINAVO_QUERYDATA_TOKEN",
    "ASTROQUERY_CHINAVO_ACCESS_TOKEN",
    "CHINAVO_QUERYDATA_ACCESS_TOKEN",
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
                         headers=None, json_data=None):
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

    response_content = content or b''

    if isinstance(response_content, bytes):
        response_text = response_content.decode('utf-8', errors='replace')
    else:
        response_text = str(response_content)

    response = Mock(spec=[
        'status_code', 'ok', 'headers', 'content', 'text', 'json',
        'iter_content', 'raise_for_status'
    ])
    response.status_code = status_code
    response.ok = status_code < 400
    response.headers = response_headers
    response.content = response_content
    response.text = response_text

    def json_method():
        return json.loads(response_content)
    response.json = json_method

    def iter_content(chunk_size=8192):
        data = response_content
        for i in range(0, len(data), chunk_size):
            yield data[i:i+chunk_size]
    response.iter_content = iter_content

    def raise_for_status():
        if status_code >= 400:
            raise HTTPError(f"{status_code} mock response", response=response)
    response.raise_for_status = raise_for_status

    return response
