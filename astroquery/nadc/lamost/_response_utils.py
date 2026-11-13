# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
Internal response parsing helpers for the LAMOST service.
"""

from __future__ import annotations

import re
from xml.etree import ElementTree

from astropy.utils import minversion


_FIELD_START_TAG_RE = re.compile(rb"<FIELD\b([^>]*?)\s*(/?)>", re.IGNORECASE)
_EMPTY_ARRAYSIZE_RE = re.compile(rb'arraysize=""', re.IGNORECASE)
_ZERO_ARRAYSIZE_RE = re.compile(rb'\s+arraysize="0"', re.IGNORECASE)


def widen_tabledata_strings(content: bytes) -> bytes:
    """Widen undersized scalar string FIELDs using their TABLEDATA values.

    This LAMOST server workaround can be removed after the archive supplies
    correct string lengths. Binary layouts and multidimensional fields are
    left untouched; any remaining truncation is rejected by the caller.
    Bounded variable-length binary strings require Astropy >= 7.1.1 to
    avoid incorrect decoding on older versions.
    """
    root = ElementTree.fromstring(content)
    changed = False
    for table in root.iterfind('.//{*}TABLE'):
        fields = table.findall('{*}FIELD')
        rows = table.find('{*}DATA/{*}TABLEDATA')
        if rows is None:
            # Astropy #18105: older converters treat bounded variable-length
            # binary strings as fixed-length, corrupting values and row counts.
            if (any(table.find(f'{{*}}DATA/{{*}}{layout}') is not None for layout in ('BINARY', 'BINARY2'))
                    and any(field.get('datatype') in {'char', 'unicodeChar'}
                            and re.fullmatch(r'[0-9]+\*', field.get('arraysize', '')) for field in fields)
                    and not minversion('astropy', '7.1.1')):
                raise ValueError('Reading bounded variable-length binary strings requires Astropy >= 7.1.1.')
            continue
        widths = {}
        for i, field in enumerate(fields):
            size = field.get('arraysize', '1')
            if field.get('datatype') in {'char', 'unicodeChar'} and re.fullmatch(r'[0-9]+', size):
                widths[i] = int(size)
        if not widths:
            continue
        for row in rows:
            cells = list(row)
            if (row.tag.rsplit('}', 1)[-1] != 'TR' or len(cells) != len(fields)
                    or any(cell.tag.rsplit('}', 1)[-1] != 'TD' or len(cell) for cell in cells)):
                raise ValueError('Cannot reliably map LAMOST VOTable TABLEDATA cells to columns.')
            for i in widths:
                widths[i] = max(widths[i], len(cells[i].text or ''))
        for i, width in widths.items():
            if width > int(fields[i].get('arraysize', '1')):
                fields[i].set('arraysize', str(width))
                changed = True
    return ElementTree.tostring(root, encoding='utf-8') if changed else content


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
    if "text/html" in content_type or "application/xhtml+xml" in content_type:
        return True

    prefix = response.content[:256].decode("utf-8-sig", "ignore").lstrip().lower()
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
            # Repair the start tag only, whether the element is self-closing,
            # empty, or carries DESCRIPTION/VALUES children.
            attributes, closing = match.group(1), match.group(2)
            if b"datatype=" in attributes.lower():
                return match.group(0)

            fixed_attributes = attributes.rstrip()
            if b"arraysize=" not in fixed_attributes.lower():
                fixed_attributes += b' arraysize="*"'

            return b'<FIELD' + fixed_attributes + b' datatype="char"' + closing + b'>'

        sanitized = _FIELD_START_TAG_RE.sub(_fix_field, sanitized)

    if fix_empty_arraysize and b'arraysize=""' in sanitized:
        sanitized = _EMPTY_ARRAYSIZE_RE.sub(b'arraysize="*"', sanitized)

    if fix_empty_arraysize and b'arraysize="0"' in sanitized:
        # arraysize="0" is invalid for scalar fields and can trigger downstream
        # masked-array fill-value errors during VOTable -> Table conversion.
        sanitized = _ZERO_ARRAYSIZE_RE.sub(b"", sanitized)

    return sanitized
