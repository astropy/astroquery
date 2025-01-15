# Licensed under a 3-clause BSD style license - see LICENSE.rst

import os
import pytest
import tempfile
import astropy.units as u
from astropy.table import Table
from astropy.coordinates import SkyCoord
from packaging.version import Version

from astropy.utils.exceptions import AstropyDeprecationWarning
from astroquery.exceptions import NoResultsWarning
import pyvo

from astroquery.heasarc import Heasarc


OBJ_LIST = [
    "NGC 4151",
    "182d38m08.64s 39d24m21.06s",
    SkyCoord(l=155.0771, b=75.0631, unit=(u.deg, u.deg), frame="galactic"),
]

DEFAULT_COLS = [
    [
        "nicermastr",
        [
            "name",
            "ra",
            "dec",
            "time",
            "obsid",
            "exposure",
            "processing_status",
            "processing_date",
            "public_date",
            "obs_type",
        ],
    ],
    [
        "numaster",
        [
            "name",
            "ra",
            "dec",
            "time",
            "obsid",
            "status",
            "exposure_a",
            "observation_mode",
            "obs_type",
            "processing_date",
            "public_date",
            "issue_flag",
        ],
    ],
]


@pytest.mark.remote_data
class TestHeasarc:

    def test_tap(self):
        """Test Tap service"""
        assert Heasarc._tap is None
        tap = Heasarc.tap
        assert Heasarc._tap == tap

    def test_meta(self):
        """Test Meta service"""
        assert Heasarc._meta_info is None
        Heasarc._meta
        assert Heasarc._meta_info is not None

    @pytest.mark.parametrize("coordinates", OBJ_LIST)
    def test_query_region_cone(self, coordinates):
        """
        Test multiple ways of specifying coordinates for a conesearch
        """
        result = Heasarc.query_region(
            coordinates,
            catalog="suzamaster",
            spatial="cone",
            columns="*",
            radius=1 * u.arcmin,
            add_offset=True
        )
        assert isinstance(result, Table)
        assert len(result) == 3
        # assert all columns are returned
        assert len(result.colnames) == 53

    def test_query_columns_radius(self):
        """
        Test selection of only a few columns, and using a bigger radius
        """
        result = Heasarc.query_region(
            "NGC 4151", catalog="suzamaster", columns="ra,dec,obsid",
            radius=10 * u.arcmin,
            add_offset=True
        )
        assert len(result) == 4
        # assert only selected columns are returned
        assert result.colnames == ["ra", "dec", "obsid", "search_offset"]

    def test_query_region_box(self):
        result = Heasarc.query_region(
            "182d38m08.64s 39d24m21.06s",
            catalog="suzamaster",
            columns="*",
            spatial="box",
            width=2 * u.arcmin,
        )
        assert isinstance(result, Table)
        assert len(result) == 3

    def test_query_region_polygon(self):
        polygon = [(10.1, 10.1), (10.0, 10.1), (10.0, 10.0)]
        with pytest.warns(Warning) as warnings:
            result = Heasarc.query_region(
                catalog="suzamaster", spatial="polygon", polygon=polygon
            )
        assert warnings[0].category == UserWarning
        assert ("Polygon endpoints are being interpreted" in
                warnings[0].message.args[0])
        assert warnings[1].category == NoResultsWarning
        assert isinstance(result, Table)

    def test_list_catalogs(self):
        catalogs = Heasarc.list_catalogs()
        # Number of available catalogs may change over time, test only for
        # significant drop. (at the time of writing there are 1020 catalogs
        # in the list).
        assert len(catalogs) > 1000

    def test_list_catalogs__master(self):
        catalogs = list(Heasarc.list_catalogs(master=True)["name"])
        assert "numaster" in catalogs
        assert "nicermastr" in catalogs
        assert "xmmmaster" in catalogs
        assert "swiftmastr" in catalogs

    def test_list_catalogs__keywords(self):
        catalogs = list(Heasarc.list_catalogs(keywords="nustar", master=True)["name"])
        assert len(catalogs) == 1 and "numaster" in catalogs

        catalogs = list(Heasarc.list_catalogs(keywords="xmm", master=True)["name"])
        assert len(catalogs) == 1 and "xmmmaster" in catalogs

        catalogs = list(Heasarc.list_catalogs(keywords=["swift", "rosat"],
                        master=True)["name"])
        assert "swiftmastr" in catalogs
        assert "rosmaster" in catalogs
        assert "rassmaster" in catalogs

    @pytest.mark.skipif(
        Version(pyvo.__version__) < Version('1.4'),
        reason="DALOverflowWarning is available only in pyvo>=1.4"
    )
    def test_tap__maxrec(self):
        from pyvo.dal.exceptions import DALOverflowWarning
        query = "SELECT TOP 10 ra,dec FROM xray"
        with pytest.warns(
            expected_warning=DALOverflowWarning,
            match=("Partial result set. Potential causes MAXREC, "
                   "async storage space, etc."),
        ):
            result = Heasarc.query_tap(query=query, maxrec=5)
        assert len(result) == 5
        assert result.to_table().colnames == ["ra", "dec"]

    @pytest.mark.parametrize("tdefault", DEFAULT_COLS)
    def test__get_default_columns(self, tdefault):
        catalog, tdef = tdefault
        remote_default = list(Heasarc._get_default_columns(catalog))
        assert remote_default == tdef

    def test_locate_data__wrongcatalog(self):
        with pytest.raises(ValueError, match="Unknown catalog name:"):
            Heasarc.locate_data(
                Table({"__row": [1, 2, 3.0]}), catalog_name="wrongcatalog"
            )

    def test_locate_data__xmmmaster(self):
        links = Heasarc.locate_data(
            Table({"__row": [4154, 4155]}), catalog_name="xmmmaster"
        )
        assert len(links) == 2
        assert "access_url" in links.colnames
        assert "sciserver" in links.colnames
        assert "aws" in links.colnames

    def test_download_data__heasarc_file(self):
        filename = "00README"
        tab = Table({
            "access_url": [
                ("https://heasarc.gsfc.nasa.gov/FTP/rxte/"
                 f"data/archive/{filename}")
            ]
        })
        with tempfile.TemporaryDirectory() as tmpdir:
            Heasarc.download_data(tab, host="heasarc", location=tmpdir)
            assert os.path.exists(f'{tmpdir}/{filename}')

    def test_download_data__heasarc_folder(self):
        tab = Table({
            "access_url": [
                ("https://heasarc.gsfc.nasa.gov/FTP/rxte/data/archive/"
                 "AO10/P91129/91129-01-68-00A/stdprod")
            ]
        })
        with tempfile.TemporaryDirectory() as tmpdir:
            Heasarc.download_data(tab, host="heasarc", location=tmpdir)
            assert os.path.exists(f"{tmpdir}/stdprod")
            assert os.path.exists(f"{tmpdir}/stdprod/FHed_1791a7b9-1791a931.gz")
            assert os.path.exists(f"{tmpdir}/stdprod/FHee_1791a7b9-1791a92f.gz")
            assert os.path.exists(f"{tmpdir}/stdprod/FHef_1791a7b9-1791a92f.gz")

    def test_download_data__s3_file(self):
        filename = "00README"
        tab = Table(
            {"aws": [f"s3://nasa-heasarc/rxte/data/archive/{filename}"]}
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            Heasarc.enable_cloud(provider='aws', profile=None)
            Heasarc.download_data(tab, host="aws", location=tmpdir)
            assert os.path.exists(f'{tmpdir}/{filename}')

    @pytest.mark.parametrize("slash", ["", "/"])
    def test_download_data__s3_folder(self, slash):
        tab = Table(
            {
                "aws": [
                    (f"s3://nasa-heasarc/rxte/data/archive/AO10/"
                     f"P91129/91129-01-68-00A/stdprod{slash}")
                ]
            }
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            Heasarc.enable_cloud(provider='aws', profile=None)
            Heasarc.download_data(tab, host="aws", location=tmpdir)
            assert os.path.exists(f"{tmpdir}/stdprod")
            assert os.path.exists(f"{tmpdir}/stdprod/FHed_1791a7b9-1791a931.gz")
            assert os.path.exists(f"{tmpdir}/stdprod/FHee_1791a7b9-1791a92f.gz")
            assert os.path.exists(f"{tmpdir}/stdprod/FHef_1791a7b9-1791a92f.gz")

    def test_query_mission_columns(self):
        with pytest.warns(AstropyDeprecationWarning):
            Heasarc.query_mission_cols(mission="xmmmaster")

    def test_query_mission_list(self):
        with pytest.warns(AstropyDeprecationWarning):
            Heasarc.query_mission_list()

    @pytest.mark.parametrize(
        "pars",
        [
            ["mission", "xmmmaster"],
            ["fields", "*"],
            ["resultmax", 10000],
            ["entry", None],
            ["coordsys", None],
            ["equinox", None],
            ["displaymode", None],
            ["action", None],
            ["sortvar", None],
            ["cache", None],
        ],
    )
    def test_deprecated_pars(self, pars):
        """Test deprecated keywords.
        """
        keyword, value = pars
        pos = OBJ_LIST[2]
        with pytest.warns(AstropyDeprecationWarning):
            if keyword == "mission":
                Heasarc.query_region(pos, mission=value)
            else:
                Heasarc.query_region(pos, mission="xmmmaster",
                                     **{keyword: value})


@pytest.mark.remote_data
class TestHeasarcBrowse:
    """Tests for backward compatibility with the old astroquery.heasarc"""

    def test_custom_args(self):
        object_name = "Crab"
        mission = "intscw"

        heasarc = Heasarc

        with pytest.warns(AstropyDeprecationWarning):
            catalog = heasarc.query_object(
                object_name,
                mission=mission,
                radius="1 degree",
                time="2020-09-01 .. 2020-12-01",
                resultmax=10,
                good_isgri=">1000",
                cache=False,
            )
            assert len(catalog) > 0

    def test_basic_example(self):
        mission = "rosmaster"
        object_name = "3c273"

        heasarc = Heasarc
        with pytest.warns(AstropyDeprecationWarning):
            catalog = heasarc.query_object(object_name, mission=mission)

            assert len(catalog) == 63

    def test_mission_list(self):
        heasarc = Heasarc
        with pytest.warns(AstropyDeprecationWarning):
            missions = heasarc.query_mission_list()

            # Assert that there are indeed a large number of tables
            # Number of tables could change, but should be > 900
            # (currently 956)
            assert len(missions) > 900

    def test_mission_columns(self):
        heasarc = Heasarc
        mission = "rosmaster"
        with pytest.warns(AstropyDeprecationWarning):
            cols = heasarc.query_mission_cols(mission=mission)

            # we have extra columns in Xamin
            assert len(cols) == 28

            # Test that the cols list contains known names
            assert "EXPOSURE" in cols
            assert "RA" in cols
            assert "DEC" in cols

    def test_query_region(self):
        heasarc = Heasarc
        mission = "rosmaster"
        skycoord_3C_273 = SkyCoord("12h29m06.70s +02d03m08.7s", frame="icrs")

        with pytest.warns(AstropyDeprecationWarning):
            catalog = heasarc.query_region(
                skycoord_3C_273, mission=mission, radius="1 degree"
            )

            assert len(catalog) == 63

    def test_query_region_nohits(self):
        """
        Regression test for #2560: HEASARC returns a FITS file as a null result
        """
        heasarc = Heasarc

        with pytest.warns(Warning) as warnings:
            # This was an example coordinate that returned nothing
            # Since Fermi is still active, it is possible that sometime in the
            # future an event will occur here.
            catalog = heasarc.query_region(
                SkyCoord(0.28136 * u.deg, -0.09789 * u.deg, frame="fk5"),
                mission="hitomaster",
                radius=0.1 * u.deg,
            )
        assert warnings[0].category == AstropyDeprecationWarning
        assert warnings[1].category == NoResultsWarning
        assert len(catalog) == 0
