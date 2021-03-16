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
from ..tests.dummy_tap_handler import DummyXMMNewtonTapHandler


class TestXMMNewton():

    def get_dummy_tap_handler(self):
        parameterst = {'query': "select top 10 * from v_public_observations",
                       'output_file': "test2.vot",
                       'output_format': "votable",
                       'verbose': False}
        dummyTapHandler = DummyXMMNewtonTapHandler("launch_job", parameterst)
        return dummyTapHandler

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

    def test_query_xsa_tap(self):
        parameters = {'query': "select top 10 * from v_public_observations",
                      'output_file': "test2.vot",
                      'output_format': "votable",
                      'verbose': False}

        xsa = XMMNewtonClass(self.get_dummy_tap_handler())
        xsa.query_xsa_tap(**parameters)
        self.get_dummy_tap_handler().check_call("launch_job", parameters)

    def test_get_tables(self):
        parameters2 = {'only_names': True,
                       'verbose': True}

        dummyTapHandler = DummyXMMNewtonTapHandler("get_tables", parameters2)
        xsa = XMMNewtonClass(self.get_dummy_tap_handler())
        xsa.get_tables(only_names=True, verbose=True)
        dummyTapHandler.check_call("get_tables", parameters2)

    def test_get_columns(self):
        parameters2 = {'table_name': "table",
                       'only_names': True,
                       'verbose': True}

        dummyTapHandler = DummyXMMNewtonTapHandler("get_columns", parameters2)
        xsa = XMMNewtonClass(self.get_dummy_tap_handler())
        xsa.get_columns("table", only_names=True, verbose=True)
        dummyTapHandler.check_call("get_columns", parameters2)

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

    _files_lightcurves = {
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
                "P0405320501M2S003SRSPEC0053.FTZ",
                "P0405320501PNS001BGSPEC0053.FTZ",
                "P0405320501M2S003BGSPEC0053.FTZ",
                "P0405320501PNS001SRCARF0053.FTZ",
                "P0405320501M2S003SRCARF0053.FTZ",
                "P0405320501PNS001SRSPEC0053.FTZ",
                "P0405320501PNS001SRCTSR8092.FTZ",
                "P0405320501PNS001FBKTSR8092.FTZ",
                "P0405320501PNS001SRCTSR8093.FTZ",
                "P0405320501PNS001FBKTSR8093.FTZ"
            ]
        }
    }

    _rmf_files = ["epn_e2_ff20_sdY4.rmf", "m2_e9_im_pall_o.rmf"]

    def _create_tar_lightcurves(self, tarname, files):
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
                        if f[17:23] == "SRSPEC":
                            rmf_file = self._rmf_files[1]
                            if f[11:13] == "PN":
                                rmf_file = self._rmf_files[0]
                            hdr = fits.Header()
                            hdr["RESPFILE"] = rmf_file
                            hdr["SPECDELT"] = 5
                            hdu = fits.PrimaryHDU(header=hdr)
                            hdu.name = "SPECTRUM"
                            hdu.writeto(os.path.join(ob_name, ftype, f))

                        else:
                            _file = open(os.path.join(ob_name, ftype, f), "w")
                            _file.close()
                        tar.add(os.path.join(ob_name, ftype, f))
                        os.remove(os.path.join(ob_name, ftype, f))
                    shutil.rmtree(os.path.join(ob_name, ftype))
                shutil.rmtree(ob_name)

    def test_get_epic_spectra_non_existing_file(self, capsys):
        _tarname = "nonexistingfile.tar"
        _source_number = 83
        xsa = XMMNewtonClass(self.get_dummy_tap_handler())
        res = xsa.get_epic_spectra(_tarname, _source_number,
                                   instrument=[])
        assert res == {}
        out, err = capsys.readouterr()
        assert err == ("ERROR: File %s not found "
                       "[astroquery.esa.xmm_newton.core]\n" % _tarname)

    def test_get_epic_spectra_invalid_instrumnet(self, capsys):
        _tarname = "tarfile.tar"
        _invalid_instrument = "II"
        _source_number = 83
        self._create_tar(_tarname, self._files)
        xsa = XMMNewtonClass(self.get_dummy_tap_handler())
        res = xsa.get_epic_spectra(_tarname, _source_number,
                                   instrument=[_invalid_instrument])
        assert res == {}
        out, err = capsys.readouterr()
        assert err == ("WARNING: Invalid instrument %s "
                       "[astroquery.esa.xmm_newton.core]\n"
                       % _invalid_instrument)
        os.remove(_tarname)

    def test_get_epic_spectra_invalid_source_number(self, capsys):
        _tarname = "tarfile.tar"
        _invalid_source_number = 833
        _default_instrument = ['M1', 'M2', 'PN', 'EP']
        self._create_tar(_tarname, self._files)
        xsa = XMMNewtonClass(self.get_dummy_tap_handler())
        res = xsa.get_epic_spectra(_tarname, _invalid_source_number,
                                   instrument=[])
        assert res == {}
        out, err = capsys.readouterr()
        assert out == ("INFO: Nothing to extract with the given parameters:\n"
                       "  PPS: %s\n"
                       "  Source Number: %u\n"
                       "  Instrument: %s\n"
                       " [astroquery.esa.xmm_newton.core]\n"
                       % (_tarname, _invalid_source_number,
                          _default_instrument))
        os.remove(_tarname)

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
        for k, v in res.items():
            assert k in _instruments
            if type(v) == str:
                f = os.path.split(v)
                assert f[1] in self._files["0405320501"]["pps"] or \
                    f[1] in self._rmf_files
            if type(v) == list:
                for i in v:
                    f = os.path.split(i)
                    assert f[1] in self._files["0405320501"]["pps"] or \
                        f[1] in self._rmf_files

        for ob in self._files:
            assert os.path.isdir(ob)
            for t in self._files[ob]:
                assert os.path.isdir(os.path.join(ob, t))
                for s in res:
                    if type(res[s]) == str:
                        assert os.path.isfile(res[s])
                    if type(res[s]) == list:
                        for f in res[s]:
                            assert os.path.isfile(f)

        # Removing files created in this test
        for ob_name in self._files:
            shutil.rmtree(ob_name)
        os.remove(_tarname)

    def test_get_epic_images_non_existing_file(self, capsys):
        _tarname = "nonexistingfile.tar"
        xsa = XMMNewtonClass(self.get_dummy_tap_handler())
        res = xsa.get_epic_images(_tarname, [], [],
                                  get_detmask=True, get_exposure_map=True)
        assert res == {}
        out, err = capsys.readouterr()
        assert err == ("ERROR: File %s not found "
                       "[astroquery.esa.xmm_newton.core]\n" % _tarname)

    def test_get_epic_images_invalid_instrument(self, capsys):
        _tarname = "tarfile.tar"
        _invalid_instrument = "II"
        self._create_tar(_tarname, self._files)
        xsa = XMMNewtonClass(self.get_dummy_tap_handler())
        res = xsa.get_epic_images(_tarname,
                                  band=[], instrument=[_invalid_instrument],
                                  get_detmask=True, get_exposure_map=True)
        assert res == {}
        out, err = capsys.readouterr()
        assert err == ("WARNING: Invalid instrument %s "
                       "[astroquery.esa.xmm_newton.core]\n"
                       % _invalid_instrument)
        os.remove(_tarname)

    def test_get_epic_images_invalid_band(self, capsys):
        _tarname = "tarfile.tar"
        _invalid_band = 10
        self._create_tar(_tarname, self._files)
        xsa = XMMNewtonClass(self.get_dummy_tap_handler())
        res = xsa.get_epic_images(_tarname,
                                  band=[_invalid_band], instrument=[],
                                  get_detmask=True, get_exposure_map=True)
        assert res == {}
        out, err = capsys.readouterr()
        assert err == ("WARNING: Invalid band %u "
                       "[astroquery.esa.xmm_newton.core]\n" % _invalid_band)
        os.remove(_tarname)

    def test_get_epic_images(self):
        _tarname = "tarfile.tar"
        _instruments = ["M1", "M1_expo", "M1_det",
                        "M2", "M2_expo", "M2_det",
                        "PN", "PN_expo", "PN_det",
                        "EP", "EP_expo", "EP_det"]
        self._create_tar(_tarname, self._files)
        xsa = XMMNewtonClass(self.get_dummy_tap_handler())
        res = xsa.get_epic_images(_tarname, band=[], instrument=[],
                                  get_detmask=True, get_exposure_map=True)
        assert len(res) == 6     # Number of different bands
        assert len(res[1]) == 9  # Number of different inst within band 1
        assert len(res[2]) == 9  # Number of different inst within band 2
        assert len(res[3]) == 9  # Number of different inst within band 3
        assert len(res[4]) == 9  # Number of different inst within band 4
        assert len(res[5]) == 9  # Number of different inst within band 5
        assert len(res[8]) == 6  # Number of different inst within band 8
        # Notice that we consider the exposure and the detector maps as
        # an instrument
        for k, v in res[1].items():
            assert k in _instruments
            if type(v) == str:
                f = os.path.split(v)
                assert f[1] in self._files["0405320501"]["pps"]
            if type(v) == list:
                for i in v:
                    f = os.path.split(i)
                    assert f[1] in self._files["0405320501"]["pps"]
        for k, v in res[2].items():
            assert k in _instruments
            if type(v) == str:
                f = os.path.split(v)
                assert f[1] in self._files["0405320501"]["pps"]
            if type(v) == list:
                for i in v:
                    f = os.path.split(i)
                    assert f[1] in self._files["0405320501"]["pps"]
        for k, v in res[3].items():
            assert k in _instruments
            if type(v) == str:
                f = os.path.split(v)
                assert f[1] in self._files["0405320501"]["pps"]
            if type(v) == list:
                for i in v:
                    f = os.path.split(i)
                    assert f[1] in self._files["0405320501"]["pps"]
        for k, v in res[4].items():
            assert k in _instruments
            if type(v) == str:
                f = os.path.split(v)
                assert f[1] in self._files["0405320501"]["pps"]
            if type(v) == list:
                for i in v:
                    f = os.path.split(i)
                    assert f[1] in self._files["0405320501"]["pps"]
        for k, v in res[5].items():
            assert k in _instruments
            if type(v) == str:
                f = os.path.split(v)
                assert f[1] in self._files["0405320501"]["pps"]
            if type(v) == list:
                for i in v:
                    f = os.path.split(i)
                    assert f[1] in self._files["0405320501"]["pps"]
        for k, v in res[8].items():
            assert k in _instruments
            if type(v) == str:
                f = os.path.split(v)
                assert f[1] in self._files["0405320501"]["pps"]
            if type(v) == list:
                for i in v:
                    f = os.path.split(i)
                    assert f[1] in self._files["0405320501"]["pps"]

        for ob in self._files:
            assert os.path.isdir(ob)
            for t in self._files[ob]:
                assert os.path.isdir(os.path.join(ob, t))
                for b in res:
                    for i in res[b]:
                        if type(res[b][i]) == str:
                            assert os.path.isfile(res[b][i])
                        if type(res[b][i]) == list:
                            for f in res[b][i]:
                                assert os.path.isfile(f)

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

    def test_get_epic_lightcurve_non_existing_file(self, capsys):
        _tarname = "nonexistingfile.tar"
        _source_number = 146
        xsa = XMMNewtonClass(self.get_dummy_tap_handler())
        res = xsa.get_epic_lightcurve(_tarname, _source_number,
                                      instrument=[])
        assert res == {}
        out, err = capsys.readouterr()
        assert err == ("ERROR: File %s not found "
                       "[astroquery.esa.xmm_newton.core]\n" % _tarname)

    def test_get_epic_lightcurve_invalid_instrument(self, capsys):
        _tarname = "tarfile.tar"
        _invalid_instrument = "II"
        self._create_tar(_tarname, self._files)
        xsa = XMMNewtonClass(self.get_dummy_tap_handler())
        res = xsa.get_epic_images(_tarname, [], [_invalid_instrument],
                                  get_detmask=True, get_exposure_map=True)
        assert res == {}
        out, err = capsys.readouterr()
        assert err == ("WARNING: Invalid instrument %s "
                       "[astroquery.esa.xmm_newton.core]\n"
                       % _invalid_instrument)
        os.remove(_tarname)

    def test_get_epic_images_invalid_band(self, capsys):
        _tarname = "tarfile.tar"
        _invalid_band = 10
        self._create_tar(_tarname, self._files)
        xsa = XMMNewtonClass(self.get_dummy_tap_handler())
        res = xsa.get_epic_images(_tarname, [_invalid_band], [],
                                  get_detmask=True, get_exposure_map=True)
        assert res == {}
        out, err = capsys.readouterr()
        assert err == ("WARNING: Invalid band %u "
                       "[astroquery.esa.xmm_newton.core]\n" % _invalid_band)
        os.remove(_tarname)

    def test_get_epic_lightcurve_invalid_source_number(self, capsys):
        _tarname = "tarfile.tar"
        _invalid_source_number = 833
        _default_instrument = ['M1', 'M2', 'PN', 'EP']
        self._create_tar(_tarname, self._files)
        xsa = XMMNewtonClass(self.get_dummy_tap_handler())
        res = xsa.get_epic_lightcurve(_tarname, _invalid_source_number,
                                      instrument=[])
        assert res == {}
        out, err = capsys.readouterr()
        assert out == ("INFO: Nothing to extract with the given parameters:\n"
                       "  PPS: %s\n"
                       "  Source Number: %u\n"
                       "  Instrument: %s\n"
                       " [astroquery.esa.xmm_newton.core]\n"
                       % (_tarname, _invalid_source_number,
                          _default_instrument))
        os.remove(_tarname)

    def test_get_epic_images(self):
        _tarname = "tarfile.tar"
        _instruments = ["M1", "M1_expo", "M1_det",
                        "M2", "M2_expo", "M2_det",
                        "PN", "PN_expo", "PN_det",
                        "EP", "EP_expo", "EP_det"]
        self._create_tar(_tarname, self._files)
        xsa = XMMNewtonClass(self.get_dummy_tap_handler())
        res = xsa.get_epic_images(_tarname, [], [],
                                  get_detmask=True, get_exposure_map=True)
        assert len(res) == 6     # Number of different bands
        assert len(res[1]) == 9  # Number of different inst within band 1
        assert len(res[2]) == 9  # Number of different inst within band 2
        assert len(res[3]) == 9  # Number of different inst within band 3
        assert len(res[4]) == 9  # Number of different inst within band 4
        assert len(res[5]) == 9  # Number of different inst within band 5
        assert len(res[8]) == 6  # Number of different inst within band 8
        # Notice that we consider the exposure and the detector maps as
        # an instrument
        for k, v in res[1].items():
            assert k in _instruments
            if type(v) == str:
                f = os.path.split(v)
                assert f[1] in self._files["0405320501"]["pps"]
            if type(v) == list:
                for i in v:
                    f = os.path.split(i)
                    assert f[1] in self._files["0405320501"]["pps"]
        for k, v in res[2].items():
            assert k in _instruments
            if type(v) == str:
                f = os.path.split(v)
                assert f[1] in self._files["0405320501"]["pps"]
            if type(v) == list:
                for i in v:
                    f = os.path.split(i)
                    assert f[1] in self._files["0405320501"]["pps"]
        for k, v in res[3].items():
            assert k in _instruments
            if type(v) == str:
                f = os.path.split(v)
                assert f[1] in self._files["0405320501"]["pps"]
            if type(v) == list:
                for i in v:
                    f = os.path.split(i)
                    assert f[1] in self._files["0405320501"]["pps"]
        for k, v in res[4].items():
            assert k in _instruments
            if type(v) == str:
                f = os.path.split(v)
                assert f[1] in self._files["0405320501"]["pps"]
            if type(v) == list:
                for i in v:
                    f = os.path.split(i)
                    assert f[1] in self._files["0405320501"]["pps"]
        for k, v in res[5].items():
            assert k in _instruments
            if type(v) == str:
                f = os.path.split(v)
                assert f[1] in self._files["0405320501"]["pps"]
            if type(v) == list:
                for i in v:
                    f = os.path.split(i)
                    assert f[1] in self._files["0405320501"]["pps"]
        for k, v in res[8].items():
            assert k in _instruments
            if type(v) == str:
                f = os.path.split(v)
                assert f[1] in self._files["0405320501"]["pps"]
            if type(v) == list:
                for i in v:
                    f = os.path.split(i)
                    assert f[1] in self._files["0405320501"]["pps"]

        for ob in self._files:
            assert os.path.isdir(ob)
            for t in self._files[ob]:
                assert os.path.isdir(os.path.join(ob, t))
                for b in res:
                    for i in res[b]:
                        if type(res[b][i]) == str:
                            assert os.path.isfile(res[b][i])
                        if type(res[b][i]) == list:
                            for f in res[b][i]:
                                assert os.path.isfile(f)

        # Removing files created in this test
        for ob_name in self._files:
            shutil.rmtree(ob_name)
        os.remove(_tarname)
