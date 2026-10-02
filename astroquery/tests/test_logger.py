# Licensed under a 3-clause BSD style license - see LICENSE.rst

import importlib
import sys
import warnings

import pytest

from astropy.utils.exceptions import AstropyUserWarning

from astroquery import log
from astroquery.logger import AstroqueryLogger, _WITHIN_IPYTHON


@pytest.fixture(autouse=True)
def reset_logger():
    importlib.reload(warnings)
    log._showwarning_orig = None
    log._excepthook_orig = None
    log._set_defaults()
    yield


def test_logger_is_independent():
    assert isinstance(log, AstroqueryLogger)
    assert type(log).__module__ == "astroquery.logger"


def test_log_to_list_includes_origin_and_message():
    with log.log_to_list() as records:
        log.info("Message %s", "contents")

    assert len(records) == 1
    assert records[0].origin == __name__
    assert records[0].getMessage() == "Message contents"


def test_log_to_file_filters_by_origin(tmp_path):
    filename = tmp_path / "astroquery.log"

    with log.log_to_file(filename, filter_origin=__name__):
        log.info("Recorded message")

    assert "Recorded message" in filename.read_text()


def test_warnings_logging_captures_astropy_warnings():
    log.disable_warnings_logging()
    try:
        with warnings.catch_warnings(record=True) as caught:
            log.enable_warnings_logging()
            with log.log_to_list() as records:
                warnings.warn("Astroquery warning", AstropyUserWarning)
            log.disable_warnings_logging()
    finally:
        if log.warnings_logging_enabled():
            log.disable_warnings_logging()

    assert not caught
    assert records[0].levelname == "WARNING"
    assert records[0].message.startswith("Astroquery warning")


@pytest.mark.skipif(_WITHIN_IPYTHON, reason="IPython uses a custom exception hook")
def test_exception_logging_captures_uncaught_exceptions(monkeypatch):
    monkeypatch.setattr(sys, "excepthook", lambda *args: None)
    log.enable_exception_logging()
    try:
        with log.log_to_list() as records:
            try:
                raise RuntimeError("Astroquery exception")
            except RuntimeError:
                sys.excepthook(*sys.exc_info())
    finally:
        if log.exception_logging_enabled():
            log.disable_exception_logging()

    assert records[0].levelname == "ERROR"
    assert records[0].message.startswith("RuntimeError: Astroquery exception")
