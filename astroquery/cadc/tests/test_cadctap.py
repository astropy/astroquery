# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
=============
CadcClass TAP plus
=============

"""
import os
import sys

from astropy.table import Table as AstroTable
from astropy.io.fits.hdu.hdulist import HDUList
from astropy.io.votable.tree import VOTableFile, Resource, Table, Field
from astropy.io.votable import parse
from six import BytesIO
from six.moves.urllib_parse import urlsplit, parse_qs
from astroquery.utils.commons import parse_coordinates, FileContainer
from astropy import units as u
from astropy.utils.exceptions import AstropyDeprecationWarning
import pytest
import tempfile
import requests
try:
    pyvo_OK = True
    from pyvo.auth import authsession
    from astroquery.cadc import Cadc, conf
    import astroquery.cadc.core as cadc_core
except ImportError:
    pyvo_OK = False
    pytest.skip("Install pyvo for the cadc module.", allow_module_level=True)
except AstropyDeprecationWarning as ex:
    if str(ex) == \
            'The astropy.vo.samp module has now been moved to astropy.samp':
        print('AstropyDeprecationWarning: {}'.format(str(ex)))
    else:
        raise ex
try:
    from unittest.mock import Mock, patch, PropertyMock
except ImportError:
    pytest.skip("Install mock for the cadc tests.", allow_module_level=True)


def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)


@patch('astroquery.cadc.core.get_access_url',
       Mock(side_effect=lambda x: 'https://some.url'))
@pytest.mark.skipif(not pyvo_OK, reason='not pyvo_OK')
def test_get_tables():
    # default parameters
    table_set = PropertyMock()
    table_set.keys.return_value = ['table1', 'table2']
    table_set.values.return_value = ['tab1val', 'tab2val', 'tab3val']
    with patch('astroquery.cadc.core.pyvo.dal.TAPService', autospec=True) as tapservice_mock:
        tapservice_mock.return_value.tables = table_set
        cadc = Cadc()
        assert len(cadc.get_tables(only_names=True)) == 2
        assert len(cadc.get_tables()) == 3


@patch('astroquery.cadc.core.get_access_url',
       Mock(side_effect=lambda x: 'https://some.url'))
@pytest.mark.skipif(not pyvo_OK, reason='not pyvo_OK')
def test_get_table():
    table_set = PropertyMock()
    tables_result = [Mock() for _ in range(3)]
    tables_result[0].name = 'tab1'
    tables_result[1].name = 'tab2'
    tables_result[2].name = 'tab3'
    table_set.values.return_value = tables_result

    with patch('astroquery.cadc.core.pyvo.dal.TAPService', autospec=True) as tapservice_mock:
        tapservice_mock.return_value.tables = table_set
        cadc = Cadc()
        assert cadc.get_table('tab2').name == 'tab2'
        assert cadc.get_table('foo') is None


@patch('astroquery.cadc.core.get_access_url',
       Mock(side_effect=lambda x: 'https://some.url'))
@pytest.mark.skipif(not pyvo_OK, reason='not pyvo_OK')
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
@pytest.mark.skipif(not pyvo_OK, reason='not pyvo_OK')
def test_load_async_job():
    with patch('astroquery.cadc.core.pyvo.dal.TAPService', autospec=True) as tapservice_mock:
        with patch('astroquery.cadc.core.pyvo.dal.AsyncTAPJob',
                   autospec=True) as tapjob_mock:
            tapservice_mock.return_value.baseurl.return_value = 'https://www.example.com/tap'
            mock_job = Mock()
            mock_job.job_id = '123'
            tapjob_mock.return_value = mock_job
            cadc = Cadc()
            jobid = '123'
            job = cadc.load_async_job(jobid)
            assert job.job_id == '123'


@pytest.mark.skip('Disabled until job listing available in pyvo')
@patch('astroquery.cadc.core.get_access_url',
       Mock(side_effect=lambda x: 'https://some.url'))
@pytest.mark.skipif(not pyvo_OK, reason='not pyvo_OK')
def test_list_async_jobs():
    with patch('astroquery.cadc.core.pyvo.dal.TAPService', autospec=True) as tapservice_mock:
        tapservice_mock.return_value.baseurl.return_value = 'https://www.example.com/tap'
        cadc = Cadc()
        cadc.list_async_jobs()


@patch('astroquery.cadc.core.get_access_url',
       Mock(side_effect=lambda x, y=None: 'https://some.url'))
@pytest.mark.skipif(not pyvo_OK, reason='not pyvo_OK')
def test_auth():
    # the Cadc() will cause a remote data call to TAP service capabilities
    # To avoid this, use an anonymous session and replace it with an
    # auth session later
    cadc = Cadc(auth_session=requests.Session())
    cadc.cadctap._session = authsession.AuthSession()
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
    assert cadc.cadctap._session.credentials.get(
        'ivo://ivoa.net/sso#tls-with-certificate').cert == cert
    # reset and try with user password/cookies
    cadc.cadctap._session = authsession.AuthSession()
    post_mock = Mock()
    cookie = 'ABC'
    mock_resp = Mock()
    mock_resp.text = cookie
    post_mock.return_value.cookies = requests.cookies.RequestsCookieJar()
    post_mock.return_value = mock_resp
    cadc._request = post_mock
    cadc.login(user=user, password=password)
    assert cadc.cadctap._session.credentials.get(
        'ivo://ivoa.net/sso#cookie').cookies[cadc_core.CADC_COOKIE_PREFIX] == \
        '"{}"'.format(cookie)


# make sure that caps is reset at the end of the test
@patch('astroquery.cadc.core.get_access_url.caps', {})
@pytest.mark.skipif(not pyvo_OK, reason='not pyvo_OK')
def test_get_access_url():
    # testing implementation of requests.get method:
    def get(url, **kwargs):
        class ServiceResponse:
            def __init__(self):
                self.text = 'ivo://cadc.nrc.ca/mytap = http://my.org/mytap'

            def raise_for_status(self):
                pass

        class CapabilitiesResponse:
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
        assert 'https://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/argus/tables' == \
            cadc_core.get_access_url('mytap',
                                     'ivo://ivoa.net/std/VOSI#tables-1.1')


@patch('astroquery.cadc.core.get_access_url',
       Mock(side_effect=lambda x, y=None: 'https://some.url'))
@pytest.mark.skipif(not pyvo_OK, reason='not pyvo_OK')
def test_get_data_urls():

    def get(*args, **kwargs):
        class CapsResponse:
            def __init__(self):
                self.status_code = 200
                self.content = b''

            def raise_for_status(self):
                pass
        return CapsResponse()

    class Result:
        pass

    file1 = Mock()
    file1.semantics = '#this'
    file1.access_url = 'https://get.your.data/path'
    file2 = Mock()
    file2.semantics = '#aux'
    file2.access_url = 'https://get.your.data/auxpath'
    file3 = Mock()
    file3.semantics = '#preview'
    file3.access_url = 'https://get.your.data/previewpath'
    # add the package file that should be filtered out
    package_file = Mock()
    package_file.semantics = 'http://www.openadc.org/caom2#pkg'
    result = [file1, file2, file3, package_file]
    with patch('pyvo.dal.adhoc.DatalinkResults.from_result_url') as dl_results_mock:
        dl_results_mock.return_value = result
        cadc = Cadc()
        cadc._request = get  # mock the request
        assert [file1.access_url] == \
            cadc.get_data_urls({'publisherID': ['ivo://cadc.nrc.ca/foo']})
        assert [file1.access_url, file2.access_url, file3.access_url] == \
            cadc.get_data_urls({'publisherID': ['ivo://cadc.nrc.ca/foo']},
                               include_auxiliaries=True)
    with pytest.raises(AttributeError):
        cadc.get_data_urls(None)
    with pytest.raises(AttributeError):
        cadc.get_data_urls({'noPublisherID': 'test'})


@patch('astroquery.cadc.core.get_access_url',
       Mock(side_effect=lambda x, y=None: 'https://some.url'))
@pytest.mark.skipif(not pyvo_OK, reason='not pyvo_OK')
def test_misc():
    cadc = Cadc()

    coords = '08h45m07.5s +54d18m00s'
    coords_ra = parse_coordinates(coords).fk5.ra.degree
    coords_dec = parse_coordinates(coords).fk5.dec.degree

    assert "SELECT * from caom2.Observation o join caom2.Plane p ON " \
           "o.obsID=p.obsID WHERE INTERSECTS( CIRCLE('ICRS', " \
           "{}, {}, 0.3), position_bounds) = 1 " \
           "AND (quality_flag IS NULL OR quality_flag != 'junk') " \
           "AND collection='CFHT' AND dataProductType='image'".\
           format(coords_ra, coords_dec) == \
           cadc._args_to_payload(**{'coordinates': coords,
                                    'radius': 0.3 * u.deg, 'collection':
                                        'CFHT',
                                    'data_product_type': 'image'})['query']

    # no collection or data_product_type
    assert "SELECT * from caom2.Observation o join caom2.Plane p ON " \
           "o.obsID=p.obsID WHERE INTERSECTS( CIRCLE('ICRS', " \
           "{}, {}, 0.3), position_bounds) = 1 AND (quality_flag IS NULL OR " \
           "quality_flag != 'junk')".format(coords_ra, coords_dec) ==  \
           cadc._args_to_payload(**{'coordinates': coords,
                                 'radius': '0.3 deg'})['query']


@patch('astroquery.cadc.core.get_access_url',
       Mock(side_effect=lambda x, y=None: 'https://some.url'))
@pytest.mark.skipif(not pyvo_OK, reason='not pyvo_OK')
def test_get_image_list():
    def get(*args, **kwargs):
        class CapsResponse:
            def __init__(self):
                self.status_code = 200
                self.content = b''

            def raise_for_status(self):
                pass

        return CapsResponse()

    class Params:
        def __init__(self, **param_dict):
            self.__dict__.update(param_dict)

    coords = '08h45m07.5s +54d18m00s'
    coords_ra = parse_coordinates(coords).fk5.ra.degree
    coords_dec = parse_coordinates(coords).fk5.dec.degree
    radius = 0.1*u.deg

    uri = 'im_an_ID'
    run_id = 'im_a_RUNID'
    pos = 'CIRCLE {} {} {}'.format(coords_ra, coords_dec, radius.value)

    service_def1 = Mock()
    service_def1.access_url = \
        b'https://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/caom2ops/sync'
    service_def1.input_params = [Params(name='ID', value=uri),
                                 Params(name='RUNID', value=run_id)]

    service_def2 = Mock()
    service_def2.access_url = \
        b'https://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/caom2ops/async'
    service_def2.input_params = [Params(name='ID', value=uri),
                                 Params(name='RUNID', value=run_id)]

    result = Mock()
    service_def_list = [service_def1, service_def2]
    result.bysemantics.return_value = service_def_list

    with patch('pyvo.dal.adhoc.DatalinkResults.from_result_url') as dl_results_mock:
        dl_results_mock.return_value = result
        cadc = Cadc()
        cadc._request = get  # Mock the request
        url_list = cadc.get_image_list(
            {'publisherID': ['ivo://cadc.nrc.ca/foo']}, coords, radius)

        assert len(url_list) == 1

        params = parse_qs(urlsplit(url_list[0]).query)

        assert params['ID'][0] == uri
        assert params['RUNID'][0] == run_id
        assert params['POS'][0] == pos

    with pytest.raises(TypeError):
        cadc.get_image_list(None)
    with pytest.raises(AttributeError):
        cadc.get_image_list(None, coords, radius)
    with pytest.raises(TypeError):
        cadc.get_image_list({'publisherID': [
            'ivo://cadc.nrc.ca/foo']}, coords, 0.1)


@patch('astroquery.cadc.core.get_access_url',
       Mock(side_effect=lambda x, y=None: 'https://some.url'))
@pytest.mark.skipif(not pyvo_OK, reason='not pyvo_OK')
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
    cadc = Cadc(auth_session=requests.Session())
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
    try:
        # TODO remove when astropy LTS upgraded
        from astropy.utils.diff import report_diff_values
        assert report_diff_values(table, actual_table, fileobj=sys.stdout)
    except ImportError:
        pass


@patch('astroquery.cadc.core.CadcClass.exec_sync', Mock())
@patch('astroquery.cadc.core.CadcClass.get_image_list',
       Mock(side_effect=lambda x, y, z: ['https://some.url']))
@pytest.mark.skipif(not pyvo_OK, reason='not pyvo_OK')
def test_get_images():
    with patch('astroquery.utils.commons.get_readable_fileobj', autospec=True) as readable_fobj_mock:
        readable_fobj_mock.return_value = open(data_path('query_images.fits'), 'rb')

        cadc = Cadc()
        fits_images = cadc.get_images('08h45m07.5s +54d18m00s', 0.01*u.deg,
                                      get_url_list=True)
        assert fits_images == ['https://some.url']

        fits_images = cadc.get_images('08h45m07.5s +54d18m00s', '0.01 deg')
        assert fits_images is not None
        assert isinstance(fits_images[0], HDUList)


@patch('astroquery.cadc.core.CadcClass.exec_sync', Mock())
@patch('astroquery.cadc.core.CadcClass.get_image_list',
       Mock(side_effect=lambda x, y, z: ['https://some.url']))
@pytest.mark.skipif(not pyvo_OK, reason='not pyvo_OK')
def test_get_images_async():
    with patch('astroquery.utils.commons.get_readable_fileobj', autospec=True) as readable_fobj_mock:
        readable_fobj_mock.return_value = open(data_path('query_images.fits'), 'rb')

    cadc = Cadc()
    readable_objs = cadc.get_images_async('08h45m07.5s +54d18m00s',
                                          0.01*u.arcmin,
                                          get_url_list=True)
    assert readable_objs == ['https://some.url']

    readable_objs = cadc.get_images_async('08h45m07.5s +54d18m00s',
                                          '0.01 arcsec')
    assert readable_objs is not None
    assert isinstance(readable_objs[0], FileContainer)
