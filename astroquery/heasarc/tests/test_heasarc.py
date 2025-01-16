# Licensed under a 3-clause BSD style license - see LICENSE.rst

import os
import pytest
import tempfile
from unittest.mock import patch, PropertyMock
from astropy.coordinates import SkyCoord
from astropy.table import Table
import astropy.units as u

from astroquery.heasarc import Heasarc, HeasarcClass
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


# used in the tap fixture
class MockTap:
    class vColumn:
        def __init__(self, name, desc, unit=None):
            self.name = name
            self.description = desc
            self.unit = unit

    class vTable:
        def __init__(self, desc, cols=[]):
            self.description = desc
            self.columns = cols

    cols = []
    for icol in [1, 2, 3]:
        cols.append(vColumn(f'col-{icol}', f'desc-{icol}'))

    tables = {
        'name-1': vTable('description-1 xmm', cols),
        'name-2': vTable('description-2 chandra', cols),
        'TAPname': None
    }


@pytest.fixture
def mock_tap():
    with patch('astroquery.heasarc.core.HeasarcClass.tap', new_callable=PropertyMock) as tap:
        tap.return_value = MockTap()
        yield tap


@pytest.fixture
def mock_default_cols():
    with patch('astroquery.heasarc.core.HeasarcClass._get_default_columns') as get_cols:
        get_cols.return_value = ['col-3', 'col-2']
        yield get_cols


@pytest.fixture
def mock_meta():
    with patch('astroquery.heasarc.core.HeasarcClass._meta', new_callable=PropertyMock) as meta:
        meta.return_value = Table(dict(
            table=['tab1', 'tab2', 'tab1', 'tab1'],
            par=['p1', 'p2', 'p3', ''],
            value=[1.2, 1.6, 2.0, 3.0]
        ))
        yield meta


@pytest.mark.parametrize("coordinates", OBJ_LIST)
@pytest.mark.parametrize("radius", SIZE_LIST)
@pytest.mark.parametrize("offset", [True, False])
def test_query_region_cone(coordinates, radius, offset):
    # use columns='*' to avoid remote call to obtain the default columns
    query = Heasarc.query_region(
        coordinates,
        catalog="suzamaster",
        spatial="cone",
        radius=radius,
        columns="*",
        get_query_payload=True,
        add_offset=True,
    )

    # We don't fully float compare in this string, there are slight
    # differences due to the name-coordinate resolution and conversions
    if offset:
        distance_text = ",DISTANCE(POINT('ICRS',ra,dec), POINT('ICRS',182.63"
    else:
        distance_text = ""
    assert (f"SELECT *{distance_text}") in query
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
        catalog="suzamaster",
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
        catalog="suzamaster",
        spatial="polygon",
        polygon=polygon,
        columns="*",
        get_query_payload=True,
    )
    query2 = Heasarc.query_region(
        "ngc4151",
        catalog="suzamaster",
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
        catalog="suzamaster", spatial="all-sky", columns="*",
        get_query_payload=True
    )
    query2 = Heasarc.query_region(
        "m31",
        catalog="suzamaster",
        spatial="all-sky",
        columns="*",
        get_query_payload=True,
    )

    assert query1 == query2 == "SELECT * FROM suzamaster"


@pytest.mark.parametrize("spatial", ["space", "invalid"])
def test_spatial_invalid(spatial):
    with pytest.raises(ValueError):
        Heasarc.query_region(
            OBJ_LIST[0], catalog="invalid_spatial", columns="*", spatial=spatial
        )


def test_no_catalog():
    with pytest.raises(InvalidQueryError):
        Heasarc.query_region("m31", spatial="cone", columns="*")


def test_tap_def():
    # Use a new HeasarcClass object
    Heasarc = HeasarcClass()
    assert Heasarc._tap is None
    Heasarc.tap
    assert Heasarc._tap is not None


def test_meta_def():
    class MockResult:
        def to_table(self):
            return Table({'value': ['1.5', '1.2', '-0.3']})
    # Use a new HeasarcClass object
    Heasarc = HeasarcClass()
    assert Heasarc._meta_info is None
    with patch('astroquery.heasarc.core.HeasarcClass.query_tap') as mock_query_tap:
        mock_query_tap.return_value = MockResult()
        meta = Heasarc._meta
        assert meta['value'][0] == 1.5


def test__get_default_columns(mock_meta):
    # Use a new HeasarcClass object
    Heasarc = HeasarcClass()
    cols = Heasarc._get_default_columns('tab1')
    assert list(cols) == ['p1', 'p3']


def test__get_default_radius(mock_meta):
    # Use a new HeasarcClass object
    Heasarc = HeasarcClass()
    radius = Heasarc.get_default_radius('tab1')
    assert radius.value == 3.0


def test__set_session():
    with pytest.raises(ValueError):
        Heasarc._set_session('not session object')


def test__list_catalogs(mock_tap):
    catalogs = Heasarc.list_catalogs()
    assert list(catalogs['name']) == [
        lab for lab in MockTap().tables.keys() if 'TAP' not in lab
    ]
    assert list(catalogs['description']) == [
        desc.description for lab, desc in MockTap().tables.items() if 'TAP' not in lab
    ]


def test_list_catalogs_keywords_non_str():
    with pytest.raises(ValueError, match="non-str found in keywords elements"):
        Heasarc.list_catalogs(keywords=12)


def test_list_catalogs_keywords_list_non_str():
    with pytest.raises(ValueError, match="non-str found in keywords elements"):
        Heasarc.list_catalogs(keywords=['x-ray', 12])


def test__list_columns__missing_table(mock_tap):
    with pytest.raises(ValueError, match="not available as a public catalog"):
        Heasarc.list_columns(catalog_name='missing-table')


def test__list_columns(mock_tap, mock_default_cols):
    cols = Heasarc.list_columns(catalog_name='name-1')
    assert list(cols['name']) == ['col-2', 'col-3']
    assert list(cols['description']) == ['desc-2', 'desc-3']


def test_locate_data():
    with pytest.raises(ValueError, match="query_result is None"):
        Heasarc.locate_data()

    with pytest.raises(
        TypeError, match="query_result need to be an astropy.table.Table"
    ):
        Heasarc.locate_data([1, 2])

    with pytest.raises(ValueError, match="No __row column found"):
        Heasarc.locate_data(Table({"id": [1, 2, 3.0]}), catalog_name="xray")


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
        match=f"No {host_col} column found in the table. Call `~locate_data` first"
    ):
        Heasarc.download_data(Table({"id": [1]}), host=host)


def test_download_data__sciserver():
    with tempfile.TemporaryDirectory() as tmpdir:
        datadir = f'{tmpdir}/data'
        downloaddir = f'{tmpdir}/download'
        os.makedirs(datadir, exist_ok=True)
        with open(f'{datadir}/file.txt', 'w') as fp:
            fp.write('data')
        # include both a file and a directory
        tab = Table({'sciserver': [f'{tmpdir}/data/file.txt', f'{tmpdir}/data']})
        # The patch is to avoid the test that we are on sciserver
        with patch('os.path.exists') as exists:
            exists.return_value = True
            Heasarc.download_data(tab, host="sciserver", location=downloaddir)
        assert os.path.exists(f'{downloaddir}/file.txt')
        assert os.path.exists(f'{downloaddir}/data')
        assert os.path.exists(f'{downloaddir}/data/file.txt')


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
    with tempfile.TemporaryDirectory() as tmpdir:
        Heasarc.download_data(links, host="aws", location=tmpdir)
        file = s3_key1.split("/")[-1]
        assert os.path.exists(f'{tmpdir}/{file}')


@pytest.mark.filterwarnings("ignore::DeprecationWarning")
@pytest.mark.skipif("not DO_AWS_S3")
def test_s3_mock_directory(s3_mock):
    links = Table({"aws": [f"s3://{s3_bucket}/{s3_dir}"]})
    Heasarc.enable_cloud(profile=False)
    with tempfile.TemporaryDirectory() as tmpdir:
        Heasarc.download_data(links, host="aws", location=tmpdir)
        assert os.path.exists(f"{tmpdir}/location")
        assert os.path.exists(f"{tmpdir}/location/file1.txt")
        assert os.path.exists(f"{tmpdir}/location/sub/file2.txt")
        assert os.path.exists(f"{tmpdir}/location/sub/sub2/file3.txt")
