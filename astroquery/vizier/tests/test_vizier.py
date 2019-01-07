# Licensed under a 3-clause BSD style license - see LICENSE.rst
import os
import requests
from numpy import testing as npt
import pytest
from astropy.table import Table
import astropy.units as u
import six
from six.moves import urllib_parse as urlparse
from ... import vizier
from ...utils import commons
from ...utils.testing_tools import MockResponse

if six.PY3:
    str, = six.string_types

VO_DATA = {'HIP,NOMAD,UCAC': "viz.xml",
           'NOMAD,UCAC': "viz.xml",
           'B/iram/pdbi': "afgl2591_iram.xml",
           'J/ApJ/706/83': "kang2010.xml"}


def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)


@pytest.fixture
def patch_post(request):
    try:
        mp = request.getfixturevalue("monkeypatch")
    except AttributeError:  # pytest < 3
        mp = request.getfuncargvalue("monkeypatch")
    mp.setattr(requests.Session, 'request', post_mockreturn)
    return mp


def post_mockreturn(self, method, url, data=None, timeout=10, files=None,
                    params=None, headers=None, **kwargs):
    if method != 'POST':
        raise ValueError("A 'post request' was made with method != POST")
    datad = dict([urlparse.parse_qsl(d)[0] for d in data.split('\n')])
    filename = data_path(VO_DATA[datad['-source']])
    content = open(filename, "rb").read()
    return MockResponse(content, **kwargs)


def parse_objname(obj):
    d = {'AFGL 2591': commons.ICRSCoordGenerator(307.35388 * u.deg,
                                                 40.18858 * u.deg)}
    return d[obj]


@pytest.fixture
def patch_coords(request):
    try:
        mp = request.getfixturevalue("monkeypatch")
    except AttributeError:  # pytest < 3
        mp = request.getfuncargvalue("monkeypatch")
    mp.setattr(commons, 'parse_coordinates', parse_objname)
    return mp


@pytest.mark.parametrize(('dim', 'expected_out'),
                         [(5 * u.deg, ('d', 5)),
                          (5 * u.arcmin, ('m', 5)),
                          (5 * u.arcsec, ('s', 5)),
                          (0.314 * u.rad, ('d', 18)),
                          ('5d5m5.5s', ('d', 5.0846))
                          ])
def test_parse_angle(dim, expected_out):
    actual_out = vizier.core._parse_angle(dim)
    actual_unit, actual_value = actual_out
    expected_unit, expected_value = expected_out
    assert actual_unit == expected_unit
    npt.assert_approx_equal(actual_value, expected_value, significant=2)


def test_parse_angle_err():
    with pytest.raises(Exception):
        vizier.core._parse_angle(5 * u.kg)


@pytest.mark.parametrize(('filepath'),
                         list(set(VO_DATA.values())))
def test_parse_result_verbose(filepath, capsys):
    with open(data_path(filepath), 'rb') as f:
        table_contents = f.read()
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
    table_contents = open(data_path(filepath), 'rb').read()
    response = MockResponse(table_contents)
    result = vizier.core.Vizier._parse_result(response)
    assert isinstance(result, commons.TableList)
    assert len(result) == objlen
    assert isinstance(result[result.keys()[0]], Table)


def test_query_region_async(patch_post):
    target = commons.ICRSCoordGenerator(ra=299.590, dec=35.201,
                                        unit=(u.deg, u.deg))
    response = vizier.core.Vizier.query_region_async(
        target, radius=5 * u.deg, catalog=["HIP", "NOMAD", "UCAC"])
    assert response is not None


def test_query_region(patch_post):
    target = commons.ICRSCoordGenerator(ra=299.590, dec=35.201,
                                        unit=(u.deg, u.deg))
    result = vizier.core.Vizier.query_region(target,
                                             radius=5 * u.deg,
                                             catalog=["HIP", "NOMAD", "UCAC"])

    assert isinstance(result, commons.TableList)


def test_query_regions(patch_post):
    """
    This ONLY tests that calling the function works -
    the data currently used for the test is *NOT* appropriate
    for the multi-object query.  There is no test for parsing
    that return (yet - but see test_multicoord in remote_data)
    """
    targets = commons.ICRSCoordGenerator(ra=[299.590, 299.90],
                                         dec=[35.201, 35.201],
                                         unit=(u.deg, u.deg))
    vizier.core.Vizier.query_region(targets,
                                    radius=5 * u.deg,
                                    catalog=["HIP", "NOMAD", "UCAC"])


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
