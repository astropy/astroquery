# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
Shared response parsing helpers for NADC service modules.
"""

from __future__ import annotations

import re


_FIELD_WITHOUT_DATATYPE_RE = re.compile(rb"<FIELD\s+([^>]*?)></FIELD>", re.IGNORECASE)
_EMPTY_ARRAYSIZE_RE = re.compile(rb'arraysize=""', re.IGNORECASE)
_ZERO_ARRAYSIZE_RE = re.compile(rb'\s+arraysize="0"', re.IGNORECASE)


def response_looks_like_html(response) -> bool:
    """Heuristically detect HTML returned in place of data.

    Parameters
    ----------
    response : requests.Response
        HTTP response object to inspect.

    Returns
    -------
    bool
        `True` when the response content type or leading bytes look like an
        HTML document.
    """
    content_type = (response.headers.get("Content-Type") or "").lower()
    if "text/html" in content_type:
        return True

    prefix = response.content[:256].decode("utf-8", "ignore").lstrip().lower()
    return prefix.startswith(("<!doctype html", "<html"))


def sanitize_votable_content(
    content: bytes,
    *,
    fix_invalid_date: bool = False,
    fix_missing_field_datatype: bool = False,
    fix_empty_arraysize: bool = False,
) -> bytes:
    """Repair common NADC VOTable schema issues before parsing.

    Parameters
    ----------
    content : bytes
        Raw VOTable response bytes.
    fix_invalid_date : bool, optional
        Convert unsupported ``datatype="date"`` fields to character fields.
    fix_missing_field_datatype : bool, optional
        Add a character datatype to ``FIELD`` elements missing ``datatype``.
    fix_empty_arraysize : bool, optional
        Normalize invalid empty or zero ``arraysize`` attributes.

    Returns
    -------
    bytes
        Sanitized VOTable bytes.
    """
    sanitized = content

    if fix_invalid_date and b'datatype="date"' in sanitized:
        sanitized = sanitized.replace(
            b'datatype="date"',
            b'datatype="char" arraysize="*"',
        )

    if fix_missing_field_datatype:
        def _fix_field(match):
            field_content = match.group(1)
            if b"datatype=" in field_content.lower():
                return match.group(0)

            fixed_content = field_content.rstrip()
            if b"arraysize=" not in fixed_content.lower():
                fixed_content += b' arraysize="*"'

            return b'<FIELD ' + fixed_content + b' datatype="char"></FIELD>'

        sanitized = _FIELD_WITHOUT_DATATYPE_RE.sub(_fix_field, sanitized)

    if fix_empty_arraysize and b'arraysize=""' in sanitized:
        sanitized = _EMPTY_ARRAYSIZE_RE.sub(b'arraysize="*"', sanitized)

    if fix_empty_arraysize and b'arraysize="0"' in sanitized:
        # arraysize="0" is invalid for scalar fields and can trigger downstream
        # masked-array fill-value errors during VOTable -> Table conversion.
        sanitized = _ZERO_ARRAYSIZE_RE.sub(b"", sanitized)

    return sanitized
