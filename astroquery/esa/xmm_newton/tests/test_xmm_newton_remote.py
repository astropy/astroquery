# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""

@author: Elena Colomo
@contact: ecolomo@esa.int

European Space Astronomy Centre (ESAC)
European Space Agency (ESA)

Created on 4 Sept. 2019
"""

import pytest

import sys
import tarfile
import os
import errno
import shutil
from astropy.coordinates import SkyCoord
from astropy.utils.diff import report_diff_values
from astroquery.utils.tap.core import TapPlus

from ..core import XMMNewtonClass


class TestXMMNewtonRemote():

    @pytest.mark.remote_data
    def test_download_data(self):
        parameters = {'observation_id': "0112880801",
                      'level': "ODF",
                      'filename': 'file',
                      'verbose': False}
        xsa = XMMNewtonClass(self.get_dummy_tap_handler())
        xsa.download_data(**parameters)

    @pytest.mark.remote_data
    def test_download_data_single_file(self):
        parameters = {'observation_id': "0762470101",
                      'level': "PPS",
                      'name': 'OBSMLI',
                      'filename': 'single',
                      'instname': 'OM',
                      'extension': 'FTZ',
                      'verbose': False}
        xsa = XMMNewtonClass(self.get_dummy_tap_handler())
        xsa.download_data(**parameters)

    @pytest.mark.remote_data
    def test_get_postcard(self):
        parameters = {'observation_id': "0112880801",
                      'image_type': "OBS_EPIC",
                      'filename': None,
                      'verbose': False}
        xsa = XMMNewtonClass(self.get_dummy_tap_handler())
        xsa.get_postcard(**parameters)

    @pytest.mark.remote_data
    def test_get_postcard_filename(self):
        parameters = {'observation_id': "0112880801",
                      'image_type': "OBS_EPIC",
                      'filename': "test",
                      'verbose': False}
        xsa = XMMNewtonClass(self.get_dummy_tap_handler())
        xsa.get_postcard(**parameters)

    @pytest.mark.remote_data
    def test_get_epic_spectra(self):
        _tarname = "tarfile.tar"
        _source_number = 83
        _instruments = ["M1", "M1_arf", "M1_bkg", "M1_rmf",
                        "M2", "M2_arf", "M2_bkg", "M2_rmf",
                        "PN", "PN_arf", "PN_bkg", "PN_rmf"]
        self._create_tar(_tarname, self._files)
        xsa = XMMNewtonClass(self.get_dummy_tap_handler())
        res = xsa.get_epic_spectra(_tarname, _source_number,
                                   instrument=[])
        assert len(res) == 8
        # Removing files created in this test
        for ob_name in self._files:
            shutil.rmtree(ob_name)
        os.remove(_tarname)

    @pytest.mark.remote_data
    def test_get_epic_metadata(self):
        tap_url = "http://nxsadev.esac.esa.int/tap-server/tap/"
        target_name = "4XMM J122934.7+015657"
        radius = 0.01
        epic_source_table = "xsa.v_epic_source"
        epic_source_column = "epic_source_equatorial_spoint"
        cat_4xmm_table = "xsa.v_epic_source_cat"
        cat_4xmm_column = "epic_source_cat_equatorial_spoint"
        stack_4xmm_table = "xsa.v_epic_xmm_stack_cat"
        stack_4xmm_column = "epic_stack_cat_equatorial_spoint"
        slew_source_table = "xsa.v_slew_source_cat"
        slew_source_column = "slew_source_cat_equatorial_spoint"
        xsa = XMMNewtonClass(TapPlus(url=tap_url))
        epic_source, cat_4xmm, stack_4xmm, slew_source = xsa.get_epic_metadata(target_name=target_name,
                                                                                radius=radius)
        c = SkyCoord.from_name(target_name, parse=True)
        query = ("select * from {} "
                 "where 1=contains({}, circle('ICRS', {}, {}, {}));")
        table = xsa.query_xsa_tap(query.format(epic_source_table,
                                               epic_source_column,
                                               c.ra.degree,
                                               c.dec.degree,
                                               radius))
        assert report_diff_values(epic_source, table)
        table = xsa.query_xsa_tap(query.format(cat_4xmm_table,
                                               cat_4xmm_column,
                                               c.ra.degree,
                                               c.dec.degree,
                                               radius))
        assert report_diff_values(cat_4xmm, table)
        table = xsa.query_xsa_tap(query.format(stack_4xmm_table,
                                               stack_4xmm_column,
                                               c.ra.degree,
                                               c.dec.degree,
                                               radius))
        assert report_diff_values(stack_4xmm, table)
        table = xsa.query_xsa_tap(query.format(slew_source_table,
                                               slew_source_column,
                                               c.ra.degree,
                                               c.dec.degree,
                                               radius))
        assert report_diff_values(slew_source, table)
