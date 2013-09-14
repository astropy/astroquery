# Licensed under a 3-clause BSD style license - see LICENSE.rst
import os
import xml.etree.ElementTree as tree

import astropy.units as u
import astropy.utils.data as aud
from astropy.tests.helper import pytest  # import this since the user may not have pytest installed

from ... import irsa_dust
from ...utils import commons

M31_XML = "dustm31.xml"
M81_XML = "dustm81.xml"
M101_XML = "dustm101.xml"
ERR_XML = "dust-error.xml"
EXT_TBL = "dust_ext_detail.tbl"
IMG_FITS = "test.fits"
M31_URL_ALL = [
    'http://irsa.ipac.caltech.edu//workspace/TMP_0fVHXe_17371/DUST/m31.v0001/p338Dust.fits',
    'http://irsa.ipac.caltech.edu//workspace/TMP_0fVHXe_17371/DUST/m31.v0001/p338i100.fits',
    'http://irsa.ipac.caltech.edu//workspace/TMP_0fVHXe_17371/DUST/m31.v0001/p338temp.fits'
]

M31_URL_E = [
    'http://irsa.ipac.caltech.edu//workspace/TMP_0fVHXe_17371/DUST/m31.v0001/p338i100.fits'
]

M31_URL_R = [
    'http://irsa.ipac.caltech.edu//workspace/TMP_0fVHXe_17371/DUST/m31.v0001/p338Dust.fits'
]

M31_URL_T = [
    'http://irsa.ipac.caltech.edu//workspace/TMP_0fVHXe_17371/DUST/m31.v0001/p338temp.fits'
]


@pytest.fixture
def patch_request(request):
    mp = request.getfuncargvalue("monkeypatch")
    mp.setattr(
        commons,
        'send_request',
        TestDust(
        ).send_request_mockreturn)
    return mp


class DustTestCase(object):

    def data(self, filename):
        data_dir = os.path.join(os.path.dirname(__file__), 'data')
        return os.path.join(data_dir, filename)


class TestDust(DustTestCase):

    def test_parse_number(self):
        string = "1.234 (mag)"
        number = irsa_dust.utils.parse_number(string)
        assert number == 1.234

    def test_parse_coords(self):
        string = "2.345 -12.256 equ J2000"
        coords = irsa_dust.utils.parse_coords(string)
        assert coords[0] == 2.345
        assert coords[1] == -12.256
        assert coords[2] == "equ J2000"

    def test_parse_units(self):
        string = "-6.273 (mJy/sr)"
        expected_units = u.format.Generic().parse("mJy/sr")
        actual_units = irsa_dust.utils.parse_units(string)
        assert expected_units == actual_units

    def test_xml_ok(self):
        data = open(self.data(M31_XML), "r").read()
        xml_tree = irsa_dust.utils.xml(data)
        assert xml_tree is not None

    def test_xml_err(self):
        data = open(self.data(ERR_XML), "r").read()
        with pytest.raises(Exception) as ex:
            xml_tree = irsa_dust.utils.xml(data)

# TODO : Add more examples. Add for "1 degree"-like parameters
    @pytest.mark.parametrize(('coordinate', 'radius', 'expected_payload'),
                             [("m81", None, dict(locstr="m81")),
                              ("m31", "5d0m", dict(locstr="m31", regSize=5.0)),
                              ("m31", 5*u.deg, dict(locstr="m31", regSize=5))
                              ])
    def test_args_to_payload_instance_1(
            self, coordinate, radius, expected_payload):
        payload = irsa_dust.core.IrsaDust()._args_to_payload(
            coordinate, radius=radius)
        assert payload == expected_payload

    def test_args_to_payload_instance_2(self):
        with pytest.raises(Exception) as ex:
            payload = irsa_dust.core.IrsaDust()._args_to_payload(
                "m81", radius="5")
        assert ex.value.args[0] == "Radius not specified with proper unit."

    @pytest.mark.parametrize(('radius'), ['1d0m', '40d0m', 45*u.deg])
    def test_args_to_payload_instance_3(self, radius):
        errmsg = ("Radius (in any unit) must be in the"
                  " range of 2.0 to 37.5 degrees")
        with pytest.raises(ValueError) as ex:
            payload = irsa_dust.core.IrsaDust()._args_to_payload(
                "m81", radius=radius)
        assert ex.value.args[0] == errmsg

    @pytest.mark.parametrize(('coordinate', 'radius', 'expected_payload'),
                             [("m81", None, dict(locstr="m81")),
                              ("m31", "5d0m", dict(locstr="m31", regSize=5.0)),
                              ("m31", 5*u.deg, dict(locstr="m31", regSize=5))
                              ])
    def test_args_to_payload_class_1(
            self, coordinate, radius, expected_payload):
        payload = irsa_dust.core.IrsaDust._args_to_payload(
            coordinate, radius=radius)
        assert payload == expected_payload

    def test_args_to_payload_class_2(self):
        with pytest.raises(Exception) as ex:
            payload = irsa_dust.core.IrsaDust._args_to_payload(
                "m81", radius="5")
        assert ex.value.args[0] == "Radius not specified with proper unit."

    @pytest.mark.parametrize(('radius'), ['1d0m', '40d0m', 45*u.deg])
    def test_args_to_payload_class_3(self, radius):
        errmsg = ("Radius (in any unit) must be in the"
                  " range of 2.0 to 37.5 degrees")
        with pytest.raises(ValueError) as ex:
            payload = irsa_dust.core.IrsaDust._args_to_payload(
                "m81", radius=radius)
        assert ex.value.args[0] == errmsg

    @pytest.mark.parametrize(('image_type', 'expected_urls'),
                             [(None, M31_URL_ALL),
                              ('100um', M31_URL_E),
                              ('ebv', M31_URL_R),
                              ('extinction', M31_URL_T),
                              ])
    def test_extract_image_urls_instance(self, image_type, expected_urls):
        raw_xml = open(self.data(M31_XML), "r").read()
        url_list = irsa_dust.core.IrsaDust().extract_image_urls(
            raw_xml, image_type=image_type)
        assert url_list == expected_urls

    def test_extract_image_urls_instance__err(self):
        raw_xml = open(self.data(M31_XML), "r").read()
        with pytest.raises(ValueError):
            irsa_dust.core.IrsaDust().extract_image_urls(
                raw_xml, image_type="l")

    @pytest.mark.parametrize(('image_type', 'expected_urls'),
                             [(None, M31_URL_ALL),
                              ('100um', M31_URL_E),
                              ('ebv', M31_URL_R),
                              ('extinction', M31_URL_T),
                              ])
    def test_extract_image_urls_class(self, image_type, expected_urls):
        raw_xml = open(self.data(M31_XML), "r").read()
        url_list = irsa_dust.core.IrsaDust.extract_image_urls(
            raw_xml, image_type=image_type)
        assert url_list == expected_urls

    def test_extract_image_urls_class__err(self):
        raw_xml = open(self.data(M31_XML), "r").read()
        with pytest.raises(ValueError):
            irsa_dust.core.IrsaDust.extract_image_urls(raw_xml, image_type="l")

    @pytest.mark.parametrize(('section', 'expected_length'),
                             [(None, 35),
                              ('100um', 10),
                              ('location', 4),
                              ('ebv', 11),
                              ('extinction', 10)
                              ])
    def test_query_table_class(self, patch_request, section, expected_length):
        qtable = irsa_dust.core.IrsaDust.get_query_table(
            "m31", section=section)
        assert len(qtable.colnames) == expected_length

    @pytest.mark.parametrize(('section', 'expected_length'),
                             [(None, 35),
                              ('100um', 10),
                              ('location', 4),
                              ('ebv', 11),
                              ('extinction', 10)
                              ])
    def test_query_table_instance(
            self, patch_request, section, expected_length):
        qtable = irsa_dust.core.IrsaDust.get_query_table(
            "m31", section=section)
        assert len(qtable.colnames) == expected_length

    def test_get_extinction_table_async_class(self, patch_request):
        readable_obj = irsa_dust.core.IrsaDust.get_extinction_table_async(
            "m31")
        assert readable_obj is not None

    def test_get_extinction_table_async_instance(self, patch_request):
        readable_obj = irsa_dust.core.IrsaDust().get_extinction_table_async(
            "m31")
        assert readable_obj is not None

    def test_get_extinction_table_class(self, monkeypatch):
        monkeypatch.setattr(
            irsa_dust.core.IrsaDust, 'get_extinction_table_async',
            self.get_ext_table_async_mockreturn)
        table = irsa_dust.core.IrsaDust.get_extinction_table("m31")
        assert table is not None

    def test_get_extinction_table_instance(self, monkeypatch):
        monkeypatch.setattr(
            irsa_dust.core.IrsaDust, 'get_extinction_table_async',
            self.get_ext_table_async_mockreturn)
        table = irsa_dust.core.IrsaDust().get_extinction_table("m31")
        assert table is not None

    @pytest.mark.parametrize(('image_type', 'expected_urls'),
                             [(None, M31_URL_ALL),
                              ('100um', M31_URL_E),
                              ('ebv', M31_URL_R),
                              ('extinction', M31_URL_T),
                              ])
    def test_get_image_list_class(
            self, patch_request, image_type, expected_urls):
        url_list = irsa_dust.core.IrsaDust.get_image_list(
            "m81", image_type=image_type)
        assert url_list == expected_urls

    @pytest.mark.parametrize(('image_type', 'expected_urls'),
                             [(None, M31_URL_ALL),
                              ('100um', M31_URL_E),
                              ('ebv', M31_URL_R),
                              ('extinction', M31_URL_T),
                              ])
    def test_get_image_list_instance(
            self, patch_request, image_type, expected_urls):
        url_list = irsa_dust.core.IrsaDust().get_image_list(
            "m81", image_type=image_type)
        assert url_list == expected_urls

    @pytest.mark.parametrize(('image_type'),
                             [(None),
                              ('100um'),
                              ('ebv'),
                              ('extinction'),
                              ])
    def test_get_images_async_class(self, monkeypatch, image_type):
        monkeypatch.setattr(irsa_dust.core.IrsaDust, 'get_image_list',
                            self.get_image_list_mockreturn)
        readable_objs = irsa_dust.core.IrsaDust.get_images_async("m81",
                                                                 image_type=image_type)
        assert readable_objs is not None

    @pytest.mark.parametrize(('image_type'),
                             [(None),
                              ('100um'),
                              ('ebv'),
                              ('extinction'),
                              ])
    def test_get_images_async_instance(self, monkeypatch, image_type):
        monkeypatch.setattr(irsa_dust.core.IrsaDust, 'get_image_list',
                            self.get_image_list_mockreturn)
        readable_objs = irsa_dust.core.IrsaDust().get_images_async("m81",
                                                                   image_type=image_type)
        assert readable_objs is not None

    def test_get_images_class(self, monkeypatch):
        monkeypatch.setattr(irsa_dust.core.IrsaDust, 'get_images_async',
                            self.get_images_async_mockreturn)
        images = irsa_dust.core.IrsaDust.get_images("m81")
        assert images is not None

    def test_get_images_instance(self, monkeypatch):
        monkeypatch.setattr(irsa_dust.core.IrsaDust, 'get_images_async',
                            self.get_images_async_mockreturn)
        images = irsa_dust.core.IrsaDust().get_images("m81")
        assert images is not None

    def test_list_image_types_class(self):
        types = irsa_dust.core.IrsaDust.list_image_types()
        assert types is not None

    def test_list_image_types_instance(self):
        types = irsa_dust.core.IrsaDust().list_image_types()
        assert types is not None

    def send_request_mockreturn(self, url, data, timeout):
        class MockResponse:
            text = open(self.data(M31_XML), "r").read()
        return MockResponse

    def get_ext_table_async_mockreturn(self, coordinate, radius=None,
                                       timeout=irsa_dust.core.IrsaDust.TIMEOUT):
        return(aud.get_readable_fileobj(self.data(EXT_TBL)))

    def get_image_list_mockreturn(
        self, coordinate, radius=None, image_type=None,
            timeout=irsa_dust.core.IrsaDust.TIMEOUT):
        return [self.data(IMG_FITS)]

    def get_images_async_mockreturn(
        self, coordinate, radius=None, image_type=None,
        timeout=irsa_dust.core.IrsaDust.TIMEOUT,
            get_query_payload=False):
        readable_obj = aud.get_readable_fileobj(self.data(IMG_FITS))
        return [readable_obj]

    def set_ext_table_text(self, text, xml_tree):
        results_node = irsa_dust.utils.find_result_node(
            "E(B-V) Reddening", xml_tree)
        table_node = results_node.find("./data/table")
        table_url = text
        table_node.text = table_url

    def set_ext_image_text(self, text, xml_tree):
        results_node = irsa_dust.utils.find_result_node(
            "E(B-V) Reddening", xml_tree)
        image_node = results_node.find("./data/image")
        image_url = text
        image_node.text = image_url

