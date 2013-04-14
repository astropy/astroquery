# Licensed under a 3-clause BSD style license - see LICENSE.rst
import os
import xml.etree.ElementTree as tree
import astropy.units as u
from ... import irsadust

M31_XML = "dustm31.xml"
M81_XML = "dustm81.xml"
M101_XML = "dustm101.xml"

class DustTestCase(object):
    def data(self, filename):
        data_dir = os.path.join(os.path.dirname(__file__), 'data')
        return os.path.join(data_dir, filename)

class TestDust(DustTestCase):
    def test_parse_number(self):
        string = "1.234 (mag)"
        number = irsadust.utils.parse_number(string)
        assert number == 1.234

    def test_parse_coords(self):
        string = "2.345 -12.256 equ J2000"
        coords = irsadust.utils.parse_coords(string)
        assert coords[0] == 2.345
        assert coords[1] == -12.256
        assert coords[2] == "equ J2000"

    def test_parse_units(self):
        string = "-6.273 (mJy/sr)"
        expected_units = u.format.Generic().parse("mJy/sr")
        actual_units = irsadust.utils.parse_units(string)
        assert expected_units == actual_units

    def test_get_xml(self):
        data = self.data(M31_XML)
        xml_tree = tree.ElementTree().parse(data)
        assert xml_tree != None

    def test_get_image(self):
        url = "file:" + self.data("test.fits")
        img = irsadust.utils.image(url)
        assert img != None

    def test_get_ext_detail_table(self):
        url = "file:" + self.data("dust_ext_detail.tbl")
        table = irsadust.utils.ext_detail_table(url)
        assert table != None

    def test_find_result_node(self):
        data = self.data(M31_XML)
        xml_tree = tree.ElementTree().parse(data)

        desc = "E(B-V) Reddening"
        node = irsadust.utils.find_result_node(desc, xml_tree)
        assert node != None

    def test_dust_result_table(self):
        data = self.data(M31_XML)
        xml_tree = tree.ElementTree().parse(data)
        result = irsadust.SingleDustResult(xml_tree, "m31")
        results = irsadust.DustResults([result])
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

    def test_append_results(self):
        # Build first DustResults, length 1
        data = self.data(M31_XML)
        xml_tree = tree.ElementTree().parse(data)
        result1 = irsadust.SingleDustResult(xml_tree, "m31")
        results_a = irsadust.DustResults([result1])

        assert len(results_a.table()) == 1

        # Build second DustResults, length 2
        data = self.data(M81_XML)
        xml_tree = tree.ElementTree().parse(data)
        result2 = irsadust.SingleDustResult(xml_tree, "m81")

        data = self.data(M101_XML)
        xml_tree = tree.ElementTree().parse(data)
        result3 = irsadust.SingleDustResult(xml_tree, "m101")

        results_b = irsadust.DustResults([result2, result3])

        assert len(results_b.table()) == 2

        # Append second to first
        results_a.append(results_b)
       
        # Verify 
        assert len(results_a.table()) == 3
        assert results_a.result_set[2].query_loc == "m101"
        assert results_a.table()[2]["Dec"] == float("54.348950")

    def test_dust_result_image(self):
        data = self.data(M31_XML)
        xml_tree = tree.ElementTree().parse(data)
        self.set_ext_image_text("file:" + self.data("test.fits"), xml_tree)
        result = irsadust.SingleDustResult(xml_tree, "m31")
        results = irsadust.DustResults([result])

        image = results.image("red", row=1)
        assert image != None

    def test_dust_result_ext_detail_table(self):
        data = self.data(M31_XML)
        xml_tree = tree.ElementTree().parse(data)
        self.set_ext_table_text("file:" + self.data("dust_ext_detail.tbl"), xml_tree)
        result = irsadust.SingleDustResult(xml_tree, "m31")
        results = irsadust.DustResults([result])

        ext_detail = results.ext_detail_table(row=1)
        assert ext_detail != None

    def test_multi_row_tables(self):
        data = self.data(M31_XML)
        xml_tree = tree.ElementTree().parse(data)
        result1 = irsadust.SingleDustResult(xml_tree, "m31")

        data = self.data(M81_XML)
        xml_tree = tree.ElementTree().parse(data)
        result2 = irsadust.SingleDustResult(xml_tree, "m81")

        data = self.data(M101_XML)
        xml_tree = tree.ElementTree().parse(data)
        result3 = irsadust.SingleDustResult(xml_tree, "m101")

        results = irsadust.DustResults([result1, result2, result3])
        table = results.table()
        
        assert table != None

        table = results.table("location")
        assert table != None

        table = results.table("temp")
        assert table != None

    def test_multi_query_images(self):
        data = self.data(M31_XML)
        xml_tree = tree.ElementTree().parse(data)
        result1 = irsadust.SingleDustResult(xml_tree, "m31")

        data = self.data(M81_XML)
        xml_tree = tree.ElementTree().parse(data)
        self.set_ext_image_text("file:" + self.data("test.fits"), xml_tree)
        result2 = irsadust.SingleDustResult(xml_tree, "m81")

        results = irsadust.DustResults([result1, result2])
        image = results.image("red", 2)
        assert image != None

        # When row is out of bounds, make sure correct exception is raised 
        try:
            image = results.image("temp", 3)
        except IndexError as e:
            msg = str(e)
        assert msg != None

    def test_multi_query_detail_tables(self):
        data = self.data(M31_XML)
        xml_tree = tree.ElementTree().parse(data)
        result1 = irsadust.SingleDustResult(xml_tree, "m31")

        data = self.data(M81_XML)
        xml_tree = tree.ElementTree().parse(data)
        self.set_ext_table_text("file:" + self.data("dust_ext_detail.tbl"), xml_tree)
        result2 = irsadust.SingleDustResult(xml_tree, "m81")

        results = irsadust.DustResults([result1, result2])
        table = results.ext_detail_table(2)
        assert table != None

    def set_ext_table_text(self, text, xml_tree):
        results_node = irsadust.utils.find_result_node("E(B-V) Reddening", xml_tree)
        table_node = results_node.find("./data/table")
        table_url = text
        table_node.text = table_url

    def set_ext_image_text(self, text, xml_tree):
        results_node = irsadust.utils.find_result_node("E(B-V) Reddening", xml_tree)
        image_node = results_node.find("./data/image")
        image_url = text
        image_node.text = image_url
