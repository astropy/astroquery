# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
=================
eHST Remote Tests
=================

European Space Astronomy Centre (ESAC)
European Space Agency (ESA)

"""

import tempfile

import os
import numpy as np

import pytest
from astroquery.esa.hubble import ESAHubble
from astropy import coordinates

esa_hubble = ESAHubble()


def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)


def create_temp_folder():
    return tempfile.TemporaryDirectory()


def remove_last_job():
    jobs = esa_hubble._tap.list_async_jobs()
    if len(jobs) > 0:
        esa_hubble._tap.remove_jobs(jobs[-1].jobid)


@pytest.mark.remote_data
class TestEsaHubbleRemoteData:
    obs_query = "select top 2050 a.observation_id from ehst.archive a"

    top_obs_query = "select top 100 a.observation_id from ehst.archive a"

    hst_query = "select top 50 a.observation_id from ehst.archive " \
                "a where a.collection='HST'"

    top_artifact_query = "select a.artifact_id, a.observation_id from ehst.artifact a " \
                         "where a.observation_id = 'iexn02e9q'"

    temp_folder = create_temp_folder()
    temp_folder_for_fits = create_temp_folder()

    def test_query_tap_async(self):
        result = esa_hubble.query_tap(query=self.top_obs_query, async_job=True)
        assert len(result) > 10
        assert "observation_id" in result.keys()
        remove_last_job()

    def test_download_product(self):
        result = esa_hubble.query_tap(query=self.hst_query)
        observation_id = np.random.choice((result['observation_id']))
        temp_file = os.path.join(self.temp_folder.name, observation_id)
        esa_hubble.download_product(observation_id=observation_id,
                                    filename=temp_file)
        possible_values = [os.path.exists(temp_file + '.jpg'),
                           os.path.exists(temp_file + '.zip'),
                           os.path.exists(temp_file + 'fits.gz')]
        assert any([os.path.exists(f) for f in possible_values])

    def test_get_artifact(self):
        result = esa_hubble.query_tap(query=self.top_artifact_query)
        assert "artifact_id" in result.keys()
        artifact_id = np.random.choice(result["artifact_id"])
        temp_file = os.path.join(self.temp_folder.name, artifact_id)
        esa_hubble.get_artifact(artifact_id=artifact_id, filename=temp_file)
        possible_values = [os.path.exists(temp_file),
                           os.path.exists(temp_file + '.zip'),
                           os.path.exists(temp_file + 'fits.gz')]
        assert any([os.path.exists(f) for f in possible_values])

    def test_cone_search(self):
        c = coordinates.SkyCoord("00h42m44.51s +41d16m08.45s", frame='icrs')
        compressed_temp_file = os.path.join(self.temp_folder.name, "cone_search_m31_5.vot.gz")
        # open & extracting the file
        table = esa_hubble.cone_search(coordinates=c, radius=7, filename=compressed_temp_file, verbose=True)
        assert 'observation_id' in table.columns
        assert len(table) > 0
        remove_last_job()

    # tests for get_related_members
    def test_hst_composite_to_hst_simple(self):
        result = esa_hubble.get_member_observations('jdrz0c010')
        assert result == ['jdrz0cjxq', 'jdrz0cjyq']

    def test_hst_simple_to_hst_composite(self):
        result = esa_hubble.get_member_observations(observation_id='hst_12069_b2_acs_wfc_f775w_jbf6b2')
        assert 'hst_12069_b2_acs_wfc_f775w_jbf6b2cf' in result

    def test_hap_composite_to_hap_simple(self):
        result = esa_hubble.get_member_observations(observation_id='hst_15446_4v_acs_wfc_f606w_jdrz4v')
        assert result == ['hst_15446_4v_acs_wfc_f606w_jdrz4vkv', 'hst_15446_4v_acs_wfc_f606w_jdrz4vkw']

    def test_hap_simple_to_hap_composite(self):
        result = esa_hubble.get_member_observations(observation_id='hst_16316_71_acs_sbc_f150lp_jec071i9')
        assert result == ['hst_16316_71_acs_sbc_f150lp_jec071']

    def test_hap_simple_to_hst_simple(self):
        result = esa_hubble.get_hap_hst_link(observation_id='hst_16316_71_acs_sbc_f150lp_jec071i9')
        assert result == ['jec071i9q']

    def test_hst_simple_to_hap_simple(self):
        result = esa_hubble.get_hap_hst_link(observation_id='jec071i9q')
        assert result == ['hst_16316_71_acs_sbc_f150lp_jec071i9']

    def test_query_target(self):
        compressed_temp_file = os.path.join(self.temp_folder.name, "m31_query.xml.gz")
        table = esa_hubble.query_target(name="m3", filename=compressed_temp_file)
        assert 'observation_id' in table.columns

    def test_retrieve_observations_from_program(self):
        results = esa_hubble.get_observations_from_program(program=5773)
        assert 'u2lx0507t' in results['observation_id']

    def test_retrieve_fits_from_program(self):
        esa_hubble.download_files_from_program(program=5410,
                                               instrument_name='WFPC2',
                                               obs_collection='HLA',
                                               filters=['F814W/F450W'],
                                               folder=str(self.temp_folder_for_fits.name))
        assert len(os.listdir(self.temp_folder_for_fits.name)) > 0
