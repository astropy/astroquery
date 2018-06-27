#!/usr/bin/env python
# -*- coding: utf-8 -*

# Licensed under a 3-clause BSD style license - see LICENSE.rst
import pytest
import os
import json
from sys import getsizeof

from ..core import cds

from astropy import coordinates

DATA_FILES = {
    'CONE_SEARCH': 'cone_search.json',
    'POLYGON_SEARCH': 'polygon_search.json',
    'PROPERTIES_SEARCH': 'properties.json',
    'HIPS_FROM_SAADA_AND_ALASKY': 'hips_from_saada_alasky.json'
}


def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)


@pytest.fixture
def get_request_results():
    """Perform the request using the astroquery.MocServer  API"""

    def process_query(region_type, get_query_payload, verbose, **kwargs):
        request_result = cds.query_region(region_type,
                                          get_query_payload,
                                          verbose,
                                          **kwargs)
        return request_result

    return process_query


@pytest.fixture
def get_true_request_results():
    """
    Get the results of the MocServer

    obtained by performing the request on http://alasky.unistra.fr/MocServer/query
    and saving it into the data directory

    """

    def load_true_result_query(data_file_id):
        filename = data_path(DATA_FILES[data_file_id])
        with open(filename, 'r') as f_in:
            content = f_in.read()
        return json.loads(content)

    return load_true_result_query


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


@pytest.mark.parametrize('type, params, data_file_id',
                         [(cds.RegionType.AllSky, dict(meta_data=meta_data_ex), 'PROPERTIES_SEARCH'),
                          (cds.RegionType.AllSky, dict(meta_data=meta_data_hips_from_saada_alasky),
                           'HIPS_FROM_SAADA_AND_ALASKY')])
def test_request_results(type, params, data_file_id,
                         get_true_request_results,
                         get_request_results):
    """
    Compare the request result obtained with the astroquery.Mocserver API

    with the one obtained on the http://alasky.unistra.fr/MocServer/query
    """
    request_results = get_request_results(region_type=type,
                                          get_query_payload=False,
                                          verbose=True,
                                          **params)
    true_request_results = get_true_request_results(data_file_id=data_file_id)

    assert getsizeof(request_results) == getsizeof(true_request_results)
    assert request_results == true_request_results


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
try:
    from mocpy import MOC

    # test of moc_order payload
    @pytest.mark.parametrize('moc_order', [5, 10])
    def test_moc_order_param(moc_order):
        result = cds.query_region(region_type=cds.RegionType.MOC,
                                  url='http://alasky.u-strasbg.fr/SDSS/DR9/color/Moc.fits',
                                  # return a mocpy obj
                                  output_format=cds.ReturnFormat.moc,
                                  moc_order=moc_order,
                                  get_query_payload=False)

        assert isinstance(result, MOC)


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
except ImportError:
    pass


"""
Tests requiring pyvo

"""
try:
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

except ImportError:
    pass
