# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
============
CHEOPS tests
============

European Space Astronomy Centre (ESAC)
European Space Agency (ESA)

"""
import os

import pytest
from astropy.coordinates import SkyCoord
from astropy.table import Table
from unittest.mock import Mock, patch, PropertyMock

from astroquery.esa.emds.cheops import conf
from astroquery.esa.emds.cheops import CheopsClass


class TestCheopsTap:

    def test_get_tables(self):
        table_set = PropertyMock()
        table_set.keys.return_value = ['cheops.observation_request']

        t1 = Mock()
        t1.name = 'cheops.observation_request'
        table_set.values.return_value = [t1]

        with patch('astroquery.esa.utils.utils.pyvo.dal.TAPService', autospec=True) as tap_mock:
            tap_mock.return_value.tables = table_set
            cheops = CheopsClass()
            assert len(cheops.get_tables(only_names=True)) == 1
            assert len(cheops.get_tables()) == 1

    @patch('astroquery.esa.utils.utils.pyvo.dal.TAPService.capabilities', [])
    @patch('astropy.table.Table.write')
    @patch('astroquery.esa.utils.utils.pyvo.dal.TAPService.search')
    def test_query_tap_sync(self, search_mock, table_write_mock):
        # Simulate pyvo search() result with a .to_table() method
        mock_result = Mock()
        mock_result.to_table.return_value = Table({'a': [1]})
        search_mock.return_value = mock_result

        cheops = CheopsClass()
        cheops.query_tap(query='SELECT 1', output_file='dummy.vot')

        search_mock.assert_called_once_with('SELECT 1')
        table_write_mock.assert_called()  # called when writing output_file

    @patch('astroquery.esa.utils.utils.pyvo.dal.TAPService.capabilities', [])
    @patch('astroquery.esa.utils.utils.pyvo.dal.TAPService.run_async')
    def test_query_tap_async(self, run_async_mock):
        mock_job = Mock()
        mock_job.to_table.return_value = Table({'a': [1]})
        run_async_mock.return_value = mock_job

        cheops = CheopsClass()
        cheops.query_tap(query='SELECT 1', async_job=True)

        run_async_mock.assert_called_once()

    @patch('astroquery.esa.utils.utils.pyvo.dal.TAPService.capabilities', [])
    @patch('astroquery.esa.emds.cheops.core.CheopsClass.query_table')
    def test_get_observations(self, query_table_mock):
        cheops = CheopsClass()
        cheops.get_observations(coordinates='81.1238 17.4175')

        print(query_table_mock)

        query_table_mock.assert_called_once_with(table_name='cheops.observation_request', columns=None,
                                                 custom_filters='1=CONTAINS(POINT(\'ICRS\', ra, dec),'
                                                                'CIRCLE(\'ICRS\', 81.1238, 17.4175, 0.01))',
                                                 get_metadata=False, async_job=False, output_file=None,
                                                 output_format='votable')

    @patch('astroquery.esa.utils.utils.pyvo.dal.TAPService.capabilities', [])
    @patch('astroquery.esa.emds.core.esautils.resolve_target')
    @patch('astroquery.esa.emds.cheops.core.CheopsClass.query_table')
    def test_get_observations_target_name(
            self, query_table_mock, resolve_target_mock
    ):
        resolve_target_mock.return_value = SkyCoord(ra=12, dec=13, unit='deg')

        cheops = CheopsClass()
        cheops.get_observations(target_name='M31', radius=2.2)

        query_table_mock.assert_called_once()
        _, kwargs = query_table_mock.call_args

        assert kwargs['table_name'] == 'cheops.observation_request'
        assert kwargs['async_job'] is False

        cone = kwargs['custom_filters']
        assert cone is not None
        assert 'CONTAINS' in cone
        assert 'CIRCLE' in cone
        assert '12.0' in cone
        assert '13.0' in cone

    @patch('astroquery.esa.utils.utils.pyvo.dal.TAPService.capabilities', [])
    @patch('astroquery.esa.emds.cheops.core.CheopsClass.query_table')
    def test_get_observations_with_columns(self, query_table_mock):
        cheops = CheopsClass()
        cheops.get_observations(columns=['obs_cat', 'ra', 'dec'])

        query_table_mock.assert_called_once_with(table_name='cheops.observation_request',
                                                 columns=['obs_cat', 'ra', 'dec'],
                                                 custom_filters=None, get_metadata=False, async_job=False,
                                                 output_file=None,
                                                 output_format='votable')

    def test_get_observations_error_target_and_coordinates(self):
        cheops = CheopsClass()

        with pytest.raises(TypeError) as err:
            cheops.get_observations(target_name='M31', coordinates='12 13')

        assert 'Please use only target or coordinates' in str(err.value)

    @patch('astroquery.esa.utils.utils.pyvo.dal.TAPService.capabilities', [])
    @patch('astroquery.esa.emds.cheops.core.CheopsClass.query_table')
    def test_get_observations_with_filters(self, query_table_mock):
        cheops = CheopsClass()
        cheops.get_observations(observation_request_id=3000240001)

        query_table_mock.assert_called_once()

        # Check core arguments
        _, kwargs = query_table_mock.call_args
        assert kwargs['table_name'] == 'cheops.observation_request'
        assert kwargs['columns'] is None
        assert kwargs['custom_filters'] is None
        assert kwargs['get_metadata'] is False
        assert kwargs['async_job'] is False
        assert kwargs['output_file'] is None
        assert kwargs['output_format'] == 'votable'

        # Check that filters are forwarded
        assert kwargs['observation_request_id'] == 3000240001

    @patch('astroquery.esa.utils.utils.pyvo.dal.TAPService.capabilities', [])
    @patch.object(CheopsClass, '_get_programme_from_pi')
    def test_get_program_by_pi_name(self, get_from_pi_mock):
        expected = Table({'programme_key': ['PR010001']})
        get_from_pi_mock.return_value = expected

        cheops = CheopsClass()
        result = cheops.get_program(pi_name='pi_name')

        assert result is expected
        get_from_pi_mock.assert_called_once_with('pi_name')

    @patch('astroquery.esa.utils.utils.pyvo.dal.TAPService.capabilities', [])
    @patch.object(CheopsClass, '_get_programme_from_key_or_title')
    def test_get_program_by_programme_key(self, get_from_key_or_title_mock):
        expected = Table({'programme_key': ['PR010001']})
        get_from_key_or_title_mock.return_value = expected

        cheops = CheopsClass()
        result = cheops.get_program(programme_key='PR010001')

        assert result is expected
        get_from_key_or_title_mock.assert_called_once_with(programme_key='PR010001')

    @patch('astroquery.esa.utils.utils.pyvo.dal.TAPService.capabilities', [])
    @patch.object(CheopsClass, '_get_programme_from_key_or_title')
    def test_get_program_by_title(self, get_from_key_or_title_mock):
        expected = Table({'programme_key': ['PR010001']})
        get_from_key_or_title_mock.return_value = expected

        cheops = CheopsClass()
        result = cheops.get_program(title='Exoplanets')

        assert result is expected
        get_from_key_or_title_mock.assert_called_once_with(title='%Exoplanets%')

    @patch('astroquery.esa.utils.utils.pyvo.dal.TAPService.capabilities', [])
    @patch.object(CheopsClass, 'query_table')
    def test_get_programme_from_pi(self, query_table_mock):
        query_table_mock.side_effect = [Table({'pi_oid': [10]}),
                                        Table({
                                            'type': [1, 2],
                                            'id': [23, 7],
                                            'programme_oid': [1001, 1002]
                                        }),
                                        Table({
                                            'programme_key': ['PR010023', 'PR020007'],
                                            'title': ['Programme A', 'Programme B'],
                                            'abstract': ['Abstract A', 'Abstract B']
                                        })
                                        ]

        cheops = CheopsClass()
        result = cheops._get_programme_from_pi('PI 1')

        assert len(result) == 2
        assert list(result['programme_key']) == ['PR010023', 'PR020007']
        assert list(result['programme_oid']) == [1001, 1002]

        assert query_table_mock.call_count == 3

        # Verify the call to the subsequent tables
        query_table_mock.assert_any_call(table_name=conf.CHEOPS_PI_TABLE, columns=['pi_oid'], name='%PI 1%',
                                         verbose=False)

        query_table_mock.assert_any_call(conf.CHEOPS_PROGRAMME_TABLE, pi_oid=10, verbose=False)

    @patch('astroquery.esa.utils.utils.pyvo.dal.TAPService.capabilities', [])
    @patch.object(CheopsClass, 'query_table')
    def test_get_programme_from_key(self, query_table_mock):
        query_table_mock.side_effect = [
            Table({'programme_key': ['PR010023', 'PR020007'], 'title': ['Programme A', 'Programme B'],
                   'abstract': ['Abstract A', 'Abstract B']}),
            Table({'pi_oid': [10], 'programme_oid': [1001]}),
            Table({'name': ['PI 1']}),
            Table({'pi_oid': [20], 'programme_oid': [1002]}),
            Table({'name': ['PI 2']})
        ]

        cheops = CheopsClass()
        result = cheops._get_programme_from_key_or_title(programme_key=['PR010023', 'PR020007'])

        # Check returned programme information
        assert list(result['programme_key']) == ['PR010023', 'PR020007']

        assert list(result['pi_name']) == ['PI 1', 'PI 2']

        assert list(result['programme_oid']) == [1001, 1002]

        # Initial query + 2 queries per programme
        assert query_table_mock.call_count == 5

        # Query programme information
        args, kwargs = query_table_mock.call_args_list[0]
        assert kwargs['table_name'] == conf.CHEOPS_PROGRAMME_INFO_TABLE
        assert kwargs['columns'] == ['programme_key', 'title', 'abstract']
        assert kwargs['programme_key'] == ['PR010023', 'PR020007']
        assert kwargs['verbose'] is False

        # Test programme info to programme table
        args, kwargs = query_table_mock.call_args_list[1]
        assert args[0] == conf.CHEOPS_PROGRAMME_TABLE
        assert kwargs['columns'] == ['pi_oid', 'programme_oid']
        assert kwargs['type'] == 1
        assert kwargs['id'] == 23
        assert kwargs['verbose'] is False

        # Test programme info to PI table
        args, kwargs = query_table_mock.call_args_list[2]
        assert args[0] == conf.CHEOPS_PI_TABLE
        assert kwargs['columns'] == ['name']
        assert kwargs['pi_oid'] == 10
        assert kwargs['verbose'] is False

    @patch('astroquery.esa.utils.utils.pyvo.dal.TAPService.capabilities', [])
    @patch.object(CheopsClass, 'query_table')
    def test_get_programme_from_title(self, query_table_mock):
        query_table_mock.side_effect = [
            Table({'programme_key': ['PR010023'], 'title': ['Planet transit'], 'abstract': ['Abstract']}),
            Table({'pi_oid': [10], 'programme_oid': [1001]}),
            Table({'name': ['PI 1']})
        ]

        cheops = CheopsClass()
        result = cheops._get_programme_from_key_or_title(title='%transit%')

        assert result['programme_key'][0] == 'PR010023'
        assert result['pi_name'][0] == 'PI 1'
        assert result['programme_oid'][0] == 1001

    @patch('astroquery.esa.utils.utils.pyvo.dal.TAPService.capabilities', [])
    @patch.object(CheopsClass, 'get_observations')
    @patch.object(CheopsClass, 'get_program')
    def test_get_observations_from_program(self, get_program_mock, get_observations_mock):
        get_program_mock.return_value = Table({'programme_oid': [1001]})

        cheops = CheopsClass()
        result = cheops.get_observations_from_program(programme_key='PR010023')

        assert result is get_observations_mock.return_value
        get_program_mock.assert_called_once_with('PR010023', None, None)
        get_observations_mock.assert_called_once_with(programme_oid=1001)

    @patch('astroquery.esa.utils.utils.pyvo.dal.TAPService.capabilities', [])
    @patch.object(CheopsClass, 'query_table')
    def test_get_visit_from_observation_oid(self, query_table_mock):
        cheops = CheopsClass()

        result = cheops.get_visit_from_observation(1234)

        assert result is query_table_mock.return_value
        query_table_mock.assert_called_once_with(conf.CHEOPS_VISIT_TABLE, observation_request_oid=1234, verbose=False)

    @patch('astroquery.esa.utils.utils.pyvo.dal.TAPService.capabilities', [])
    @patch.object(CheopsClass, 'query_table')
    def test_get_visit_from_observation_row(self, query_table_mock):
        observations = Table({'observation_request_oid': ['OBS-123']})
        observation = observations[0]

        cheops = CheopsClass()
        result = cheops.get_visit_from_observation(observation)

        assert result is query_table_mock.return_value
        query_table_mock.assert_called_once_with(conf.CHEOPS_VISIT_TABLE, observation_request_oid='OBS-123',
                                                 verbose=False)

    @patch('astroquery.esa.utils.utils.pyvo.dal.TAPService.capabilities', [])
    def test_get_visit_from_observation_rejects_invalid_type(self):
        cheops = CheopsClass()

        with pytest.raises(TypeError, match='Please use either the value of the row'):
            cheops.get_visit_from_observation(observation='abcd')

    @patch('astroquery.esa.utils.utils.pyvo.dal.TAPService.capabilities', [])
    @patch.object(CheopsClass, 'query_table')
    @patch.object(CheopsClass, 'get_observations')
    def test_get_products_from_targets_or_coordinates(self, get_observations_mock, query_table_mock):
        get_observations_mock.return_value = Table({'observation_request_oid': [1111, 2222]})

        visits_1 = Table({'visit_id': [1234, 5678]})
        visits_2 = Table({'visit_id': [5678, 9012]})

        products_1 = Table({'filename': ['product-1.fits']})
        products_2 = Table({'filename': ['product-2.fits']})

        products_3 = Table({'filename': ['product-3.fits']})

        query_table_mock.side_effect = [visits_1, products_1, products_2, visits_2, products_3]

        cheops = CheopsClass()

        result = cheops.get_products_from_targets_or_coordinates(target_name='M31', radius=2.0, level='L2')

        assert len(result) == 3
        assert list(result['filename']) == ['product-1.fits', 'product-2.fits', 'product-3.fits', ]

        get_observations_mock.assert_called_once_with(target_name='M31', coordinates=None, radius=2.0)

        assert query_table_mock.call_count == 5

        # From observation, extract the visits
        args, kwargs = query_table_mock.call_args_list[0]
        assert kwargs['table_name'] == conf.CHEOPS_VISIT_TABLE
        assert kwargs['observation_request_oid'] == 1111
        assert kwargs['verbose'] is False

        # From the visit, extract the products
        args, kwargs = query_table_mock.call_args_list[1]
        assert kwargs['table_name'] == conf.CHEOPS_DATA_PRODUCT_TABLE
        assert kwargs['visit_id'] == 1234
        assert kwargs['level'] == 'L2'
        assert kwargs['verbose'] is False

        # VISIT-2 -> products
        args, kwargs = query_table_mock.call_args_list[2]
        assert kwargs['table_name'] == conf.CHEOPS_DATA_PRODUCT_TABLE
        assert kwargs['visit_id'] == 5678
        assert kwargs['level'] == 'L2'
        assert kwargs['verbose'] is False

        # From the second observation, extract the visit
        args, kwargs = query_table_mock.call_args_list[3]
        assert kwargs['table_name'] == conf.CHEOPS_VISIT_TABLE
        assert kwargs['observation_request_oid'] == 2222
        assert kwargs['verbose'] is False

        # Verify that visits are processed only once
        args, kwargs = query_table_mock.call_args_list[4]
        assert kwargs['table_name'] == conf.CHEOPS_DATA_PRODUCT_TABLE
        assert kwargs['visit_id'] == 9012
        assert kwargs['level'] == 'L2'
        assert kwargs['verbose'] is False

    @patch('astroquery.esa.utils.utils.pyvo.dal.TAPService.capabilities', [])
    @patch.object(CheopsClass, 'query_table')
    @patch.object(CheopsClass, 'get_visit_from_observation')
    def test_get_products_from_observation_deduplicates_visits(self, get_visit_mock, query_table_mock):
        get_visit_mock.return_value = Table({'visit_id': [1234, 1234, 5678]})

        query_table_mock.side_effect = [Table({'filename': ['product-1.fits']}),
                                        Table({'filename': ['product-2.fits']}),
                                        ]

        cheops = CheopsClass()

        result = cheops.get_products_from_observation(1111, level='L1')

        assert len(result) == 2
        assert list(result['filename']) == ['product-1.fits', 'product-2.fits']

        get_visit_mock.assert_called_once_with(1111)

        # VISIT-1 is duplicated and must only be queried once.
        assert query_table_mock.call_count == 2

        # VISIT-1
        args, kwargs = query_table_mock.call_args_list[0]
        assert args[0] == conf.CHEOPS_DATA_PRODUCT_TABLE
        assert kwargs['visit_id'] == 1234
        assert kwargs['verbose'] is False
        assert kwargs['level'] == 'L1'

        # VISIT-2
        args, kwargs = query_table_mock.call_args_list[1]
        assert args[0] == conf.CHEOPS_DATA_PRODUCT_TABLE
        assert kwargs['visit_id'] == 5678
        assert kwargs['verbose'] is False
        assert kwargs['level'] == 'L1'

    @patch('astroquery.esa.utils.utils.pyvo.dal.TAPService.capabilities', [])
    @patch.object(CheopsClass, 'query_table')
    def test_get_products_from_visit_using_string(self, query_table_mock):
        cheops = CheopsClass()

        result = cheops.get_products_from_visit(1234, level='L2')

        assert result is query_table_mock.return_value

        query_table_mock.assert_called_once()

        args, kwargs = query_table_mock.call_args

        assert args[0] == conf.CHEOPS_DATA_PRODUCT_TABLE
        assert kwargs['visit_id'] == 1234
        assert kwargs['verbose'] is False
        assert kwargs['level'] == 'L2'

    @patch('astroquery.esa.utils.utils.pyvo.dal.TAPService.capabilities', [])
    @patch.object(CheopsClass, 'query_table')
    def test_get_products_from_visit_using_row_without_level(self, query_table_mock):
        visit = Table({'visit_id': [1234]})[0]

        cheops = CheopsClass()

        result = cheops.get_products_from_visit(visit)

        assert result is query_table_mock.return_value

        query_table_mock.assert_called_once()

        args, kwargs = query_table_mock.call_args

        assert args[0] == conf.CHEOPS_DATA_PRODUCT_TABLE
        assert kwargs['visit_id'] == 1234
        assert kwargs['verbose'] is False

        # level=None should not be forwarded to query_table
        assert 'level' not in kwargs

    @patch('astroquery.esa.utils.utils.pyvo.dal.TAPService.capabilities', [])
    @patch.object(CheopsClass, 'get_products_from_observation')
    @patch.object(CheopsClass, 'get_observations_from_program')
    def test_get_products_from_program(self, get_observations_mock, get_products_mock):
        get_observations_mock.return_value = Table({'observation_request_oid': [1111, 2222]})

        get_products_mock.side_effect = [Table({'filename': ['product-1.fits']}),
                                         Table({'filename': ['product-2.fits']})]

        cheops = CheopsClass()

        result = cheops.get_products_from_program(programme_key='PR010023', level='L2')

        assert len(result) == 2
        assert list(result['filename']) == ['product-1.fits', 'product-2.fits']

        get_observations_mock.assert_called_once_with(programme_key='PR010023', title=None, pi_name=None)

        assert get_products_mock.call_count == 2

        # Products for first observation
        args, kwargs = get_products_mock.call_args_list[0]

        assert args[0]['observation_request_oid'] == 1111
        assert kwargs['level'] == 'L2'

        # Products for second observation
        args, kwargs = get_products_mock.call_args_list[1]

        assert args[0]['observation_request_oid'] == 2222
        assert kwargs['level'] == 'L2'

    @pytest.mark.parametrize(
        ('level', 'expected'),
        [
            (None, {}),
            ('EXT', {'level': 'EXT'}),
            ('L0.5', {'level': 'L0.5'}),
            ('L1', {'level': 'L1'}),
            ('L2', {'level': 'L2'}),
        ],
    )
    @patch('astroquery.esa.utils.utils.pyvo.dal.TAPService.capabilities', [])
    def test_get_kwargs_for_level(self, level, expected):
        cheops = CheopsClass()

        result = cheops._get_kwargs_for_level(level)

        assert result == expected

    @patch('astroquery.esa.utils.utils.pyvo.dal.TAPService.capabilities', [])
    @patch.object(CheopsClass, 'download_product')
    @patch.object(CheopsClass, 'get_products_from_targets_or_coordinates')
    def test_download_products_from_targets_or_coordinates(self, get_products_mock, download_product_mock, tmp_path):
        get_products_mock.return_value = Table({'filename': ['one.fits', 'two.fits']})

        destination = os.path.join(tmp_path, 'downloads')

        cheops = CheopsClass()

        cheops.download_products_from_targets_or_coordinates(coordinates='12 13', radius=0.5,
                                                             level='L2', path=str(destination))

        get_products_mock.assert_called_once_with(target_name=None, coordinates='12 13', radius=0.5, level='L2')

        assert download_product_mock.call_count == 2

        args, kwargs = download_product_mock.call_args_list[0]
        assert kwargs['filename'] == 'one.fits'
        assert kwargs['path'] == str(destination)

        args, kwargs = download_product_mock.call_args_list[1]
        assert kwargs['filename'] == 'two.fits'
        assert kwargs['path'] == str(destination)

    @patch('astroquery.esa.utils.utils.pyvo.dal.TAPService.capabilities', [])
    @patch.object(CheopsClass, 'download_product')
    @patch.object(CheopsClass, 'get_products_from_observation')
    def test_download_products_from_observation(self, get_products_mock, download_product_mock, tmp_path):
        get_products_mock.return_value = Table({'filename': ['one.fits', 'two.fits']})

        destination = f"{tmp_path}/downloads"

        cheops = CheopsClass()

        cheops.download_products_from_observation(1111, level='L1', path=str(destination))

        get_products_mock.assert_called_once_with(observation=1111, level='L1')

        assert download_product_mock.call_count == 2

        args, kwargs = download_product_mock.call_args_list[0]
        assert kwargs['filename'] == 'one.fits'
        assert kwargs['path'] == str(destination)

        args, kwargs = download_product_mock.call_args_list[1]
        assert kwargs['filename'] == 'two.fits'
        assert kwargs['path'] == str(destination)

    @patch('astroquery.esa.utils.utils.pyvo.dal.TAPService.capabilities', [])
    @patch.object(CheopsClass, 'download_product')
    @patch.object(CheopsClass, 'get_products_from_visit')
    def test_download_products_from_visit(self, get_products_mock, download_product_mock, tmp_path):
        get_products_mock.return_value = Table({'filename': ['one.fits', 'two.fits']})

        destination = f"{tmp_path}/downloads"

        cheops = CheopsClass()

        cheops.download_products_from_visit(1234, level='L0.5', path=str(destination))

        get_products_mock.assert_called_once_with(visit=1234, level='L0.5')

        assert download_product_mock.call_count == 2

        args, kwargs = download_product_mock.call_args_list[0]
        assert kwargs['filename'] == 'one.fits'
        assert kwargs['path'] == str(destination)

    @patch('astroquery.esa.utils.utils.pyvo.dal.TAPService.capabilities', [])
    @patch.object(CheopsClass, 'download_product')
    @patch.object(CheopsClass, 'get_products_from_program')
    def test_download_products_from_program(self, get_products_mock, download_product_mock, tmp_path):
        get_products_mock.return_value = Table({'filename': ['one.fits', 'two.fits']})

        destination = f"{tmp_path}/downloads"

        cheops = CheopsClass()

        cheops.download_products_from_program(programme_key='PR010023', level='L2', path=str(destination))

        get_products_mock.assert_called_once_with(programme_key='PR010023', title=None, pi_name=None, level='L2')

        assert download_product_mock.call_count == 2

        args, kwargs = download_product_mock.call_args_list[0]
        assert kwargs['filename'] == 'one.fits'
        assert kwargs['path'] == str(destination)

    @patch('astroquery.esa.utils.utils.pyvo.dal.TAPService.capabilities', [])
    @patch.object(CheopsClass, 'download_product')
    @patch.object(CheopsClass, 'get_products_from_visit')
    def test_bulk_download_uses_current_directory_when_path_is_empty(self, get_products_mock, download_product_mock):
        get_products_mock.return_value = Table({'filename': ['one.fits']})

        cheops = CheopsClass()

        cheops.download_products_from_visit(1234)

        get_products_mock.assert_called_once_with(visit=1234, level=None)

        download_product_mock.assert_called_once_with(filename='one.fits', path='')
