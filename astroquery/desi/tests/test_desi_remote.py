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

        coordinates = SkyCoord('11h04m27s +38d12m32s')

        radius = Angle(5, unit='arcmin')

        query1 = DESILegacySurvey.query_region(coordinates, radius=radius, data_release=9)

        assert isinstance(query1, Table)

    @pytest.mark.parametrize("valid_inputs", [True, False])
    def test_get_images(self, valid_inputs):

        if valid_inputs:
            ra = 166.1125
            dec = 38.209
            radius_input = 0.5
            pixels = 60
        else:
            ra = 86.633212
            dec = 22.01446
            radius_input = 3
            pixels = 1296000

        pos = SkyCoord(ra, dec, unit='degree')
        radius = Angle(radius_input, unit='arcmin')

        if valid_inputs:
            query1 = DESILegacySurvey.get_images(pos, pixels, radius, data_release=9)
            assert isinstance(query1, list)
            assert isinstance(query1[0], HDUList)
        else:
            with pytest.raises(NoResultsWarning):
                DESILegacySurvey.get_images(pos, pixels, radius, data_release=9)
