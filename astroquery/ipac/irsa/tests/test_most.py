# Licensed under a 3-clause BSD style license - see LICENSE.rst

import io
import os
import pytest

from astropy.io import votable
from astropy.table import Table
from astroquery.utils.mocks import MockResponse
from astroquery.ipac.irsa.most import Most
from astropy.utils.diff import report_diff_values


DATA_FILES = {
    "Regular": "MOST_regular.html",
    "Full": "MOST_full_with_tarballs.html",
    "VOTable": "MOST_VOTable.xml",
    "Brief": "most_results_table.tbl",
    "Gator": "most_gator_table.tbl"
}


def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)


@pytest.fixture
def patch_get(request):
    mp = request.getfixturevalue("monkeypatch")
    mp.setattr(Most, '_request', get_mockreturn)
    return mp


def get_mockreturn(method=None, url=None, data=None, timeout=120, **kwargs):
    if method == "GET":
        filename = data_path(url)
    else:
        filename = data_path(DATA_FILES[data["output_mode"]])
    with open(filename, 'rb') as infile:
        content = infile.read()
    return MockResponse(content, **kwargs)


def test_validation(patch_get):
    with pytest.raises(ValueError):
        Most.query()

    with pytest.raises(ValueError):
        Most.query(catalog="wise_allsky_4band")

    # make sure no funny business happens with
    # overwriting of default values
    Most.query(
        catalog="wise_allsky_4band",
        obj_name="Victoria"
    )
    Most.query(
        catalog="wise_allsky_4band",
        obj_name="Victoria",
        input_type="name_input"
    )

    with pytest.raises(ValueError):
        # fails because insufficient orbital parameters specified
        Most.query(
            catalog="wise_allsky_4band",
            output_mode="Brief",
            input_type="manual_input",
            obj_type="Asteroid",
            perih_dist=1.5,
            eccentricity=0.5
        )

    Most.query(
        catalog="wise_allsky_4band",
        output_mode="Brief",
        input_type="manual_input",
        obj_type="Asteroid",
        semimajor_axis=2.68,
        eccentricity=0.33,
    )

    with pytest.raises(ValueError):
        # Comets require perihel_dist keyword
        # instead of smimajor_axis
        Most.query(
            catalog="wise_allsky_4band",
            output_mode="Brief",
            input_type="manual_input",
            obj_type="Comet",
            semimajor_axis=2.68,
            eccentricity=0.33
        )

    with pytest.raises(ValueError):
        # object type is case sensitive
        Most.query(
            catalog="wise_allsky_4band",
            output_mode="Brief",
            input_type="manual_input",
            obj_type="comet",
            semimajor_axis=2.68,
            eccentricity=0.33
        )

    with pytest.raises(ValueError):
        # missing mpc_data and obj_type
        Most.query(
            catalog="wise_allsky_4band",
            output_mode="Brief",
            input_type="mpc_input"
        )

    Most.query(
        catalog="wise_allsky_4band",
        output_mode="Brief",
        input_type="mpc_input",
        obj_type="Asteroid",
        mpc_data="K10N010+2010+08+16.1477+1.494525+0.533798+153.4910+113.2118+12.8762+20100621+17.0+4.0+P/2010+N1+(WISE)+MPC+75712"  # noqa: E501
    )


def test_regular(patch_get):
    response = Most.query(obj_name="Victoria")

    assert "results" in response
    assert "metadata" in response
    assert "region" in response
    assert "fits_tarball" not in response
    assert "region_tarball" not in response

    results = Table.read(data_path("most_results_table.tbl"), format="ipac")
    metadata = Table.read(data_path("most_imgframes_matched_final_table.tbl"), format="ipac")
    url = "https://irsa.ipac.caltech.edu/workspace/TMP_XIBNAd_17194/MOST/pid10499/ds9region/ds9_orbit_path.reg"

    silent_stream = io.StringIO()
    assert report_diff_values(results, response["results"], silent_stream)
    assert report_diff_values(metadata, response["metadata"], silent_stream)
    assert url == response["region"]


def test_get_full_with_tarballs(patch_get):
    response = Most.query(
        obj_name="Victoria",
        output_mode="Full",
        fits_region_files=True
    )

    assert "results" in response
    assert "metadata" in response
    assert "region" in response
    assert "fits_tarball" in response
    assert "region_tarball" in response

    results = Table.read(data_path("most_results_table.tbl"), format="ipac")
    metadata = Table.read(data_path("most_imgframes_matched_final_table.tbl"), format="ipac")
    url = "https://irsa.ipac.caltech.edu/workspace/TMP_XIBNAd_17194/MOST/pid10499/ds9region/ds9_orbit_path.reg"
    region_tar = "https://irsa.ipac.caltech.edu/workspace/TMP_XIBNAd_17194/MOST/pid10499/ds9region_A850RA.tar"
    fits_tar = "https://irsa.ipac.caltech.edu/workspace/TMP_XIBNAd_17194/MOST/pid10499/fitsimage_A850RA.tar.gz"

    silent_stream = io.StringIO()
    assert report_diff_values(results, response["results"], silent_stream)
    assert report_diff_values(metadata, response["metadata"], silent_stream)
    assert url == response["region"]
    assert region_tar == response["region_tarball"]
    assert fits_tar == response["fits_tarball"]


def test_votable(patch_get):
    response = Most.query(
        output_mode="VOTable",
        obj_name="Victoria"
    )

    vtbl = votable.parse(data_path("MOST_VOTable.xml"))
    silent_stream = io.StringIO()
    assert report_diff_values(response, vtbl, silent_stream)


def test_gator(patch_get):
    response = Most.query(
        output_mode="Gator",
        obj_name="Victoria"
    )

    tbl = Table.read(data_path("most_gator_table.tbl"), format="ipac")
    silent_stream = io.StringIO()
    assert report_diff_values(tbl, response, silent_stream)
