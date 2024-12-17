# Licensed under a 3-clause BSD style license - see LICENSE.rst

import os
import shutil
import pytest
from astropy.coordinates import SkyCoord
from astropy.table import Table
import astropy.units as u

from astroquery.heasarc import Heasarc
from astroquery.exceptions import InvalidQueryError

try:
    # Both boto3, botocore and moto are optional dependencies,
    # but the former 2 are dependencies of the latter, so it's enough
    # to handle them with one variable
    import boto3
    from moto import mock_aws

    DO_AWS_S3 = True
except ImportError:
    DO_AWS_S3 = False


OBJ_LIST = [
    "182d38m08.64s 39d24m21.06s",
    SkyCoord(l=155.0771, b=75.0631, unit=(u.deg, u.deg), frame="galactic"),
]

SIZE_LIST = [2 * u.arcmin, "0d2m0s"]


@pytest.mark.parametrize("coordinates", OBJ_LIST)
@pytest.mark.parametrize("radius", SIZE_LIST)
def test_query_region_cone(coordinates, radius):
    # use columns='*' to avoid remote call to obtain the default columns
    query = Heasarc.query_region(
        coordinates,
        table="suzamaster",
        spatial="cone",
        radius=radius,
        columns="*",
        get_query_payload=True,
    )

    # We don't fully float compare in this string, there are slight
    # differences due to the name-coordinate resolution and conversions
    assert ("SELECT *,DISTANCE(POINT('ICRS',ra,dec), "
            "POINT('ICRS',182.63") in query
    assert (
        "FROM suzamaster WHERE CONTAINS(POINT('ICRS',ra,dec),"
        "CIRCLE('ICRS',182.63" in query
    )
    assert ",39.40" in query
    assert ",0.0333" in query


@pytest.mark.parametrize("coordinates", OBJ_LIST)
@pytest.mark.parametrize("width", SIZE_LIST)
def test_query_region_box(coordinates, width):
    query = Heasarc.query_region(
        coordinates,
        table="suzamaster",
        spatial="box",
        width=2 * u.arcmin,
        columns="*",
        get_query_payload=True,
    )

    assert (
        "SELECT * FROM suzamaster WHERE CONTAINS(POINT('ICRS',ra,dec),"
        "BOX('ICRS',182.63" in query
    )
    assert ",39.40" in query
    assert ",0.0333" in query


poly1 = [
    SkyCoord(ra=10.1 * u.deg, dec=10.1 * u.deg),
    SkyCoord(ra=10.0 * u.deg, dec=10.1 * u.deg),
    SkyCoord(ra=10.0 * u.deg, dec=10.0 * u.deg),
]
poly2 = [
    (10.1 * u.deg, 10.1 * u.deg),
    (10.0 * u.deg, 10.1 * u.deg),
    (10.0 * u.deg, 10.0 * u.deg),
]


@pytest.mark.parametrize("polygon", [poly1, poly2])
def test_query_region_polygon(polygon):
    # position is not used for polygon
    query1 = Heasarc.query_region(
        table="suzamaster",
        spatial="polygon",
        polygon=polygon,
        columns="*",
        get_query_payload=True,
    )
    query2 = Heasarc.query_region(
        "ngc4151",
        table="suzamaster",
        spatial="polygon",
        polygon=polygon,
        columns="*",
        get_query_payload=True,
    )

    assert query1 == query2
    assert query1 == (
        "SELECT * FROM suzamaster "
        "WHERE CONTAINS(POINT('ICRS',ra,dec),POLYGON('ICRS',"
        "10.1,10.1,10.0,10.1,10.0,10.0))=1"
    )


def test_query_allsky():
    query1 = Heasarc.query_region(
        table="suzamaster", spatial="all-sky", columns="*",
        get_query_payload=True
    )
    query2 = Heasarc.query_region(
        "m31",
        table="suzamaster",
        spatial="all-sky",
        columns="*",
        get_query_payload=True,
    )

    assert query1 == query2 == "SELECT * FROM suzamaster"


@pytest.mark.parametrize("spatial", ["space", "invalid"])
def test_spatial_invalid(spatial):
    with pytest.raises(ValueError):
        Heasarc.query_region(
            OBJ_LIST[0], table="invalid_spatial", columns="*", spatial=spatial
        )


def test_no_table():
    with pytest.raises(InvalidQueryError):
        Heasarc.query_region("m31", spatial="cone", columns="*")


def test_list_tables_keywords_non_str():
    with pytest.raises(ValueError, match="non-str found in keywords elements"):
        Heasarc.tables(keywords=12)


def test_list_tables_keywords_list_non_str():
    with pytest.raises(ValueError, match="non-str found in keywords elements"):
        Heasarc.tables(keywords=['x-ray', 12])


def test_get_datalink():
    with pytest.raises(ValueError, match="query_result is None"):
        Heasarc.get_datalinks()

    with pytest.raises(
        TypeError, match="query_result need to be an astropy.table.Table"
    ):
        Heasarc.get_datalinks([1, 2])

    with pytest.raises(ValueError, match="No __row column found"):
        Heasarc.get_datalinks(Table({"id": [1, 2, 3.0]}), tablename="xray")


def test_download_data__empty():
    with pytest.raises(ValueError, match="Input links table is empty"):
        Heasarc.download_data(Table())


def test_download_data__wronghost():
    with pytest.raises(
        ValueError, match="host has to be one of heasarc, sciserver, aws"
    ):
        Heasarc.download_data(Table({"id": [1]}), host="nohost")


@pytest.mark.parametrize("host", ["heasarc", "sciserver", "aws"])
def test_download_data__missingcolumn(host):
    host_col = "access_url" if host == "heasarc" else host
    with pytest.raises(
        ValueError,
        match=f"No {host_col} column found in the table. Call ~get_datalinks first"
    ):
        Heasarc.download_data(Table({"id": [1]}), host=host)


def test_download_data__outside_sciserver():
    with pytest.raises(
        FileNotFoundError,
        match="No data archive found. This should be run on Sciserver",
    ):
        Heasarc.download_data(
            Table({"sciserver": ["some-link"]}), host="sciserver"
        )


# S3 mock tests
s3_bucket = "nasa-heasarc"
s3_key1 = "some/location/file1.txt"
s3_key2 = "some/location/sub/file2.txt"
s3_key3 = "some/location/sub/sub2/file3.txt"
s3_dir = "some/location"


@pytest.fixture(name="s3_mock")
def _s3_mock(mocker):
    with mock_aws():
        conn = boto3.resource("s3", region_name="us-east-1")
        conn.create_bucket(Bucket=s3_bucket)
        s3_client = conn.meta.client
        s3_client.put_object(Bucket=s3_bucket, Key=s3_key1,
                             Body="my content")
        s3_client.put_object(Bucket=s3_bucket, Key=s3_key2,
                             Body="my other content")
        s3_client.put_object(Bucket=s3_bucket, Key=s3_key3,
                             Body="my other content")
        yield conn


@pytest.mark.filterwarnings("ignore::DeprecationWarning")
@pytest.mark.skipif("not DO_AWS_S3")
def test_s3_mock_basic(s3_mock):
    body = s3_mock.Object(s3_bucket, s3_key1).get()["Body"]
    content = body.read().decode("utf-8")
    assert content == "my content"


@pytest.mark.filterwarnings("ignore::DeprecationWarning")
@pytest.mark.skipif("not DO_AWS_S3")
def test_s3_mock_file(s3_mock):
    links = Table({"aws": [f"s3://{s3_bucket}/{s3_key1}"]})
    Heasarc.enable_cloud(profile=False)
    Heasarc.download_data(links, host="aws", location=".")
    file = s3_key1.split("/")[-1]
    assert os.path.exists(file)
    os.remove(file)


@pytest.mark.filterwarnings("ignore::DeprecationWarning")
@pytest.mark.skipif("not DO_AWS_S3")
def test_s3_mock_directory(s3_mock):
    links = Table({"aws": [f"s3://{s3_bucket}/{s3_dir}"]})
    Heasarc.enable_cloud(profile=False)
    Heasarc.download_data(links, host="aws", location=".")
    assert os.path.exists("location")
    assert os.path.exists("location/file1.txt")
    assert os.path.exists("location/sub/file2.txt")
    assert os.path.exists("location/sub/sub2/file3.txt")
    shutil.rmtree("location")
