# Licensed under a 3-clause BSD style license - see LICENSE.rst


import pytest
from astropy.table import Table

from ..core import hyperleda


@pytest.mark.remote_data
class TestHyperLEDAClass:

    def test_query_object(self):
        result = hyperleda.query_object('UGC12591', properties=['bt', 'vt'])
        assert isinstance(result, Table)
        assert len(result) == 1

    def test_query_sql(self):
        sample_query = "(modbest<=30 and t>=-3 and t<=0 and type='S0') \
        or (modbest<=30 and t>=-3 and t<=0 and type='S0-a')"
        result = hyperleda.query_sql(sample_query, properties='all')
        assert isinstance(result, Table)
        assert len(result) >= 1
