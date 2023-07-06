import pytest


def test_raises_deprecation_warning():
    with pytest.raises(
        DeprecationWarning,
        match="The ``cds`` module has been moved to astroquery.mocserver,"
        "and ``CdsClass`` has been renamed ``MOCserver``. It means that"
        " 'from astroquery.cds import cds' became 'from astroquery.mocserver"
        " import mocserver'. Please update your imports.",
    ):
        from astroquery.cds import cds  # noqa: F401
