import pytest

from ...xmatch import XMatch


def test_xmatch_query_invalid_max_distance():
    with pytest.raises(ValueError):
        XMatch().query('', '', 181, '')


def test_xmatch_query_invalid_format():
    with pytest.raises(ValueError):
        XMatch().query('', '', 100, 'html')


def test_get_avail_tables_invalid_format():
    with pytest.raises(ValueError):
        XMatch().get_available_tables('votable')
    with pytest.raises(ValueError):
        XMatch().get_available_tables('csv')
    with pytest.raises(ValueError):
        XMatch().get_available_tables('tsv')
