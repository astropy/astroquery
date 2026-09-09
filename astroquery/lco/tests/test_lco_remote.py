# Licensed under a 3-clause BSD style license - see LICENSE.rst

import os
import warnings

import pytest

import astropy.units as u
from astropy.coordinates import SkyCoord
from astropy.table import Table

from astroquery.exceptions import MaxResultsWarning
from astroquery.lco import LcoArchive, LcoArchiveQuery


pytestmark = pytest.mark.remote_data


# Every query below is pinned to a narrow date range in the past.
# It keeps the load on the archive small and makes the responses reproducible.
#
# This window contains exactly nine public reduced frames whose footprints
# cover M101. These dates are well in the past so we should not expect
# the search results to change in the future
WINDOW = {'start': '2024-03-01', 'end': '2024-03-08'}
M101 = SkyCoord(210.802429, 54.348750, unit='deg')
EXPECTED_FRAME_IDS = {69021388, 69081552, 69081653, 69081666, 69081771,
                      69081784, 69081980, 69085778, 69086104}

# Thumbnails were only stored from 2025 onwards, so they need their own window.
THUMBNAIL_WINDOW = {'start': '2025-03-02', 'end': '2025-03-03'}

# A single night at one site, used for the pagination test.
BIAS_WINDOW = {'start': '2024-03-02', 'end': '2024-03-03'}


def footprint_contains(frame, coordinates):
    """Test whether a frame's footprint contains a position.

    The archive reports footprints as GeoJSON polygons with longitudes in
    [-180, 180], so RA has to be wrapped before the point-in-polygon test.
    """
    ring = frame['area']['coordinates'][0]
    lon = coordinates.ra.deg
    lon = lon - 360 if lon > 180 else lon
    lat = coordinates.dec.deg

    inside = False
    j = len(ring) - 1
    for i, (x, y) in enumerate(ring):
        xj, yj = ring[j]
        if (y > lat) != (yj > lat) and lon < (xj - x) * (lat - y) / (yj - y) + x:
            inside = not inside
        j = i
    return inside


@pytest.fixture(autouse=True)
def _allow_truncation():
    # Tests here cap row_limit to keep the load on the archive small, which
    # legitimately triggers the truncation warning. Tests that care about the
    # warning set their own filter, which takes precedence over this one.
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', MaxResultsWarning)
        yield


class TestLcoArchive:

    def test_query_region_covers_the_position(self):
        result = LcoArchive.query_region(M101, reduction_level=91,
                                         public=True, row_limit=-1, **WINDOW)
        assert isinstance(result, Table)
        assert set(result['id']) == EXPECTED_FRAME_IDS

        # The real invariant: every frame returned by a point query must have
        # a footprint containing that point.
        for frame_id in result['id']:
            frame = LcoArchive.get_frame(frame_id)
            assert footprint_contains(frame, M101), \
                f"frame {frame_id} does not cover the queried position"

    def test_query_region_radius_includes_the_point_matches(self):
        result = LcoArchive.query_region(M101, radius=0.2*u.deg,
                                         reduction_level=91, public=True,
                                         row_limit=-1, **WINDOW)
        # A cone around the position must return at least everything whose
        # footprint contains the position itself.
        assert EXPECTED_FRAME_IDS <= set(result['id'])

    def test_query_region_box(self):
        result = LcoArchive.query_region(M101, width=0.4*u.deg,
                                         height=0.4*u.deg, reduction_level=91,
                                         public=True, row_limit=-1, **WINDOW)
        assert EXPECTED_FRAME_IDS <= set(result['id'])

    def test_query_object(self):
        result = LcoArchive.query_object('SN2023ixf', reduction_level=91,
                                         public=True, row_limit=-1, **WINDOW)
        assert set(result['target_name']) == {'SN2023ixf'}
        assert set(result['id']) == EXPECTED_FRAME_IDS

    def test_query_criteria_filters_are_applied(self):
        result = LcoArchive.query_criteria(site_id='lsc',
                                           configuration_type='BIAS',
                                           reduction_level=0, public=True,
                                           row_limit=5, **BIAS_WINDOW)
        assert 0 < len(result) <= 5
        assert set(result['site_id']) == {'lsc'}
        assert set(result['configuration_type']) == {'BIAS'}
        assert set(result['reduction_level']) == {0}

    def test_dates_are_within_the_requested_window(self):
        result = LcoArchive.query_criteria(site_id='lsc',
                                           configuration_type='BIAS',
                                           reduction_level=0, public=True,
                                           row_limit=10, **BIAS_WINDOW)
        for date in result['observation_date']:
            assert BIAS_WINDOW['start'] <= date[:10] <= BIAS_WINDOW['end']

    def test_row_limit_paginates(self):
        # Anonymous pages hold 100 frames, so this needs a second page.
        result = LcoArchive.query_criteria(site_id='lsc',
                                           configuration_type='BIAS',
                                           reduction_level=0, public=True,
                                           row_limit=150, **BIAS_WINDOW)
        assert len(result) == 150
        assert len(set(result['id'])) == 150

    def test_truncated_results_warn(self):
        # This window holds far more than three frames, so the user needs to
        # be told the table is not the whole answer.
        with pytest.warns(MaxResultsWarning, match='truncated to 3 frames'):
            result = LcoArchive.query_criteria(site_id='lsc',
                                               configuration_type='BIAS',
                                               reduction_level=0, public=True,
                                               row_limit=3, **BIAS_WINDOW)
        assert len(result) == 3

    def test_no_warning_when_everything_fits(self):
        # The nine M101 frames are the complete answer, so nothing is
        # truncated and no warning should be raised.
        with warnings.catch_warnings():
            warnings.simplefilter('error', MaxResultsWarning)
            result = LcoArchive.query_object('SN2023ixf', reduction_level=91,
                                             public=True, row_limit=-1,
                                             **WINDOW)
        assert len(result) == len(EXPECTED_FRAME_IDS)

    def test_row_limit_is_respected_below_a_page(self):
        result = LcoArchive.query_criteria(site_id='lsc',
                                           configuration_type='BIAS',
                                           reduction_level=0, public=True,
                                           row_limit=3, **BIAS_WINDOW)
        assert len(result) == 3

    def test_include_thumbnails(self):
        result = LcoArchive.query_criteria(reduction_level=91, public=True,
                                           include_thumbnails=True,
                                           thumbnail_size='small',
                                           row_limit=20, **THUMBNAIL_WINDOW)
        assert 'thumbnail_url' in result.colnames
        urls = [url for url in result['thumbnail_url'] if url]
        assert len(urls) > 0
        assert all(url.startswith('https://') for url in urls)

        names = [n for n in result['thumbnail_filename'] if n]
        assert all(n.endswith('-small_thumbnail.jpg') for n in names)

    def test_get_frame_keeps_nested_fields(self):
        frame = LcoArchive.get_frame(sorted(EXPECTED_FRAME_IDS)[0])
        assert frame['id'] == sorted(EXPECTED_FRAME_IDS)[0]
        for key in ('area', 'version_set', 'related_frames'):
            assert key in frame

    def test_download_files(self, tmp_path):
        result = LcoArchive.query_criteria(site_id='lsc',
                                           configuration_type='BIAS',
                                           reduction_level=0, public=True,
                                           row_limit=1, **BIAS_WINDOW)
        paths = LcoArchive.download_files(result, download_dir=str(tmp_path))
        assert len(paths) == 1
        assert os.path.getsize(paths[0]) > 0
        assert paths[0].endswith(result['filename'][0])

    def test_download_thumbnails(self, tmp_path):
        result = LcoArchive.query_criteria(reduction_level=91, public=True,
                                           include_thumbnails=True,
                                           row_limit=20, **THUMBNAIL_WINDOW)
        # Not every frame has a thumbnail, so keep the first one that does.
        result = result[[bool(url) for url in result['thumbnail_url']]][:1]
        assert len(result) == 1

        paths = LcoArchive.download_thumbnails(result,
                                               download_dir=str(tmp_path))
        assert len(paths) == 1
        assert os.path.getsize(paths[0]) > 0

    def test_list_helpers(self):
        assert 'lsc' in LcoArchive.list_sites()
        assert 'BIAS' in LcoArchive.list_configuration_types()
        assert len(LcoArchive.list_instruments()) > 0

    def test_anonymous_users_see_no_proprietary_frames(self):
        from astroquery.exceptions import NoResultsWarning
        with pytest.warns(NoResultsWarning):
            result = LcoArchive.query_criteria(public=False, row_limit=5,
                                               **WINDOW)
        assert len(result) == 0


@pytest.mark.skipif(not os.environ.get('LCO_API_TOKEN'),
                    reason='requires an LCO API token in $LCO_API_TOKEN')
class TestLcoArchiveAuthenticated:
    """Runs only when a token is supplied; no credentials live in the repo."""

    @pytest.fixture
    def lco(self):
        archive = LcoArchiveQuery()
        archive.login(token=os.environ['LCO_API_TOKEN'])
        assert archive.authenticated()
        return archive

    def test_login(self, lco):
        assert lco.authenticated()

    def test_larger_page_size_when_authenticated(self, lco):
        assert lco._page_size == 1000

    def test_query_still_works_when_authenticated(self, lco):
        result = lco.query_object('SN2023ixf', reduction_level=91,
                                  row_limit=5, **WINDOW)
        assert len(result) > 0

    def test_download_works_when_authenticated(self, lco, tmp_path):
        # presigned URLs carry their own credentials, so make sure we are
        # stripping out any Auth headers before downloading.
        result = lco.query_criteria(site_id='lsc', configuration_type='BIAS',
                                    reduction_level=0, public=True,
                                    row_limit=1, **BIAS_WINDOW)
        paths = lco.download_files(result, download_dir=str(tmp_path))
        assert len(paths) == 1
        assert os.path.getsize(paths[0]) > 0

    def test_bad_token_is_rejected(self):
        archive = LcoArchiveQuery()
        archive.login(token='definitely-not-a-real-token')
        assert not archive.authenticated()
