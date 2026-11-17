# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
================
eJWST DATA Tests
================

European Space Astronomy Centre (ESAC)
European Space Agency (ESA)

"""
import os
from unittest.mock import patch

import pytest
from requests import HTTPError

from astroquery.esa.jwst import conf
from astroquery.esa.jwst.core import JwstClass


def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)


def get_product_mock(params, *args, **kwargs):
    if kwargs and kwargs.get('file_name'):
        return "00000000-0000-0000-8740-65e2827c9895"
    else:
        return "jw00617023001_02102_00001_nrcb4_uncal.fits"


@pytest.fixture(autouse=True)
def get_product_request(request):
    mp = request.getfixturevalue("monkeypatch")
    mp.setattr(JwstClass, '_query_get_product', get_product_mock)
    return mp


class TestData:

    @patch('astroquery.esa.utils.utils.pyvo.dal.TAPService.capabilities', [])
    @patch('astroquery.esa.jwst.core.esautils.download_file')
    @patch.object(JwstClass, '_query_get_product',
                  return_value='jw00617023001_02102_00001_nrcb4_uncal.fits')
    def test_get_product(self, mock_qget, mock_download):
        jwst = JwstClass(show_messages=False)

        with pytest.raises(ValueError) as err:
            jwst.get_product()
        assert "Missing required argument: 'artifact_id'" in str(err.value)

        artifact_id = "00000000-0000-0000-8740-65e2827c9895"
        mock_download.return_value = \
            "/tmp/jw00617023001_02102_00001_nrcb4_uncal.fits"

        result = jwst.get_product(artifact_id=artifact_id)

        mock_qget.assert_called_once_with(artifact_id=artifact_id)
        mock_download.assert_called_once()
        _, kwargs = mock_download.call_args

        assert kwargs["url"] == conf.JWST_DATA_SERVER
        assert kwargs["session"] is jwst.tap._session
        assert kwargs["params"] == {
            "RETRIEVAL_TYPE": "PRODUCT",
            "TAPCLIENT": "ASTROQUERY",
            "ARTIFACTID": artifact_id,
        }
        expected_filename = "jw00617023001_02102_00001_nrcb4_uncal.fits"
        assert kwargs["filename"] == expected_filename
        assert result is not None


@pytest.mark.remote_data
def test_login_error():
    jwst = JwstClass(show_messages=False)
    with pytest.raises(HTTPError) as err:
        jwst.login(user="dummy", password="dummy")
    assert "401" in err.value.args[0]
