# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""

@author: Javier Espinosa
@contact: javier.espinosa@sciops.esa.int

European Space Astronomy Centre (ESAC)
European Space Agency (ESA)

Created on 13 Jan. 2021


"""
import tempfile

import os

import pytest
from astroquery.esa.hubble import ESAHubble
from astropy import coordinates
import random

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
    obs_query = "select top 2050 o.observation_id from ehst.observation o"

    top_obs_query = "select top 100 o.observation_id from ehst.observation o"

    hst_query = "select top 50 o.observation_id from ehst.observation " \
                "o where o.collection='HST'"

    top_artifact_query = "select top 50 a.artifact_id, a.observation_id " \
                         " from ehst.artifact a"

    temp_folder = create_temp_folder()

    def test_query_hst_tap_async(self):
        result = esa_hubble.query_hst_tap(self.top_obs_query, async_job=True)
        assert len(result) > 10
        assert "observation_id" in result.keys()
        remove_last_job()

    def test_download_product(self):
        result = esa_hubble.query_hst_tap(self.hst_query)
        observation_id = random.choice(result['observation_id'])
        temp_file = self.temp_folder.name + "/" + observation_id + ".tar"
        esa_hubble.download_product(observation_id=observation_id,
                                    filename=temp_file)
        assert os.path.exists(temp_file)

    def test_get_artifact(self):
        result = esa_hubble.query_hst_tap(self.top_artifact_query)
        assert "artifact_id" in result.keys()
        artifact_id = random.choice(result["artifact_id"])
        temp_file = self.temp_folder.name + "/" + artifact_id + ".gz"
        esa_hubble.get_artifact(artifact_id, temp_file)
        assert os.path.exists(temp_file)

    def test_cone_search(self):
        esa_hubble = ESAHubble()
        c = coordinates.SkyCoord("00h42m44.51s +41d16m08.45s", frame='icrs')
        temp_file = self.temp_folder.name + "/cone_search_m31_5.vot"
        table = esa_hubble.cone_search(c, 7, temp_file, verbose=True)
        assert os.path.exists(temp_file)
        assert 'observation_id' in table.columns
        assert len(table) > 0
        remove_last_job()

    # tests for get_related_members
    def test_hst_composite_to_hst_simple(self):
        esa_hubble = ESAHubble()
        result = esa_hubble.get_member_observations('jdrz0c010')
        assert result == ['jdrz0cjxq', 'jdrz0cjyq']

    def test_hst_simple_to_hst_composite(self):
        esa_hubble = ESAHubble()
        result = esa_hubble.get_member_observations('jdrz0cjxq')
        assert result == ['jdrz0c010']

    def test_hap_composite_to_hap_simple(self):
        esa_hubble = ESAHubble()
        result = esa_hubble.get_member_observations('hst_15446_4v_acs_wfc_f606w_jdrz4v')
        assert result == ['hst_15446_4v_acs_wfc_f606w_jdrz4vkv', 'hst_15446_4v_acs_wfc_f606w_jdrz4vkw']

    def test_hap_simple_to_hap_composite(self):
        esa_hubble = ESAHubble()
        result = esa_hubble.get_member_observations('hst_16316_71_acs_sbc_f150lp_jec071i9')
        assert result == ['hst_16316_71_acs_sbc_f150lp_jec071']

    def test_hap_simple_to_hst_simple(self):
        esa_hubble = ESAHubble()
        result = esa_hubble.get_hap_hst_link('hst_16316_71_acs_sbc_f150lp_jec071i9')
        assert result == ['jec071i9q']

    def test_hst_simple_to_hap_simple(self):
        esa_hubble = ESAHubble()
        result = esa_hubble.get_hap_hst_link('jec071i9q')
        assert result == ['hst_16316_71_acs_sbc_f150lp_jec071i9']

    def test_query_target(self):
        temp_file = self.temp_folder.name + "/" + "m31_query.xml"
        table = esa_hubble.query_target(name="m3", filename=temp_file)
        assert os.path.exists(temp_file)
        assert 'observation_id' in table.columns
