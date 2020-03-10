# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
=============
VoImageQuery tests
=============

"""
import os

from six import BytesIO
from astropy import units as u
from astropy.coordinates import SkyCoord
from astropy.utils.exceptions import AstropyDeprecationWarning
import pytest
import tempfile
try:
    pyvo_OK = True
    from astroquery.vo import VoImageQuery
except ImportError:
    pyvo_OK = False
    pytest.skip("Install pyvo for the vo module.", allow_module_level=True)
except AstropyDeprecationWarning as ex:
    if str(ex) == \
            'The astropy.vo.samp module has now been moved to astropy.samp':
        print('AstropyDeprecationWarning: {}'.format(str(ex)))
    else:
        raise ex
try:
    from unittest.mock import Mock, patch, MagicMock
except ImportError:
    pytest.skip("Install mock for the vo tests.", allow_module_level=True)


def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)


@patch('astroquery.vo.core.VoImageQuery.find_service_url',
       Mock(side_effect=lambda x: 'https://some.url'))
@patch('pyvo.dal.sia2.SIAService')
@pytest.mark.skipif(not pyvo_OK, reason='not pyvo_OK')
def test_query(sia_mock):
    sia_service_mock = Mock()
    sia_mock.return_value = sia_service_mock
    vo = VoImageQuery(authority_id='ivo://some.authority')
    pos = SkyCoord('09h45m07.5s +54d18m00s')
    vo.query_region(coordinates=pos, radius=0.01*u.deg)

    assert len(sia_service_mock.mock_calls) == 1
    name, pos_args, keyword_args = sia_service_mock.mock_calls[0]
    assert name == 'search'
    for ka in keyword_args:
        if ka == 'pos':
            assert keyword_args[ka] ==\
                (pos.ra.to(u.deg), pos.dec.to(u.deg), 0.01*u.deg)
        else:
            assert not keyword_args[ka]

    # pick a different search criteria
    sia_service_mock.reset_mock()
    vo.query_region(pos=(1*u.deg, 2*u.deg, 3*u.deg), collection='acollection')
    assert len(sia_service_mock.mock_calls) == 1
    name, pos_args, keyword_args = sia_service_mock.mock_calls[0]
    assert name == 'search'
    for ka in keyword_args:
        if ka == 'pos':
            assert keyword_args[ka] == (1*u.deg, 2*u.deg, 3*u.deg)
        elif ka == 'collection':
            assert keyword_args[ka] == 'acollection'
        else:
            assert not keyword_args[ka]


@patch('astroquery.vo.core.VoImageQuery.find_service_url',
       Mock(side_effect=lambda x: 'https://some.url'))
@patch('pyvo.dal.sia2.SIAService', Mock())
@pytest.mark.skipif(not pyvo_OK, reason='not pyvo_OK')
def test_get_file_urls():
    sia_results_mock = Mock()
    sia_results_mock.iter_datalinks.return_value = [('data1url', 'data1prev'),
                                                    ('data2url', 'data2prev')]
    vo = VoImageQuery(authority_id='ivo://some.authority')

    result = vo.get_data_urls(sia_results=sia_results_mock, types=None)
    assert len(result) == 4
    assert 'data1url' in result
    assert 'data2url' in result
    assert 'data1prev' in result
    assert 'data2prev' in result

    # specific types
    sia_results_mock.reset_mock()

    def bysemantics(semantics):
        if semantics == '#this':
            return ['thisurl']
        elif semantics == '#preview':
            return ['previewurl']

    dl_mock = Mock()
    dl_mock.bysemantics = bysemantics
    sia_results_mock.iter_datalinks.return_value = [dl_mock]

    result = vo.get_data_urls(sia_results=sia_results_mock)
    assert len(result) == 1
    assert 'thisurl' == result[0]

    result = vo.get_data_urls(sia_results=sia_results_mock, types='#preview')
    assert len(result) == 1
    assert 'previewurl' == result[0]

    result = vo.get_data_urls(sia_results=sia_results_mock,
                              types=['#preview', '#this'])
    assert len(result) == 2
    assert 'previewurl' in result
    assert 'thisurl' in result


@patch('astroquery.vo.core.VoImageQuery.find_service_url',
       Mock(side_effect=lambda x: 'https://some.url'))
@patch('pyvo.dal.sia2.SIAService', Mock())
@pytest.mark.skipif(not pyvo_OK, reason='not pyvo_OK')
def test_get_images():
    sia_results_mock = Mock()

    dl_mock = MagicMock()
    dl_res_mock = Mock()
    dl_res_mock.id = 'ivo://authority/data1'
    downloaded_file = BytesIO(b'Just a test')
    downloaded_file.id = dl_res_mock.id
    dl_res_mock.processed.return_value = downloaded_file
    dl_mock.bysemantics.return_value = [dl_res_mock]
    first_dl_mock = Mock()
    first_dl_mock.id = dl_res_mock.id
    dl_mock[0] = first_dl_mock
    sia_results_mock.iter_datalinks.return_value = [dl_mock]
    vo = VoImageQuery(authority_id='ivo://some.authority')
    tmpdir = tempfile.TemporaryDirectory()
    result = vo.get_images(sia_results=sia_results_mock, dest_dir=tmpdir.name)
    assert vo.download_errors
    assert vo.download_errors[0] == 'Empty or corrupt FITS file'
    assert not result

    dl_res_mock.reset_mock()
    dl_mock.reset_mock()
    # repeat test but stop on error
    with pytest.raises(OSError):
        vo.get_images(sia_results=sia_results_mock, dest_dir=tmpdir.name,
                      stop_on_error=True)

    # repeat test with cutouts and sample fits file
    dl_res_mock.reset_mock()
    dl_mock.reset_mock()
    with open(data_path('sample.fits'), 'rb') as f:
        downloaded_file = BytesIO(f.read())
    downloaded_file.id = dl_res_mock.id
    dl_res_mock.processed.return_value = downloaded_file

    images = vo.get_images(sia_results=sia_results_mock, dest_dir=tmpdir.name)
    assert not vo.download_errors
    assert len(images) == 1
    files = []
    # r=root, d=directories, f = files
    for r, d, f in os.walk(tmpdir.name):
        for file in f:
            files.append(file)
    assert len(images) == len(files)
    assert images[0]._file.name == \
        os.path.join(tmpdir.name, first_dl_mock.id.replace('/', '_'))
