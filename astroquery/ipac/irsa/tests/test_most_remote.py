# Licensed under a 3-clause BSD style license - see LICENSE.rst
import os
import pytest
import warnings

import numpy as np

import astropy.io.fits as fits
from astropy.table import Table
from astroquery.ipac.irsa import Most
from astroquery.exceptions import InvalidQueryError

# each MOST query is given a PID and a temporary directory availible publicly
# from this base URL. This URL is then used to create links on the returned
# HTML page and data returned to the user
REGULAR_BASE_URL = "https://irsa.ipac.caltech.edu/workspace/TMP_FmruWd_8104/MOST/pid17003/"
FULL_BASE_URL = "https://irsa.ipac.caltech.edu/workspace/TMP_FmruWd_8104/MOST/pid10459/"


def data_path(filename):
    """Returns the path to the file in the module's test data directory."""
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)


@pytest.mark.remote_data
def test_query_object():
    """Tests the default MOST query returns expected results."""
    response = Most.query_object(
        obj_name="Victoria",
        obs_begin="2014-05-21",
        obs_end="2014-05-30"
    )

    # check expected fields were returned
    assert "results" in response
    assert "metadata" in response
    assert "region" in response
    assert "fits_tarball" not in response
    assert "region_tarball" not in response

    # check content is as expected for the columns we don't expect to change
    # This excludes URLS, they contain PIDs. The rest can be compared, but the
    # problem is that report_diff_values doesn't sort the values and they are
    # not returned in same order nor header width. So we have to compare
    # manually
    results = Table.read(data_path("most_regular_results.tbl"), format="ipac")

    columns = [col for col in results.columns if col not in ("image_url", "postcard_url", "region_file")]
    for col in columns:
        response_col = response["results"][col]
        results_col = results[col]
        response_col.sort()
        results_col.sort()
        if 'float' in response_col.dtype.name:
            assert np.allclose(response_col, results_col, rtol=0.005)
        else:
            # probably a string like Img_ID or datetime stamps
            assert all(response_col == results_col)


@pytest.mark.remote_data
def test_get_images():
    """Tests images are returned by MOST get_images."""

    images = Most.get_images(
        obj_name="Victoria",
        obs_begin="2014-05-21",
        obs_end="2014-05-22"
    )

    assert len(images) == 2
    assert isinstance(images[0], fits.HDUList)
    assert "2014-05-21" in images[0][0].header["DATIME"]


@pytest.mark.remote_data
def test_list_catalogs():
    expected = [
        '2mass', 'spitzer_bcd', 'ptf', 'sofia', 'wise_merge', 'wise_allsky_4band',
        'wise_allsky_3band', 'wise_allsky_2band', 'wise_neowiser',
        'wise_neowiser_yr1', 'wise_neowiser_yr2', 'wise_neowiser_yr3',
        'wise_neowiser_yr4', 'wise_neowiser_yr5', 'wise_neowiser_yr6',
        'wise_neowiser_yr7', 'wise_neowiser_yr8', 'wise_neowiser_yr9', 'ztf',
        'wise_merge_int', 'wise_neowiser_int', 'wise_neowiser_yr10'
    ]

    cats = Most.list_catalogs()
    assert expected == cats


@pytest.mark.remote_data
def test_no_results():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        response = Most.query_object(
            obj_name="Victoria",
            obs_begin="2019-05-21",
            obs_end="2019-05-22"
        )

    assert response is None

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        response = Most.get_images(
            obj_name="Victoria",
            obs_begin="2019-05-21",
            obs_end="2019-05-22"
        )

    assert response is None


@pytest.mark.remote_data
def test_invalid_query():
    with pytest.raises(InvalidQueryError):
        Most.query_object(
            obj_name="Victoria",
            obs_begin="2014-05-21",
            obs_end="2014-05-19"
        )

    with pytest.raises(InvalidQueryError):
        Most.get_images(
            obj_name="Victoria",
            obs_begin="2014-05-21",
            obs_end="2014-05-19"
        )
