# Licensed under a 3-clause BSD style license - see LICENSE.rst
from datetime import datetime, timezone
import os
from pathlib import Path
from urllib.parse import urlparse
import re
from unittest.mock import Mock, MagicMock, patch

from astropy import coordinates
from astropy import units as u
import numpy as np
import pytest

from pyvo.dal.exceptions import DALOverflowWarning

from astroquery.exceptions import CorruptDataWarning
from .. import Nrao


@pytest.mark.remote_data
class TestNrao:
    def test_SgrAstar(self, tmp_path, nrao):
        nrao.cache_location = tmp_path
        result_s = nrao.query_object('Sgr A*', maxrec=5)

    def test_ra_dec(self, nrao):
        payload = {'ra_dec': '181.0192d -0.01928d'}
        result = nrao.query(payload)
        assert len(result) > 0

    def test_query(self, tmp_path, nrao):
        nrao.cache_location = tmp_path

        result = nrao.query_object('M83', maxrec=5)
