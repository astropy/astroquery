from __future__ import print_function

from astropy.tests.helper import pytest
from astropy.tests.helper import remote_data
from ...utils.testing_tools import MockResponse

from ... import vo
from astroquery.vo import Registry
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

    def test_query_timeout(self):
        shr = SharedRegistryTests()
        shr.query_timeout()

    ##
    ## Below are tests that don't use even the simulated network.
    ## The test building the ADQL.
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
