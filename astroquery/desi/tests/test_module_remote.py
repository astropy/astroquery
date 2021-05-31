# Licensed under a 3-clause BSD style license - see LICENSE.rst

import pytest
from astropy.io.fits import HDUList
from astroquery.exceptions import NoResultsWarning


@pytest.mark.remote_data
class TestLegacySurveyClass:

    def test_query_region(self):
        import astroquery.desi
        from astropy.coordinates import SkyCoord
        from astropy.coordinates import Angle
        from astropy.table import Table

        ra = Angle('11h04m27s', unit='hourangle').degree
        dec = Angle('+38d12m32s', unit='hourangle').degree
        coordinates = SkyCoord(ra, dec, unit='degree')

        radius = Angle(5, unit='arcmin')

        query1 = astroquery.desi.DESILegacySurvey.query_region(coordinates, radius=radius, data_release=9)

        assert isinstance(query1, Table)

    @pytest.mark.parametrize("valid_inputs", [True, False])
    def test_get_images(self, valid_inputs):
        import astroquery.desi
        from astropy.coordinates import SkyCoord
        from astropy.coordinates import Angle

        if valid_inputs:
            ra = Angle('11h04m27s', unit='hourangle').degree
            dec = Angle('+38d12m32s', unit='hourangle').degree
            radius_input = 0.5  # arcmin
            pixels = 60
        else:
            ra = Angle('86.633212', unit='degree').degree
            dec = Angle('22.01446', unit='degree').degree
            radius_input = 3  # arcmin
            pixels = 1296000

        pos = SkyCoord(ra, dec, unit='degree')
        radius = Angle(radius_input, unit='arcmin')

        if valid_inputs:
            query1 = astroquery.desi.DESILegacySurvey.get_images(pos, data_release=9, radius=radius, pixels=pixels)
            assert isinstance(query1, list)
            assert isinstance(query1[0], HDUList)
        else:
            with pytest.raises(NoResultsWarning):
                astroquery.desi.DESILegacySurvey.get_images(pos, data_release=9, radius=radius, pixels=pixels)
