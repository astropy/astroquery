# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""Tests for VO Cone Search."""

# STDLIB
import os
import time

# THIRD-PARTY
import numpy as np
import pytest

# ASTROPY
from astropy import units as u
from astropy.coordinates import ICRS, SkyCoord
from astropy.io.votable.exceptions import W25
from astropy.io.votable.tree import Table as VOTable
from astropy.table import Table
from astropy.utils.data import get_pkg_data_filename
from astropy.utils import data

# LOCAL
from .. import conf, conesearch, vos_catalog
from ..core import _validate_coord, ConeSearch
from ..exceptions import VOSError, ConeSearchError
from ...exceptions import NoResultsWarning

__doctest_skip__ = ['*']


# Global variables for TestConeSearch
SCS_RA = 0
SCS_DEC = 0
SCS_SR = 0.1
SCS_CENTER = ICRS(SCS_RA * u.degree, SCS_DEC * u.degree)
SCS_RADIUS = SCS_SR * u.degree


@pytest.mark.remote_data
class TestConeSearch:
    """
    Test Cone Search on a pre-defined access URL.

    .. note::

        This test will fail if the URL becomes inaccessible,
        which is beyond Astroquery's control. When this happens,
        change the test to use a different URL.

        At the time this was written, ``pedantic=True`` will
        not yield any successful search.
    """

    def setup_class(self):
        # If this link is broken, use the next in database that works
        self.url = ('http://vizier.unistra.fr/viz-bin/votable/-A?-out.all&'
                    '-source=I/252/out&')
        self.catname = 'USNO-A2'

        # Avoid downloading the full database
        conf.conesearch_dbname = 'conesearch_simple'

        # Sometimes 3s is not enough
        data.conf.remote_timeout = 10

        self.verbose = False

    def test_cat_listing(self):
        assert (conesearch.list_catalogs()
                == ['BROKEN', 'USNO ACT', 'USNO NOMAD', 'USNO-A2', 'USNO-B1'])
        assert (conesearch.list_catalogs(pattern='usno*a')
                == ['USNO ACT', 'USNO NOMAD', 'USNO-A2'])

    def test_no_result_classic(self):
        with pytest.warns(NoResultsWarning, match='returned 0 result'):
            result = conesearch.conesearch(
                SCS_CENTER, 0.001, catalog_db=self.url, verbose=self.verbose)
        assert result is None

    def test_no_result_astroquery(self):
        with pytest.warns(NoResultsWarning, match='returned 0 result'):
            result = ConeSearch.query_region(
                SCS_CENTER, '0.001 deg', verbose=self.verbose,
                service_url=self.url)
        assert result is None

    @pytest.mark.filterwarnings('ignore::astropy.io.votable.exceptions.W25')
    @pytest.mark.parametrize(('center', 'radius'),
                             [((SCS_RA, SCS_DEC), SCS_SR),
                              (SCS_CENTER, SCS_RADIUS)])
    def test_one_search_classic(self, center, radius):
        """
        This does not necessarily uses ``self.url`` because of
        unordered dict in JSON tree.
        """
        tab_1 = conesearch.conesearch(
            center, radius, verbose=self.verbose, return_astropy_table=False)
        assert isinstance(tab_1, VOTable)
        assert hasattr(tab_1, 'url')
        assert tab_1.array.size > 0

    def test_one_search_astroquery(self):
        tab_1 = ConeSearch.query_region(
            SCS_CENTER, SCS_RADIUS, verbose=self.verbose, service_url=self.url)
        assert isinstance(tab_1, Table)
        assert hasattr(tab_1, 'url')
        assert len(tab_1) > 0

    def test_sky_coord_classic(self):
        """
        Check that searching with a SkyCoord works too.
        """
        sc_cen = SkyCoord(SCS_CENTER)
        tab = conesearch.conesearch(
            sc_cen, SCS_RADIUS, catalog_db=self.url, verbose=self.verbose)
        assert len(tab) > 0

    def test_timeout_classic(self):
        """Test timed out query."""
        with pytest.warns(W25, match='timed out'):
            with conf.set_temp('timeout', 1e-6):
                result = conesearch.conesearch(
                    SCS_CENTER, SCS_RADIUS, cache=False,
                    verbose=self.verbose, catalog_db=self.url)
        assert result is None

    def test_searches_classic(self):
        tab_2 = conesearch.conesearch(
            SCS_CENTER, SCS_RADIUS, catalog_db=self.url, verbose=self.verbose,
            return_astropy_table=False)

        tab_3 = conesearch.conesearch(
            SCS_CENTER, SCS_RADIUS,
            catalog_db=[self.catname, self.url], verbose=self.verbose,
            return_astropy_table=False)

        tab_4 = conesearch.conesearch(
            SCS_CENTER, SCS_RADIUS,
            catalog_db=vos_catalog.get_remote_catalog_db(
                conf.conesearch_dbname), verbose=self.verbose,
            return_astropy_table=False)

        assert tab_2.url == tab_3.url
        np.testing.assert_array_equal(tab_2.array, tab_3.array)

        assert tab_2.url == tab_4.url
        np.testing.assert_array_equal(tab_2.array, tab_4.array)

    @pytest.mark.filterwarnings('ignore::astropy.io.votable.exceptions.W25')
    @pytest.mark.parametrize(('center', 'radius'),
                             [((SCS_RA, SCS_DEC), SCS_SR),
                              (SCS_CENTER, SCS_RADIUS)])
    def test_search_all(self, center, radius):
        all_results = conesearch.search_all(
            center, radius, catalog_db=['BROKEN', self.url],
            verbose=self.verbose, return_astropy_table=False)

        assert len(all_results) == 1

        tab_1 = all_results[self.url[:-1]]

        assert tab_1.array.size > 0

    @pytest.mark.filterwarnings('ignore::astropy.io.votable.exceptions.W25')
    def test_async(self):
        async_search = conesearch.AsyncConeSearch(
            SCS_CENTER, SCS_RADIUS, return_astropy_table=False)

        # Wait a little for the instance to set up properly
        time.sleep(1)

        tab = async_search.get(timeout=data.conf.remote_timeout)

        try:
            assert async_search.done()
        except AssertionError as exc:
            pytest.xfail(str(exc))
        else:
            assert tab.array.size > 0

    @pytest.mark.filterwarnings('ignore::astropy.io.votable.exceptions.W25')
    def test_async_all(self):
        async_search_all = conesearch.AsyncSearchAll(
            SCS_CENTER, SCS_RADIUS, return_astropy_table=False)

        # Wait a little for the instance to set up properly
        time.sleep(1)

        all_results = async_search_all.get(
            timeout=data.conf.remote_timeout * 3)

        try:
            assert async_search_all.done()
        except AssertionError as exc:
            pytest.xfail(str(exc))
        else:
            for tab in all_results.values():
                assert tab.array.size > 0

    @pytest.mark.parametrize(('center', 'radius'),
                             [((SCS_RA, SCS_DEC), 0.8),
                              (SCS_CENTER, 0.8 * u.degree)])
    def test_prediction(self, center, radius):
        """Prediction tests are not very accurate but will have to do."""
        t_1, tab_1 = conesearch.conesearch_timer(
            center, radius, catalog_db=self.url, verbose=self.verbose,
            return_astropy_table=False)
        n_1 = tab_1.array.size

        t_2, n_2 = conesearch.predict_search(
            self.url, center, radius, verbose=self.verbose)

        assert n_2 > 0 and n_2 <= n_1 * 1.5

        # Timer depends on network latency as well, so upper limit is very lax.
        assert t_2 > 0 and t_2 <= t_1 * 10

    def test_prediction_neg_radius(self):
        with pytest.raises(ConeSearchError):
            t, n = conesearch.predict_search(
                self.url, SCS_CENTER, -1, verbose=self.verbose)

    def teardown_class(self):
        conf.reset('conesearch_dbname')
        data.conf.reset('remote_timeout')


class TestErrorResponse:
    """
    Test Cone Search error response handling.

    This is defined in Section 2.3 of Simple Cone Search Version 1.03,
    IVOA Recommendation, 22 February 2008.

    Also see https://github.com/astropy/astropy/issues/1001
    """

    def setup_class(self):
        self.datadir = 'data'
        self.pedantic = False
        self.conesearch_errmsg = {
            'conesearch_error1.xml': 'Error in input RA value: as3f',
            'conesearch_error2.xml': 'Error in input RA value: as3f',
            'conesearch_error3.xml': 'Invalid data type: text/html',
            'conesearch_error4.xml': 'Invalid data type: text/html'}

    def conesearch_compare(self, xmlfile, msg):
        """
        Bypassing Cone Search query and just imitating the reply,
        then check if appropriate error message is caught.
        """
        # conesearch_error4.xml is a wont-fix for now
        if xmlfile == 'conesearch_error4.xml':
            pytest.xfail('Currently not supported, '
                         'see astropy.io.votable.exceptions.W22')

        url = get_pkg_data_filename(os.path.join(self.datadir, xmlfile))
        with pytest.raises(VOSError) as excinfo:
            vos_catalog._vo_service_request(url, self.pedantic, {})
        assert msg in str(excinfo.value)

    @pytest.mark.parametrize(('id'), [1, 2, 3, 4])
    def test_conesearch_response(self, id):
        xml = 'conesearch_error{0}.xml'.format(id)
        msg = self.conesearch_errmsg[xml]
        self.conesearch_compare(xml, msg)


@pytest.mark.parametrize(
    ('c', 'ans'),
    [(ICRS(6.02233 * u.degree, -72.08144 * u.degree),
      [6.022330000000011, -72.08144]),
     (SkyCoord(6.02233 * u.degree, -72.08144 * u.degree, frame='icrs'),
      [6.022330000000011, -72.08144]),
     ((-0, 0), [0, 0]),
     ((-1, -1), [359, -1])])
def test_validate_coord(c, ans):
    """Valid coordinates should not raise an error."""
    result = _validate_coord(c)
    np.testing.assert_allclose(result, ans)
