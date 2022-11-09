import pytest

from astroquery.desi import DESILegacySurvey
from astropy.io.fits import HDUList
from astropy.coordinates import SkyCoord
from astropy.coordinates import Angle
from astropy.table import Table
from astroquery.exceptions import NoResultsWarning


@pytest.mark.remote_data
class TestLegacySurveyClass:

    def test_query_region(self):
        ra = 166.1125
        dec = 38.209
        coordinates = SkyCoord(ra, dec, unit='degree')

        width = Angle(15, unit='arcsec')

        query1 = DESILegacySurvey.query_region(coordinates, width=width, data_release=9)

        assert isinstance(query1, Table)

    @pytest.mark.parametrize(('ra', 'dec', 'width', 'pixels'),
                             ((166.1125, 38.209, 0.5, 60),))
    def test_get_images(self, ra, dec, width, pixels):
        pos = SkyCoord(ra, dec, unit='degree')
        width = Angle(width, unit='arcmin')

        query1 = DESILegacySurvey.get_images(pos, pixels=pixels, width=width, data_release=9)
        assert isinstance(query1, list)
        assert isinstance(query1[0], HDUList)

    def test_noresults_warning(self):
        # Using position with no coverage
        pos = SkyCoord(86.633212, 22.01446, unit='degree')
        width = Angle(3, unit='arcmin')

        with pytest.warns(NoResultsWarning):
            DESILegacySurvey.get_images(pos, width=width, pixels=100)
