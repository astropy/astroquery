# Licensed under a 3-clause BSD style license - see LICENSE.rst
import pytest
from astropy.coordinates import SkyCoord
import astropy.units as u
from astropy.tests.helper import remote_data
from astropy.table import Table
from ... import ibe

# Some very basic remote tests based on examples from
# http://www.ptf.caltech.edu/system/media_files/binaries/5/original/ptf_irsaibeguide.pdf


@remote_data
def test_ibe_pos():
    table = ibe.Ibe.query_region(
        SkyCoord(148.969687 * u.deg, 69.679383 * u.deg),
        where='expid <= 43010')
    assert isinstance(table, Table)
    assert len(table) == 21


@remote_data
def test_ibe_field_id():
    table = ibe.Ibe.query_region(
        where="ptffield = 4808 and filter='R'")
    assert isinstance(table, Table)
    assert len(table) == 22
