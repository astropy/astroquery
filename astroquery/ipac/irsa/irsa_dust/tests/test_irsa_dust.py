# Licensed under a 3-clause BSD style license - see LICENSE.rst
import os
import types
import pytest

import astropy.units as u
from astropy.coordinates import SkyCoord
from astropy.coordinates.name_resolve import NameResolveError

from astroquery.utils import commons

from astroquery.ipac.irsa import irsa_dust
from astroquery.ipac.irsa.irsa_dust import IrsaDust, IrsaDustClass


M31_XML = "dustm31.xml"
M81_XML = "dustm81.xml"
M101_XML = "dustm101.xml"
ERR_XML = "dust-error.xml"
EXT_TBL = "dust_ext_detail.tbl"
IMG_FITS = "test.fits"
M31_URL_ALL = [
    'http://irsa.ipac.caltech.edu//workspace/TMP_kRQo9a_8160/DUST/m31.v0002/p338Dust.fits',
    'http://irsa.ipac.caltech.edu//workspace/TMP_kRQo9a_8160/DUST/m31.v0002/p338i100.fits',
    'http://irsa.ipac.caltech.edu//workspace/TMP_kRQo9a_8160/DUST/m31.v0002/p338temp.fits']


M31_URL_R = [
    'http://irsa.ipac.caltech.edu//workspace/TMP_kRQo9a_8160/DUST/m31.v0002/p338Dust.fits']


M31_URL_E = [
    'http://irsa.ipac.caltech.edu//workspace/TMP_kRQo9a_8160/DUST/m31.v0002/p338i100.fits']


M31_URL_T = [
    'http://irsa.ipac.caltech.edu//workspace/TMP_kRQo9a_8160/DUST/m31.v0002/p338temp.fits']


galcoords = {"m31": SkyCoord(ra=10.6847083 * u.deg, dec=41.26875 * u.deg, frame="icrs"),
             "m81": SkyCoord(ra=148.888221083 * u.deg, dec=69.065294722 * u.deg,
                             frame="icrs")}


def format(coord):
    C = coord.transform_to('fk5')
    return "{0} {1}".format(C.ra.deg, C.dec.deg)


@pytest.fixture
def patch_request(request):
    mp = request.getfixturevalue("monkeypatch")

    mp.setattr(irsa_dust.IrsaDustClass, '_request',
               TestDust().send_request_mockreturn)
    return mp


@pytest.fixture
def patch_fromname(request):
    mp = request.getfixturevalue("monkeypatch")

    def fromname(self, name, frame=None):
        if isinstance(name, str):
            return galcoords[name]
        else:
            raise NameResolveError
    mp.setattr(SkyCoord, "from_name", types.MethodType(fromname, SkyCoord))


class DustTestCase:

    def data(self, filename):
        data_dir = os.path.join(os.path.dirname(__file__), 'data')
        return os.path.join(data_dir, filename)

    def read_data(self, filename):
        with open(self.data(filename), "r") as f:
            return f.read()


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
        data = self.read_data(M31_XML)
        xml_tree = irsa_dust.utils.xml(data)
        assert xml_tree is not None

    def test_xml_err(self):
        data = self.read_data(ERR_XML)
        with pytest.raises(Exception):
            irsa_dust.utils.xml(data)

# TODO : Add more examples. Add for "1 degree"-like parameters
    @pytest.mark.parametrize(
        ('coordinate', 'radius', 'expected_payload'),
        ((galcoords["m81"], None, {}),
         (galcoords["m31"], "5d0m", {"regSize": 5.0}),
         (galcoords["m31"], 5 * u.deg, {"regSize": 5}),
         ("m31", 5 * u.deg, {"locstr": "m31", "regSize": 5}),
         (galcoords["m81"], 5 * u.deg, {"regSize": 5})))
    def test_args_to_payload_instance_1(self, coordinate, radius,
                                        expected_payload, patch_fromname):
        if isinstance(coordinate, str):
            expected_payload["locstr"] = coordinate
        else:
            expected_payload["locstr"] = format(coordinate)
        payload = IrsaDust()._args_to_payload(coordinate, radius=radius)
        assert payload == expected_payload

    def test_args_to_payload_instance_2(self, patch_fromname):
        with pytest.raises(Exception) as ex:
            IrsaDust()._args_to_payload("m81", radius="5")
        assert ex.value.args[0] == "No unit specified"

    @pytest.mark.parametrize(('radius'), ['1d0m', '40d0m', 45 * u.deg])
    def test_args_to_payload_instance_3(self, radius, patch_fromname):
        errmsg = ("Radius (in any unit) must be in the"
                  " range of 2.0 to 37.5 degrees")
        with pytest.raises(ValueError) as ex:
            IrsaDust()._args_to_payload("m81", radius=radius)
        assert ex.value.args[0] == errmsg

    @pytest.mark.parametrize(('coordinate', 'radius', 'expected_payload'),
                             [("m81", None,
                               dict(locstr="m81")),
                              (galcoords["m81"], None,
                               dict(locstr=format(galcoords["m81"]))),
                              (galcoords["m31"], "5d0m",
                               dict(locstr=format(galcoords['m31']),
                                    regSize=5.0)),
                              (galcoords["m31"], 5 * u.deg,
                               dict(locstr=format(galcoords['m31']),
                                    regSize=5))
                              ])
    def test_args_to_payload_class_1(self, coordinate, radius,
                                     expected_payload, patch_fromname):
        payload = IrsaDust._args_to_payload(coordinate, radius=radius)
        assert payload == expected_payload

    def test_args_to_payload_class_2(self, patch_fromname):
        with pytest.raises(Exception) as ex:
            IrsaDust._args_to_payload("m81", radius="5")
        assert ex.value.args[0] == "No unit specified"

    @pytest.mark.parametrize(('radius'), ['1d0m', '40d0m', 45 * u.deg])
    def test_args_to_payload_class_3(self, radius, patch_fromname):
        errmsg = ("Radius (in any unit) must be in the"
                  " range of 2.0 to 37.5 degrees")
        with pytest.raises(ValueError) as ex:
            IrsaDust._args_to_payload("m81", radius=radius)
        assert ex.value.args[0] == errmsg

    @pytest.mark.parametrize(('image_type', 'expected_urls'),
                             [(None, M31_URL_ALL),
                              ('100um', M31_URL_E),
                              ('ebv', M31_URL_R),
                              ('temperature', M31_URL_T),
                              ])
    def test_extract_image_urls_instance(self, image_type, expected_urls):
        raw_xml = self.read_data(M31_XML)
        url_list = IrsaDust().extract_image_urls(
            raw_xml, image_type=image_type)
        assert url_list == expected_urls

    def test_extract_image_urls_instance__err(self):
        raw_xml = self.read_data(M31_XML)
        with pytest.raises(ValueError):
            IrsaDust().extract_image_urls(
                raw_xml, image_type="l")

    @pytest.mark.parametrize(('image_type', 'expected_urls'),
                             [(None, M31_URL_ALL),
                              ('100um', M31_URL_E),
                              ('ebv', M31_URL_R),
                              ('temperature', M31_URL_T),
                              ])
    def test_extract_image_urls_class(self, image_type, expected_urls):
        raw_xml = self.read_data(M31_XML)
        url_list = IrsaDust.extract_image_urls(
            raw_xml, image_type=image_type)
        assert url_list == expected_urls

    def test_extract_image_urls_class__err(self):
        raw_xml = self.read_data(M31_XML)
        with pytest.raises(ValueError):
            IrsaDust.extract_image_urls(raw_xml, image_type="l")

    @pytest.mark.parametrize(('section', 'expected_length'),
                             [(None, 43),
                              ('100um', 10),
                              ('location', 4),
                              ('ebv', 19),
                              ('temperature', 10)
                              ])
    def test_query_table_class(self, patch_request, section, expected_length,
                               patch_fromname):
        qtable = IrsaDust.get_query_table("m31",
                                          section=section)
        assert len(qtable.colnames) == expected_length

    @pytest.mark.parametrize(('section', 'expected_length'),
                             [(None, 43),
                              ('100um', 10),
                              ('location', 4),
                              ('ebv', 19),
                              ('temperature', 10)
                              ])
    def test_query_table_instance(self, patch_request, section,
                                  expected_length, patch_fromname):
        qtable = IrsaDust.get_query_table("m31",
                                          section=section)
        assert len(qtable.colnames) == expected_length

    def test_get_extinction_table_async_class(self, patch_request,
                                              patch_fromname):
        readable_obj = IrsaDust.get_extinction_table_async("m31")
        assert readable_obj is not None

    def test_get_extinction_table_async_instance(self, patch_request,
                                                 patch_fromname):
        readable_obj = IrsaDust().get_extinction_table_async(
            "m31")
        assert readable_obj is not None

    def test_get_extinction_table_class(self, monkeypatch):
        monkeypatch.setattr(
            IrsaDust, 'get_extinction_table_async',
            self.get_ext_table_async_mockreturn)
        table = IrsaDust.get_extinction_table("m31")
        assert table is not None

    def test_get_extinction_table_instance(self, monkeypatch):
        monkeypatch.setattr(IrsaDustClass, 'get_extinction_table_async',
                            self.get_ext_table_async_mockreturn)
        table = IrsaDust().get_extinction_table("m31")
        assert table is not None

    @pytest.mark.parametrize(('image_type', 'expected_urls'),
                             [(None, M31_URL_ALL),
                              ('100um', M31_URL_E),
                              ('ebv', M31_URL_R),
                              ('temperature', M31_URL_T),
                              ])
    def test_get_image_list_class(self, patch_request, image_type,
                                  expected_urls, patch_fromname):
        url_list = IrsaDust.get_image_list(
            "m81", image_type=image_type)
        assert url_list == expected_urls

    @pytest.mark.parametrize(('image_type', 'expected_urls'),
                             [(None, M31_URL_ALL),
                              ('100um', M31_URL_E),
                              ('ebv', M31_URL_R),
                              ('temperature', M31_URL_T),
                              ])
    def test_get_image_list_instance(self, patch_request, image_type,
                                     expected_urls, patch_fromname):
        url_list = IrsaDust().get_image_list("m81", image_type=image_type)
        assert url_list == expected_urls

    @pytest.mark.parametrize(('image_type'),
                             [(None),
                              ('100um'),
                              ('ebv'),
                              ('temperature'),
                              ])
    def test_get_images_async_class(self, monkeypatch, image_type):
        monkeypatch.setattr(IrsaDust, 'get_image_list',
                            self.get_image_list_mockreturn)
        readable_objs = IrsaDust.get_images_async("m81", image_type=image_type)
        assert readable_objs is not None

    @pytest.mark.parametrize(('image_type'),
                             [(None),
                              ('100um'),
                              ('ebv'),
                              ('temperature'),
                              ])
    def test_get_images_async_instance(self, monkeypatch, image_type):
        monkeypatch.setattr(IrsaDustClass, 'get_image_list',
                            self.get_image_list_mockreturn)
        readable_objs = IrsaDust().get_images_async("m81",
                                                    image_type=image_type)
        assert readable_objs is not None

    def test_get_images_class(self, monkeypatch):
        monkeypatch.setattr(IrsaDust, 'get_images_async',
                            self.get_images_async_mockreturn)
        images = IrsaDust.get_images("m81")
        assert images is not None

    def test_get_images_instance(self, monkeypatch):
        monkeypatch.setattr(IrsaDustClass, 'get_images_async',
                            self.get_images_async_mockreturn)
        images = IrsaDust().get_images("m81")
        assert images is not None

    def test_list_image_types_class(self):
        types = IrsaDust.list_image_types()
        assert types is not None

    def test_list_image_types_instance(self):
        types = IrsaDust().list_image_types()
        assert types is not None

    def send_request_mockreturn(self, method, url, data, timeout):
        class MockResponse:
            text = self.read_data(M31_XML)
        return MockResponse

    def get_ext_table_async_mockreturn(self, coordinate, radius=None,
                                       timeout=IrsaDust.TIMEOUT,
                                       show_progress=True):
        return commons.FileContainer(self.data(EXT_TBL), show_progress=show_progress)

    def get_image_list_mockreturn(
        self, coordinate, radius=None, image_type=None,
            timeout=IrsaDust.TIMEOUT):
        return [self.data(IMG_FITS)]

    def get_images_async_mockreturn(self, coordinate, radius=None,
                                    image_type=None, timeout=IrsaDust.TIMEOUT,
                                    get_query_payload=False,
                                    show_progress=True):
        readable_obj = commons.FileContainer(self.data(IMG_FITS),
                                             encoding='binary',
                                             show_progress=show_progress)
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


def test_deprecated_namespace_import_warning():
    with pytest.warns(DeprecationWarning):
        import astroquery.irsa_dust  # noqa: F401
