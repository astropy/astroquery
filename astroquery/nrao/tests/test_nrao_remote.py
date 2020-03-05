# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import print_function

import pytest
import astropy.coordinates as coord
from astropy.table import Table
from astropy import units as u

from astroquery.utils.commons import ASTROPY_LT_4_1
from ... import nrao


@pytest.mark.remote_data
class TestNrao:

    def test_query_region_async(self):
        response = nrao.core.Nrao.query_region_async(
            coord.SkyCoord("04h33m11.1s 05d21m15.5s"),
            retry=5)
        assert response is not None
        assert response.content

    def test_query_region(self):
        result = nrao.core.Nrao.query_region(
            coord.SkyCoord("04h33m11.1s 05d21m15.5s"),
            retry=5)
        assert isinstance(result, Table)
        assert (b'0430+052' if ASTROPY_LT_4_1 else '0430+052') in result['Source']

    def test_query_region_project_code(self):
        result = nrao.core.Nrao.query_region(
            coord.SkyCoord("04h33m11.1s 05d21m15.5s"),
            project_code="AD0094", retry=5)
        assert len(result) == 42
        assert len(set(result['Project'])) == 1
        assert "AD0094" in list(set(result['Project']))[0]

    def test_query_region_archive(self):
        result = nrao.core.Nrao.query_region(
            coord.SkyCoord("05h35.8m 35d43m"), querytype='ARCHIVE',
            retry=5, radius='1d')
        assert len(result) >= 230
        assert 'VLA_XH78003_file15.dat' in result['Archive File']

    def test_query_multiconfig(self):
        # regression test for issue 1020
        orion = coord.SkyCoord.from_name("Orion Core")
        result = nrao.core.Nrao.query_region(coordinates=orion,
                                             radius=1*u.arcmin,
                                             telescope='jansky_vla',
                                             telescope_config=['A', 'AB', 'B'],
                                             obs_band=['K', 'Ka', 'Q'])
        assert (b'ORION-KL' if ASTROPY_LT_4_1 else 'ORION-KL') in [x.strip() for x in result['Source']]

        # NOTE: This could change if future observations in AB config are ever
        # taken, or A- or B- config observations with fewer antennae.  Neither
        # are *expected*, but it could happen.
        assert set(result['Telescope:config']) == {'EVLA:A:1:26',
                                                   'EVLA:A:1:27',
                                                   'EVLA:B:1:26',
                                                   'EVLA:B:1:27'}
