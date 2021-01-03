# Licensed under a 3-clause BSD style license - see LICENSE.rst
import pytest

from ... import lamda


@pytest.mark.remote_data
def test_query():
    result = lamda.Lamda.query(mol='co')
    assert [len(r) for r in result] == [2, 40, 41]
    collider_dict = result[0]
    assert set(collider_dict.keys()) == set(['PH2', 'OH2'])
    assert [len(collider_dict[r]) for r in collider_dict] == [820, 820]
