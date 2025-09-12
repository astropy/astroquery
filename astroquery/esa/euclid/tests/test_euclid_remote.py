import astropy.units as u
import pytest
from astropy.coordinates import SkyCoord

from astroquery.esa.euclid import EuclidClass
from astroquery.utils.tap.model.filter import Filter


@pytest.mark.remote_data
def test_query_object_columns_with_radius():
    euclid = EuclidClass()
    sc = SkyCoord(ra=0 * u.deg, dec=0 * u.deg)
    table = euclid.query_object(sc, radius=10 * u.arcsec, columns=['right_ascension'], async_job=True)
    assert table.colnames == ['right_ascension', 'dist']


@pytest.mark.remote_data
@pytest.mark.filterwarnings("ignore::astropy.units.UnitsWarning")
def test_query_object_row_limit():
    euclid = EuclidClass()
    coord = SkyCoord(ra=265.8, dec=64.1, unit=(u.degree, u.degree), frame='icrs')
    width = u.Quantity(0.1, u.deg)
    height = u.Quantity(0.1, u.deg)
    r = euclid.query_object(coordinate=coord, width=width, height=height, async_job=True, verbose=True)

    assert len(r) == 50

    euclid.ROW_LIMIT = 10
    r = euclid.query_object(coordinate=coord, width=width, height=height, async_job=True)

    assert len(r) == 10 == euclid.ROW_LIMIT

    euclid.ROW_LIMIT = -1
    r = euclid.query_object(coordinate=coord, width=width, height=height, async_job=True, verbose=True)

    assert len(r) == 1948


@pytest.mark.remote_data
def test_cone_search_row_limit():
    euclid = EuclidClass()
    coord = SkyCoord(ra=265.8, dec=64.1, unit=(u.degree, u.degree), frame='icrs')
    radius = u.Quantity(0.1, u.deg)
    j = euclid.cone_search(coord, radius=radius, async_job=True)
    r = j.get_results()

    assert len(r) == euclid.ROW_LIMIT

    euclid.ROW_LIMIT = 10
    j = euclid.cone_search(coord, radius=radius, async_job=True)
    r = j.get_results()

    assert len(r) == 10 == euclid.ROW_LIMIT

    euclid.ROW_LIMIT = -1
    j = euclid.cone_search(coord, radius=radius, async_job=True)
    r = j.get_results()

    assert len(r) == 14606


@pytest.mark.remote_data
def test_search_async_jobs():
    euclid = EuclidClass()
    jobfilter = Filter()
    jobfilter.limit = 10
    jobs = euclid.search_async_jobs(jobfilter=jobfilter, verbose=True)
    assert len(jobs) == 10


@pytest.mark.remote_data
def test_get_tables():
    euclid = EuclidClass()
    r = euclid.load_tables()
    assert len(r) > 1

    table = euclid.load_table("catalogue.mer_catalogue")
    assert len(table.columns) == 471
