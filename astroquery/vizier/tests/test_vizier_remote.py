# Licensed under a 3-clause BSD style license - see LICENSE.rst
import pytest
import numpy as np

import astropy.units as u
from astropy.coordinates import SkyCoord

from astroquery.vizier import Vizier
from astroquery.utils import commons
from .conftest import scalar_skycoord, vector_skycoord


@pytest.mark.remote_data
class TestVizierRemote:

    def test_query_object(self):
        result = Vizier.query_object(
            "HD 226868", catalog=["NOMAD", "UCAC"])

        assert isinstance(result, commons.TableList)

    def test_query_another_object(self):
        result = Vizier.query_region(
            "AFGL 2591", radius='0d5m', catalog="B/iram/pdbi")
        assert isinstance(result, commons.TableList)

    def test_query_object_async(self):
        response = Vizier.query_object_async(
            "HD 226868", catalog=["NOMAD", "UCAC"])
        assert response is not None

    def test_query_region(self):
        result = Vizier.query_region(
            scalar_skycoord, radius=5 * u.deg, catalog=["HIP", "NOMAD", "UCAC"])

        assert isinstance(result, commons.TableList)

    def test_query_region_async(self):
        response = Vizier.query_region_async(
            scalar_skycoord, radius=5 * u.deg, catalog=["HIP", "NOMAD", "UCAC"])
        assert response is not None

    def test_query_region_async_galactic(self):
        response = Vizier.query_region_async(
            scalar_skycoord, radius=0.5 * u.deg, catalog="HIP", frame="galactic")
        assert response is not None
        payload = Vizier.query_region_async(
            scalar_skycoord, radius=0.5 * u.deg, catalog="HIP",
            frame="galactic", get_query_payload=True)
        assert "-c=G" in payload

    def test_query_Vizier_instance(self):
        with pytest.warns(UserWarning, match="xry : No such keyword"):
            vizier = Vizier(
                columns=['_RAJ2000', 'DEJ2000', 'B-V', 'Vmag', 'Plx'],
                column_filters={"Vmag": ">10"}, keywords=["optical", "xry"])

        result = vizier.query_object("HD 226868", catalog=["NOMAD", "UCAC"])
        assert isinstance(result, commons.TableList)
        result = vizier.query_region(
            scalar_skycoord, width="5d0m0s", height="3d0m0s", catalog=["NOMAD", "UCAC"])
        assert isinstance(result, commons.TableList)

    def test_vizier_column_restriction(self):
        # Check that the column restriction worked.  At least some of these
        # catalogs include Bmag's
        vizier = Vizier(
            columns=['_RAJ2000', 'DEJ2000', 'B-V', 'Vmag', 'Plx'],
            column_filters={"Vmag": ">10"}, keywords=["optical", "X-ray"])

        result = vizier.query_object("HD 226868", catalog=["NOMAD", "UCAC"])
        for table in result:
            assert 'Bmag' not in table.columns

    def test_vizier_column_exotic_characters(self):
        # column names can contain any ascii characters. This checks that they are not
        # replaced by underscores, see issue #3124
        result = Vizier(columns=["r'mag"],
                        row_limit=1).get_catalogs(catalog="II/336/apass9")[0]
        assert "r'mag" in result.colnames

    @pytest.mark.parametrize('all', ('all', '*'))
    def test_alls_withaddition(self, all):
        # Check that all the expected columns are there plus the _r
        # (radius from target) that we've added
        vizier = Vizier(columns=[all, "+_r"], catalog="II/246")
        result = vizier.query_region("HD 226868", radius="20s")
        table = result['II/246/out']
        assert 'Jmag' in table.columns
        assert '_r' in table.columns

    def test_get_catalogs(self):
        result = Vizier.get_catalogs('J/ApJ/706/83')
        assert isinstance(result, commons.TableList)

    def test_get_catalog_metadata(self):
        meta = Vizier(catalog="I/324").get_catalog_metadata()
        assert meta['title'] == "The Initial Gaia Source List (IGSL)"

    def test_query_two_wavelengths(self):
        vizier = Vizier(
            columns=['_RAJ2000', 'DEJ2000', 'B-V', 'Vmag', 'Plx'],
            column_filters={"Vmag": ">10"}, keywords=["optical", "radio"])
        vizier.ROW_LIMIT = 1
        vizier.query_object('M 31')

    def test_regressiontest_invalidtable(self):
        vizier = Vizier(
            columns=['all'], ucd='(spect.dopplerVeloc*|phys.veloc*)',
            keywords=['Radio', 'IR'], row_limit=5000)
        coordinate = SkyCoord(359.61687 * u.deg, -0.242457 * u.deg, frame="galactic")

        # With newer versions UnitsWarning may be issued as well
        with pytest.warns() as warnings:
            vizier.query_region(coordinate, radius=2 * u.arcmin)

        for i in warnings:
            message = str(i.message)
            assert ("VOTABLE parsing raised exception" in message or "not supported by the VOUnit standard" in message)

    def test_multicoord(self):

        # Regression test: the columns of the default should never
        # be modified from default
        assert Vizier.columns == ['*']
        # Coordinate selection is entirely arbitrary
        result = Vizier.query_region(
            vector_skycoord, radius=10 * u.arcsec, catalog=["HIP", "NOMAD", "UCAC"])

        assert len(result) >= 5
        assert 'I/239/hip_main' in result.keys()
        assert 'HIP' in result['I/239/hip_main'].columns
        assert result['I/239/hip_main']['HIP'] == 98298

    def test_findcatalog_maxcatalog(self):
        vizier = Vizier()
        cats = vizier.find_catalogs('eclipsing binary planets', max_catalogs=5000)
        assert len(cats) >= 39  # as of 2024

    def test_findcatalog_ucd(self):
        vizier = Vizier()
        ucdresult = vizier(ucd='phys.albedo').find_catalogs('mars', max_catalogs=5000)
        result = vizier.find_catalogs('mars', max_catalogs=5000)

        assert len(ucdresult) >= 1
        assert len(result) >= 11
        # important part: we're testing that UCD is parsed and some catalogs are ruled out
        assert len(ucdresult) < len(result)

    def test_asu_tsv_return_type(self):
        vizier = Vizier()
        result = vizier.query_object("HD 226868", catalog=["NOMAD", "UCAC"], return_type='asu-tsv', cache=False)

        assert isinstance(result, list)
        assert len(result) == 2

    def test_query_constraints(self):
        vizier = Vizier(row_limit=3)
        result = vizier.query_constraints(catalog="I/130/main", mB2="=14.7")[0]
        # row_limit is taken in account
        assert len(result) == 3
        # the criteria is respected
        assert np.all(np.isclose(result["mB2"].data.data, 14.7, rtol=1e-09, atol=1e-09))
