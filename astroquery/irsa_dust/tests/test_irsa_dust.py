# Licensed under a 3-clause BSD style license - see LICENSE.rst
import os
import xml.etree.ElementTree as tree
import astropy.units as u
import astropy.utils.data as aud
from astropy.tests.helper import pytest # import this since the user may not have pytest installed
from ... import irsa_dust

M31_XML = "dustm31.xml"
M81_XML = "dustm81.xml"
M101_XML = "dustm101.xml"
ERR_XML = "dust-error.xml"
EXT_TBL = "dust_ext_detail.tbl"
 
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
        assert xml_tree != None

    def test_xml_err(self):
        data = open(self.data(ERR_XML), "r").read()
        with pytest.raises(Exception) as ex:
            xml_tree = irsa_dust.utils.xml(data)
        
    def test_args_to_payload_instance_1(self):
        payload = irsa_dust.core.IrsaDust().args_to_payload("m81")
        assert payload == dict(locstr="m81") 
    
    def test_args_to_payload_instance_2(self):
        payload = irsa_dust.core.IrsaDust().args_to_payload("m81", radius = "5 degree")
        assert payload == dict(locstr="m81", regSize=5.0)
        with pytest.raises(Exception) as ex:
            payload = irsa_dust.core.IrsaDust().args_to_payload("m81", radius = "5")
        assert ex.value.args[0] == "Radius not specified with proper unit."
        
    def test_args_to_payload_instance_3(self):
        errmsg = ("Radius (in any unit) must be in the"
                  " range of 2.0 to 37.5 degrees")
        with pytest.raises(ValueError) as ex:
            payload = irsa_dust.core.IrsaDust().args_to_payload("m81", radius = "1 degree")
        assert ex.value.args[0] == errmsg
        with pytest.raises(ValueError) as ex:
            payload = irsa_dust.core.IrsaDust().args_to_payload("m81", radius = "40 degree")
        assert ex.value.args[0] == errmsg
        
    def test_args_to_payload_class_1(self):
        payload = irsa_dust.core.IrsaDust.args_to_payload("m81")
        assert payload == dict(locstr="m81") 
        
    def test_args_to_payload_class_2(self):
        payload = irsa_dust.core.IrsaDust.args_to_payload("m81", radius = "5 degree")
        assert payload == dict(locstr="m81", regSize=5.0)
        with pytest.raises(Exception) as ex:
            payload = irsa_dust.core.IrsaDust.args_to_payload("m81", radius = "5")
        assert ex.value.args[0] == "Radius not specified with proper unit."
        
    def test_args_to_payload_class_3(self):
        errmsg = ("Radius (in any unit) must be in the"
                  " range of 2.0 to 37.5 degrees")
        with pytest.raises(ValueError) as ex:
            payload = irsa_dust.core.IrsaDust.args_to_payload("m81", radius = "1 degree")
        assert ex.value.args[0] == errmsg
        with pytest.raises(ValueError) as ex:
            payload = irsa_dust.core.IrsaDust.args_to_payload("m81", radius = "40 degree")
        assert ex.value.args[0] == errmsg
    
    def test_extract_image_urls_instance_all(self):
        raw_xml = open(self.data(M31_XML), "r").read()
        url_list = irsa_dust.core.IrsaDust().extract_image_urls(raw_xml)
        assert url_list == [
        'http://irsa.ipac.caltech.edu//workspace/TMP_0fVHXe_17371/DUST/m31.v0001/p338Dust.fits',
        'http://irsa.ipac.caltech.edu//workspace/TMP_0fVHXe_17371/DUST/m31.v0001/p338i100.fits',
        'http://irsa.ipac.caltech.edu//workspace/TMP_0fVHXe_17371/DUST/m31.v0001/p338temp.fits'
        ]
        
    def test_extract_image_urls_instance_e(self):
        raw_xml = open(self.data(M31_XML), "r").read()
        for val in ['e', 'em', 'emission']:
            url_list = irsa_dust.core.IrsaDust().extract_image_urls(raw_xml, section=val)
            assert url_list == [
            'http://irsa.ipac.caltech.edu//workspace/TMP_0fVHXe_17371/DUST/m31.v0001/p338i100.fits'
            ]
    
    def test_extract_image_urls_instance_r(self):
        raw_xml = open(self.data(M31_XML), "r").read()
        for val in ['r', 'red', 'reddening']:
            url_list = irsa_dust.core.IrsaDust().extract_image_urls(raw_xml, section=val)
            assert url_list == [
            'http://irsa.ipac.caltech.edu//workspace/TMP_0fVHXe_17371/DUST/m31.v0001/p338Dust.fits'
            ]
    
    def test_extract_image_urls_instance_t(self):
        raw_xml = open(self.data(M31_XML), "r").read()
        for val in ['t', 'temp', 'temperature']:
            url_list = irsa_dust.core.IrsaDust().extract_image_urls(raw_xml, section=val)
            assert url_list == [
            'http://irsa.ipac.caltech.edu//workspace/TMP_0fVHXe_17371/DUST/m31.v0001/p338temp.fits'
            ]
    
    def test_extract_image_urls_instance__err(self):
        raw_xml = open(self.data(M31_XML), "r").read()
        with pytest.raises(ValueError):
            irsa_dust.core.IrsaDust().extract_image_urls(raw_xml, section="l")
            
    def test_extract_image_urls_class_all(self):
        raw_xml = open(self.data(M31_XML), "r").read()
        url_list = irsa_dust.core.IrsaDust.extract_image_urls(raw_xml)
        assert url_list == [
        'http://irsa.ipac.caltech.edu//workspace/TMP_0fVHXe_17371/DUST/m31.v0001/p338Dust.fits',
        'http://irsa.ipac.caltech.edu//workspace/TMP_0fVHXe_17371/DUST/m31.v0001/p338i100.fits',
        'http://irsa.ipac.caltech.edu//workspace/TMP_0fVHXe_17371/DUST/m31.v0001/p338temp.fits'
        ]
        
    def test_extract_image_urls_class_e(self):
        raw_xml = open(self.data(M31_XML), "r").read()
        for val in ['e', 'em', 'emission']:
            url_list = irsa_dust.core.IrsaDust.extract_image_urls(raw_xml, section=val)
            assert url_list == [
            'http://irsa.ipac.caltech.edu//workspace/TMP_0fVHXe_17371/DUST/m31.v0001/p338i100.fits'
            ]
    
    def test_extract_image_urls_class_r(self):
        raw_xml = open(self.data(M31_XML), "r").read()
        for val in ['r', 'red', 'reddening']:
            url_list = irsa_dust.core.IrsaDust.extract_image_urls(raw_xml, section=val)
            assert url_list == [
            'http://irsa.ipac.caltech.edu//workspace/TMP_0fVHXe_17371/DUST/m31.v0001/p338Dust.fits'
            ]
    
    def test_extract_image_urls_class_t(self):
        raw_xml = open(self.data(M31_XML), "r").read()
        for val in ['t', 'temp', 'temperature']:
            url_list = irsa_dust.core.IrsaDust.extract_image_urls(raw_xml, section=val)
            assert url_list == [
            'http://irsa.ipac.caltech.edu//workspace/TMP_0fVHXe_17371/DUST/m31.v0001/p338temp.fits'
            ]
    
    def test_extract_image_urls_class__err(self):
        raw_xml = open(self.data(M31_XML), "r").read()
        with pytest.raises(ValueError):
            irsa_dust.core.IrsaDust.extract_image_urls(raw_xml, section="l")

# tests using monkeypatching. TODO: Find how to apply a common patch to a group of functions    
    def test_query_table_class_all(self, monkeypatch):
        def mockreturn(url, data, timeout):
            class MockResponse:
                    text = open(self.data(M31_XML), "r").read()
            return MockResponse
        monkeypatch.setattr(irsa_dust.core, 'send_request', mockreturn)
        qtable = irsa_dust.core.IrsaDust.get_query_table("m31")
        assert len(qtable.colnames) == 35
        qtable = irsa_dust.core.IrsaDust.get_query_table("m31", section="all")
        assert len(qtable.colnames) == 35
               
    def test_query_table_class_e(self, monkeypatch):
        def mockreturn(url, data, timeout):
            class MockResponse:
                    text = open(self.data(M31_XML), "r").read()
            return MockResponse
        monkeypatch.setattr(irsa_dust.core, 'send_request', mockreturn)
        qtable = irsa_dust.core.IrsaDust.get_query_table("m31", section = "e")
        assert len(qtable.colnames) == 10
    
    def test_query_table_class_l(self, monkeypatch):
        def mockreturn(url, data, timeout):
            class MockResponse:
                    text = open(self.data(M31_XML), "r").read()
            return MockResponse
        monkeypatch.setattr(irsa_dust.core, 'send_request', mockreturn)
        qtable = irsa_dust.core.IrsaDust.get_query_table("m31", section = "l")
        assert len(qtable.colnames) == 4
    
    def test_query_table_class_r(self, monkeypatch):
        def mockreturn(url, data, timeout):
            class MockResponse:
                    text = open(self.data(M31_XML), "r").read()
            return MockResponse
        monkeypatch.setattr(irsa_dust.core, 'send_request', mockreturn)
        qtable = irsa_dust.core.IrsaDust.get_query_table("m31", section = "r")
        assert len(qtable.colnames) == 11
    
    def test_query_table_class_t(self, monkeypatch):
        def mockreturn(url, data, timeout):
            class MockResponse:
                    text = open(self.data(M31_XML), "r").read()
            return MockResponse
        monkeypatch.setattr(irsa_dust.core, 'send_request', mockreturn)
        qtable = irsa_dust.core.IrsaDust.get_query_table("m31", section = "t")
        assert len(qtable.colnames) == 10

    def test_query_table_instance_all(self, monkeypatch):
        def mockreturn(url, data, timeout):
            class MockResponse:
                    text = open(self.data(M31_XML), "r").read()
            return MockResponse
        monkeypatch.setattr(irsa_dust.core, 'send_request', mockreturn)
        qtable = irsa_dust.core.IrsaDust().get_query_table("m31")
        assert len(qtable.colnames) == 35
        qtable = irsa_dust.core.IrsaDust().get_query_table("m31", section="all")
        assert len(qtable.colnames) == 35
               
    def test_query_table_instance_e(self, monkeypatch):
        def mockreturn(url, data, timeout):
            class MockResponse:
                    text = open(self.data(M31_XML), "r").read()
            return MockResponse
        monkeypatch.setattr(irsa_dust.core, 'send_request', mockreturn)
        qtable = irsa_dust.core.IrsaDust().get_query_table("m31", section = "e")
        assert len(qtable.colnames) == 10
    
    def test_query_table_instance_l(self, monkeypatch):
        def mockreturn(url, data, timeout):
            class MockResponse:
                    text = open(self.data(M31_XML), "r").read()
            return MockResponse
        monkeypatch.setattr(irsa_dust.core, 'send_request', mockreturn)
        qtable = irsa_dust.core.IrsaDust().get_query_table("m31", section = "l")
        assert len(qtable.colnames) == 4
    
    def test_query_table_instance_r(self, monkeypatch):
        def mockreturn(url, data, timeout):
            class MockResponse:
                    text = open(self.data(M31_XML), "r").read()
            return MockResponse
        monkeypatch.setattr(irsa_dust.core, 'send_request', mockreturn)
        qtable = irsa_dust.core.IrsaDust().get_query_table("m31", section = "r")
        assert len(qtable.colnames) == 11
    
    def test_query_table_instance_t(self, monkeypatch):
        def mockreturn(url, data, timeout):
            class MockResponse:
                    text = open(self.data(M31_XML), "r").read()
            return MockResponse
        monkeypatch.setattr(irsa_dust.core, 'send_request', mockreturn)
        qtable = irsa_dust.core.IrsaDust().get_query_table("m31", section = "t")
        assert len(qtable.colnames) == 10
    
    def test_get_extinction_table_async_class(self, monkeypatch):
        def mockreturn(url, data, timeout):
            class MockResponse:
                    text = open(self.data(M31_XML), "r").read()
            return MockResponse
        monkeypatch.setattr(irsa_dust.core, 'send_request', mockreturn)
        readable_obj = irsa_dust.core.IrsaDust.get_extinction_table_async("m31")
        assert readable_obj != None

    def test_get_extinction_table_async_instance(self, monkeypatch):
        def mockreturn(url, data, timeout):
            class MockResponse:
                    text = open(self.data(M31_XML), "r").read()
            return MockResponse
        monkeypatch.setattr(irsa_dust.core, 'send_request', mockreturn)
        readable_obj = irsa_dust.core.IrsaDust().get_extinction_table_async("m31")
        assert readable_obj != None
    
    
    """
    def test_get_xml(self): #what does it test?
        data = self.data(M31_XML)
        xml_tree = tree.ElementTree().parse(data)
        assert xml_tree != None

    def test_get_image(self):   #remove
        url = "file:" + self.data("test.fits")
        img = irsa_dust.utils.image(url)
        assert img != None

    def test_get_ext_detail_table(self): #remove
        url = "file:" + self.data("dust_ext_detail.tbl")
        table = irsa_dust.utils.ext_detail_table(url)
        assert table != None

    def test_find_result_node(self):
        data = self.data(M31_XML)
        xml_tree = tree.ElementTree().parse(data)

        desc = "E(B-V) Reddening"
        node = irsa_dust.utils.find_result_node(desc, xml_tree)
        assert node != None

    def test_dust_result_table(self): #remove
        data = self.data(M31_XML)
        xml_tree = tree.ElementTree().parse(data)
        result = irsa_dust.SingleDustResult(xml_tree, "m31")
        results = irsa_dust.DustResults([result])
        table = results.table()
        assert table != None

        table = results.table("loc")
        assert table != None

        table = results.table("reddening")
        assert table != None

        table = results.table("e")
        assert table != None

        table = results.table("temp")
        assert table != None

    def test_append_results(self):#remove
        # Build first DustResults, length 1
        data = self.data(M31_XML)
        xml_tree = tree.ElementTree().parse(data)
        result1 = irsa_dust.SingleDustResult(xml_tree, "m31")
        results_a = irsa_dust.DustResults([result1])

        assert len(results_a.table()) == 1

        # Build second DustResults, length 2
        data = self.data(M81_XML)
        xml_tree = tree.ElementTree().parse(data)
        result2 = irsa_dust.SingleDustResult(xml_tree, "m81")

        data = self.data(M101_XML)
        xml_tree = tree.ElementTree().parse(data)
        result3 = irsa_dust.SingleDustResult(xml_tree, "m101")

        results_b = irsa_dust.DustResults([result2, result3])

        assert len(results_b.table()) == 2

        # Append second to first
        results_a.append(results_b)
       
        # Verify 
        assert len(results_a.table()) == 3
        assert results_a.result_set[2].query_loc == "m101"
        assert results_a.table()[2]["Dec"] == float("54.348950")

    def test_dust_result_image(self):#remove
        data = self.data(M31_XML)
        xml_tree = tree.ElementTree().parse(data)
        self.set_ext_image_text("file:" + self.data("test.fits"), xml_tree)
        result = irsa_dust.SingleDustResult(xml_tree, "m31")
        results = irsa_dust.DustResults([result])

        image = results.image("red", row=1)
        assert image != None

    def test_dust_result_ext_detail_table(self):#remove
        data = self.data(M31_XML)
        xml_tree = tree.ElementTree().parse(data)
        self.set_ext_table_text("file:" + self.data("dust_ext_detail.tbl"), xml_tree)
        result = irsa_dust.SingleDustResult(xml_tree, "m31")
        results = irsa_dust.DustResults([result])

        ext_detail = results.ext_detail_table(row=1)
        assert ext_detail != None

    def test_multi_row_tables(self):#remove
        data = self.data(M31_XML)
        xml_tree = tree.ElementTree().parse(data)
        result1 = irsa_dust.SingleDustResult(xml_tree, "m31")

        data = self.data(M81_XML)
        xml_tree = tree.ElementTree().parse(data)
        result2 = irsa_dust.SingleDustResult(xml_tree, "m81")

        data = self.data(M101_XML)
        xml_tree = tree.ElementTree().parse(data)
        result3 = irsa_dust.SingleDustResult(xml_tree, "m101")

        results = irsa_dust.DustResults([result1, result2, result3])
        table = results.table()
        
        assert table != None

        table = results.table("location")
        assert table != None

        table = results.table("temp")
        assert table != None

    def test_multi_query_images(self):#remove
        data = self.data(M31_XML)
        xml_tree = tree.ElementTree().parse(data)
        result1 = irsa_dust.SingleDustResult(xml_tree, "m31")

        data = self.data(M81_XML)
        xml_tree = tree.ElementTree().parse(data)
        self.set_ext_image_text("file:" + self.data("test.fits"), xml_tree)
        result2 = irsa_dust.SingleDustResult(xml_tree, "m81")

        results = irsa_dust.DustResults([result1, result2])
        image = results.image("red", 2)
        assert image != None

        # When row is out of bounds, make sure correct exception is raised 
        try:
            image = results.image("temp", 3)
        except IndexError as e:
            msg = str(e)
        assert msg != None

    def test_multi_query_detail_tables(self):#remove
        data = self.data(M31_XML)
        xml_tree = tree.ElementTree().parse(data)
        result1 = irsa_dust.SingleDustResult(xml_tree, "m31")

        data = self.data(M81_XML)
        xml_tree = tree.ElementTree().parse(data)
        self.set_ext_table_text("file:" + self.data("dust_ext_detail.tbl"), xml_tree)
        result2 = irsa_dust.SingleDustResult(xml_tree, "m81")

        results = irsa_dust.DustResults([result1, result2])
        table = results.ext_detail_table(2)
        assert table != None
"""
    def set_ext_table_text(self, text, xml_tree):
        results_node = irsa_dust.utils.find_result_node("E(B-V) Reddening", xml_tree)
        table_node = results_node.find("./data/table")
        table_url = text
        table_node.text = table_url

    def set_ext_image_text(self, text, xml_tree):
        results_node = irsa_dust.utils.find_result_node("E(B-V) Reddening", xml_tree)
        image_node = results_node.find("./data/image")
        image_url = text
        image_node.text = image_url
