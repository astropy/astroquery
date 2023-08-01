import pytest
from astropy.utils.exceptions import AstropyDeprecationWarning


def test_raises_deprecation_warning():
    with pytest.raises(
        AstropyDeprecationWarning,
        match="The ``cds`` module has been moved to astroquery.mocserver, "
              "and ``CdsClass`` has been renamed to ``MOCServerClass``. "
              "Please update your imports."):
        from astroquery.cds import cds  # noqa: F401
