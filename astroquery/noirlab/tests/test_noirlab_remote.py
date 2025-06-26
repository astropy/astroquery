# Licensed under a 3-clause BSD style license - see LICENSE.rst
# Python library
from __future__ import print_function
# External packages
from astropy import units as u
from astropy.coordinates import SkyCoord
from astropy.tests.helper import remote_data
# Local packages
from .. import Noirlab
from . import expected as exp

# performs similar tests as test_module.py, but performs
# the actual HTTP request rather than monkeypatching them.
# should be disabled or enabled at will - use the
# remote_data decorator from astropy:


@remote_data
class TestNoirlabClass(object):

    # ###############################################################
    # ### (2) SIA; /api/sia/
    # ###
    # voimg, vohdu

    def test_service_metadata(self):
        """Test compliance with 6.1 of SIA spec v1.0"""
        r = Noirlab().service_metadata()
        actual = r
        print(f'DBG: test_service_metadata={actual}')
        expected = exp.service_metadata
        assert actual == expected

    def test_query_region_0(self):
        """Search FILES using default type (which) selector"""

        c = SkyCoord(ra=10.625*u.degree, dec=41.2*u.degree, frame='icrs')
        r = Noirlab().query_region(c, radius='0.1')
        actual = set(list(r['md5sum']))
        expected = exp.query_region_1
        assert expected.issubset(actual)

    def test_query_region_1(self):
        """Search FILES.
        Ensure query gets at least the set of files we expect.
        Its ok if more files have been added to the remote Archive."""

        c = SkyCoord(ra=10.625*u.degree, dec=41.2*u.degree, frame='icrs')
        r = Noirlab(which='file').query_region(c, radius='0.1')
        actual = set(list(r['md5sum']))
        expected = exp.query_region_1
        assert expected.issubset(actual)

    def test_query_region_2(self):
        """Search HDUs.
        Ensure query gets at least the set of files we expect.
        Its ok if more files have been added to the remote Archive."""

        c = SkyCoord(ra=10.625*u.degree, dec=41.2*u.degree, frame='icrs')
        r = Noirlab(which='hdu').query_region(c, radius='0.07')
        actual = set(list(r['md5sum']))
        expected = exp.query_region_2
        assert expected.issubset(actual)

    # ###############################################################
    # ### (7) Advanced Search; /api/adv_search/
    # ###
    #
    # (2) aux_{file,hdu}_fields/<instrument>/<proctype>
    # (2) core_{file,hdu}_fields/
    #     [(2) {f,h}adoc  JUST LINK to these]
    # (2) {f,h}asearch
    # cat_list

    # ##
    # ## File (default type)
    # ##

    def test_aux_file_fields(self):
        """List the available AUX FILE fields."""
        r = Noirlab().aux_fields('decam', 'instcal')
        actual = r
        # Returned results may increase over time.
        print(f'DBG: test_aux_file_fields={actual}')
        expected = exp.aux_file_fields
        assert actual == expected

    def test_core_file_fields(self):
        """List the available CORE FILE fields."""
        r = Noirlab().core_fields()
        actual = r
        print(f'DBG: test_core_file_fields={actual}')
        expected = exp.core_file_fields
        assert actual == expected

    def test_query_file_metadata(self):
        """Search FILE metadata."""
        qspec = {
            "outfields": [
                "md5sum",
                "archive_filename",
                "original_filename",
                "instrument",
                "proc_type"
            ],
            "search": [
                ['original_filename', 'c4d_', 'contains']
            ]
        }

        r = Noirlab().query_metadata(qspec, limit=3)
        actual = r
        print(f'DBG: test_query_file_metadata={actual.pformat_all()}')
        expected = exp.query_file_metadata
        assert actual.pformat_all() == expected

    # ##
    # ## HDU
    # ##

    def test_aux_hdu_fields(self):
        """List the available AUX HDU fields."""
        r = Noirlab(which='hdu').aux_fields('decam', 'instcal')
        actual = r
        # Returned results may increase over time.
        print(f'DBG: test_aux_hdu_fields={actual}')
        expected = exp.aux_hdu_fields
        assert actual == expected

    def test_core_hdu_fields(self):
        """List the available CORE HDU fields."""
        r = Noirlab(which='hdu').core_fields()
        actual = r
        print(f'DBG: test_core_file_fields={actual}')
        expected = exp.core_hdu_fields
        assert actual == expected

    def test_query_hdu_metadata(self):
        """Search HDU metadata."""
        qspec = {
            "outfields": [
                "fitsfile__archive_filename",
                "fitsfile__caldat",
                "fitsfile__instrument",
                "fitsfile__proc_type",
                "AIRMASS"  # AUX field. Slows search
            ],
            "search": [
                ["fitsfile__caldat", "2017-08-14", "2017-08-16"],
                ["fitsfile__instrument", "decam"],
                ["fitsfile__proc_type", "raw"]
            ]
        }

        r = Noirlab(which='hdu').query_metadata(qspec, limit=3)
        actual = r
        print(f'DBG: test_query_hdu_metadata={actual.pformat_all()}')
        expected = exp.query_hdu_metadata
        assert actual.pformat_all() == expected

    # ##
    # ## Agnostic
    # ##

    def test_categoricals(self):
        """List categories."""
        r = Noirlab().categoricals()
        actual = r
        # Returned results may increase over time.
        print(f'DBG: test_categoricals={actual}')
        expected = exp.categoricals
        assert actual == expected

    # ##############################################################
    # ### (3) Other
    # get_token
    # retrieve/<md5>
    # version

    def test_retrieve(self):
        hdul = Noirlab().retrieve('f92541fdc566dfebac9e7d75e12b5601')
        actual = list(hdul[0].header.keys())
        expected = exp.retrieve
        assert actual == expected

    def test_version(self):
        r = Noirlab().version()
        assert r < 3.0

    def test_get_token(self):
        actual = Noirlab().get_token('nobody@university.edu', '123456789')
        expected = {'detail':
                    'No active account found with the given credentials'}
        assert actual == expected
