# Licensed under a 3-clause BSD style license - see LICENSE.rst


# performs similar tests as test_module.py, but performs
# the actual HTTP request rather than monkeypatching them.
# should be disabled or enabled at will - use the
# remote_data decorator from astropy:

import pytest
from astropy.table import Table

@pytest.mark.remote_data
class TestLegacySurveyClass:
    # now write tests for each method here
    def test_query_object(self):
        import astroquery.legacysurvey

        # TODO: add other parameters
        table = astroquery.legacysurvey.LegacySurvey.query_object("Mrk421") # type: Table

        print(table)

        assert len(table) > 10

    def test_query_region(self):
        import astroquery.legacysurvey
        from astropy.coordinates import SkyCoord
        from astropy.coordinates import Angle, Latitude, Longitude  # Angles

        ra = Angle('0h8m05.63s', unit='hourangle').degree
        dec = Angle('+14d50m23.3s', unit='hourangle').degree
        radius_input = 3.0  # arcmin

        source = SkyCoord(ra, dec, unit='degree')
        radius = Angle(radius_input, unit='arcmin')

        photoobj_fields = ['run', 'rerun', 'camcol', 'field', 'ra', 'dec', 'mode',
                           'psfFlux_u', 'psfFlux_g', 'psfFlux_r', 'psfFlux_i', 'psfFlux_z',
                           'psfFluxIvar_u', 'psfFluxIvar_g', 'psfFluxIvar_r', 'psfFluxIvar_i', 'psfFluxIvar_z',
                           'TAI_u', 'TAI_g', 'TAI_r', 'TAI_i', 'TAI_z', 'objID', 'thingId']

        query1 = astroquery.legacysurvey.LegacySurvey.query_region(source, radius=radius, data_release=16,
                                        photoobj_fields=photoobj_fields)

        print(query1)

    def test_query_brick_list(self):
        import astroquery.legacysurvey

        # TODO: add other parameters
        table = astroquery.legacysurvey.LegacySurvey.query_brick_list(data_release=9) # type: Table

        print(table)

        assert len(table) > 10
