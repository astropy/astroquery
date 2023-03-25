# Licensed under a 3-clause BSD style license - see LICENSE.rst

import io
import os
import pytest

from astropy.io import votable
from astropy.table import Table
from astroquery.utils.mocks import MockResponse
from astroquery.ipac.irsa.most import Most
from astropy.utils.diff import report_diff_values


OUTPUTMODE_FILE_MAP = {
    "Regular": "MOST_regular.html",
    "Full": "MOST_full_with_tarballs.html",
    "VOTable": "MOST_VOTable.xml",
    "Brief": "most_results_table.tbl",
    "Gator": "most_gator_table.tbl"
}


def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)


def get_mocked_return(method=None, url=None, data=None, timeout=120, **kwargs):
    if "results.tbl" in url:
        url = "most_results_table.tbl"
    elif "imgframes_matched_final_table.tbl" in url:
        url = "most_imgframes_matched_final_table.tbl"
    elif "applications" in url:
        url = "MOST_application.html"

    if method == "GET":
        filename = data_path(url)
    else:
        filename = data_path(OUTPUTMODE_FILE_MAP[data["output_mode"]])

    with open(filename, 'rb') as infile:
        content = infile.read()

    return MockResponse(content, **kwargs)


@pytest.fixture
def patch_get_regular(request):
    mp = request.getfixturevalue("monkeypatch")
    mp.setattr(Most, '_request', get_mocked_return)
    return mp


def test_validation(patch_get_regular):
    with pytest.raises(ValueError):
        Most.query_object()

    with pytest.raises(ValueError):
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

    with pytest.raises(ValueError):
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

    with pytest.raises(ValueError):
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

    with pytest.raises(ValueError):
        # object type is case sensitive
        Most.query_object(
            catalog="wise_allsky_4band",
            output_mode="Brief",
            input_mode="manual_input",
            obj_type="comet",
            semimajor_axis=2.68,
            eccentricity=0.33
        )

    with pytest.raises(ValueError):
        # missing mpc_data and obj_type
        Most.query_object(
            catalog="wise_allsky_4band",
            output_mode="Brief",
            input_mode="mpc_input"
        )

    Most.query_object(
        catalog="wise_allsky_4band",
        output_mode="Brief",
        input_mode="mpc_input",
        obj_type="Asteroid",
        mpc_data="K10N010+2010+08+16.1477+1.494525+0.533798+153.4910+113.2118+12.8762+20100621+17.0+4.0+P/2010+N1+(WISE)+MPC+75712"  # noqa: E501
    )


def test_regular(patch_get_regular):
    response = Most.query_object(obj_name="Victoria")

    assert "results" in response
    assert "metadata" in response
    assert "region" in response
    assert "fits_tarball" not in response
    assert "region_tarball" not in response

    results = Table.read(data_path("most_results_table.tbl"), format="ipac")
    metadata = Table.read(data_path("most_imgframes_matched_final_table.tbl"), format="ipac")
    url = "https://irsa.ipac.caltech.edu/workspace/TMP_noPis4_23270/MOST/pid30587/ds9region/ds9_orbit_path.reg"

    silent_stream = io.StringIO()
    assert report_diff_values(results, response["results"], silent_stream)
    assert report_diff_values(metadata, response["metadata"], silent_stream)
    assert url == response["region"]


def test_get_full_with_tarballs(patch_get_regular):
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

    results = Table.read(data_path("most_results_table.tbl"), format="ipac")
    metadata = Table.read(data_path("most_imgframes_matched_final_table.tbl"), format="ipac")
    url = "https://irsa.ipac.caltech.edu/workspace/TMP_noPis4_23270/MOST/pid1957/ds9region/ds9_orbit_path.reg"
    region_tar = "https://irsa.ipac.caltech.edu/workspace/TMP_noPis4_23270/MOST/pid1957/ds9region_A850RA.tar"
    fits_tar = "https://irsa.ipac.caltech.edu/workspace/TMP_noPis4_23270/MOST/pid1957/fitsimage_A850RA.tar.gz"

    silent_stream = io.StringIO()
    assert report_diff_values(results, response["results"], silent_stream)
    assert report_diff_values(metadata, response["metadata"], silent_stream)
    assert url == response["region"]
    assert region_tar == response["region_tarball"]
    assert fits_tar == response["fits_tarball"]


def test_votable(patch_get_regular):
    response = Most.query_object(
        output_mode="VOTable",
        obj_name="Victoria"
    )

    vtbl = votable.parse(data_path("MOST_VOTable.xml"))
    silent_stream = io.StringIO()
    assert report_diff_values(response, vtbl, silent_stream)


def test_list_catalogs(patch_get_regular):
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


def test_gator(patch_get_regular):
    response = Most.query_object(
        output_mode="Gator",
        obj_name="Victoria"
    )

    tbl = Table.read(data_path("most_gator_table.tbl"), format="ipac")
    silent_stream = io.StringIO()
    assert report_diff_values(tbl, response, silent_stream)
