# Licensed under a 3-clause BSD style license - see LICENSE.rst

import hashlib
from io import BytesIO
import json
from pathlib import Path

import pytest

from astropy.io import fits
from astropy.io.votable import parse as parse_votable
from astropy.table import Table

from astroquery.nadc._response_utils import sanitize_votable_content


NADC_ROOT = Path(__file__).parents[1]
DATA_DIRS = sorted(NADC_ROOT.glob("*/tests/data"))
TEXT_SUFFIXES = {".csv", ".json", ".xml"}


def _sha256(path):
    content = path.read_bytes()
    if path.suffix in TEXT_SUFFIXES:
        content = content.replace(b"\r\n", b"\n")
    return hashlib.sha256(content).hexdigest()


def test_sha256_normalizes_text_newlines(tmp_path):
    path = tmp_path / "fixture.json"
    path.write_bytes(b'{"ok": true}\r\n')
    assert _sha256(path) == hashlib.sha256(b'{"ok": true}\n').hexdigest()


@pytest.mark.parametrize("data_dir", DATA_DIRS, ids=lambda path: path.parts[-3])
def test_service_data_manifest_matches_files(data_dir):
    manifest_path = data_dir / "manifest.json"
    assert manifest_path.exists()

    manifest = json.loads(manifest_path.read_text())
    expected = set(manifest["files"]) | {"manifest.json"}
    actual = {path.name for path in data_dir.iterdir() if path.is_file()}
    assert actual == expected

    for filename, metadata in manifest["files"].items():
        path = data_dir / filename
        assert _sha256(path) == metadata["sha256"]


@pytest.mark.parametrize(
    "path",
    [path for data_dir in DATA_DIRS for path in sorted(data_dir.iterdir()) if path.is_file()],
    ids=lambda path: "/".join(path.parts[-4:]),
)
def test_service_data_files_are_parseable(path):
    content = path.read_bytes()

    if path.suffix == ".json":
        json.loads(content.decode("utf-8"))
    elif path.suffix == ".csv":
        Table.read(path, format="csv")
    elif path.suffix == ".xml":
        sanitized = sanitize_votable_content(
            content,
            fix_invalid_date=True,
            fix_missing_field_datatype=True,
            fix_empty_arraysize=True,
        )
        tables = list(parse_votable(BytesIO(sanitized)).iter_tables())
        assert tables
        assert isinstance(tables[0].to_table(use_names_over_ids=True), Table)
    elif path.suffix == ".png":
        assert content.startswith(b"\x89PNG\r\n\x1a\n")
    elif path.name.endswith(".fits.gz"):
        with fits.open(path) as hdul:
            assert len(hdul) > 0
    else:
        raise AssertionError(f"Unhandled service data file type: {path}")
