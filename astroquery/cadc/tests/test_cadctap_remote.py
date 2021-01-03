# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
=============
Canadian Astronomy Data Centre
=============
"""

import pytest
import os
import requests
from datetime import datetime
from astropy.coordinates import SkyCoord
from astropy.io import fits
from astropy import units as u

from astroquery.cadc import Cadc
from astropy.utils.exceptions import AstropyDeprecationWarning
from astroquery.utils.commons import parse_coordinates, FileContainer

try:
    pyvo_OK = True
    import pyvo   # noqa
    from pyvo.auth import authsession
except ImportError:
    pyvo_OK = False
except AstropyDeprecationWarning as e:
    if str(e) == 'The astropy.vo.samp module has now been moved to astropy.samp':
        print('AstropyDeprecationWarning: {}'.format(str(e)))
    else:
        raise e

# to run just one test during development, set this variable to True
# and comment out the skipif of the single test to run.
one_test = False

# Skip the very slow tests to avoid timeout errors
skip_slow = True


@pytest.mark.remote_data
class TestCadcClass:
    # now write tests for each method here
    @pytest.mark.skipif(one_test, reason='One test mode')
    @pytest.mark.skipif(not pyvo_OK, reason='not pyvo_OK')
    def test_get_collections(self):
        cadc = Cadc()
        result = cadc.get_collections()
        assert len(result) > 10
        # test for the presence of a few known collections
        assert 'CFHT' in result
        assert 'Infrared' in result['CFHT']['Bands']
        assert 'Optical' in result['CFHT']['Bands']
        assert 'MOST' in result
        assert 'Optical' in result['MOST']['Bands']
        assert 'GEMINI' in result
        assert 'Infrared' in result['GEMINI']['Bands']
        assert 'Optical' in result['GEMINI']['Bands']
        assert 'JCMT' in result
        assert 'Millimeter' in result['JCMT']['Bands']
        assert 'DAO' in result
        assert 'Infrared' in result['DAO']['Bands']
        assert 'Optical' in result['DAO']['Bands']

    @pytest.mark.skipif(one_test, reason='One test mode')
    @pytest.mark.skipif(not pyvo_OK, reason='not pyvo_OK')
    def test_query_region(self):
        cadc = Cadc()
        result = cadc.query_region('08h45m07.5s +54d18m00s', collection='CFHT')
        # do some manipulation of the results. Below it's filtering out based
        # on target name but other manipulations are possible.
        assert len(result) > 0
        urls = cadc.get_data_urls(result[result['target_name'] == 'Nr3491_1'])
        assert len(urls) > 0
        # urls are a subset of the results that match target_name==Nr3491_1
        assert len(result) >= len(urls)
        urls_data_only = len(urls)
        # now get the auxilary files too
        urls = cadc.get_data_urls(result[result['target_name'] == 'Nr3491_1'],
                                  include_auxiliaries=True)
        assert urls_data_only <= len(urls)

        # the same result should be obtained by querying the entire region
        # and filtering out on the CFHT collection
        result2 = cadc.query_region('08h45m07.5s +54d18m00s')
        assert len(result) == len(result2[result2['collection'] == 'CFHT'])

        # search for a target
        results = cadc.query_region(SkyCoord.from_name('M31'), radius=0.016)
        assert len(results) > 20

    @pytest.mark.skipif(one_test, reason='One test mode')
    @pytest.mark.skipif(not pyvo_OK, reason='not pyvo_OK')
    def test_query_name(self):
        cadc = Cadc()
        result1 = cadc.query_name('M31-B14')
        assert len(result1) > 20
        # test case insensitive
        result2 = cadc.query_name('m31-b14')
        assert len(result1) == len(result2)

    @pytest.mark.skipif(one_test, reason='One test mode')
    @pytest.mark.skipif(not pyvo_OK, reason='not pyvo_OK')
    def test_query(self):
        cadc = Cadc()
        result = cadc.exec_sync(
            "select count(*) from caom2.Observation where target_name='M31'")
        assert 1000 < result[0][0]

        # test that no proprietary results are returned when not logged in
        now = datetime.utcnow()
        query = "select top 1 * from caom2.Plane where " \
                "metaRelease>'{}'".format(now.strftime('%Y-%m-%dT%H:%M:%S.%f'))
        result = cadc.exec_sync(query)
        assert len(result) == 0

    @pytest.mark.skipif(one_test, reason='One test mode')
    @pytest.mark.skip('Disabled for now until pyvo starts supporting '
                      'different output formats')
    @pytest.mark.skipif(not pyvo_OK, reason='not pyvo_OK')
    def test_query_format(self):
        cadc = Cadc()
        query = "select top 1 observationID, collection from caom2.Observation"
        result = cadc.exec_sync(query, output_format='csv')
        print(result)

    @pytest.mark.skipif(one_test, reason='One test mode')
    @pytest.mark.skipif(('CADC_USER' not in os.environ
                        or 'CADC_PASSWD' not in os.environ),
                        reason='Requires real CADC user/password (CADC_USER '
                               'and CADC_PASSWD environment variables)')
    @pytest.mark.skipif(not pyvo_OK, reason='not pyvo_OK')
    def test_login_with_user_password(self):
        for auth_session in [None, authsession.AuthSession(),
                             requests.Session()]:
            cadc = Cadc(auth_session=auth_session)
            now = datetime.utcnow()
            query = \
                "select top 1 * from caom2.Plane where metaRelease>'{}'".\
                format(now.strftime('%Y-%m-%dT%H:%M:%S.%f'))
            result = cadc.exec_sync(query)
            assert len(result) == 0
            cadc.login(os.environ['CADC_USER'], os.environ['CADC_PASSWD'])
            query = "select top 1 * from caom2.Plane where metaRelease>'{}'".\
                format(now.strftime('%Y-%m-%dT%H:%M:%S.%f'))
            result = cadc.exec_sync(query)
            assert len(result) == 1
            # repeat after logout
            cadc.logout()
            query = \
                "select top 1 * from caom2.Plane where metaRelease>'{}'".\
                format(now.strftime('%Y-%m-%dT%H:%M:%S.%f'))
            result = cadc.exec_sync(query)
            assert len(result) == 0

    @pytest.mark.skipif(one_test, reason='One test mode')
    @pytest.mark.skipif('CADC_CERT' not in os.environ,
                        reason='Requires real CADC certificate (CADC_CERT '
                               'environment variable)')
    @pytest.mark.skipif(not pyvo_OK, reason='not pyvo_OK')
    def test_login_with_cert(self):
        for auth_session in [requests.Session()]:
            cadc = Cadc(auth_session=auth_session)
            now = datetime.utcnow()
            query = \
                "select top 1 * from caom2.Plane where metaRelease>'{}'".\
                format(now.strftime('%Y-%m-%dT%H:%M:%S.%f'))
            result = cadc.exec_sync(query)
            assert len(result) == 0
            # following query is to test login with certificates when an
            # anonymous query is executed first.
            cadc.login(certificate_file=os.environ['CADC_CERT'])
            query = \
                "select top 1 * from caom2.Plane where metaRelease>'{}'".\
                format(now.strftime('%Y-%m-%dT%H:%M:%S.%f'))
            result = cadc.exec_sync(query)
            assert len(result) == 1
            cadc.logout()
            query = \
                "select top 1 * from caom2.Plane where metaRelease>'{}'".\
                format(now.strftime('%Y-%m-%dT%H:%M:%S.%f'))
            result = cadc.exec_sync(query)
            assert len(result) == 0

    @pytest.mark.skipif(one_test, reason='One test mode')
    @pytest.mark.skipif('CADC_CERT' not in os.environ,
                        reason='Requires real CADC certificate (CADC_CERT '
                               'environment variable)')
    @pytest.mark.skipif(not pyvo_OK, reason='not pyvo_OK')
    def test_authsession(self):
        # repeat previous test
        auth_session = requests.Session()
        auth_session.cert = os.environ['CADC_CERT']
        cadc = Cadc(auth_session=auth_session)
        now = datetime.utcnow()
        query = "select top 1 * from caom2.Plane where " \
                "metaRelease>'{}'".format(now.strftime('%Y-%m-%dT%H:%M:%S.%f'))
        result = cadc.exec_sync(query)
        assert len(result) == 1
        annon_session = requests.Session()
        cadc = Cadc(auth_session=annon_session)
        now = datetime.utcnow()
        query = "select top 1 * from caom2.Plane where " \
                "metaRelease>'{}'".format(now.strftime('%Y-%m-%dT%H:%M:%S.%f'))
        result = cadc.exec_sync(query)
        assert len(result) == 0

    @pytest.mark.skipif(one_test, reason='One test mode')
    @pytest.mark.skipif(not pyvo_OK, reason='not pyvo_OK')
    def test_get_images(self):
        cadc = Cadc()
        coords = '08h45m07.5s +54d18m00s'
        radius = 0.005*u.deg
        images = cadc.get_images(coords, radius, collection='CFHT')
        assert images is not None

        for image in images:
            assert isinstance(image, fits.HDUList)

    @pytest.mark.skipif(one_test, reason='One test mode')
    @pytest.mark.skipif(not pyvo_OK, reason='not pyvo_OK')
    @pytest.mark.skipif(skip_slow, reason='Avoid timeout errors')
    def test_get_images_against_AS(self):
        cadc = Cadc()
        coords = '08h45m07.5s +54d18m00s'
        radius = 0.05*u.deg

        # Compare results from cadc advanced search to get_images
        query = cadc._args_to_payload(**{'coordinates': coords,
                                         'radius': radius,
                                         'data_product_type': 'image'})['query']
        result = cadc.exec_sync(query)
        uri_list = [uri.decode('ascii') for uri in result['publisherID']]
        access_url = 'https://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/en/download'
        icrs_coords = parse_coordinates(coords).icrs
        data = {'uris': ' '.join(uri_list),
                'params': 'cutout=Circle ICRS {} {} {}'.
                format(icrs_coords.ra.degree, icrs_coords.dec.degree,
                       radius.value),
                'method': 'URL List'
                }

        resp_urls = requests.post(access_url, data).text.split('\r\n')

        # Filter out the errors and empty strings
        filtered_resp_urls = list(filter(lambda url:
                                         not url.startswith('ERROR')
                                         and url != '', resp_urls))

        # This function should return nearly the same urls
        image_urls = cadc.get_images(coords, radius, get_url_list=True)

        assert len(filtered_resp_urls) == len(image_urls)

    @pytest.mark.skipif(one_test, reason='One test mode')
    @pytest.mark.skipif(not pyvo_OK, reason='not pyvo_OK')
    def test_get_images_async(self):
        cadc = Cadc()
        coords = '01h45m07.5s +23d18m00s'
        radius = '0.05 deg'
        readable_objs = cadc.get_images_async(coords, radius, collection="CFHT")
        assert readable_objs is not None
        for obj in readable_objs:
            assert isinstance(obj, FileContainer)

    @pytest.mark.skipif(one_test, reason='One test mode')
    @pytest.mark.skipif(not pyvo_OK, reason='not pyvo_OK')
    def test_async(self):
        # test async calls
        cadc = Cadc()

        # run the query in sync mode first
        expected = cadc.exec_sync(
            "select top 3 observationID from caom2.Observation where "
            "collection='IRIS' order by observationID")

        # now run the query in async mode
        job = cadc.create_async(
            "select top 3 observationID from caom2.Observation where "
            "collection='IRIS' order by observationID")
        job = job.run().wait()
        job.raise_if_error()
        result = job.fetch_result().to_table()
        assert len(expected) == len(result)
        for ii in range(0, 2):
            assert expected['observationID'][ii] == result['observationID'][ii]
        # load job again
        loaded_job = cadc.load_async_job(job.job_id)
        result = loaded_job.fetch_result().to_table()
        assert len(expected) == len(result)
        for ii in range(0, 2):
            assert expected['observationID'][ii] == result['observationID'][ii]
        # job.delete()  # BUG in CADC

    @pytest.mark.skipif(one_test, reason='One test mode')
    @pytest.mark.skipif(not pyvo_OK, reason='not pyvo_OK')
    def test_list_tables(self):
        cadc = Cadc()
        table_names = cadc.get_tables(only_names=True)
        assert len(table_names) > 20
        assert 'caom2.Observation' in table_names
        assert 'ivoa.ObsCore' in table_names
        assert 'tap_schema.tables' in table_names
        tables = cadc.get_tables()
        assert len(table_names) == len(tables)
        for table in tables:
            assert table.name in table_names

        table = cadc.get_table('caom2.Observation')
        assert 'caom2.Observation' == table.name

    @pytest.mark.skipif(one_test, reason='One test mode')
    @pytest.mark.skipif('CADC_CERT' not in os.environ,
                        reason='Requires real CADC certificate (CADC_CERT '
                               'environment variable)')
    @pytest.mark.skipif(not pyvo_OK, reason='not pyvo_OK')
    def test_list_jobs(self):
        cadc = Cadc()
        cadc.login(certificate_file=os.environ['CADC_CERT'])
        job = cadc.create_async(
            "select top 3 observationID from caom2.Observation where "
            "collection='IRIS' order by observationID")
        job = job.run().wait()
        job.raise_if_error()
        job.fetch_result().to_table()
        jobs = cadc.list_async_jobs()
        assert len(jobs) > 0
        if len(jobs) > 5:
            jobs_subset = cadc.list_async_jobs(last=5)
            assert len(jobs_subset) == 5
