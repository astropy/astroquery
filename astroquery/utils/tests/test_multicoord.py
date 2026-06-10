# Licensed under a 3-clause BSD style license - see LICENSE.rst
import threading

import pytest

import astropy.units as u
from astropy.coordinates import SkyCoord
from astropy.table import Table
from astropy.utils.decorators import deprecated_renamed_argument
from astropy.utils.exceptions import AstropyDeprecationWarning

from astroquery.utils.commons import TableList
from astroquery.utils.multicoord import support_multiple_coordinates, conf


COORDS = SkyCoord([10, 20, 30] * u.deg, [-10, 0, 10] * u.deg)


class DummyQuery:
    """Single-position query class for exercising the decorator."""

    def __init__(self):
        self.lock = threading.Lock()
        self.active = 0
        self.max_active = 0

    def _track(self):
        with self.lock:
            self.active += 1
            self.max_active = max(self.max_active, self.active)

    def _untrack(self):
        with self.lock:
            self.active -= 1

    @support_multiple_coordinates()
    def query_region(self, coordinates, radius=1 * u.deg):
        if not (isinstance(coordinates, str) or coordinates.isscalar):
            raise TypeError("scalar input required")
        self._track()
        try:
            ra = (coordinates if isinstance(coordinates, str)
                  else str(coordinates.ra.deg))
            result = Table({'ra': [ra], 'radius': [str(radius)]})
        finally:
            self._untrack()
        return result

    @support_multiple_coordinates(coord_arg='coordinates', max_workers=1)
    def query_serial(self, coordinates):
        self._track()
        try:
            with self.lock:
                concurrent = self.active
        finally:
            self._untrack()
        return Table({'concurrent': [concurrent]})

    @support_multiple_coordinates()
    def query_payload(self, coordinates, get_query_payload=False):
        return {'POS': str(coordinates)}

    @support_multiple_coordinates()
    def query_tablelist(self, coordinates):
        return TableList({'mission': Table({'ra': [str(coordinates)]})})


def test_scalar_passthrough():
    result = DummyQuery().query_region(COORDS[0])
    assert isinstance(result, Table)
    assert len(result) == 1
    assert 'query_index' not in result.colnames


def test_string_passthrough():
    result = DummyQuery().query_region("10 -10")
    assert len(result) == 1


def test_vector_skycoord_stacks_in_order():
    result = DummyQuery().query_region(COORDS, radius=2 * u.deg)
    assert isinstance(result, Table)
    assert len(result) == 3
    assert list(result['query_index']) == [0, 1, 2]
    assert list(result['ra']) == [str(c.ra.deg) for c in COORDS]
    assert all(result['radius'] == str(2 * u.deg))


def test_list_of_coordinates():
    result = DummyQuery().query_region([COORDS[0], COORDS[1]])
    assert len(result) == 2
    assert list(result['query_index']) == [0, 1]


def test_list_of_strings():
    result = DummyQuery().query_region(["10 -10", "20 0"])
    assert list(result['ra']) == ["10 -10", "20 0"]


def test_empty_list_raises():
    with pytest.raises(ValueError, match="empty list"):
        DummyQuery().query_region([])


def test_max_workers_one_is_serial():
    dummy = DummyQuery()
    result = dummy.query_serial(list(COORDS))
    assert dummy.max_active == 1
    assert len(result) == 3


def test_parallelism_is_bounded():
    dummy = DummyQuery()
    coords = SkyCoord(range(1, 21) * u.deg, range(1, 21) * u.deg)
    with conf.set_temp('max_parallel_queries', 2), \
            conf.set_temp('min_request_interval', 0):
        dummy.query_region(coords)
    assert dummy.max_active <= 2


def test_non_table_results_return_list():
    result = DummyQuery().query_payload(list(COORDS[:2]), get_query_payload=True)
    assert isinstance(result, list)
    assert len(result) == 2
    assert all('POS' in payload for payload in result)


def test_tablelist_results_merge():
    result = DummyQuery().query_tablelist(list(COORDS[:2]))
    assert isinstance(result, TableList)
    assert len(result['mission']) == 2
    assert list(result['mission']['query_index']) == [0, 1]


def test_missing_coord_arg_raises_at_definition():
    with pytest.raises(TypeError, match="no 'coordinates' parameter"):
        @support_multiple_coordinates()
        def query(self, position):
            pass


def test_composes_with_deprecated_renamed_argument():
    class Legacy:
        @deprecated_renamed_argument("coordinate", "coordinates", since="0.4.12")
        @support_multiple_coordinates()
        def query_region(self, coordinates=None):
            return Table({'ra': [str(coordinates)]})

    with pytest.warns(AstropyDeprecationWarning):
        result = Legacy().query_region(coordinate=["10 -10", "20 0"])
    assert len(result) == 2
