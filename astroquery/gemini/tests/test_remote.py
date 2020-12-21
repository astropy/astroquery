""" Test Gemini Astroquery module.

Remote tests to exercise interaction with the actual REST service.

For information on how/why this test is built the way it is, see the astroquery
documentation at:

https://astroquery.readthedocs.io/en/latest/testing.html
"""
import pytest

import os
import shutil
import tempfile

from astropy import units
from astropy.coordinates import SkyCoord
from astropy.table import Table

from astroquery import gemini


""" Coordinates to use for testing """
coords = SkyCoord(210.80242917, 54.34875, unit="deg")


@pytest.mark.remote_data
class TestGemini:
    def test_observations_query_region(self):
        """ test query against a region of the sky against actual archive """
        result = gemini.Observations.query_region(coords, radius=0.3 * units.deg)
        assert isinstance(result, Table)
        assert len(result) > 0

    def test_observations_query_criteria(self):
        """ test query against an instrument/program via criteria against actual archive """
        result = gemini.Observations.query_criteria(instrument='GMOS-N', program_id='GN-CAL20191122',
                                                    observation_type='BIAS')
        assert isinstance(result, Table)
        assert len(result) > 0

    def test_observations_query_criteria_ascending_sort(self):
        """ test query against an instrument/program via criteria against actual archive """
        result = gemini.Observations.query_criteria(instrument='GMOS-N', program_id='GN-CAL20191122',
                                                    observation_type='BIAS', orderby='filename_asc')
        assert isinstance(result, Table)
        assert len(result) > 0
        last = None
        for row in result:
            assert last is None or last <= row['filename']
            last = row['filename']

    def test_observations_query_criteria_descending_sort(self):
        """ test query against an instrument/program via criteria against actual archive """
        result = gemini.Observations.query_criteria(instrument='GMOS-N', program_id='GN-CAL20191122',
                                                    observation_type='BIAS', orderby='filename_desc')
        assert isinstance(result, Table)
        assert len(result) > 0
        # server is not respecting descending filename sort.  This is not an issue with the
        # astroquery side, but for now I am not validating the results until it gets fixed
        # in the webservice.

    def test_observations_query_raw(self):
        """ test querying raw against actual archive """
        result = gemini.Observations.query_raw('GMOS-N', 'BIAS', progid='GN-CAL20191122')
        assert isinstance(result, Table)
        assert len(result) > 0

    def test_get_file(self):
        """ test querying raw against actual archive """
        tempdir = tempfile.mkdtemp('_gemini_test')
        filename = '20190105_GN-CAL20190105_obslog.txt'
        gemini.Observations.get_file(filename, download_dir=tempdir)
        filepath = os.path.join(tempdir, filename)
        assert os.path.isfile(filepath)
        assert os.stat(filepath).st_size == 7624
        if os.path.exists(filepath):
            os.unlink(filepath)
        if os.path.exists(tempdir):
            shutil.rmtree(tempdir)
