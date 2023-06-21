# Licensed under a 3-clause BSD style license - see LICENSE.rst

import io
import os
import pytest

from astropy.io import votable
from astropy.table import Table
from astroquery.utils.mocks import MockResponse
from astroquery.ipac.irsa import Most
from astropy.utils.diff import report_diff_values


# each MOST query is given a PID and a temporary directory availible publicly
# from this base URL. This URL is then used to create links on the returned
# HTML page and data returned to the user
REGULAR_BASE_URL = "https://irsa.ipac.caltech.edu/workspace/TMP_FmruWd_8104/MOST/pid17003/"
FULL_BASE_URL = "https://irsa.ipac.caltech.edu/workspace/TMP_FmruWd_8104/MOST/pid10459/"


# When in Regular or Full output mode, there are 2 GET requests for each
# query_object call that fetch the results and metadata separately. Since Full
# and Regular are two different jobs with two different PIDs we need individual
# results files
GET_FILENAME_MAP = {
    REGULAR_BASE_URL+"results.tbl": "most_regular_results.tbl",
    REGULAR_BASE_URL+"imgframes_matched_final_table.tbl": "most_regular_metadata.tbl",
    FULL_BASE_URL+"results.tbl": "most_full_results.tbl",
    FULL_BASE_URL+"imgframes_matched_final_table.tbl": "most_full_metadata.tbl",
    "https://irsa.ipac.caltech.edu/applications/MOST/": "MOST_application.html"
}


# In brief, votable and gator output modes MOST includes the results, a text
# file, in the reponse to the POST request. We return these without making
# additional GET requests, unlike above. Which file should be returned can be
# determined from the output_mode given in the POST request.
POST_FILENAME_MAP = {
    "Regular": "MOST_regular.html",
    "Full": "MOST_full_with_tarballs.html",
    "VOTable": "most_votable.xml",
    "Brief": "most_regular_results.tbl",
    "Gator": "most_gator.tbl"
}


class MockResponse(MockResponse):
    """
    We overwrite the default MockResponse to provide it wih `ok`
    attribute. In these tests it is assumed they are all expected
    to pass so it's fine to put it always True.

    This is ok, these tests can really only cover parsing errors
    because the mocking of failure cases of MOST is too complicated.
    These tests are farmed out to remote data tests.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ok = True


def data_path(filename):
    """Returns the path to the file in the module's test data directory."""
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)


def get_mocked_response(method=None, url=None, data=None, timeout=120, **kwargs):
    """Returns an appropriate MockedResponse based on type and content of the request."""
    if method == "GET":
        filepath = data_path(GET_FILENAME_MAP[url])
    else:
        filepath = data_path(POST_FILENAME_MAP[data["output_mode"]])

    with open(filepath, 'rb') as infile:
        content = infile.read()

    return MockResponse(content, **kwargs)


@pytest.fixture
def patch_requests(request):
    mp = request.getfixturevalue("monkeypatch")
    mp.setattr(Most, '_request', get_mocked_response)
    return mp


def test_validation(patch_requests):
    """Tests MOST parameter validation."""
    with pytest.raises(ValueError, match="When input type is 'name_input' key 'obj_name' is required."):
        Most.query_object()

    with pytest.raises(ValueError, match="When input type is 'name_input' key 'obj_name' is required."):
        Most.query_object(catalog="wise_allsky_4band")

    # make sure no funny business happens with
    # overwriting of default values
    Most.query_object(
        catalog="wise_allsky_4band",
        obj_name="Victoria"
    )
    Most.query_object(
        catalog="wise_allsky_4band",
        obj_name="Victoria",
        input_mode="name_input"
    )

    with pytest.raises(ValueError, match="When obj_type is 'Asteroid', 'semimajor_axis' is required."):
        # fails because insufficient orbital parameters specified
        Most.query_object(
            catalog="wise_allsky_4band",
            output_mode="Brief",
            input_mode="manual_input",
            obj_type="Asteroid",
            perih_dist=1.5,
            eccentricity=0.5
        )

    Most.query_object(
        catalog="wise_allsky_4band",
        output_mode="Brief",
        input_mode="manual_input",
        obj_type="Asteroid",
        semimajor_axis=2.68,
        eccentricity=0.33,
    )

    with pytest.raises(ValueError, match="When obj_type is 'Comet', 'perih_dist' is required."):
        # Comets require perihel_dist keyword
        # instead of smimajor_axis
        Most.query_object(
            catalog="wise_allsky_4band",
            output_mode="Brief",
            input_mode="manual_input",
            obj_type="Comet",
            semimajor_axis=2.68,
            eccentricity=0.33
        )

    with pytest.raises(ValueError, match="Object type is case sensitive and must be one of: 'Asteroid' or 'Comet'"):
        # object type is case sensitive
        Most.query_object(
            catalog="wise_allsky_4band",
            output_mode="Brief",
            input_mode="manual_input",
            obj_type="comet",
            semimajor_axis=2.68,
            eccentricity=0.33
        )

    with pytest.raises(ValueError, match="When input type is 'mpc_input' key 'obj_type' is required."):
        # missing mpc_data and obj_type
        Most.query_object(
            catalog="wise_allsky_4band",
            output_mode="Brief",
            input_mode="mpc_input"
        )

    response = Most.query_object(
        catalog="wise_allsky_4band",
        output_mode="Brief",
        input_mode="mpc_input",
        obj_type="Asteroid",
        mpc_data="K10N010+2010+08+16.1477+1.494525+0.533798+153.4910+113.2118+12.8762+20100621+17.0+4.0+P/2010+N1+(WISE)+MPC+75712"  # noqa: E501
    )
    assert len(response) > 0


def test_regular(patch_requests):
    """Tests the default MOST query returns expected results."""
    results = Most.query_object(obj_name="Victoria")

    assert "results" in results
    assert "metadata" in results
    assert "region" in results
    assert "fits_tarball" not in results
    assert "region_tarball" not in results

    expected_results = Table.read(data_path("most_regular_results.tbl"), format="ipac")
    expected_metadata = Table.read(data_path("most_imgframes_matched_final_table.tbl"), format="ipac")
    url = REGULAR_BASE_URL + "ds9region/ds9_orbit_path.reg"

    silent_stream = io.StringIO()
    assert report_diff_values(expected_results, results["results"], silent_stream)
    assert report_diff_values(expected_metadata, results["metadata"], silent_stream)
    assert url == results["region"]


def test_get_full_with_tarballs(patch_requests):
    response = Most.query_object(
        obj_name="Victoria",
        output_mode="Full",
        with_tarballs=True
    )

    assert "results" in response
    assert "metadata" in response
    assert "region" in response
    assert "fits_tarball" in response
    assert "region_tarball" in response

    results = Table.read(data_path("most_full_results.tbl"), format="ipac")
    metadata = Table.read(data_path("most_imgframes_matched_final_table.tbl"), format="ipac")
    url = FULL_BASE_URL + "ds9region/ds9_orbit_path.reg"
    region_tar = FULL_BASE_URL + "ds9region_A850RA.tar"
    fits_tar = FULL_BASE_URL + "fitsimage_A850RA.tar.gz"

    silent_stream = io.StringIO()
    assert report_diff_values(results, response["results"], silent_stream)
    assert report_diff_values(metadata, response["metadata"], silent_stream)
    assert url == response["region"]
    assert region_tar == response["region_tarball"]
    assert fits_tar == response["fits_tarball"]


def test_votable(patch_requests):
    response = Most.query_object(
        output_mode="VOTable",
        obj_name="Victoria"
    )

    vtbl = votable.parse(data_path("most_votable.xml"))
    silent_stream = io.StringIO()
    assert report_diff_values(response, vtbl, silent_stream)


def test_list_catalogs(patch_requests):
    expected = [
        '2mass', 'spitzer_bcd', 'ptf', 'sofia', 'wise_merge', 'wise_allsky_4band',
        'wise_allsky_3band', 'wise_allsky_2band', 'wise_neowiser',
        'wise_neowiser_yr1', 'wise_neowiser_yr2', 'wise_neowiser_yr3',
        'wise_neowiser_yr4', 'wise_neowiser_yr5', 'wise_neowiser_yr6',
        'wise_neowiser_yr7', 'wise_neowiser_yr8', 'wise_neowiser_yr9', 'ztf',
        'wise_merge_int', 'wise_neowiser_int', 'wise_neowiser_yr10'
    ]

    response = Most.list_catalogs()

    assert response == expected


def test_gator(patch_requests):
    response = Most.query_object(
        output_mode="Gator",
        obj_name="Victoria"
    )

    tbl = Table.read(data_path("most_gator.tbl"), format="ipac")
    silent_stream = io.StringIO()
    assert report_diff_values(tbl, response, silent_stream)
