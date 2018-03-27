# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""Tests for `astroquery.vo_conesearch.validator.inspect`."""
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from astropy.extern.six.moves import zip

# STDLIB
import os

# ASTROPY
from astropy.utils.data import _find_pkg_data_path, get_pkg_data_filename

# LOCAL
from .. import inspect
from ... import conf as cs_conf

__doctest_skip__ = ['*']


class TestConeSearchResults(object):
    """Inspection of ``TestConeSearchValidation`` results."""
    def setup_class(self):
        self.datadir = 'data'
        test_vos_path = _find_pkg_data_path(self.datadir) + os.sep

        # Convert to a proper file:// URL--on *NIXen this is not necessary but
        # Windows paths will blow up if we don't do this.
        test_vos_path = '/'.join(test_vos_path.split(os.sep))
        if not test_vos_path.startswith('/'):
            test_vos_path = '/' + test_vos_path

        cs_conf.vos_baseurl = 'file://' + test_vos_path
        self.r = inspect.ConeSearchResults()

    def test_catkeys(self):
        assert (self.r.catkeys['good'] ==
                ['The USNO-A2.0 Catalogue (Monet+ 1998) 1'])
        assert self.r.catkeys['warn'] == []
        assert self.r.catkeys['exception'] == []
        assert self.r.catkeys['error'] == []

    def gen_cmp(self, func, out_file, *args, **kwargs):
        oname = os.path.basename(out_file)
        dat_file = get_pkg_data_filename(os.path.join(self.datadir, oname))
        with open(out_file, 'w') as fout:
            func(fout=fout, *args, **kwargs)

        with open(dat_file) as f1:
            contents_1 = f1.readlines()
        with open(out_file) as f2:
            contents_2 = f2.readlines()

        assert len(contents_1) == len(contents_2)

        # json.dumps() might or might not add trailing whitespace
        # http://bugs.python.org/issue16333
        for line1, line2 in zip(contents_1, contents_2):
            assert line1.rstrip() == line2.rstrip()

    def test_tally(self, tmpdir):
        self.gen_cmp(self.r.tally, str(tmpdir.join('tally.out')))

    def test_listcats(self, tmpdir):
        self.gen_cmp(self.r.list_cats, str(tmpdir.join('listcats1.out')),
                     'good')
        self.gen_cmp(self.r.list_cats, str(tmpdir.join('listcats2.out')),
                     'good', ignore_noncrit=True)

    def test_printcat(self, tmpdir):
        self.gen_cmp(self.r.print_cat, str(tmpdir.join('printcat.out')),
                     'The USNO-A2.0 Catalogue (Monet+ 1998) 1')

    def teardown_class(self):
        cs_conf.reset('vos_baseurl')
