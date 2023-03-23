# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
=======================
XMM-Newton Remote Tests
=======================

European Space Astronomy Centre (ESAC)
European Space Agency (ESA)

"""

import pytest
from astroquery.exceptions import LoginError

import tarfile
import os
import errno
import shutil
from astropy.coordinates import SkyCoord
from astropy.utils.diff import report_diff_values
from astroquery.utils.tap.core import TapPlus

from ..core import XMMNewtonClass
from ..tests.dummy_tap_handler import DummyXMMNewtonTapHandler


def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)


@pytest.mark.remote_data
class TestXMMNewtonRemote:
    _files = {
        "0405320501": {
            "pps": [
                "P0405320501M1S002EXPMAP1000.FTZ",
                "P0405320501M1S002IMAGE_4000.FTZ",
                "P0405320501M2S003EXPMAP2000.FTZ",
                "P0405320501M2S003IMAGE_5000.FTZ",
                "P0405320501PNS001EXPMAP3000.FTZ",
                "P0405320501PNS001IMAGE_8000.FTZ",
                "P0405320501M1S002EXPMAP2000.FTZ",
                "P0405320501M1S002IMAGE_5000.FTZ",
                "P0405320501M2S003EXPMAP3000.FTZ",
                "P0405320501M2S003IMAGE_8000.FTZ",
                "P0405320501PNS001EXPMAP4000.FTZ",
                "P0405320501PNX000DETMSK1000.FTZ",
                "P0405320501M1S002EXPMAP3000.FTZ",
                "P0405320501M1S002IMAGE_8000.FTZ",
                "P0405320501M2S003EXPMAP4000.FTZ",
                "P0405320501M2X000DETMSK1000.FTZ",
                "P0405320501PNS001EXPMAP5000.FTZ",
                "P0405320501PNX000DETMSK2000.FTZ",
                "P0405320501M1S002EXPMAP4000.FTZ",
                "P0405320501M1X000DETMSK1000.FTZ",
                "P0405320501M2S003EXPMAP5000.FTZ",
                "P0405320501M2X000DETMSK2000.FTZ",
                "P0405320501PNS001EXPMAP8000.FTZ",
                "P0405320501PNX000DETMSK3000.FTZ",
                "P0405320501M1S002EXPMAP5000.FTZ",
                "P0405320501M1X000DETMSK2000.FTZ",
                "P0405320501M2S003EXPMAP8000.FTZ",
                "P0405320501M2X000DETMSK3000.FTZ",
                "P0405320501PNS001IMAGE_1000.FTZ",
                "P0405320501PNX000DETMSK4000.FTZ",
                "P0405320501M1S002EXPMAP8000.FTZ",
                "P0405320501M1X000DETMSK3000.FTZ",
                "P0405320501M2S003IMAGE_1000.FTZ",
                "P0405320501M2X000DETMSK4000.FTZ",
                "P0405320501PNS001IMAGE_2000.FTZ",
                "P0405320501PNX000DETMSK5000.FTZ",
                "P0405320501M1S002IMAGE_1000.FTZ",
                "P0405320501M1X000DETMSK4000.FTZ",
                "P0405320501M2S003IMAGE_2000.FTZ",
                "P0405320501M2X000DETMSK5000.FTZ",
                "P0405320501PNS001IMAGE_3000.FTZ",
                "P0405320501M1S002IMAGE_2000.FTZ",
                "P0405320501M1X000DETMSK5000.FTZ",
                "P0405320501M2S003IMAGE_3000.FTZ",
                "P0405320501PNS001EXPMAP1000.FTZ",
                "P0405320501PNS001IMAGE_4000.FTZ",
                "P0405320501M1S002IMAGE_3000.FTZ",
                "P0405320501M2S003EXPMAP1000.FTZ",
                "P0405320501M2S003IMAGE_4000.FTZ",
                "P0405320501PNS001EXPMAP2000.FTZ",
                "P0405320501PNS001IMAGE_5000.FTZ",
                "P0405320501PNU001IMAGE_5000.FTZ",
                "P0405320501PNX001IMAGE_5000.FTZ"
            ]
        }
    }

    def get_dummy_tap_handler(self):
        parameters = {'query': "select top 10 * from v_public_observations",
                      'output_file': "test2.vot",
                      'output_format': "votable",
                      'verbose': False}
        dummyTapHandler = DummyXMMNewtonTapHandler("launch_job", parameters)
        return dummyTapHandler

    def _create_tar(self, tarname, files):
        with tarfile.open(tarname, "w") as tar:
            for ob_name, ob in self._files.items():
                for ftype, ftype_val in ob.items():
                    for f in ftype_val:
                        try:
                            os.makedirs(os.path.join(ob_name, ftype))
                        except OSError as exc:
                            if exc.errno == errno.EEXIST and \
                                    os.path.isdir(os.path.join(ob_name, ftype)):
                                pass
                            else:
                                raise
                        _file = open(os.path.join(ob_name, ftype, f), "w")
                        _file.close()
                        tar.add(os.path.join(ob_name, ftype, f))
                        os.remove(os.path.join(ob_name, ftype, f))
                    shutil.rmtree(os.path.join(ob_name, ftype))
                    shutil.rmtree(ob_name)

    def test_download_data(self, tmp_cwd):
        parameters = {'observation_id': "0112880801",
                      'level': "ODF",
                      'filename': 'file',
                      'verbose': False}
        xsa = XMMNewtonClass(self.get_dummy_tap_handler())
        xsa.download_data(**parameters)

    def test_download_data_single_file(self, tmp_cwd):
        parameters = {'observation_id': "0762470101",
                      'level': "PPS",
                      'name': 'OBSMLI',
                      'filename': 'single',
                      'instname': 'OM',
                      'extension': 'FTZ',
                      'verbose': False}
        xsa = XMMNewtonClass(self.get_dummy_tap_handler())
        xsa.download_data(**parameters)

    def test_get_postcard(self, tmp_cwd):
        parameters = {'observation_id': "0112880801",
                      'image_type': "OBS_EPIC",
                      'filename': None,
                      'verbose': False}
        xsa = XMMNewtonClass(self.get_dummy_tap_handler())
        xsa.get_postcard(**parameters)

    def test_get_postcard_filename(self, tmp_cwd):
        parameters = {'observation_id': "0112880801",
                      'image_type': "OBS_EPIC",
                      'filename': "test",
                      'verbose': False}
        xsa = XMMNewtonClass(self.get_dummy_tap_handler())
        xsa.get_postcard(**parameters)

    def test_get_epic_metadata(self):
        tap_url = "https://nxsa.esac.esa.int/tap-server/tap/"
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

    def test_download_proprietary_data_incorrect_credentials(self, tmp_cwd):
        parameters = {'observation_id': "0861270201",
                      'prop': 'True',
                      'credentials_file': data_path("dummy_config.ini"),
                      'level': "PPS",
                      'name': 'OBSMLI',
                      'filename': 'single',
                      'instname': 'OM',
                      'extension': 'FTZ',
                      'verbose': False}
        xsa = XMMNewtonClass(self.get_dummy_tap_handler())
        with pytest.raises(LoginError):
            xsa.download_data(**parameters)

    def test_download_proprietary_data_without_credentials(self, tmp_cwd):
        parameters = {'observation_id': "0861270201",
                      'level': "PPS",
                      'name': 'OBSMLI',
                      'filename': 'single',
                      'instname': 'OM',
                      'extension': 'FTZ',
                      'verbose': False}
        xsa = XMMNewtonClass(self.get_dummy_tap_handler())
        with pytest.raises(LoginError):
            xsa.download_data(**parameters)

    def test_get_epic_spectra(self, tmp_cwd):
        _tarname = "tarfile.tar"
        _source_number = 83
        self._create_tar(_tarname, self._files)
        xsa = XMMNewtonClass(self.get_dummy_tap_handler())
        res = xsa.get_epic_spectra(_tarname, _source_number,
                                   instrument=[])
        assert len(res) == 0
