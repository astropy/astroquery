# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
=============
CadcClass TAP plus
=============

"""
import os
import sys

from astropy.table import Table as AstroTable
from astropy.io.votable.tree import VOTableFile, Resource, Table, Field
from astropy.io.votable import parse
from astropy.utils.diff import report_diff_values
from six import BytesIO
from astroquery.cadc import Cadc, conf
import astroquery.cadc.core as cadc_core
from astroquery.utils.commons import parse_coordinates
from unittest.mock import Mock, patch, PropertyMock
import pytest
import tempfile
from pyvo.dal import tap


# monkeypatch get_access_url to prevent internet calls
def get_access_url_mock(arg1, arg2=None):
    return "https://some.url"


def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)


@patch('astroquery.cadc.core.get_access_url',
       Mock(side_effect=lambda x: 'https://some.url'))
def test_get_tables():
    # default parameters
    table_set = PropertyMock()
    table_set.keys.return_value = ['table1', 'table2']
    table_set.values.return_value = ['tab1val', 'tab2val', 'tab3val']
    with patch('astroquery.cadc.core.pyvo.dal.TAPService', autospec=True) as m:
        m.return_value.tables = table_set
        tap = Cadc()
        assert len(tap.get_tables(only_names=True)) == 2
        assert len(tap.get_tables()) == 3


@patch('astroquery.cadc.core.get_access_url',
       Mock(side_effect=lambda x: 'https://some.url'))
def test_get_table():
    table_set = PropertyMock()
    tables_result = [Mock(), Mock(), Mock()]
    tables_result[0].name = 'tab1'
    tables_result[1].name = 'tab2'
    tables_result[2].name = 'tab3'
    table_set.values.return_value = tables_result

    with patch('astroquery.cadc.core.pyvo.dal.TAPService', autospec=True) as m:
        m.return_value.tables = table_set
        tap = Cadc()
        assert tap.get_table('tab2').name == 'tab2'
        assert tap.get_table('foo') is None


@patch('astroquery.cadc.core.get_access_url',
       Mock(side_effect=lambda x: 'https://some.url'))
def test_get_collections():
    cadc = Cadc()

    def mock_run_query(query, output_format=None, maxrec=None,
                       output_file=None):
        assert query == \
               'select distinct collection, energy_emBand from caom2.EnumField'
        assert output_format is None
        assert maxrec is None
        assert output_file is None
        table = AstroTable(rows=[('CFHT', 'Optical'), ('CFHT', 'Infrared'),
                                 ('JCMT', 'Millimeter'), ('DAO', 'Optical'),
                                 ('DAO', 'Infrared')],
                           names=('collection', 'energy_emBand'))
        return table
    cadc.exec_sync = mock_run_query
    result = cadc.get_collections()
    assert len(result) == 3
    assert 'CFHT' in result
    assert 'JCMT' in result
    assert 'DAO' in result


@patch('astroquery.cadc.core.get_access_url',
       Mock(side_effect=lambda x: 'https://some.url'))
def test_load_async_job():
    with patch('astroquery.cadc.core.pyvo.dal.TAPService', autospec=True) as t:
        with patch('astroquery.cadc.core.pyvo.dal.AsyncTAPJob',
                   autospec=True) as j:
            t.return_value.baseurl.return_value = 'https://www.example.com/tap'
            mock_job = Mock()
            mock_job.job_id = '123'
            j.return_value = mock_job
            tap = Cadc()
            jobid = '123'
            job = tap.load_async_job(jobid)
            assert job.job_id == '123'


@pytest.mark.skip('Disabled until job listing available in pyvo')
@patch('astroquery.cadc.core.get_access_url',
       Mock(side_effect=lambda x: 'https://some.url'))
def test_list_async_jobs():
    with patch('astroquery.cadc.core.pyvo.dal.TAPService', autospec=True) as t:
        t.return_value.baseurl.return_value = 'https://www.example.com/tap'
        tap = Cadc()
        tap.list_async_jobs()


@patch('astroquery.cadc.core.get_access_url',
       Mock(side_effect=lambda x, y=None: 'https://some.url'))
def test_auth():
    cadc = Cadc()
    user = 'user'
    password = 'password'
    cert = 'cert'
    with pytest.raises(AttributeError):
        cadc.login(None, None, None)
    with pytest.raises(AttributeError):
        cadc.login(user=user)
    with pytest.raises(AttributeError):
        cadc.login(password=password)
    cadc.login(certificate_file=cert)
    assert tap.s.cert == cert
    cadc.logout()
    assert tap.s.cert is None
    with patch('astroquery.cadc.core.requests.post') as m:
        cookie = 'ABC'
        mock_resp = Mock()
        mock_resp.text = cookie
        m.return_value = mock_resp
        cadc.login(user=user, password=password)
    assert tap.s.cookies[cadc_core.CADC_COOKIE_PREFIX] == '"{}"'.format(cookie)


def test_get_access_url():
    # testing implementation of requests.get method:
    def get(url, **kwargs):
        class ServiceResponse(object):
            def __init__(self):
                self.text = 'ivo://cadc.nrc.ca/mytap = http://my.org/mytap'

            def raise_for_status(self):
                pass

        class CapabilitiesResponse(object):
            def __init__(self):
                caps_file = data_path('tap_caps.xml')
                self.text = open(caps_file, 'r').read()

            def raise_for_status(self):
                pass
        if url == conf.CADC_REGISTRY_URL:
            return ServiceResponse()
        else:
            return CapabilitiesResponse()

    # now use it in testing
    with patch.object(cadc_core.requests, 'get', get):
        cadc_core.get_access_url.caps = {}
        assert 'http://my.org/mytap' == cadc_core.get_access_url('mytap')
        assert 'https://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/tap/tables' == \
            cadc_core.get_access_url('mytap',
                                     'ivo://ivoa.net/std/VOSI#tables-1.1')


@patch('astroquery.cadc.core.get_access_url',
       Mock(side_effect=lambda x, y=None: 'https://some.url'))
def test_get_data_urls():

    def get(*args, **kwargs):
        class CapsResponse(object):
            def __init__(self):
                self.status_code = 200
                self.content = b''

            def raise_for_status(self):
                pass
        return CapsResponse()

    class Result(object):
        pass

    vot_result = Result()
    vot_result.array = [{'semantics': b'#this',
                         'access_url': b'https://get.your.data/path'},
                        {'semantics': b'#aux',
                         'access_url': b'https://get.your.data/auxpath'}]

    with patch.object(cadc_core, 'parse_single_table', lambda x: vot_result):
        cadc = Cadc()
        cadc._request = get  # mock the request
        assert [vot_result.array[0]['access_url'].decode('ascii')] == \
            cadc.get_data_urls({'publisherID': ['ivo://cadc.nrc.ca/foo']})
        assert [vot_result.array[0]['access_url'].decode('ascii'),
                vot_result.array[1]['access_url'].decode('ascii')] == \
            cadc.get_data_urls({'publisherID': ['ivo://cadc.nrc.ca/foo']},
                               include_auxiliaries=True)
    with pytest.raises(AttributeError):
        cadc.get_data_urls(None)
    with pytest.raises(AttributeError):
        cadc.get_data_urls({'noPublisherID': 'test'})


@patch('astroquery.cadc.core.get_access_url',
       Mock(side_effect=lambda x, y=None: 'https://some.url'))
def test_misc():
    cadc = Cadc()

    coords = '08h45m07.5s +54d18m00s'
    coords_ra = parse_coordinates(coords).fk5.ra.degree
    coords_dec = parse_coordinates(coords).fk5.dec.degree

    assert "SELECT * from caom2.Observation o join caom2.Plane p ON " \
           "o.obsID=p.obsID WHERE INTERSECTS( CIRCLE('ICRS', " \
           "{}, {}, 0.3), position_bounds) = 1 " \
           "AND (quality_flag IS NULL OR quality_flag != 'junk') " \
           "AND collection='CFHT'".format(coords_ra, coords_dec) == \
           cadc._args_to_payload(**{'coordinates': coords,
                                 'radius': 0.3, 'collection': 'CFHT'})['query']

    # no collection
    assert "SELECT * from caom2.Observation o join caom2.Plane p ON " \
           "o.obsID=p.obsID WHERE INTERSECTS( CIRCLE('ICRS', " \
           "{}, {}, 0.3), position_bounds) = 1 AND (quality_flag IS NULL OR " \
           "quality_flag != 'junk')".format(coords_ra, coords_dec) ==  \
           cadc._args_to_payload(**{'coordinates': coords,
                                 'radius': 0.3})['query']


@patch('astroquery.cadc.core.get_access_url',
       Mock(side_effect=lambda x, y=None: 'https://some.url'))
def test_exec_sync():
    # save results in a file
    # create the VOTable result
    # example from http://docs.astropy.org/en/stable/io/votable/
    votable = VOTableFile()
    resource = Resource()
    votable.resources.append(resource)
    table = Table(votable)
    resource.tables.append(table)
    table.fields.extend([
        Field(votable, name="filename", datatype="char", arraysize="*"),
        Field(votable, name="matrix", datatype="double", arraysize="2x2")])
    table.create_arrays(2)
    table.array[0] = ('test1.xml', [[1, 0], [0, 1]])
    table.array[1] = ('test2.xml', [[0.5, 0.3], [0.2, 0.1]])
    buffer = BytesIO()
    votable.to_xml(buffer)
    cadc = Cadc()
    response = Mock()
    response.to_table.return_value = buffer.getvalue()
    cadc.cadctap.search = Mock(return_value=response)
    output_file = '{}/test_vooutput.xml'.format(tempfile.tempdir)
    cadc.exec_sync('some query', output_file=output_file)

    actual = parse(output_file)
    assert len(votable.resources) == len(actual.resources) == 1
    assert len(votable.resources[0].tables) ==\
        len(actual.resources[0].tables) == 1
    actual_table = actual.resources[0].tables[0]
    assert report_diff_values(table, actual_table, fileobj=sys.stdout)
