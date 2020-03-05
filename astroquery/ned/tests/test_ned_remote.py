# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import print_function

import pytest
from astropy.table import Table

from ... import ned


@pytest.mark.remote_data
class TestNed:

    def test_get_references(self):
        response = ned.core.Ned.get_table_async(
            "m1", table='references', from_year=2010)
        assert response is not None
        result = ned.core.Ned.get_table(
            "m1", table='references', to_year=2012, extended_search=True)
        assert isinstance(result, Table)

    def test_get_positions_async(self):
        response = ned.core.Ned.get_table_async("m1", table='positions')
        assert response is not None

    def test_get_positions(self):
        result = ned.core.Ned.get_table("m1", table='positions')
        assert isinstance(result, Table)

    def test_get_redshifts_async(self):
        response = ned.core.Ned.get_table_async("3c 273", table='redshifts')
        assert response is not None

    def test_get_redshifts(self):
        result = ned.core.Ned.get_table("3c 273", table='redshifts')
        assert isinstance(result, Table)

    def test_get_photometry_async(self):
        response = ned.core.Ned.get_table_async("3C 273", table='photometry')
        assert response is not None

    def test_photometry(self):
        result = ned.core.Ned.get_table("3c 273", table='photometry')
        assert isinstance(result, Table)

    def test_get_image_list(self):
        response = ned.core.Ned.get_image_list('m1')
        assert len(response) > 0

    def test_get_images_async(self):
        readable_objs = ned.core.Ned.get_images_async('m1')
        assert readable_objs is not None

    def test_get_images(self):
        fits_images = ned.core.Ned.get_images('m1')
        assert fits_images is not None

    def test_query_refcode_async(self):
        response = ned.core.Ned.query_refcode_async('1997A&A...323...31K')
        assert response is not None

    def test_query_refcode(self):
        result = ned.core.Ned.query_refcode('1997A&A...323...31K')
        assert isinstance(result, Table)

    def test_query_region_iau_async(self):
        response = ned.core.Ned.query_region_iau_async('1234-423')
        assert response is not None

    def test_query_region_iau(self):
        result = ned.core.Ned.query_region_iau('1234-423')
        assert isinstance(result, Table)

    def test_query_region_async(self):
        response = ned.core.Ned.query_region_async("05h35m17.3s +22d00m52.2s")
        assert response is not None

    def test_query_region(self):
        result = ned.core.Ned.query_region("m1")
        assert isinstance(result, Table)

    def test_query_object_async(self):
        response = ned.core.Ned.query_object_async('m1')
        assert response is not None

    def test_query_object(self):
        result = ned.core.Ned.query_object('m1')
        assert isinstance(result, Table)

    def test_get_object_notes_async(self):
        response = ned.core.Ned.get_table_async('m1', table='object_notes')
        assert response is not None

    def test_get_object_notes(self):
        result = ned.core.Ned.get_table('3c 273', table='object_notes')
        assert isinstance(result, Table)
