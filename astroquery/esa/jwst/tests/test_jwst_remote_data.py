# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
===============
JWST REMOTE DATA Tests
===============

@author: Javier Espinosa Aranda
@contact: javier.espinosa@sciops.esa.int

European Space Astronomy Centre (ESAC)
European Space Agency (ESA)

Created on 19 aug. 2020


"""

import getpass
import os
import shutil
import tempfile
import unittest
from decimal import Decimal

import astropy.units as u
import mock
import numpy as np
import pytest
import requests
from astropy import units as u
from astropy.coordinates.sky_coordinate import SkyCoord
from astropy.io.votable import parse
from astropy.table import Table
from astropy.table.table import Table
from astropy.tests.helper import remote_data
from astropy.units import Quantity
from astroquery.esa.jwst import JwstClass
from astroquery.ned import Ned
from astroquery.simbad import Simbad
from astroquery.utils import TableList
from astroquery.utils.tap.core import TapPlus
from astroquery.utils.tap.model.filter import Filter
from astroquery.utils.tap.xmlparser import utils
from astroquery.vizier import Vizier


def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)


def create_temp_folder():
    return tempfile.TemporaryDirectory()


def get_license():
    with open(data_path('test_license.txt'), "r") as file:
        user = file.readline()
        password = file.readline()
    return user, password


@remote_data
class TestRemoteData(unittest.TestCase):

    temp_file_vot = '/temp.vot'

    def test_load_tables(self):
        # This test will cover load_tables and load_table methods
        jwst = JwstClass()
        # load_tables
        tables = jwst.load_tables(only_names=True, include_shared_tables=True)
        table_names = []
        for table in (tables):
            table_names.append(table.name)
        # Checking main tables in TAP
        assert 'jwst.main' in table_names
        assert 'jwst.artifact' in table_names
        assert 'jwst.observation' in table_names
        assert 'jwst.observationmember' in table_names
        assert 'tap_schema.tables' in table_names
        assert 'tap_schema.schemas' in table_names

        # load_table
        table = jwst.load_table('jwst.main')
        columns = []
        for column in table.columns:
            columns.append(column.name)
        # Checking columns in table
        assert 'obsid' in columns
        assert 'planeid' in columns
        assert 'calibrationlevel' in columns
        assert 'observationid' in columns
        assert 'target_ra' in columns
        assert 'target_dec' in columns
        print('a')

    def test_launch_job(self):
        # This test will cover launch_job method
        jwst = JwstClass()
        job = jwst.launch_job('SELECT TOP 100 '
                              'instrument_name, observationuri, planeid, '
                              'calibrationlevel, dataproducttype, '
                              'target_ra, target_dec FROM jwst.main ORDER BY '
                              'instrument_name, observationuri',)
        r = job.get_results()
        assert(len(r) == 100)

        # save_results => check if this method works
        # jwst.save_results(job)

        temp_folder = create_temp_folder()
        temp_file = temp_folder.name + self.temp_file_vot
        jwst.launch_job('SELECT TOP 100 '
                        'instrument_name, observationuri, planeid, '
                        'calibrationlevel, dataproducttype, '
                        'target_ra, target_dec FROM jwst.main ORDER BY '
                        'instrument_name, observationuri',
                        output_file=temp_file, dump_to_file=True)
        result = Table.read(temp_file)
        columns = []
        for column in result.columns:
            columns.append(column)
        # Checking columns in table
        assert 'observationuri' in columns
        assert 'planeid' in columns
        assert 'calibrationlevel' in columns
        assert 'instrument_name' in columns
        assert 'target_ra' in columns
        assert 'target_dec' in columns
        temp_folder.cleanup()

    def test_async_job(self):
        # This test will cover launch_job_async, load_async_job,
        # search_async_job, list_async_job, save_results and
        # remove_jobs methods
        jwst = JwstClass()
        # launch_job_async
        job = jwst.launch_job_async(query='select top 100 * from jwst.main',
                                    name='test_job')
        jobid = job.jobid

        # list_async_job
        jobs = jwst.list_async_jobs()
        assert len(jobs) > 0

        # search_async_job
        # jobfilter = Filter()
        # jobfilter.add_filter('job', 'test_job')
        # Not working, something to be solved in TAP class?
        # searched_job = jwst.search_async_jobs(jobfilter)
        # assert job == searched_job

        # load_async_job
        loaded_job = jwst.load_async_job(jobid)
        assert job.jobid == loaded_job.jobid
        assert job.name == loaded_job.name
        for x in range(len(loaded_job.get_results()[0])):
            assert str(job.get_results()[0][x]) == \
                   str(loaded_job.get_results()[0][x])

        # remove_jobs
        jwst.remove_jobs([jobid])
        jobs = jwst.list_async_jobs()
        for job in jobs:
            assert (job.jobid != jobid)

    def test_query_region(self):
        # This test will cover query_region and query_region_async methods
        jwst = JwstClass()
        # query_region
        coord = SkyCoord(ra=53, dec=-27, unit=(u.degree, u.degree),
                         frame='icrs')
        width = u.Quantity(5, u.deg)
        height = u.Quantity(5, u.deg)
        r = jwst.query_region(coordinate=coord, width=width, height=height)
        assert len(r) > 0 and len(r) <= 2000
        # check if the results are in the required box
        for result in r:
            assert Decimal(result['target_ra']) >= 50.5
            assert Decimal(result['target_ra']) <= 55.5
            assert Decimal(result['target_dec']) >= -29.5
            assert Decimal(result['target_dec']) <= -24.5

        # query_region_async
        r_async = jwst.query_region_async(coordinate=coord, width=width,
                                          height=height)
        assert len(r_async) > 0
        # check if the results are in the required box
        for result in r_async:
            assert Decimal(result['target_ra']) >= 50.5
            assert Decimal(result['target_ra']) <= 55.5
            assert Decimal(result['target_dec']) >= -29.5
            assert Decimal(result['target_dec']) <= -24.5

    def test_cone_search(self):
        # This test will cover cone_search and cone_search_async methods
        jwst = JwstClass()
        # cone_search
        coord = SkyCoord(ra=53, dec=-27, unit=(u.degree, u.degree),
                         frame='icrs')
        radius = u.Quantity(5.0, u.deg)
        j = jwst.cone_search(coord, radius)
        r = j.get_results()
        for result in r:
            result_coord = SkyCoord(ra=Decimal(result['target_ra']),
                                    dec=Decimal(result['target_dec']),
                                    unit=(u.degree, u.degree),
                                    frame='icrs')
            sep = coord.separation(result_coord)
            assert sep.deg <= 5

        # cone_search_async
        coord = SkyCoord(ra=45, dec=20, unit=(u.degree, u.degree),
                         frame='icrs')
        radius = u.Quantity(2.0, u.deg)
        j_async = jwst.cone_search_async(coord, radius)
        r_async = j_async.get_results()
        for result in r_async:
            result_coord = SkyCoord(ra=Decimal(result['target_ra']),
                                    dec=Decimal(result['target_dec']),
                                    unit=(u.degree, u.degree),
                                    frame='icrs')
            sep = coord.separation(result_coord)
            assert sep.deg <= 2

    def test_query_target(self):
        # This test will cover query_target and
        # resolve_target_coordinates methods
        jwst = JwstClass()

        # resolve_target_coordinates 1
        target_name = 'M1'
        target_resolver = 'ALL'
        coord = jwst.resolve_target_coordinates(target_name,
                                                target_resolver)
        assert coord.ra.deg
        assert coord.dec.deg

        # query_target 1
        radius = u.Quantity(3, u.deg)
        r = jwst.query_target(target_name=target_name,
                              target_resolver=target_resolver,
                              radius=radius)
        for result in r:
            result_coord = SkyCoord(ra=Decimal(result['target_ra']),
                                    dec=Decimal(result['target_dec']),
                                    unit=(u.degree, u.degree),
                                    frame='icrs')
            sep = coord.separation(result_coord)
            assert sep.deg <= 3

        # resolve_target_coordinates 2
        target_name = 'LMC'
        target_resolver = 'NED'
        coord = jwst.resolve_target_coordinates(target_name,
                                                target_resolver)
        assert coord.ra.deg
        assert coord.dec.deg

        # query_target 2
        width = u.Quantity(5, u.deg)
        height = u.Quantity(5, u.deg)
        r = jwst.query_target(target_name=target_name,
                              target_resolver=target_resolver,
                              width=width,
                              height=height)
        for result in r:
            assert Decimal(result['target_ra']) >= coord.ra.deg - 2.5
            assert Decimal(result['target_ra']) <= coord.ra.deg + 2.5
            assert Decimal(result['target_dec']) >= coord.dec.deg - 2.5
            assert Decimal(result['target_dec']) <= coord.dec.deg + 2.5

    @pytest.mark.skipif(not os.path.exists(data_path('test_license.txt')),
                        reason='Test license is not available')
    def test_login_logout(self):
        # This test will cover login, login_gui and logout methods
        jwst = JwstClass()
        user, password = get_license()
        # login
        with pytest.raises(requests.HTTPError) as err:
            jwst.login(user='test', password='test')
        assert "HTTP Status 401 – Unauthorized" in err.value.args[0]

        jwst.login(user=user, password=password)

        # logout
        jwst.logout()

        print('a')

    def test_get_products(self):
        # This test will cover get_product_list, get_related_observation,
        # get_product and get_obs_products methods
        jwst = JwstClass()

        # get_product_list
        observation_id = 'jw00777011001_02104_00001_nrcblong'
        product_list = jwst.get_product_list(observation_id=observation_id)
        assert(len(product_list) > 0)

        # get_related_observation
        rel_obs = jwst.get_related_observations(observation_id=observation_id)
        assert(len(rel_obs) > 0)

        # get_product
        query = "select a.artifactid, a.uri from jwst.artifact a, jwst.plane "\
                "p where p.planeid=a.planeid and "\
                "p.obsid='00000000-0000-0000-9c08-f5be8f3df805'"
        job = jwst.launch_job(query)
        job.get_results()
        artifact_id = '00000000-0000-0000-b8af-4b8f29f2b0d6'
        file_name = 'jw00617-o113_t001_nircam_f277w_cat.ecsv'
        output_file = jwst.get_product(file_name=file_name)
        assert os.path.exists(output_file)
        os.remove(output_file)
        output_file = jwst.get_product(artifact_id=artifact_id)
        assert os.path.exists(output_file)
        os.remove(output_file)

        # get_obs_products
        observation_id = 'jw00617-o113_t001_nircam_f277w'
        temp_folder = create_temp_folder()
        jwst.get_obs_products(observation_id=observation_id,
                              cal_level='ALL',
                              product_type='science',
                              output_file=temp_folder.name + '/test.tar')
        assert os.path.exists(temp_folder.name)
        assert os.path.exists(temp_folder.name + '/test.tar')
        assert os.path.exists(temp_folder.name + '/jw00617')
        assert os.path.exists(temp_folder.name + '/jw00617/level_3')
        temp_folder.cleanup()

    @pytest.mark.skip
    def decode(self, key, string):
        encoded_chars = []
        for i in range(len(string)):
            key_c = key[i % len(key)]
            encoded_c = chr((ord(string[i]) - ord(key_c) + 256) % 256)
            encoded_chars.append(encoded_c)
        encoded_string = ''.join(encoded_chars)
        return encoded_string


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
