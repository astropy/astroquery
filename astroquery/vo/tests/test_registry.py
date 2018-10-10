import sys
import pytest
from ...utils.testing_tools import MockResponse

from ... import vo
from astroquery.vo import Registry
from ..utils import sval, astropy_table_from_votable_string
from .shared_registry import SharedRegistryTests

## To run just this test,
##
## ( cd ../../ ; python setup.py test -t astroquery/vo/tests/test_registry.py )
##


@pytest.fixture()
def patch(request):
    try:
        mp = request.getfixturevalue("monkeypatch")
    except AttributeError:  # pytest < 3
        mp = request.getfuncargvalue("monkeypatch")
    mp.setattr(vo.Registry, '_request', mockreturn)
    return mp


def mockreturn(method="POST", url=None, data=None, params=None, timeout=10, **kwargs):
    # Determine the test case from the URL and/or data
    assert "query" in data
    if "ivoid like '%heasarc%'" in data['query'] and "cap_type like '%simpleimageaccess%'" in data['query']:
        testcase = "query_basic_content"
    elif "order by count_" in data['query']:
        testcase = "query_counts_content"
    else:
        raise ValueError("Can't figure out the test case from data={}".format(data))

    trl = TestRegistryLocal()
    filepath = trl.data_path(trl.DATA_FILES[testcase])
    content = trl.file2content(filepath)
    return MockResponse(content=content)


@pytest.mark.usefixtures("patch")
class TestRegistryLocal(SharedRegistryTests):
    "Monkey patch all shared tests.  Also run the local-specific tests."

    def test_query_basic(self):
        shr = SharedRegistryTests()
        shr.query_basic()

    def test_query_counts(self):
        shr = SharedRegistryTests()
        shr.query_counts()

    def test_bad_queries(self):
        with pytest.raises(ValueError) as err:
            Registry.query(service_type='not_a_service_type')
        assert "service_type must be one of" in err.value.args[0]

    ##
    ## Below are tests that don't use even the simulated network.
    ## They test building the ADQL query string.
    ##
    def fix_white(self, s):
        fixed = " ".join(s.split())
        return fixed

    def test_adql_service(self):
        result = self.fix_white(Registry._build_adql(service_type="image"))
        expected = self.fix_white("""
            select res.waveband,res.short_name,cap.ivoid,res.res_description,
            intf.access_url,res.reference_url,res_role.role_name as publisher,cap.cap_type as service_type
            from rr.capability as cap
            natural join rr.resource as res
            natural join rr.interface as intf
            natural join rr.res_role as res_role
            where cap.cap_type like '%simpleimageaccess%' and
            standard_id != 'ivo://ivoa.net/std/sia#query-2.0' and res_role.base_role = 'publisher'
        """)
        assert result == expected

        result = self.fix_white(Registry._build_adql(service_type="spectr"))
        expected = self.fix_white("""
            select res.waveband,res.short_name,cap.ivoid,res.res_description,
            intf.access_url,res.reference_url,res_role.role_name as publisher,cap.cap_type as service_type
            from rr.capability as cap
            natural join rr.resource as res
            natural join rr.interface as intf
            natural join rr.res_role as res_role
            where cap.cap_type like '%simplespectralaccess%' and
            res_role.base_role = 'publisher'
        """)
        assert result == expected

        result = self.fix_white(Registry._build_adql(service_type="cone"))
        expected = self.fix_white("""
            select res.waveband,res.short_name,cap.ivoid,res.res_description,
            intf.access_url,res.reference_url,res_role.role_name as publisher,cap.cap_type as service_type
            from rr.capability as cap
            natural join rr.resource as res
            natural join rr.interface as intf
            natural join rr.res_role as res_role
            where cap.cap_type like '%conesearch%' and
            res_role.base_role = 'publisher'
        """)
        assert result == expected

        result = self.fix_white(Registry._build_adql(service_type="tap"))
        expected = self.fix_white("""
            select res.waveband,res.short_name,cap.ivoid,res.res_description,
            intf.access_url,res.reference_url,res_role.role_name as publisher,cap.cap_type as service_type
            from rr.capability as cap
            natural join rr.resource as res
            natural join rr.interface as intf
            natural join rr.res_role as res_role
            where cap.cap_type like '%tableaccess%' and
            res_role.base_role = 'publisher'
        """)
        assert result == expected

        result = self.fix_white(Registry._build_adql(service_type="table"))
        expected = self.fix_white("""
            select res.waveband,res.short_name,cap.ivoid,res.res_description,
            intf.access_url,res.reference_url,res_role.role_name as publisher,cap.cap_type as service_type
            from rr.capability as cap
            natural join rr.resource as res
            natural join rr.interface as intf
            natural join rr.res_role as res_role
            where cap.cap_type like '%tableaccess%' and
            res_role.base_role = 'publisher'
        """)
        assert result == expected

    def test_adql_keyword(self):
        result = self.fix_white(Registry._build_adql(keyword="foobar", service_type="image"))
        expected = self.fix_white("""
            select res.waveband,res.short_name,cap.ivoid,res.res_description,
            intf.access_url,res.reference_url,res_role.role_name as publisher,cap.cap_type as service_type
            from rr.capability as cap
            natural join rr.resource as res
            natural join rr.interface as intf
            natural join rr.res_role as res_role
             where cap.cap_type like '%simpleimageaccess%' and standard_id != 'ivo://ivoa.net/std/sia#query-2.0'
             and res_role.base_role = 'publisher' and
             (res.res_description like '%foobar%' or
            res.res_title like '%foobar%' or
            cap.ivoid like '%foobar%')
        """)

        assert result == expected

    def test_adql_waveband(self):
        result = self.fix_white(Registry._build_adql(waveband='foobar', service_type="image"))
        expected = self.fix_white("""
            select res.waveband,res.short_name,cap.ivoid,res.res_description,
          intf.access_url,res.reference_url,res_role.role_name as publisher,cap.cap_type as service_type
          from rr.capability as cap
            natural join rr.resource as res
            natural join rr.interface as intf
            natural join rr.res_role as res_role
             where cap.cap_type like '%simpleimageaccess%' and
             standard_id != 'ivo://ivoa.net/std/sia#query-2.0' and
             res.waveband like '%foobar%' and res_role.base_role = 'publisher'
        """)
        assert result == expected

        result = self.fix_white(Registry._build_adql(waveband='foo,bar,baz', service_type="image"))
        expected = self.fix_white("""
            select res.waveband,res.short_name,cap.ivoid,res.res_description,
          intf.access_url,res.reference_url,res_role.role_name as publisher,cap.cap_type as service_type
          from rr.capability as cap
            natural join rr.resource as res
            natural join rr.interface as intf
            natural join rr.res_role as res_role
             where cap.cap_type like '%simpleimageaccess%' and
             standard_id != 'ivo://ivoa.net/std/sia#query-2.0' and
             (res.waveband like '%foo%' or res.waveband like '%bar%' or res.waveband like '%baz%')
             and res_role.base_role = 'publisher'
        """)
        assert result == expected

    def test_adql_source(self):
        result = self.fix_white(Registry._build_adql(source='foobar', service_type="image"))
        expected = self.fix_white("""
            select res.waveband,res.short_name,cap.ivoid,res.res_description,
          intf.access_url,res.reference_url,res_role.role_name as publisher,cap.cap_type as service_type
          from rr.capability as cap
            natural join rr.resource as res
            natural join rr.interface as intf
            natural join rr.res_role as res_role
             where cap.cap_type like '%simpleimageaccess%' and
             standard_id != 'ivo://ivoa.net/std/sia#query-2.0' and
             cap.ivoid like '%foobar%' and res_role.base_role = 'publisher'
        """)

        assert result == expected

    def test_adql_publisher(self):
        result = self.fix_white(Registry._build_adql(publisher='foobar', service_type="image"))
        expected = self.fix_white("""
            select res.waveband,res.short_name,cap.ivoid,res.res_description,
          intf.access_url,res.reference_url,res_role.role_name as publisher,cap.cap_type as service_type
          from rr.capability as cap
            natural join rr.resource as res
            natural join rr.interface as intf
            natural join rr.res_role as res_role
             where cap.cap_type like '%simpleimageaccess%' and
             standard_id != 'ivo://ivoa.net/std/sia#query-2.0' and
             res_role.base_role = 'publisher' and res_role.role_name like '%foobar%'
        """)

        assert result == expected

    def test_adql_orderby(self):
        result = self.fix_white(Registry._build_adql(order_by="foobar", service_type="image"))
        expected = self.fix_white("""
            select res.waveband,res.short_name,cap.ivoid,res.res_description,
          intf.access_url,res.reference_url,res_role.role_name as publisher,cap.cap_type as service_type
          from rr.capability as cap
            natural join rr.resource as res
            natural join rr.interface as intf
            natural join rr.res_role as res_role
             where cap.cap_type like '%simpleimageaccess%' and
             standard_id != 'ivo://ivoa.net/std/sia#query-2.0' and
             res_role.base_role = 'publisher'order by foobar
             """)

        assert result == expected

    def test_sval(self):
        if sys.version_info[0] > 2:
            assert sval(b'Test byte string') == 'Test byte string'
            assert sval('Test plain string') == 'Test plain string'
            assert sval(42) == '42'
            assert sval(3.14) == '3.14'

    def test_sval_empty_tables(self):
        # With an empty table, it's difficult to show that stringify_table does nothing,
        # but exercise the code path anyway.
        vot_string = self.file2content(self.data_path(self.DATA_FILES['empty_votable']))
        ap_table = astropy_table_from_votable_string(vot_string)
        assert len(ap_table) == 0

    def test_counts_adql(self):
        counts = self.fix_white(Registry._build_counts_adql('publisher'))
        expected = self.fix_white("""
        select * from (select role_name as publisher, count(role_name)
        as count_publisher from rr.res_role where base_role = 'publisher'
        group by role_name) as count_table where count_publisher >= 1
        order by count_publisher desc
        """)
        assert counts == expected

        counts = self.fix_white(Registry._build_counts_adql('waveband'))
        expected = self.fix_white("""
        select * from (select waveband as waveband, count(waveband)
        as count_waveband from rr.resource group by waveband)
        as count_table where count_waveband >= 1 order by count_waveband desc
        """)
        assert counts == expected

        counts = self.fix_white(Registry._build_counts_adql('service_type'))
        expected = self.fix_white("""
        select * from (select cap_type as service_type, count(cap_type)
        as count_service_type from rr.capability group by cap_type)
        as count_table where count_service_type >= 1 order by count_service_type desc
        """)
        assert counts == expected

        counts = self.fix_white(Registry._build_counts_adql('service_type', minimum=10))
        expected = self.fix_white("""
        select * from (select cap_type as service_type, count(cap_type)
        as count_service_type from rr.capability group by cap_type)
        as count_table where count_service_type >= 10 order by count_service_type desc
        """)
        assert counts == expected

        counts = Registry._build_counts_adql('not_real_field')
        assert counts is None
