# Licensed under a 3-clause BSD style license - see LICENSE.rst
import os
import requests
from astropy.tests.helper import pytest
from numpy import testing as npt
from astropy.table import Table
from ... import vizier
from ... utils import commons
from ...utils.testing_tools import MockResponse
import astropy.units as u
import astropy.coordinates as coord
import urlparse
VO_DATA = {'HIP,NOMAD,UCAC': "viz.xml",
           'NOMAD,UCAC': "viz.xml",
           'J/ApJ/706/83': "kang2010.xml"}


def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)


@pytest.fixture
def patch_post(request):
    mp = request.getfuncargvalue("monkeypatch")
    mp.setattr(requests, 'post', post_mockreturn)
    return mp


def post_mockreturn(url, data=None, timeout=10, **kwargs):
    datad = dict([urlparse.parse_qsl(d)[0] for d in data.split('\n')]) 
    filename = data_path(VO_DATA[datad['-source']])
    content = open(filename, "r").read()
    return MockResponse(content, **kwargs)


def test_str_to_unit():
    with pytest.raises(KeyError):
        vizier.core._str_to_unit('rad')


@pytest.mark.parametrize(('dim', 'expected_out'),
                         [(5 * u.deg, ('d', 5)),
                          (5 * u.arcmin, ('m', 5)),
                          (5 * u.arcsec, ('s', 5)),
                          (0.314 * u.rad, ('d', 18)),
                          ('5d5m5.5s', ('d', 5.0846))
                          ])
def test_parse_dimension(dim, expected_out):
    actual_out = vizier.core._parse_dimension(dim)
    actual_unit, actual_value = actual_out
    expected_unit, expected_value = expected_out
    assert actual_unit == expected_unit
    npt.assert_approx_equal(actual_value, expected_value, significant=2)


def test_parse_dimension_err():
    with pytest.raises(Exception):
        vizier.core._parse_dimension(5 * u.kg)

@pytest.mark.parametrize(('filepath'),
                         list(set(VO_DATA.values())))
def test_parse_result_verbose(filepath, capsys):
    with open(data_path(filepath), 'r') as f:
        table_contents = f.read()
    response = MockResponse(table_contents)
    vizier.core.Vizier._parse_result(response)
    out, err = capsys.readouterr()
    assert out == ''


@pytest.mark.parametrize(('filepath','objlen'),
                         [('viz.xml',231),
                          ('kang2010.xml',1)]) # TODO: 1->50 because it is just 1 table
def test_parse_result(filepath, objlen):
    table_contents = open(data_path(filepath), 'r').read()
    response = MockResponse(table_contents)
    result = vizier.core.Vizier._parse_result(response)
    assert isinstance(result, commons.TableList)
    assert len(result) == objlen
    assert isinstance(result[result.keys()[0]], Table)


def test_query_region_async(patch_post):
    response = vizier.core.Vizier.query_region_async(coord.ICRSCoordinates(ra=299.590, dec=35.201, unit=(u.deg, u.deg)),
                                                     radius=5 * u.deg,
                                                     catalog=["HIP", "NOMAD", "UCAC"])
    assert response is not None


def test_query_region(patch_post):
    result = vizier.core.Vizier.query_region(coord.ICRSCoordinates(ra=299.590, dec=35.201, unit=(u.deg, u.deg)),
                                             radius=5 * u.deg,
                                             catalog=["HIP", "NOMAD", "UCAC"])

    assert isinstance(result, commons.TableList)


def test_query_object_async(patch_post):
    response = vizier.core.Vizier.query_object_async("HD 226868", catalog=["NOMAD", "UCAC"])
    assert response is not None


def test_query_object(patch_post):
    result = vizier.core.Vizier.query_object("HD 226868", catalog=["NOMAD", "UCAC"])
    assert isinstance(result, commons.TableList)


def test_get_catalogs_async(patch_post):
    response = vizier.core.Vizier.get_catalogs_async('J/ApJ/706/83')
    assert response is not None


def test_get_catalogs(patch_post):
    result = vizier.core.Vizier.get_catalogs('J/ApJ/706/83')
    assert isinstance(result, commons.TableList)


class TestVizierClass:

    def test_empty_init(self):
        v = vizier.core.Vizier()
        assert v.keywords is None
        assert v.columns is None
        assert v.column_filters is None

    def test_keywords(self):
        v = vizier.core.Vizier(keywords=['optical', 'chandra', 'ans'])
        assert str(v.keywords) == '-kw.Wavelength=optical\n-kw.Mission=ANS,Chandra'
        v = vizier.core.Vizier(keywords=['xy', 'optical'])
        assert str(v.keywords) == '-kw.Wavelength=optical'
        v.keywords = ['optical', 'cobe']
        assert str(v.keywords) == '-kw.Wavelength=optical\n-kw.Mission=COBE'
        del v.keywords
        assert v.keywords is None

    def test_columns(self):
        v = vizier.core.Vizier(columns=['Vmag', 'B-V', '_RAJ2000', '_DEJ2000'])
        assert len(v.columns) == 4
        del v.columns
        assert v.columns is None

    def test_column_filters(self):
        with pytest.raises(Exception):
            v = vizier.core.Vizier(column_filters={"Plx":">50"})
        with pytest.raises(Exception):
            v = vizier.core.Vizier(columns=['B-V'], column_filters={"Vmag":"<12.5"})
        v = vizier.core.Vizier(columns=['Vmag', 'B-V'], column_filters={'Vmag':"<12.5"})
        assert 'Vmag' in v.column_filters
        with pytest.raises(Exception):
            del v.columns
        del v.column_filters
        assert v.column_filters is None

class TestVizierKeywordClass:

    def test_init(self):
        v = vizier.core.VizierKeyword(keywords=['cobe', 'xmm'])
        assert v.keyword_dict is not None

    def test_keywords(self, capsys):
        vizier.core.VizierKeyword(keywords=['xxx','coBe'])
        out, err = capsys.readouterr()
        # warning must be emitted
        assert out != ""

