# Licensed under a 3-clause BSD style license - see LICENSE.rst

import pytest
from astropy.coordinates import SkyCoord
from astropy.table import Table
import astropy.units as u

from astroquery.ipac.irsa import Irsa, IrsaClass
from astroquery.exceptions import InvalidQueryError

OBJ_LIST = ["00h42m44.330s +41d16m07.50s",
            SkyCoord(l=121.1743 * u.deg, b=-21.5733 * u.deg, frame="galactic")]

SIZE_LIST = [2 * u.arcmin, '0d2m0s']


@pytest.mark.parametrize("coordinates", OBJ_LIST)
@pytest.mark.parametrize("radius", SIZE_LIST)
def test_query_region_cone(coordinates, radius):
    query = Irsa.query_region(coordinates, catalog='fp_psc', spatial='Cone', radius=radius,
                              get_query_payload=True)

    # We don't fully float compare in this string, there are slight differences due to the name-coordinate
    # resolution and conversions
    assert "SELECT * FROM fp_psc WHERE CONTAINS(POINT('ICRS',ra,dec),CIRCLE('ICRS',10.68" in query
    assert ",41.26" in query
    assert ",0.0333" in query


@pytest.mark.parametrize("coordinates", OBJ_LIST)
@pytest.mark.parametrize("width", SIZE_LIST)
def test_query_region_box(coordinates, width):
    query = Irsa.query_region(coordinates, catalog='fp_psc', spatial='Box', width=2 * u.arcmin,
                              get_query_payload=True)

    assert "SELECT * FROM fp_psc WHERE CONTAINS(POINT('ICRS',ra,dec),BOX('ICRS',10.68" in query
    assert ",41.26" in query
    assert ",0.0333" in query


poly1 = [SkyCoord(ra=10.1 * u.deg, dec=10.1 * u.deg),
         SkyCoord(ra=10.0 * u.deg, dec=10.1 * u.deg),
         SkyCoord(ra=10.0 * u.deg, dec=10.0 * u.deg)]
poly2 = [(10.1 * u.deg, 10.1 * u.deg), (10.0 * u.deg, 10.1 * u.deg),
         (10.0 * u.deg, 10.0 * u.deg)]


@pytest.mark.parametrize("polygon", [poly1, poly2])
def test_query_region_polygon(polygon):
    query1 = Irsa.query_region(catalog="fp_psc", spatial="Polygon", polygon=polygon,
                               get_query_payload=True)
    query2 = Irsa.query_region("m31", catalog="fp_psc", spatial="polygon", polygon=polygon,
                               get_query_payload=True)

    assert query1 == query2
    assert query1 == ("SELECT * FROM fp_psc "
                      "WHERE CONTAINS(POINT('ICRS',ra,dec),POLYGON('ICRS',10.1,10.1,10.0,10.1,10.0,10.0))=1")


def test_query_allsky():
    query1 = Irsa.query_region(catalog="fp_psc", spatial="All-Sky", get_query_payload=True)
    query2 = Irsa.query_region("m31", catalog="fp_psc", spatial="allsky", get_query_payload=True)

    assert query1 == query2 == "SELECT * FROM fp_psc"


@pytest.mark.parametrize('spatial', ['random_nonsense', 'invalid'])
def test_spatial_invalid(spatial):
    with pytest.raises(ValueError):
        Irsa.query_region(OBJ_LIST[0], catalog='invalid_spatial', spatial=spatial)


def test_no_catalog():
    with pytest.raises(InvalidQueryError):
        Irsa.query_region("m31", spatial='Cone')


def test_deprecated_namespace_import_warning():
    with pytest.warns(DeprecationWarning):
        import astroquery.irsa  # noqa: F401


@pytest.fixture
def irsa_mocked_collections(monkeypatch):
    """An ``IrsaClass`` instance with the collection listing stubbed out, along
    with the list of servicetypes it has been looked up for."""
    irsa = IrsaClass()
    lookups = []

    def mock_list_collections(*, servicetype=None, filter=None):
        lookups.append(servicetype)
        collections = {'SIA': ['spitzer_seip', 'wise_allwise'],
                       'SSA': ['sofia_exes']}[servicetype]
        return Table({'collection': collections})

    monkeypatch.setattr(irsa, 'list_collections', mock_list_collections)
    return irsa, lookups


def test_query_sia_invalid_collection(irsa_mocked_collections):
    irsa, _ = irsa_mocked_collections
    with pytest.raises(InvalidQueryError, match="'foobar' is not a valid SIA collection."):
        irsa.query_sia(collection='foobar')


def test_query_ssa_invalid_collection(irsa_mocked_collections):
    irsa, _ = irsa_mocked_collections
    with pytest.raises(InvalidQueryError, match="'foobar' is not a valid SSA collection."):
        irsa.query_ssa(collection='foobar')


def test_invalid_collection_close_match(irsa_mocked_collections):
    irsa, _ = irsa_mocked_collections
    with pytest.raises(InvalidQueryError, match="Did you mean 'wise_allwise'\\?"):
        irsa.query_sia(collection='wise_allwize')


def test_invalid_collection_no_close_match(irsa_mocked_collections):
    irsa, _ = irsa_mocked_collections
    with pytest.raises(InvalidQueryError, match="use Irsa.list_collections\\(servicetype='SIA'\\)"):
        irsa.query_sia(collection='foobar')


def test_invalid_collection_in_list(irsa_mocked_collections):
    """``collection`` also accepts a list, each of which should be validated."""
    irsa, _ = irsa_mocked_collections
    with pytest.raises(InvalidQueryError, match="'foobar' is not a valid SIA collection."):
        irsa.query_sia(collection=['spitzer_seip', 'foobar'])


@pytest.mark.parametrize('collection', ['spitzer_seip', ['spitzer_seip', 'wise_allwise'], None])
def test_validate_valid_collection(irsa_mocked_collections, collection):
    irsa, _ = irsa_mocked_collections
    irsa._validate_collection(collection=collection, servicetype='SIA')


def test_validate_collection_none_skips_lookup(irsa_mocked_collections):
    irsa, lookups = irsa_mocked_collections
    irsa._validate_collection(collection=None, servicetype='SIA')

    assert lookups == []


def test_validate_collection_is_cached(irsa_mocked_collections):
    irsa, lookups = irsa_mocked_collections
    irsa._validate_collection(collection='spitzer_seip', servicetype='SIA')
    irsa._validate_collection(collection='wise_allwise', servicetype='SIA')
    irsa._validate_collection(collection='sofia_exes', servicetype='SSA')

    # The SIA collections should have been looked up only once, and the SSA ones
    # cached separately from them.
    assert lookups == ['SIA', 'SSA']
