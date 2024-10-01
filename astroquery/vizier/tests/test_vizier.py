# Licensed under a 3-clause BSD style license - see LICENSE.rst
import os
import requests
from numpy import testing as npt
import pytest
from pyvo import registry
from astropy.coordinates import SkyCoord
import astropy.io.votable.tree as votree
from astropy.table import Table
import astropy.units as u

from ... import vizier
from ...exceptions import EmptyResponseError
from ...utils import commons
from astroquery.utils.mocks import MockResponse
from .conftest import scalar_skycoord, vector_skycoord


VO_DATA = {'HIP,NOMAD,UCAC': "viz.xml",
           'NOMAD,UCAC': "viz.xml",
           'B/iram/pdbi': "afgl2591_iram.xml",
           'J/ApJ/706/83': "kang2010.xml",
           "find_2009ApJ...706...83K": "find_kangapj70683.xml"}


def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)


@pytest.fixture
def patch_post(request):
    mp = request.getfixturevalue("monkeypatch")

    mp.setattr(requests.Session, 'request', post_mockreturn)
    return mp


def post_mockreturn(self, method, url, data=None, timeout=10, files=None,
                    params=None, headers=None, **kwargs):
    if method != 'POST':
        raise ValueError("A 'post request' was made with method != POST")
    if isinstance(data, dict):
        datad = data
    else:
        datad = {}
        for line in data.split('\n'):
            if '=' in line:
                key, value = line.split('=', maxsplit=1)
                datad[key.strip()] = value.strip()
            else:
                datad[line] = None
    if '-source' in datad:
        # a request for the actual data
        filename = data_path(VO_DATA[datad['-source']])
    elif '-words' in datad:
        # a find_catalog request/only metadata
        filename = data_path(VO_DATA['find_' + datad['-words'].split("&")[0]])

    with open(filename, 'rb') as infile:
        content = infile.read()
    return MockResponse(content, **kwargs)


def parse_objname(obj):
    d = {"AFGL 2591": SkyCoord(307.35388 * u.deg, 40.18858 * u.deg, frame="icrs")}
    return d[obj]


@pytest.fixture
def patch_coords(request):
    mp = request.getfixturevalue("monkeypatch")

    mp.setattr(commons, 'parse_coordinates', parse_objname)
    return mp


@pytest.mark.parametrize("dim,expected_unit,expected_unit_str,expected_value",
                         [(5 * u.deg, u.deg, "d", 5),
                          (5 * u.arcmin, u.arcmin, "m", 5),
                          (5 * u.arcsec, u.arcsec, "s", 5),
                          (0.314 * u.rad, u.deg, "d", 18),
                          ("5d5m5.5s", u.deg, "d", 5.0846)])
def test_parse_angle(dim, expected_unit, expected_unit_str, expected_value):
    actual_unit, actual_unit_str, actual_value = vizier.core._parse_angle(dim)
    assert actual_unit == expected_unit
    assert actual_unit_str == expected_unit_str
    npt.assert_approx_equal(actual_value, expected_value, significant=2)


def test_parse_angle_err():
    with pytest.raises(Exception):
        vizier.core._parse_angle(5 * u.kg)


@pytest.mark.parametrize(('filepath'),
                         list(set(VO_DATA.values())))
def test_parse_result_verbose(filepath, capsys):
    with open(data_path(filepath), 'rb') as infile:
        table_contents = infile.read()
    response = MockResponse(table_contents)
    vizier.core.Vizier._parse_result(response)
    out, err = capsys.readouterr()
    assert out == ''


@pytest.mark.parametrize(('filepath', 'objlen'),
                         [('viz.xml', 231),
                          ('afgl2591_iram.xml', 1),
                          ('kang2010.xml', 1),
                          ]
                         )  # TODO: 1->50 because it is just 1 table
def test_parse_result(filepath, objlen):
    with open(data_path(filepath), 'rb') as infile:
        table_contents = infile.read()
    response = MockResponse(table_contents)
    result = vizier.core.Vizier._parse_result(response)
    assert isinstance(result, commons.TableList)
    assert len(result) == objlen
    assert isinstance(result[result.keys()[0]], Table)


def test_query_region_async(patch_post):
    response = vizier.core.Vizier.query_region_async(
        scalar_skycoord, radius=5 * u.deg, catalog=["HIP", "NOMAD", "UCAC"])
    assert response is not None


@pytest.mark.parametrize(
    "inner_r,region_str",
    [(1 * u.deg, "-c.rd=1.0,5.0"), (60 * u.arcmin, "-c.rm=60.0,300.0")])
@pytest.mark.parametrize("outer_r", (5 * u.deg, 300 * u.arcmin))
def test_query_region_async_with_inner_radius(inner_r, outer_r, region_str):
    query = vizier.VizierClass().query_region_async(
        scalar_skycoord, radius=outer_r, inner_radius=inner_r, get_query_payload=True)
    assert region_str in query.splitlines()


@pytest.mark.parametrize(
    "width,region_str",
    [(1 * u.deg, "-c.bd=1.0x5.0"), (60 * u.arcmin, "-c.bm=60.0x300.0")])
@pytest.mark.parametrize("height", (5 * u.deg, 300 * u.arcmin))
def test_query_region_async_rectangle(width, height, region_str):
    query = vizier.VizierClass().query_region_async(
        scalar_skycoord, width=width, height=height, get_query_payload=True)
    assert region_str in query.splitlines()


def test_query_region(patch_post):
    result = vizier.core.Vizier.query_region(
        scalar_skycoord, radius=5 * u.deg, catalog=["HIP", "NOMAD", "UCAC"])

    assert isinstance(result, commons.TableList)


def test_query_regions(patch_post):
    """
    This ONLY tests that calling the function works -
    the data currently used for the test is *NOT* appropriate
    for the multi-object query.  There is no test for parsing
    that return (yet - but see test_multicoord in remote_data)
    """
    vizier.core.Vizier.query_region(
        vector_skycoord, radius=5 * u.deg, catalog=["HIP", "NOMAD", "UCAC"])


def test_query_object_async(patch_post):
    response = vizier.core.Vizier.query_object_async(
        "HD 226868", catalog=["NOMAD", "UCAC"])
    assert response is not None


def test_query_object(patch_post):
    result = vizier.core.Vizier.query_object(
        "HD 226868", catalog=["NOMAD", "UCAC"])
    assert isinstance(result, commons.TableList)


def test_query_another_object(patch_post, patch_coords):
    result = vizier.core.Vizier.query_region("AFGL 2591", radius='0d5m',
                                             catalog="B/iram/pdbi")
    assert isinstance(result, commons.TableList)


def test_get_catalogs_async(patch_post):
    response = vizier.core.Vizier.get_catalogs_async('J/ApJ/706/83')
    assert response is not None


def test_get_catalogs(patch_post):
    result = vizier.core.Vizier.get_catalogs('J/ApJ/706/83')
    assert isinstance(result, commons.TableList)


def test_find_resource_then_get(patch_post):
    reses = vizier.core.Vizier.find_catalogs('2009ApJ...706...83K')
    res = next(iter(reses.values()))

    result = vizier.core.Vizier.get_catalogs(res)
    assert isinstance(result, commons.TableList)
    assert next(iter(result.keys())).startswith(res.name)

    resultl = vizier.core.Vizier.get_catalogs([res])
    assert isinstance(result, type(resultl))
    assert len(result) == len(resultl)
    assert len(result[0]) == len(resultl[0])


def test_catalog_consistency_issue1326(patch_post):
    # regression test for issue 1326
    result1 = vizier.core.Vizier(catalog='J/ApJ/706/83').query_constraints_async(testconstraint='blah',
                                                                                 get_query_payload=True)
    result2 = vizier.core.Vizier().query_constraints_async(testconstraint='blah',
                                                           catalog='J/ApJ/706/83',
                                                           get_query_payload=True)

    assert result1 == result2


class TestVizierKeywordClass:

    def test_init(self):
        v = vizier.core.VizierKeyword(keywords=['cobe', 'xmm'])
        assert v.keyword_dict is not None

    def test_keywords(self, recwarn):
        vizier.core.VizierKeyword(keywords=['xxx', 'coBe'])
        w = recwarn.pop(UserWarning)
        # warning must be emitted
        assert (str(w.message) == 'xxx : No such keyword')


class TestVizierClass:

    def test_init(self):
        v = vizier.core.Vizier()
        assert v.keywords is None
        assert v.columns == ["*"]
        assert v.column_filters == {}

    def test_keywords(self):
        v = vizier.core.Vizier(keywords=['optical', 'chandra', 'ans'])
        assert str(v.keywords) == ('-kw.Mission=ANS\n-kw.Mission='
                                   'Chandra\n-kw.Wavelength=optical')
        with pytest.warns(UserWarning, match="xy : No such keyword"):
            v = vizier.core.Vizier(keywords=['xy', 'optical'])
        assert str(v.keywords) == '-kw.Wavelength=optical'
        v.keywords = ['optical', 'cobe']
        assert str(v.keywords) == '-kw.Mission=COBE\n-kw.Wavelength=optical'
        del v.keywords
        assert v.keywords is None

    def test_columns(self):
        v = vizier.core.Vizier(columns=['Vmag', 'B-V', '_RAJ2000', '_DEJ2000'])
        assert len(v.columns) == 4

    def test_columns_unicode(self):
        v = vizier.core.Vizier(columns=[u'Vmag', u'B-V',
                                        u'_RAJ2000', u'_DEJ2000'])
        assert len(v.columns) == 4

    def test_column_filters(self):
        v = vizier.core.Vizier(column_filters={'Vmag': '>10'})
        assert len(v.column_filters) == 1

    def test_column_filters_unicode(self):
        v = vizier.core.Vizier(column_filters={u'Vmag': u'>10'})
        assert len(v.column_filters) == 1

    def test_get_catalog_metadata(self):
        v = vizier.core.Vizier(catalog="test")
        request_dict = v.get_catalog_metadata(get_query_payload=True)
        assert request_dict["REQUEST"] == "doQuery"
        assert "WHERE ivoid = 'ivo://cds.vizier/test'" in request_dict["QUERY"]
        with pytest.raises(ValueError, match="No catalog name was provided"):
            vizier.core.Vizier().get_catalog_metadata()

    def test_get_catalog_metadata_empty_result(self, monkeypatch):
        """Checks that an empty result raises a meaningful error."""
        v = vizier.core.Vizier(catalog="should_return_empty_result")

        def return_empty_votable(_):
            if commons.ASTROPY_LT_6_0:
                table = votree.Table(votree.VOTableFile())
            else:
                table = votree.TableElement(votree.VOTableFile())
            return table

        monkeypatch.setattr(registry.regtap.RegistryQuery, "execute",
                            return_empty_votable)
        with pytest.raises(EmptyResponseError, match="'*' was not found in VizieR*"):
            v.get_catalog_metadata()
