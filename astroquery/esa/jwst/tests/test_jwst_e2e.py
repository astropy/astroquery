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

import os
import tempfile
import unittest

import pytest
import requests
from astropy import units as u
from astropy.coordinates.sky_coordinate import SkyCoord
from astropy.table.table import Table
from astropy.tests.helper import remote_data

from astroquery.esa.jwst import JwstClass
from astroquery.utils.tap import TapPlus


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
class TestEndToEnd(unittest.TestCase):

    temp_file_vot = '/temp.vot'
    coord = SkyCoord(ra=98.831495,
                     dec=-66.81864444,
                     unit=(u.degree, u.degree),
                     frame='icrs')
    radius = u.Quantity(0.001, u.deg)
    default_columns = ['dist', 'observationid', 'calibrationlevel', 'public',
                       'dataproducttype', 'instrument_name',
                       'energy_bandpassname', 'target_name', 'target_ra',
                       'target_dec', 'position_bounds_center',
                       'position_bounds_spoly']
    all_columns = ['dist', 'public', 'algorithm_name', 'calibrationlevel',
                   'collection', 'parenturi', 'creatorid',
                   'dataproducttype', 'energy_bandpassname',
                   'energy_bounds', 'energy_bounds_lower',
                   'energy_bounds_upper', 'energy_bounds_width',
                   'energy_dimension', 'energy_energybands',
                   'energy_freqsamplesize', 'energy_freqwidth',
                   'energy_resolvingpower', 'energy_restwav',
                   'energy_samplesize', 'energy_transition_species',
                   'energy_transition_transition', 'environment_ambienttemp',
                   'environment_elevation', 'environment_humidity',
                   'environment_photometric', 'environment_seeing',
                   'environment_tau', 'environment_wavelengthtau',
                   'instrument_keywords', 'instrument_name', 'intent',
                   'max_cal_level', 'members', 'metrics_background',
                   'metrics_backgroundstddev', 'metrics_fluxdensitylimit',
                   'metrics_maglimit', 'metrics_sourcenumberdensity',
                   'obs_accmetachecksum', 'obs_lastmodified',
                   'obs_maxlastmodified', 'obs_metachecksum',
                   'obs_metarelease', 'observationid', 'observationuri',
                   'obsid', 'plane_accmetachecksum', 'plane_datarelease',
                   'plane_lastmodified', 'plane_maxlastmodified',
                   'plane_metachecksum', 'plane_metarelease', 'planeid',
                   'planeuri', 'polarization_dimension', 'polarization_states',
                   'position_bounds_area', 'position_bounds_center',
                   'position_bounds_size', 'position_bounds_spoly',
                   'position_dimension_naxis1', 'position_dimension_naxis2',
                   'position_resolution', 'position_samplesize',
                   'position_timedependent', 'productid', 'proposal_id',
                   'proposal_keywords', 'proposal_pi', 'proposal_project',
                   'proposal_title', 'provenance_inputs',
                   'provenance_keywords', 'provenance_lastexecuted',
                   'provenance_name', 'provenance_producer',
                   'provenance_project', 'provenance_reference',
                   'provenance_runid', 'provenance_version', 'publisherid',
                   'quality_flag', 'requirements_flag', 'sequencenumber',
                   'target_dec', 'target_keywords', 'target_moving',
                   'target_name', 'target_ra', 'target_redshift',
                   'target_standard', 'target_type', 'targetposition_coordsys',
                   'targetposition_equinox', 'telescope_geolocationx',
                   'telescope_geolocationy', 'telescope_geolocationz',
                   'telescope_keywords', 'telescope_name', 'time_bounds',
                   'time_bounds_lower', 'time_bounds_upper',
                   'time_bounds_width', 'time_dimension', 'time_exposure',
                   'time_resolution', 'time_samplesize', 'type', 'typecode']

    def test_TAP_connection(self):
        tap = TapPlus(url="http://jwstdummytap.com",
                      data_context='data')
        jwst = JwstClass(tap_plus_handler=tap)
        with pytest.raises(requests.HTTPError) as err:
            jwst.cone_search_async(self.coord, self.radius)
        assert "404" in err.value.args[0]
        tap = TapPlus(url="http://jwstdummytap.com",
                      data_context='data')
        jwst = JwstClass(tap_plus_handler=tap)
        jwst.cone_search_async(self.coord, self.radius)

    def test_cone_search_async_no_filters(self):
        jwst = JwstClass()
        j = jwst.cone_search_async(self.coord, self.radius)
        table = j.get_results()
        assert(table[0][0] == 5.88302107189034e-06)
        assert(table[0][1].decode("UTF-8") == "jw00617198001_02102_"
               "00001_nrcb4")
        for colnames in table.colnames:
            assert(colnames in self.default_columns)

    def test_cone_search_async_show_all_columns(self):
        jwst = JwstClass()
        j = jwst.cone_search_async(self.coord,
                                   self.radius,
                                   show_all_columns=True)
        table = j.get_results()
        for colnames in table.colnames:
            assert(colnames in self.all_columns)
        for result in table['observationid', 'calibrationlevel'][0:5]:
            assert "jw" in str(result[0])
            assert result[1] <= 3

    def test_cone_search_async_with_proposal_id(self):
        jwst = JwstClass()
        j = jwst.cone_search_async(self.coord,
                                   self.radius,
                                   proposal_id='00617',
                                   show_all_columns=True)
        table = j.get_results()
        for colnames in table.colnames:
            assert(colnames in self.all_columns)
        assert "dist" in table.colnames
        for result in table['observationid', 'proposal_id'][0:5]:
            assert "00617" in str(result[1])

    def test_cone_search_async_with_proposal_cal_instr_and_output(self):
        jwst = JwstClass()
        temp_folder = create_temp_folder()
        output_file = temp_folder.name + '/test_csv.vot'
        j = jwst.cone_search_async(self.coord, self.radius,
                                   proposal_id='00617',
                                   cal_level=3,
                                   show_all_columns=True,
                                   prod_type='image',
                                   instrument_name='NIRCAM',
                                   output_file=output_file,
                                   dump_to_file=True)
        table = j.get_results()
        assert os.path.exists(output_file)
        table.sort(['observationid'])
        loaded_result = Table.read(output_file)
        loaded_result.sort(['observationid'])
        for i in range(0, 6):
            for j in range(0, len(table[i])):
                assert(str(table[i][j]) == str(loaded_result[i][j]))
        temp_folder.cleanup()

    def test_cone_search_async_with_options_proposal_and_obsid(self):
        jwst = JwstClass()
        j = jwst.cone_search_async(self.coord, self.radius,
                                   proposal_id='00617',
                                   observation_id='jw00617-o023_t001_nircam_'
                                   'f090w-sub160',
                                   instrument_name='NIRCAM',
                                   show_all_columns=True)
        table = j.get_results()
        assert(len(table) > 0)
        observation_id_index = table.colnames.index('observationid')
        proposal_id_index = table.colnames.index('proposal_id')
        instrument_index = table.colnames.index('instrument_name')
        assert(table[0][proposal_id_index].decode('UTF-8') == '00617')
        assert(table[0][observation_id_index].decode('UTF-8') == 'jw00617-'
               'o023_t001_nircam_f090w-sub160')
        assert(table[0][instrument_index].decode('UTF-8') == 'NIRCAM')

    def test_filtering_by_filter_cone_search_saving_votable(self):
        jwst = JwstClass()
        temp_folder = create_temp_folder()
        output_file = temp_folder.name + '/test.vot'
        j = jwst.cone_search(self.coord, self.radius, cal_level=3,
                             filter_name='F090W', output_file=output_file,
                             dump_to_file=True, output_format='votable',
                             only_public=True)
        table = j.get_results()
        assert os.path.exists(output_file)
        assert(len(table) > 0)
        loaded_result = Table.read(output_file)
        loaded_result.sort(['observationid'])
        table.sort(['observationid'])
        for i in range(0, len(table)):
            for j in range(0, len(table[i])):
                assert(str(table[i][j]) == str(loaded_result[i][j]))
        temp_folder.cleanup()

    def test_query_region(self):
        jwst = JwstClass()
        width = u.Quantity(3, u.deg)
        height = u.Quantity(3, u.deg)
        r = jwst.query_region(coordinate=self.coord,
                              width=width,
                              height=height,
                              show_all_columns=True,
                              only_public=True)
        assert(len(r) > 0)
        r.sort('observationid')
        index_of_observation_id = r.colnames.index('observationid')
        hasObs = False
        for result in r:
            hasObs = result[index_of_observation_id].decode('UTF-8') == 'jw00'\
                     '617-o112_t001_nircam_f090w'
            if (hasObs):
                break
        assert(hasObs)

    def test_product_list_with_observation_id(self):
        jwst = JwstClass()
        product_list = jwst.get_product_list('jw01054002001_xx102_00001_'
                                             'miri', cal_level=-1)
        assert(len(product_list) == 0)
        product_list = jwst.get_product_list('jw00617-o023_t001_nircam_'
                                             'f090w-sub160')
        uri_index = product_list.colnames.index('uri')
        cal_level_index = product_list.colnames.index('calibrationlevel')
        has_level_one = False
        has_level_two = False
        has_level_three = False
        assert(len(product_list) > 0)
        for product in product_list:
            assert('jw00617' in product[uri_index].decode('UTF-8'))
            has_level_one = has_level_one or product[cal_level_index] == 1
            has_level_two = has_level_two or product[cal_level_index] == 2
            has_level_three = has_level_three or product[cal_level_index] == 3
        assert(has_level_one and has_level_two and has_level_three)

    def test_get_product(self):
        jwst = JwstClass()
        product1 = jwst.get_product(artifact_id=None,
                                    file_name='jw00626-o025_t007_nirspec_f1'
                                    '70lp-g235h-s1600a1-sub2048_x1dints.fits')
        assert os.path.exists(product1)
        product2 = jwst.get_product(artifact_id='00000000-0000-0000-9d16-'
                                    '5ee9bfba9d2c', file_name=None)
        assert os.path.exists(product2)
        assert(product1 == product2)

    def test_get_obs_product(self):
        jwst = JwstClass()
        # All levels
        products = jwst.get_obs_products(observation_id='jw00632-o014_'
                                         't002_nircam_f212n-wlm8-nrca4',
                                         cal_level='ALL')
        has_level_one = False
        has_level_two = False
        has_level_three = False
        for product in products:
            assert os.path.exists(product)
            has_level_one = has_level_one or 'level_1' in product
            has_level_two = has_level_two or 'level_2' in product
            has_level_three = has_level_three or 'level_3' in product
        assert(has_level_one and has_level_two and has_level_three)
        # Level 3
        products = jwst.get_obs_products(observation_id='jw00626-o025_t007_ni'
                                         'rspec_f170lp-g235h-s1600a1-sub2048',
                                         cal_level=3)
        has_level_three = False
        for product in products:
            assert os.path.exists(product)
            has_level_three = has_level_three or 'level_3' in product
        assert has_level_three
        # Level 2
        products = jwst.get_obs_products(observation_id='jw00643025001_'
                                         '02101_00001_nrs1', cal_level=2)
        for product in products:
            assert os.path.exists(product)
        # Level 1
        products = jwst.get_obs_products(observation_id='jw00643025001_'
                                         '02101_00001_nrs1', cal_level=1)
        for product in products:
            assert os.path.exists(product)
        # Level -1
        with pytest.raises(ValueError) as err:
            jwst.get_obs_products(observation_id='jw80800056001_xx11d_'
                                  '00021_miri', cal_level=-1)
        assert "Cannot retrieve products" in err.value.args[0]

    def test_get_related_observations(self):
        jwst = JwstClass()
        product_list = jwst.get_related_observations('jw00617023001_02102_'
                                                     '00001_nrcb4')
        assert('jw00617-o023_t001_nircam_f090w-sub160' in product_list)
        product_list = jwst.get_related_observations('jw00777011001_02104_'
                                                     '00001_nrcblong')
        assert('jw00777-c1005_t005_nircam_f277w-sub160' in product_list)

    def test_query_target_name(self):
        jwst = JwstClass()
        width = u.Quantity(3, u.deg)
        height = u.Quantity(3, u.deg)
        target_name = 'LMC'
        target_resolver = 'SIMBAD'
        t = jwst.query_target(target_name,
                              target_resolver,
                              width,
                              height,
                              filter_name='F277W',
                              cal_level=1)
        filter_index = t.colnames.index('energy_bandpassname')
        assert('F277W' in t[0][filter_index].decode('UTF-8'))

        t = jwst.query_target(target_name,
                              target_resolver,
                              width, height,
                              instrument_name='NIRCAM',
                              observation_id='jw00322001003_02101_'
                              '00001_nrca3',
                              proposal_id='00322',
                              show_all_columns=True)
        obs_index = t.colnames.index('observationid')
        prop_index = t.colnames.index('proposal_id')
        inst_index = t.colnames.index('instrument_name')
        assert('jw00322001003_02101_'
               '00001_nrca3' in t[0][obs_index].decode('UTF-8'))
        assert('00322' in t[0][prop_index].decode('UTF-8'))
        assert('NIRCAM' in t[0][inst_index].decode('UTF-8'))


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
