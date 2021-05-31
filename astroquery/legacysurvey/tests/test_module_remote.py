# Licensed under a 3-clause BSD style license - see LICENSE.rst


# performs similar tests as test_module.py, but performs
# the actual HTTP request rather than monkeypatching them.
# should be disabled or enabled at will - use the
# remote_data decorator from astropy:

import pytest
from astropy.table import Table

@pytest.mark.remote_data
class TestLegacySurveyClass:
    # now write tests for each method here
    def test_this(self):
        import astroquery.legacysurvey

        # TODO: add other parameters
        table = astroquery.legacysurvey.LegacySurvey.query_object("Mrk421") # type: Table

        print(table)

        assert len(table) > 10
