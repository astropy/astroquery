# Licensed under a 3-clause BSD style license - see LICENSE.rst
import os
import pytest
import requests

from astropy.table import Table
import astropy.units as u

from astroquery.ipac.irsa import irsa_dust

M31_XML = "dustm31.xml"
M81_XML = "dustm81.xml"
M101_XML = "dustm101.xml"
ERR_XML = "dust-error.xml"
M51_EXT_TBL = "dust_ext_detail.tbl"
IMG_FITS = "test.fits"
M31_URL_ALL = [
    'p338Dust.fits',
    'p338i100.fits',
    'p338temp.fits'
]

M31_URL_E = [
    'p338i100.fits'
]

M31_URL_R = [
    'p338Dust.fits'
]

M31_URL_T = [
    'p338temp.fits'
]


class DustTestCase:

    def data(self, filename):
        data_dir = os.path.join(os.path.dirname(__file__), 'data')
        return os.path.join(data_dir, filename)


@pytest.mark.remote_data
class TestDust(DustTestCase):

    def test_xml_ok(self):
        response = requests.get(irsa_dust.core.IrsaDust.DUST_SERVICE_URL + "?locstr=m31")
        data = response.text
        xml_tree = irsa_dust.utils.xml(data)
        assert xml_tree is not None

    def test_xml_err(self):
        response = requests.get(irsa_dust.core.IrsaDust.DUST_SERVICE_URL + "?locstr=100")
        data = response.text
        with pytest.raises(Exception):
            irsa_dust.utils.xml(data)

    @pytest.mark.parametrize(('image_type', 'expected_tails'),
                             [(None, M31_URL_ALL),
                              ('100um', M31_URL_E),
                              ('ebv', M31_URL_R),
                              ('temperature', M31_URL_T),
                              ])
    def test_extract_image_urls_instance(self, image_type, expected_tails):
        response = requests.get(irsa_dust.core.IrsaDust.DUST_SERVICE_URL + "?locstr=m31")
        data = response.text
        url_list = irsa_dust.core.IrsaDust().extract_image_urls(
            data, image_type=image_type)
        for url, tail in zip(url_list, expected_tails):
            assert url.endswith(tail)

    @pytest.mark.parametrize(('image_type', 'expected_tails'),
                             [(None, M31_URL_ALL),
                              ('100um', M31_URL_E),
                              ('ebv', M31_URL_R),
                              ('temperature', M31_URL_T),
                              ])
    def test_extract_image_urls_class(self, image_type, expected_tails):
        response = requests.get(irsa_dust.core.IrsaDust.DUST_SERVICE_URL + "?locstr=m31")
        data = response.text
        url_list = irsa_dust.core.IrsaDust.extract_image_urls(
            data, image_type=image_type)
        for url, tail in zip(url_list, expected_tails):
            assert url.endswith(tail)

    @pytest.mark.parametrize(('section', 'expected_length'),
                             [(None, 43),
                              ('100um', 10),
                              ('location', 4),
                              ('ebv', 19),
                              ('temperature', 10)
                              ])
    def test_query_table_class(self, section, expected_length):
        qtable = irsa_dust.core.IrsaDust.get_query_table(
            "m31", section=section)
        assert len(qtable.colnames) == expected_length

    @pytest.mark.parametrize(('section', 'expected_length'),
                             [(None, 43),
                              ('100um', 10),
                              ('location', 4),
                              ('ebv', 19),
                              ('temperature', 10)
                              ])
    def test_query_table_instance(self, section, expected_length):
        qtable = irsa_dust.core.IrsaDust.get_query_table(
            "m31", section=section)
        assert len(qtable.colnames) == expected_length

    def test_get_extinction_table_async_class(self):
        readable_obj = irsa_dust.core.IrsaDust.get_extinction_table_async(
            "m51")
        assert readable_obj is not None

    def test_get_extinction_table_async_instance(self):
        readable_obj = irsa_dust.core.IrsaDust().get_extinction_table_async(
            "m51")
        assert readable_obj is not None

    def test_get_extinction_table_class(self):
        table = irsa_dust.core.IrsaDust.get_extinction_table("m51")
        expected_table = Table.read(self.data(M51_EXT_TBL), format='ipac')
        assert table.meta == expected_table.meta
        assert table['LamEff'].unit == u.micron
        assert table['A_SandF'].unit == table['A_SFD'].unit == u.mag

    def test_get_extinction_table_instance(self):
        table = irsa_dust.core.IrsaDust().get_extinction_table("m51")
        expected_table = Table.read(self.data(M51_EXT_TBL), format='ipac')
        assert table.meta == expected_table.meta
        assert table['LamEff'].unit == u.micron
        assert table['A_SandF'].unit == table['A_SFD'].unit == u.mag

    @pytest.mark.parametrize(('image_type', 'expected_tails'),
                             [(None, M31_URL_ALL),
                              ('100um', M31_URL_E),
                              ('ebv', M31_URL_R),
                              ('temperature', M31_URL_T),
                              ])
    def test_get_image_list_class(self, image_type, expected_tails):
        url_list = irsa_dust.core.IrsaDust.get_image_list(
            "m31", image_type=image_type)
        for url, tail in zip(url_list, expected_tails):
            assert url.endswith(tail)

    @pytest.mark.parametrize(('image_type', 'expected_tails'),
                             [(None, M31_URL_ALL),
                              ('100um', M31_URL_E),
                              ('ebv', M31_URL_R),
                              ('temperature', M31_URL_T),
                              ])
    def test_get_image_list_instance(self, image_type, expected_tails):
        url_list = irsa_dust.core.IrsaDust().get_image_list(
            "m31", image_type=image_type)
        for url, tail in zip(url_list, expected_tails):
            assert url.endswith(tail)

    @pytest.mark.parametrize(('image_type'),
                             [(None),
                              ('100um'),
                              ('ebv'),
                              ('temperature'),
                              ])
    def test_get_images_async_class(self, image_type):
        readable_objs = irsa_dust.core.IrsaDust.get_images_async(
            "m81", image_type=image_type)

        assert readable_objs is not None

    @pytest.mark.parametrize(('image_type'),
                             [(None),
                              ('100um'),
                              ('ebv'),
                              ('temperature'),
                              ])
    def test_get_images_async_instance(self, image_type):
        readable_objs = irsa_dust.core.IrsaDust().get_images_async(
            "m81", image_type=image_type)
        assert readable_objs is not None

    def test_get_images_class(self):
        images = irsa_dust.core.IrsaDust.get_images("m81")
        assert images is not None

    def test_get_images_instance(self):
        images = irsa_dust.core.IrsaDust().get_images("m81")
        assert images is not None
