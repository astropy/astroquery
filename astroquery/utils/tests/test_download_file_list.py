import pytest

from astropy.utils.exceptions import AstropyDeprecationWarning

from astroquery.utils.download_file_list import download_list_of_fitsfiles


def test_download_list_of_fitsfiles_deprecation():
    with pytest.warns(AstropyDeprecationWarning):
        download_list_of_fitsfiles([])
