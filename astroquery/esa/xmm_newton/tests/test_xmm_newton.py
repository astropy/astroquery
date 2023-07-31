# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
====================
XMM-Newton Tap Tests
====================

European Space Astronomy Centre (ESAC)
European Space Agency (ESA)

"""
import errno
import os
import shutil
import tarfile
from pathlib import Path
from unittest.mock import patch

import pytest
from astropy.io import fits

from astroquery.exceptions import LoginError
from astroquery.esa.xmm_newton.core import XMMNewtonClass
from .dummy_handler import DummyHandler
from .dummy_tap_handler import DummyXMMNewtonTapHandler


def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)


class mockResponse:
    headers = {'Date': 'Wed, 24 Nov 2021 13:43:50 GMT',
               'Server': 'Apache/2.4.6 (Red Hat Enterprise Linux) OpenSSL/1.0.2k-fips',
               'Content-Disposition': 'inline; filename="0560181401.tar.gz"',
               'Content-Type': 'application/x-gzip',
               'Content-Length': '6590874', 'Connection': 'close'}
    status_code = 400

    @staticmethod
    def raise_for_status():
        pass


class TestXMMNewton:
    def get_dummy_tap_handler(self):
        parameters = {'query': "select top 10 * from v_public_observations",
                      'output_file': "test2.vot",
                      'output_format': "votable",
                      'verbose': False}
        dummyTapHandler = DummyXMMNewtonTapHandler("launch_job", parameters)
        return dummyTapHandler

    def test_query_xsa_tap(self):
        parameters = {'query': "select top 10 * from v_public_observations",
                      'output_file': "test2.vot",
                      'output_format': "votable",
                      'verbose': False}

        xsa = XMMNewtonClass(self.get_dummy_tap_handler())
        xsa.query_xsa_tap(**parameters)
        self.get_dummy_tap_handler().check_call("launch_job", parameters)
        self.get_dummy_tap_handler().check_parameters(parameters, "launch_job")
        self.get_dummy_tap_handler().check_method("launch_job")
        self.get_dummy_tap_handler().get_tables()
        self.get_dummy_tap_handler().get_columns()
        self.get_dummy_tap_handler().load_tables()

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

    def test_get_columns_valueerror(self):
        with pytest.raises(ValueError):
            xsa = XMMNewtonClass(self.get_dummy_tap_handler())
            xsa.get_columns("", only_names=True, verbose=True)

    def test_dummy_handler(self):
        parameters2 = {'table_name': "table",
                       'only_names': True,
                       'verbose': True}

        dummyHandler = DummyHandler("get_columns", parameters2)
        dummyHandler.check_call("get_columns", parameters2)
        dummyHandler.check_method("get_columns")
        dummyHandler.check_parameters(parameters2, "get_columns")
        dummyHandler.reset()

    def test_parse_filename(self, tmp_path):
        filename = Path(tmp_path, "filename.tar")
        self._create_tar(filename, self._files)
        xsa = XMMNewtonClass(self.get_dummy_tap_handler())
        with tarfile.open(filename, "r") as tar:
            for i in tar.getmembers():
                paths = os.path.split(i.name)
                fname = paths[1]
                paths = os.path.split(paths[0])
                if paths[1] != "pps":
                    continue
                fname_info = xsa._parse_filename(fname)
                assert fname_info["X"] == "P"

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

    def test_create_tar_lightcurves(self, tmp_path):
        path = Path(tmp_path, "tarfile_lightcurves.tar")
        self._create_tar_lightcurves(path, self._files_lightcurves)
        assert os.path.isfile(path)

    def test_get_epic_spectra_non_existing_file(self, capsys):
        _tarname = "nonexistingfile.tar"
        _source_number = 83
        xsa = XMMNewtonClass(self.get_dummy_tap_handler())
        res = xsa.get_epic_spectra(_tarname, _source_number,
                                   instrument=[])
        assert res is None
        out, err = capsys.readouterr()
        assert err == ("ERROR: File %s not found "
                       "[astroquery.esa.xmm_newton.core]\n" % _tarname)

    def test_get_epic_spectra_invalid_instrumnet(self, tmp_path, capsys):
        path = Path(tmp_path, "tarfile.tar")
        _invalid_instrument = "II"
        _source_number = 83
        self._create_tar(path, self._files)
        xsa = XMMNewtonClass(self.get_dummy_tap_handler())
        res = xsa.get_epic_spectra(path, _source_number,
                                   instrument=[_invalid_instrument])
        assert res == {}
        out, err = capsys.readouterr()
        assert err == ("WARNING: Invalid instrument %s "
                       "[astroquery.esa.xmm_newton.core]\n"
                       % _invalid_instrument)

    def test_get_epic_spectra_invalid_source_number(self, tmp_path, capsys):
        path = Path(tmp_path, "tarfile.tar")
        _invalid_source_number = 833
        _default_instrument = ['M1', 'M2', 'PN', 'EP']
        self._create_tar(path, self._files)
        xsa = XMMNewtonClass(self.get_dummy_tap_handler())
        res = xsa.get_epic_spectra(path, _invalid_source_number,
                                   instrument=[])
        assert res == {}
        out, err = capsys.readouterr()
        assert out == ("INFO: Nothing to extract with the given parameters:\n"
                       "  PPS: %s\n"
                       "  Source Number: %u\n"
                       "  Instrument: %s\n"
                       " [astroquery.esa.xmm_newton.core]\n"
                       % (path, _invalid_source_number,
                          _default_instrument))

    def test_get_epic_images_non_existing_file(self, capsys):
        _tarname = "nonexistingfile.tar"
        xsa = XMMNewtonClass(self.get_dummy_tap_handler())
        res = xsa.get_epic_images(_tarname, [], [],
                                  get_detmask=True, get_exposure_map=True)
        assert res is None
        out, err = capsys.readouterr()
        assert err == ("ERROR: File %s not found "
                       "[astroquery.esa.xmm_newton.core]\n" % _tarname)

    def test_get_epic_images_invalid_instrument(self, tmp_path, capsys):
        path = Path(tmp_path, "tarfile.tar")
        _invalid_instrument = "II"
        self._create_tar(path, self._files)
        xsa = XMMNewtonClass(self.get_dummy_tap_handler())
        res = xsa.get_epic_images(path,
                                  band=[], instrument=[_invalid_instrument],
                                  get_detmask=True, get_exposure_map=True)
        assert res == {}
        out, err = capsys.readouterr()
        assert err == ("WARNING: Invalid instrument %s "
                       "[astroquery.esa.xmm_newton.core]\n"
                       % _invalid_instrument)

    def test_get_epic_images_invalid_band(self, tmp_path, capsys):
        path = Path(tmp_path, "tarfile.tar")
        _invalid_band = 10
        self._create_tar(path, self._files)
        xsa = XMMNewtonClass(self.get_dummy_tap_handler())
        res = xsa.get_epic_images(path,
                                  band=[_invalid_band], instrument=[],
                                  get_detmask=True, get_exposure_map=True)
        assert res == {}
        out, err = capsys.readouterr()
        assert err == ("WARNING: Invalid band %u "
                       "[astroquery.esa.xmm_newton.core]\n" % _invalid_band)

    def test_get_epic_images(self, tmp_path):
        path = Path(tmp_path, "tarfile.tar")
        _instruments = ["M1", "M1_expo", "M1_det",
                        "M2", "M2_expo", "M2_det",
                        "PN", "PN_expo", "PN_det",
                        "EP", "EP_expo", "EP_det"]
        self._create_tar(path, self._files)
        xsa = XMMNewtonClass(self.get_dummy_tap_handler())
        res = xsa.get_epic_images(path, band=[], instrument=[],
                                  get_detmask=True, get_exposure_map=True)
        assert len(res) == 6  # Number of different bands
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
            if isinstance(v, str):
                f = os.path.split(v)
                assert f[1] in self._files["0405320501"]["pps"]
            if isinstance(v, list):
                for i in v:
                    f = os.path.split(i)
                    assert f[1] in self._files["0405320501"]["pps"]
        for k, v in res[2].items():
            assert k in _instruments
            if isinstance(v, str):
                f = os.path.split(v)
                assert f[1] in self._files["0405320501"]["pps"]
            if isinstance(v, list):
                for i in v:
                    f = os.path.split(i)
                    assert f[1] in self._files["0405320501"]["pps"]
        for k, v in res[3].items():
            assert k in _instruments
            if isinstance(v, str):
                f = os.path.split(v)
                assert f[1] in self._files["0405320501"]["pps"]
            if isinstance(v, list):
                for i in v:
                    f = os.path.split(i)
                    assert f[1] in self._files["0405320501"]["pps"]
        for k, v in res[4].items():
            assert k in _instruments
            if isinstance(v, str):
                f = os.path.split(v)
                assert f[1] in self._files["0405320501"]["pps"]
            if isinstance(v, list):
                for i in v:
                    f = os.path.split(i)
                    assert f[1] in self._files["0405320501"]["pps"]
        for k, v in res[5].items():
            assert k in _instruments
            if isinstance(v, str):
                f = os.path.split(v)
                assert f[1] in self._files["0405320501"]["pps"]
            if isinstance(v, list):
                for i in v:
                    f = os.path.split(i)
                    assert f[1] in self._files["0405320501"]["pps"]
        for k, v in res[8].items():
            assert k in _instruments
            if isinstance(v, str):
                f = os.path.split(v)
                assert f[1] in self._files["0405320501"]["pps"]
            if isinstance(v, list):
                for i in v:
                    f = os.path.split(i)
                    assert f[1] in self._files["0405320501"]["pps"]

        for ob in self._files:
            assert os.path.isdir(ob)
            for t in self._files[ob]:
                assert os.path.isdir(os.path.join(ob, t))
                for b in res:
                    for i in res[b]:
                        if isinstance(res[b][i], str):
                            assert os.path.isfile(res[b][i])
                        if isinstance(res[b][i], list):
                            for f in res[b][i]:
                                assert os.path.isfile(f)

    def test_get_epic_lightcurve(self, tmp_path):
        path = Path(tmp_path, "tarfile.tar")
        self._create_tar(path, self._files)
        _source_number = 1
        xsa = XMMNewtonClass(self.get_dummy_tap_handler())
        res = xsa.get_epic_lightcurve(path, _source_number,
                                      instrument=['M1', 'M2', 'PN'])
        assert res == {}

    def test_get_epic_lightcurve_non_existing_file(self, capsys):
        _tarname = "nonexistingfile.tar"
        _source_number = 146
        xsa = XMMNewtonClass(self.get_dummy_tap_handler())
        res = xsa.get_epic_lightcurve(_tarname, _source_number,
                                      instrument=[])
        assert res is None
        out, err = capsys.readouterr()
        assert err == ("ERROR: File %s not found "
                       "[astroquery.esa.xmm_newton.core]\n" % _tarname)

    def test_get_epic_lightcurve_invalid_instrument(self, tmp_path, capsys):
        path = Path(tmp_path, "tarfile.tar")
        _invalid_instrument = "II"
        self._create_tar(path, self._files)
        xsa = XMMNewtonClass(self.get_dummy_tap_handler())
        res = xsa.get_epic_images(path, [], [_invalid_instrument],
                                  get_detmask=True, get_exposure_map=True)
        assert res == {}
        out, err = capsys.readouterr()
        assert err == ("WARNING: Invalid instrument %s "
                       "[astroquery.esa.xmm_newton.core]\n"
                       % _invalid_instrument)

    def test_get_epic_lightcurve_invalid_source_number(self, tmp_path, capsys):
        path = Path(tmp_path, "tarfile.tar")
        _invalid_source_number = 833
        _default_instrument = ['M1', 'M2', 'PN', 'EP']
        self._create_tar(path, self._files)
        xsa = XMMNewtonClass(self.get_dummy_tap_handler())
        res = xsa.get_epic_lightcurve(path, _invalid_source_number,
                                      instrument=[])
        assert res == {}
        out, err = capsys.readouterr()
        assert out == ("INFO: Nothing to extract with the given parameters:\n"
                       "  PPS: %s\n"
                       "  Source Number: %u\n"
                       "  Instrument: %s\n"
                       " [astroquery.esa.xmm_newton.core]\n"
                       % (path, _invalid_source_number,
                          _default_instrument))

    def test_create_link(self):
        xsa = XMMNewtonClass(self.get_dummy_tap_handler())
        link = xsa._create_link("0560181401")
        assert link == "https://nxsa.esac.esa.int/nxsa-sl/servlet/data-action-aio?obsno=0560181401"

    @patch('astroquery.query.BaseQuery._request')
    def test_request_link(self, mock_request):
        xsa = XMMNewtonClass(self.get_dummy_tap_handler())
        mock_request.return_value = mockResponse
        params = xsa._request_link("https://nxsa.esac.esa.int/nxsa-sl/servlet/data-action-aio?obsno=0560181401", None)
        assert params == {'filename': '0560181401.tar.gz'}

    @patch('astroquery.query.BaseQuery._request')
    def test_request_link_protected(self, mock_request):
        with pytest.raises(LoginError):
            xsa = XMMNewtonClass(self.get_dummy_tap_handler())
            dummyclass = mockResponse
            dummyclass.headers = {}
            mock_request.return_value = dummyclass
            xsa._request_link("https://nxsa.esac.esa.int/nxsa-sl/servlet/data-action-aio?obsno=0560181401", None)

    @patch('astroquery.query.BaseQuery._request')
    def test_request_link_incorrect_credentials(self, mock_request):
        with pytest.raises(LoginError):
            xsa = XMMNewtonClass(self.get_dummy_tap_handler())
            dummyclass = mockResponse
            dummyclass.headers = {}
            dummyclass.status_code = 10
            mock_request.return_value = dummyclass
            xsa._request_link("https://nxsa.esac.esa.int/nxsa-sl/servlet/data-action-aio?obsno=0560181401", None)

    @patch('astroquery.query.BaseQuery._request')
    def test_request_link_with_statuscode_401(self, mock_request):
        with pytest.raises(LoginError):
            xsa = XMMNewtonClass(self.get_dummy_tap_handler())
            dummyclass = mockResponse
            dummyclass.headers = {}
            dummyclass.status_code = 401
            mock_request.return_value = dummyclass
            xsa._request_link("https://nxsa.esac.esa.int/nxsa-sl/servlet/data-action-aio?obsno=0560181401", None)

    def test_get_username_and_password(self):
        xsa = XMMNewtonClass(self.get_dummy_tap_handler())
        file = data_path("dummy_config.ini")
        username, password = xsa._get_username_and_password(file)
        assert username == "test"
        assert password == "test"

    def test_create_filename_None(self):
        xsa = XMMNewtonClass(self.get_dummy_tap_handler())
        filename = xsa._create_filename(None, "0560181401", ['.tar', '.gz'])
        assert filename == "0560181401.tar.gz"

    def test_create_filename_Not_None(self):
        xsa = XMMNewtonClass(self.get_dummy_tap_handler())
        filename = xsa._create_filename("Test", "0560181401", ['.tar', '.gz'])
        assert filename == "Test.tar.gz"
