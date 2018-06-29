#!/usr/bin/env python
# -*- coding: utf-8 -*

# Licensed under a 3-clause BSD style license - see LICENSE.rst
import sys
import pytest
import os
import json
from sys import getsizeof
import requests
from ..core import cds

from astropy import coordinates
from ...utils.testing_tools import MockResponse

try:
    import pyvo as vo
except ImportError:
    pass

try:
    from mocpy import MOC
except ImportError:
    pass


DATA_FILES = {
    'PROPERTIES_SEARCH': 'properties.json',
    'HIPS_FROM_SAADA_AND_ALASKY': 'hips_from_saada_alasky.json'
}


@pytest.fixture
def patch_get(request):
    try:
        mp = request.getfixturevalue("monkeypatch")
    except AttributeError:  # pytest < 3
        mp = request.getfuncargvalue("monkeypatch")
    mp.setattr(requests.Session, 'request', get_mockreturn)
    return mp


def get_mockreturn(self, method, url, data=None, timeout=10,
                   files=None, params=None, headers=None, **kwargs):
    filename = data_path(DATA_FILES[data])
    content = open(filename, 'rb').read()
    return MockResponse(content)


def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)


"""List of all the constrain we want to test"""
# SPATIAL CONSTRAINTS DEFINITIONS
polygon1 = coordinates.SkyCoord([57.376, 56.391, 56.025, 56.616], [24.053, 24.622, 24.049, 24.291],
                                frame="icrs",
                                unit="deg")
polygon2 = coordinates.SkyCoord([58.376, 53.391, 56.025, 54.616], [24.053, 25.622, 22.049, 27.291],
                                frame="icrs",
                                unit="deg")

# PROPERTY CONSTRAINTS DEFINITIONS
meta_data_ex = 'ID = *SDSS* && moc_sky_fraction<=0.01'
meta_data_hips_from_saada_alasky = '(hips_service_url*=http://saada*) && (hips_service_url*=http://alasky.*)'
"""
Combination of one spatial with a property constrain

Each tuple(spatial, property) characterizes a specific query and is tested
with regards to the true results stored in a file located in the data directory

"""


@pytest.mark.parametrize('datafile',
                         ['PROPERTIES_SEARCH', 'HIPS_FROM_SAADA_AND_ALASKY'])
def test_request_results(patch_get, datafile):
    """
    Compare the request result obtained with the astroquery.Mocserver API

    with the one obtained on the http://alasky.unistra.fr/MocServer/query
    """
    results = cds.query_region(region_type=cds.RegionType.AllSky,
                               get_query_payload=False,
                               verbose=True,
                               data=datafile)
    assert results is not None


"""
Spatial Constrains requests

We test a polygon/cone/moc search and ensure the
request param 'intersect' is correct

"""


@pytest.mark.parametrize('RA, DEC, RADIUS',
                         [(10.8, 6.5, 0.5),
                          (25.6, -23.2, 1.1),
                          (150.6, 45.1, 1.5)])
def test_cone_search_spatial_request(RA, DEC, RADIUS):
    center = coordinates.SkyCoord(ra=RA, dec=DEC, unit="deg")
    radius = coordinates.Angle(RADIUS, unit="deg")

    request_payload = cds.query_region(region_type=cds.RegionType.Cone,
                                       get_query_payload=True,
                                       center=center,
                                       radius=radius,
                                       intersect='overlaps')

    assert (request_payload['DEC'] == str(DEC)) and \
           (request_payload['RA'] == str(RA)) and \
           (request_payload['SR'] == str(RADIUS))


@pytest.mark.parametrize('poly, poly_payload',
                         [(polygon1, 'Polygon 57.376 24.053 56.391 24.622 56.025 24.049 56.616 24.291'),
                          (polygon2, 'Polygon 58.376 24.053 53.391 25.622 56.025 22.049 54.616 27.291')])
def test_polygon_spatial_request(poly, poly_payload):
    request_payload = cds.query_region(region_type=cds.RegionType.Polygon,
                                       vertices=poly,
                                       intersect='overlaps',
                                       get_query_payload=True)

    assert request_payload['stc'] == poly_payload


@pytest.mark.parametrize('intersect',
                         ['encloses', 'overlaps', 'covers'])
def test_intersect_param(intersect):
    center = coordinates.SkyCoord(ra=10.8, dec=32.2, unit="deg")
    radius = coordinates.Angle(1.5, unit="deg")
    request_payload = cds.query_region(region_type=cds.RegionType.Cone,
                                       intersect=intersect,
                                       center=center,
                                       radius=radius,
                                       get_query_payload=True)
    if intersect == 'encloses':
        assert request_payload['intersect'] == 'enclosed'
    else:
        assert request_payload['intersect'] == intersect


# test of MAXREC payload
@pytest.mark.parametrize('max_rec', [3, 10, 25, 100])
def test_max_rec_param(max_rec):
    center = coordinates.SkyCoord(ra=10.8, dec=32.2, unit="deg")
    radius = coordinates.Angle(1.5, unit="deg")
    result = cds.query_region(region_type=cds.RegionType.Cone,
                              center=center,
                              radius=radius,
                              max_rec=max_rec,
                              get_query_payload=False)

    assert max_rec == len(result)


"""
Tests requiring mocpy

"""


# test of moc_order payload
@pytest.mark.skipif('mocpy' not in sys.modules,
                    reason="requires the mocpy library")
@pytest.mark.parametrize('moc_order', [5, 10])
def test_moc_order_param(moc_order):
    result = cds.query_region(region_type=cds.RegionType.MOC,
                              url='http://alasky.u-strasbg.fr/SDSS/DR9/color/Moc.fits',
                              # return a mocpy obj
                              output_format=cds.ReturnFormat.moc,
                              moc_order=moc_order,
                              get_query_payload=False)

    assert isinstance(result, MOC)


@pytest.mark.skipif('mocpy' not in sys.modules,
                    reason="requires the mocpy library")
def test_from_mocpy_obj():
    moc = MOC()
    moc.add_pix(order=5, i_pix=3, nest=True)
    moc.add_pix(order=9, i_pix=34, nest=True)
    moc.add_pix(order=9, i_pix=35, nest=True)
    moc.add_pix(order=9, i_pix=36, nest=True)
    result = cds.query_region(region_type=cds.RegionType.MOC,
                              moc=moc,
                              get_query_payload=True)

    from ast import literal_eval
    assert literal_eval(result['moc']) == {"5": [3],
                                           "9": [34, 35, 36]}


"""
Tests requiring pyvo

"""


@pytest.mark.skipif('pyvo' not in sys.modules,
                    reason="requires the pyvo library")
# test of field_l when retrieving dataset records
@pytest.mark.parametrize('field_l', [['ID'],
                                     ['ID', 'moc_sky_fraction'],
                                     ['data_ucd', 'vizier_popularity', 'ID'],
                                     ['publisher_id', 'ID']])
def test_field_l_param(field_l):
    center = coordinates.SkyCoord(ra=10.8, dec=32.2, unit="deg")
    radius = coordinates.Angle(1.5, unit="deg")
    datasets = cds.query_region(region_type=cds.RegionType.Cone,
                                center=center,
                                radius=radius,
                                output_format=cds.ReturnFormat.record,
                                meta_var=field_l,
                                get_query_payload=False)
    assert isinstance(datasets, dict)
    for id, dataset in datasets.items():
        at_least_one_field = False
        for field in field_l:
            if field in dataset.properties.keys():
                at_least_one_field = True
                break
        assert at_least_one_field


@pytest.mark.skipif('pyvo' not in sys.modules,
                    reason="requires the pyvo library")
@pytest.mark.parametrize('get_attr, get_attr_str', [(cds.ReturnFormat.id, 'id'),
                                                    (cds.ReturnFormat.record, 'record'),
                                                    (cds.ReturnFormat.number, 'number'),
                                                    (cds.ReturnFormat.moc, 'moc'),
                                                    (cds.ReturnFormat.i_moc, 'imoc')])
def test_get_attribute(get_attr, get_attr_str):
    """Test if the request parameter 'get' works for a basic cone search request"""
    center = coordinates.SkyCoord(ra=10.8, dec=32.2, unit="deg")
    radius = coordinates.Angle(1.5, unit="deg")
    result = cds.query_region(region_type=cds.RegionType.Cone,
                              center=center,
                              radius=radius,
                              output_format=get_attr,
                              get_query_payload=True)

    assert result['get'] == get_attr_str
