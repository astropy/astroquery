# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""Internal authentication, error and query helpers for LAMOST."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from html.parser import HTMLParser
import json
import os
import re
from typing import Any, Optional
from urllib.parse import urlsplit

from ._response_utils import response_looks_like_html


def _strip_optional_quotes(value: str) -> str:
    value = str(value).strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def _configured_token_from_env(env_var_names: Iterable[str]) -> Optional[str]:
    for env_name in env_var_names:
        env_value = os.environ.get(env_name)
        if env_value:
            token = _strip_optional_quotes(env_value)
            if token:
                return token
    return None


def _response_json_payload(response) -> Optional[Mapping[str, Any]]:
    content = getattr(response, "_content", None)
    if content is False:
        # Never materialize an unconsumed download, even if labeled JSON.
        return None
    content_type = (response.headers.get("Content-Type") or "").lower()
    if "json" not in content_type:
        if content is None:
            content = getattr(response, "content", None)
        if (not isinstance(content, bytes)
                or not content.removeprefix(b'\xef\xbb\xbf').lstrip().startswith((b'{', b'['))):
            return None

    try:
        data = response.json()
    except Exception:
        return None

    return data if isinstance(data, Mapping) else None


class _LoginRedirectParser(HTMLParser):
    url = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag != 'meta' or (attrs.get('http-equiv') or '').strip().lower() != 'refresh':
            return
        match = re.fullmatch(r'\s*\d+(?:\.\d+)?\s*;\s*url\s*=\s*(.*?)\s*',
                             attrs.get('content') or '', flags=re.IGNORECASE)
        if match:
            target = _strip_optional_quotes(match[1])
            try:
                parsed = urlsplit(target)
            except ValueError:
                return
            if parsed.scheme in {'https', 'http'} and parsed.hostname == 'oauth.china-vo.org':
                self.url = target


def _oauth_redirect_url(response, *, include_body=False) -> Optional[str]:
    candidates = []
    for item in [*list(getattr(response, "history", ()) or ()), response]:
        candidates.append(getattr(item, "url", None))
        headers = getattr(item, "headers", {}) or {}
        if isinstance(headers, Mapping):
            candidates.append(headers.get("Location"))

    for candidate in candidates:
        if not candidate:
            continue
        hostname = (urlsplit(str(candidate)).hostname or "").lower()
        if hostname == "oauth.china-vo.org" or hostname.startswith("oauth."):
            return str(candidate)
    if include_body and isinstance(getattr(response, '_content', None), bytes) and response_looks_like_html(response):
        parser = _LoginRedirectParser()
        parser.feed(response.content.decode('utf-8-sig', 'replace'))
        return parser.url
    return None


def _successful_response_error(response) -> Optional[str]:
    data = _response_json_payload(response)
    if data is None:
        return None

    success_keys = {"data", "rows", "tables", "columns", "sqlid", "sql_id", "jobid", "job_id"}
    if "error" in data or "error_code" in data:
        return _api_error_summary(response)
    if success_keys.isdisjoint(data) and "detail" in data:
        return _api_error_summary(response)
    status = str(data.get("status") or "").strip().lower()
    if success_keys.isdisjoint(data) and "message" in data and status in {"error", "failed", "failure"}:
        return _api_error_summary(response)
    return None


def _stringify_error_value(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, str):
        text = value.strip()
        return text or None
    if isinstance(value, Mapping):
        try:
            return json.dumps(value, ensure_ascii=False, sort_keys=True)
        except TypeError:
            return str(value)
    if isinstance(value, (list, tuple)):
        try:
            return json.dumps(value, ensure_ascii=False)
        except TypeError:
            return str(value)
    return str(value)


def _api_error_summary(response, *, preview_limit: int = 240) -> Optional[str]:
    if getattr(response, '_content', None) is False:
        return None
    data = _response_json_payload(response)
    if data is not None:
        label = (
            _stringify_error_value(data.get("error"))
            or _stringify_error_value(data.get("error_code"))
            or "api_error"
        )
        message = (
            _stringify_error_value(data.get("message"))
            or _stringify_error_value(data.get("detail"))
            or _stringify_error_value(data.get("description"))
        )
        if label and message:
            return f"{label}: {message}"
        return label or message

    text = (response.text or "").strip()
    if text:
        preview = " ".join(text.split())
        if len(preview) > preview_limit:
            preview = preview[:preview_limit] + " ..."
        return preview

    return None
