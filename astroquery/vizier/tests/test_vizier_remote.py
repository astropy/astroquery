# Licensed under a 3-clause BSD style license - see LICENSE.rst
import pytest

import astropy.units as u
from astropy import coordinates
from ... import vizier
from ...utils import commons


@pytest.mark.remote_data
class TestVizierRemote(object):

    target = commons.ICRSCoordGenerator(ra=299.590, dec=35.201,
                                        unit=(u.deg, u.deg))

    def test_query_object(self):
        result = vizier.core.Vizier.query_object(
            "HD 226868", catalog=["NOMAD", "UCAC"])

        assert isinstance(result, commons.TableList)

    def test_query_another_object(self):
        result = vizier.core.Vizier.query_region(
            "AFGL 2591", radius='0d5m', catalog="B/iram/pdbi")
        assert isinstance(result, commons.TableList)

    def test_query_object_async(self):
        response = vizier.core.Vizier.query_object_async(
            "HD 226868", catalog=["NOMAD", "UCAC"])
        assert response is not None

    def test_query_region(self):
        result = vizier.core.Vizier.query_region(
            self.target, radius=5 * u.deg, catalog=["HIP", "NOMAD", "UCAC"])

        assert isinstance(result, commons.TableList)

    def test_query_region_async(self):
        response = vizier.core.Vizier.query_region_async(
            self.target, radius=5 * u.deg, catalog=["HIP", "NOMAD", "UCAC"])

        assert response is not None

    def test_query_Vizier_instance(self):
        v = vizier.core.Vizier(
            columns=['_RAJ2000', 'DEJ2000', 'B-V', 'Vmag', 'Plx'],
            column_filters={"Vmag": ">10"}, keywords=["optical", "xry"])

        result = v.query_object("HD 226868", catalog=["NOMAD", "UCAC"])
        assert isinstance(result, commons.TableList)
        result = v.query_region(self.target,
                                width="5d0m0s", height="3d0m0s",
                                catalog=["NOMAD", "UCAC"])
        assert isinstance(result, commons.TableList)

    def test_vizier_column_restriction(self):
        # Check that the column restriction worked.  At least some of these
        # catalogs include Bmag's
        v = vizier.core.Vizier(
            columns=['_RAJ2000', 'DEJ2000', 'B-V', 'Vmag', 'Plx'],
            column_filters={"Vmag": ">10"}, keywords=["optical", "xry"])

        result = v.query_object("HD 226868", catalog=["NOMAD", "UCAC"])
        for table in result:
            assert 'Bmag' not in table.columns

    @pytest.mark.parametrize('all', ('all', '*'))
    def test_alls_withaddition(self, all):
        # Check that all the expected columns are there plus the _r
        # (radius from target) that we've added
        v = vizier.core.Vizier(columns=[all, "+_r"], catalog="II/246")
        result = v.query_region("HD 226868", radius="20s")
        table = result['II/246/out']
        assert 'Jmag' in table.columns
        assert '_r' in table.columns

    def test_get_catalogs(self):
        result = vizier.core.Vizier.get_catalogs('J/ApJ/706/83')
        assert isinstance(result, commons.TableList)

    def test_query_two_wavelengths(self):
        v = vizier.core.Vizier(
            columns=['_RAJ2000', 'DEJ2000', 'B-V', 'Vmag', 'Plx'],
            column_filters={"Vmag": ">10"}, keywords=["optical", "radio"])

        v.query_object('M 31')

    def test_regressiontest_invalidtable(self):
        V = vizier.core.Vizier(
            columns=['all'], ucd='(spect.dopplerVeloc*|phys.veloc*)',
            keywords=['Radio', 'IR'], row_limit=5000)
        C = coordinates.SkyCoord(359.61687 * u.deg, -0.242457 * u.deg,
                                 frame='galactic')

        r2 = V.query_region(C, radius=2 * u.arcmin)

    def test_multicoord(self):

        # Coordinate selection is entirely arbitrary
        targets = commons.ICRSCoordGenerator(ra=[299.590, 299.90],
                                             dec=[35.201, 35.201],
                                             unit=(u.deg, u.deg))
        # Regression test: the columns of the default should never
        # be modified from default
        assert vizier.core.Vizier.columns == ['*']
        result = vizier.core.Vizier.query_region(
            targets, radius=10 * u.arcsec, catalog=["HIP", "NOMAD", "UCAC"])

        assert len(result) >= 5
        assert 'I/239/hip_main' in result.keys()
        assert 'HIP' in result['I/239/hip_main'].columns
        assert result['I/239/hip_main']['HIP'] == 98298

    def test_findcatalog_maxcatalog(self):
        V = vizier.core.Vizier()
        cats = V.find_catalogs('eclipsing binary', max_catalogs=5000)
        assert len(cats) >= 468

        # with pytest.raises(ValueError) as exc:
        #    V.find_catalogs('eclipsing binary')
        # assert str(exc.value)==("Maximum number of catalogs exceeded."
        #                        "  Try setting max_catalogs "
        #                        "to a large number and try again")

    def test_findcatalog_ucd(self):
        V = vizier.core.Vizier()
        ucdresult = V(ucd='time.age*').find_catalogs('eclipsing binary', max_catalogs=5000)
        result = V.find_catalogs('eclipsing binary', max_catalogs=5000)

        assert len(ucdresult) >= 12  # count as of 1/15/2018
        assert len(result) >= 628
        # important part: we're testing that UCD is parsed and some catalogs are ruled out
        assert len(ucdresult) < len(result)
