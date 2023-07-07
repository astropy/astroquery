# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
Tests for `astroquery.vo_conesearch.validator.validate`.

.. note::

    This test will fail if external URL query status
    changes. This is beyond the control of AstroPy.
    When this happens, rerun or update the test.

"""
# STDLIB
import os

# THIRD-PARTY
import pytest
from numpy.testing import assert_allclose

# ASTROPY
from astropy.utils.data import get_pkg_data_filename
from astropy.utils.exceptions import AstropyUserWarning

# LOCAL
from .. import conf, validate, tstquery
from ...vos_catalog import VOSDatabase

__doctest_skip__ = ['*']


@pytest.mark.remote_data
class TestConeSearchValidation:
    """Validation on a small subset of Cone Search sites."""

    @pytest.fixture(autouse=True)
    def setup_class(self, tmp_path):
        self.datadir = 'data'
        self.out_dir = tmp_path / self.datadir
        self.out_dir.mkdir()
        self.filenames = {
            'good': 'conesearch_good.json',
            'warn': 'conesearch_warn.json',
            'excp': 'conesearch_exception.json',
            'nerr': 'conesearch_error.json'}

        conf.conesearch_master_list = get_pkg_data_filename(os.path.join(
            self.datadir, 'vao_conesearch_sites_121107_subset.xml'))

    @staticmethod
    def _compare_catnames(fname1, fname2):
        db1 = VOSDatabase.from_json(fname1)
        db2 = VOSDatabase.from_json(fname2)
        assert db1.list_catalogs() == db2.list_catalogs()

    # Ignore falling back to default size warning, ignore votable warning, and multiprocessing, too.
    # See discussion e.g. in https://github.com/astropy/astroquery/issues/2634
    @pytest.mark.filterwarnings("ignore::pytest.PytestUnraisableExceptionWarning")
    @pytest.mark.filterwarnings("ignore::astropy.io.votable.exceptions.W06")
    @pytest.mark.filterwarnings("ignore::astropy.utils.exceptions.AstropyUserWarning")
    @pytest.mark.parametrize(('parallel'), [True, False])
    def test_validation(self, parallel):

        validate.check_conesearch_sites(
            destdir=self.out_dir, parallel=parallel, url_list=None)

        for val in self.filenames.values():
            self._compare_catnames(get_pkg_data_filename(
                os.path.join(self.datadir, val)),
                os.path.join(self.out_dir, val))

    # Ignore falling back to default size warning, ignore votable warning, and multiprocessing, too.
    # See discussion e.g. in https://github.com/astropy/astroquery/issues/2634
    @pytest.mark.filterwarnings("ignore::pytest.PytestUnraisableExceptionWarning")
    @pytest.mark.filterwarnings("ignore::astropy.io.votable.exceptions.W06")
    @pytest.mark.filterwarnings("ignore::astropy.utils.exceptions.AstropyUserWarning")
    @pytest.mark.parametrize(('parallel'), [True, False])
    def test_url_list(self, parallel):
        local_outdir = os.path.join(self.out_dir, 'subtmp1')
        local_list = [
            'http://www.google.com/foo&',
            'http://vizier.unistra.fr/viz-bin/conesearch/I/252/out?']
        validate.check_conesearch_sites(destdir=local_outdir,
                                        parallel=parallel,
                                        url_list=local_list)
        self._compare_catnames(get_pkg_data_filename(
            os.path.join(self.datadir, self.filenames['good'])),
            os.path.join(local_outdir, self.filenames['good']))

    def teardown_class(self):
        conf.reset('conesearch_master_list')


@pytest.mark.remote_data
def test_tstquery():
    with pytest.warns(AstropyUserWarning, match='too large') as w:
        d = tstquery.parse_cs('ivo://cds.vizier/i/252', cap_index=4)
    assert len(w) == 1
    assert_allclose([d['RA'], d['DEC'], d['SR']],
                    [45, 0.07460390065517808, 0.1])
