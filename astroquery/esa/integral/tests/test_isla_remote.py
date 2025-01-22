# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
==============
ISLA TAP tests
==============

European Space Astronomy Centre (ESAC)
European Space Agency (ESA)

"""
import os

from astroquery.esa.integral import IntegralClass
import pytest
from pyvo import DALQueryError
from requests import HTTPError


def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)


def close_file(file):
    file.close()


def close_files(file_list):
    for file in file_list:
        close_file(file['fits'])


@pytest.mark.remote_data
class TestIntegralRemote:

    def test_get_table(self):
        isla = IntegralClass()

        obscore = isla.get_table('ivoa.obscore')
        assert obscore is not None

        ehst = isla.get_table('ehst.archive')
        assert ehst is None

    def test_query_tap(self):
        isla = IntegralClass()

        # Query an existing table
        result = isla.query_tap('select top 10 * from ivoa.obscore;')
        assert len(result) > 0

        # Query a table that does not exist
        with pytest.raises(DALQueryError) as err:
            isla.query_tap('select top 10 * from schema.table;')
        assert 'Unknown table' in err.value.args[0]

        # Store the result in a file
        filename = 'query_tap.votable'
        isla.query_tap('select top 10 * from ivoa.obscore;', output_file=filename)
        assert os.path.exists(filename)

    def test_get_sources(self):
        isla = IntegralClass()
        sources = isla.get_sources(target_name='crab')

        assert len(sources) == 1
        assert sources[0]['name'] == 'Crab'

        # Query a target that does not exist
        with pytest.raises(ValueError) as err:
            isla.get_sources(target_name='star')
        assert 'Target star cannot be resolved for ISLA' in err.value.args[0]

    def test_get_source_metadata(self):
        isla = IntegralClass()
        metadata = isla.get_source_metadata(target_name='crab')

        assert len(metadata) >= 1
        assert metadata[0]['name'] == 'Integral'
        assert metadata[0]['metadata'][0]['value'] == 'Crab'

        # Query a target that does not exist
        with pytest.raises(ValueError) as err:
            isla.get_source_metadata(target_name='star')
        assert 'Target star cannot be resolved for ISLA' in err.value.args[0]

    def test_get_observations(self):
        isla = IntegralClass()
        observations = isla.get_observations(target_name='crab', radius=12.0, start_time='2005-01-01T00:00:00Z',
                                             end_time='2005-12-31T00:00:00Z', start_revno='0290', end_revno='0599')
        assert len(observations) > 1

        # Query returned
        query = isla.get_observations(target_name='crab', radius=12.0, start_time='2005-01-01T00:00:00Z',
                                      end_time='2005-12-31T00:00:00Z', start_revno='0290', end_revno='0599',
                                      verbose=True)

        assert type(query) is str
        assert 'select * from ila.cons_pub_obs' in query

        # Invalid date format
        with pytest.raises(ValueError) as err:
            isla.get_observations(target_name='crab', radius=12.0, start_time='2005/01/01T00:00:00Z',
                                  end_time='2005/12/31T00:00:00Z', start_revno='0290', end_revno='0599')
        assert 'Invalid isoformat' in err.value.args[0]

        # Invalid revno
        with pytest.raises(ValueError) as err:
            isla.get_observations(target_name='crab', radius=12.0, start_time='2005-01-01T00:00:00Z',
                                  end_time='2005-12-31T00:00:00Z', start_revno='290', end_revno='0599')
        assert 'Revolution number 290 is not correct' in err.value.args[0]

        # No observations available
        with pytest.raises(ValueError) as err:
            isla.get_observations(target_name='star', radius=12.0, start_time='2005-01-01T00:00:00Z',
                                  end_time='2005-12-31T00:00:00Z', start_revno='0290', end_revno='0599')
        assert 'Target star cannot be resolved for ISLA' in err.value.args[0]

    def test_download_science_windows(self):
        # Simple download
        isla = IntegralClass()
        sc = isla.download_science_windows(science_windows='008100430010')
        assert len(sc) > 1

        # Only one parameter is allowed
        with pytest.raises(ValueError) as err:
            isla.download_science_windows(science_windows='008100430010', observation_id='03200490001')
        assert 'Only one parameter can be provided at a time.' in err.value.args[0]

        # Correct parameters are set
        with pytest.raises(ValueError) as err:
            isla.download_science_windows(revolution=12)
        assert 'Input parameters are wrong' in err.value.args[0]

    def test_get_timeline(self):
        isla = IntegralClass()
        timeline = isla.get_timeline(coordinates='83.63320922851562 22.01447105407715')

        assert timeline is not None
        assert 'timeline' in timeline
        assert timeline['total_items'] == len(timeline['timeline'])

        # No timeline has been found
        with pytest.raises(ValueError) as err:
            isla.get_timeline(coordinates='0 0', radius=0.8)
        assert 'No timeline is available for the current coordinates and radius.' in err.value.args[0]

    def test_get_epochs(self):
        # Nominal request
        isla = IntegralClass()
        epochs = isla.get_epochs(target_name='J011705.1-732636', band='28_40')

        assert len(epochs) > 0
        assert epochs['epoch'] is not None

        # Error when band and instrument are set
        with pytest.raises(TypeError) as err:
            isla.get_epochs(target_name='J011705.1-732636', instrument='jem-x', band='28_40')
        assert 'Please use only instrument or band as parameter.' in err.value.args[0]

        # Error when band and instrument are not set
        with pytest.raises(TypeError) as err:
            isla.get_epochs(target_name='J011705.1-732636')
        assert 'Please use at least one parameter, instrument or band.' in err.value.args[0]

        # No epochs are found
        epochs = isla.get_epochs(target_name='star', band='28_40')
        assert len(epochs) == 0

    def test_get_long_term_timeseries(self):
        isla = IntegralClass()
        ltt = isla.get_long_term_timeseries(target_name='J174537.0-290107', instrument='jem-x')

        assert len(ltt) > 0
        assert 'fits' in ltt[0]

        # No correct instrument or band
        with pytest.raises(ValueError) as err:
            isla.get_long_term_timeseries(target_name='J174537.0-290107', instrument='test')
        assert 'This is not a valid value for instrument or band.' in err.value.args[0]

        # No long term timeseries found
        ltt = isla.get_long_term_timeseries(target_name='star', instrument='jem-x')
        assert ltt is None


    def test_get_short_term_timeseries(self):
        isla = IntegralClass()
        stt = isla.get_short_term_timeseries(target_name='J011705.1-732636', band='28_40', epoch='0745_06340000001')

        assert len(stt) > 0
        assert 'fits' in stt[0]

        # No correct instrument or band
        print('error instrument')
        with pytest.raises(ValueError) as err:
            isla.get_short_term_timeseries(target_name='J011705.1-732636', band='1234', epoch='0745_06340000001')
        assert 'This is not a valid value for instrument or band.' in err.value.args[0]

        # No correct epoch
        print('error band')
        with pytest.raises(ValueError) as err:
            isla.get_short_term_timeseries(target_name='J011705.1-732636', band='28_40', epoch='123456')
        assert 'Epoch 123456 is not available for this target and instrument/band.' in err.value.args[0]

        # No long term timeseries found
        with pytest.raises(ValueError) as err:
            isla.get_short_term_timeseries(target_name='star', band='28_40', epoch='0745_06340000001')
        assert 'Epoch 0745_06340000001 is not available for this target and instrument/band.' in err.value.args[0]

    def test_get_spectra(self):
        isla = IntegralClass()
        spectra = isla.get_spectra(target_name='J011705.1-732636', instrument='ibis', epoch='0745_06340000001')

        assert len(spectra) > 0
        assert 'fits' in spectra[0]

        # No correct instrument or band
        with pytest.raises(ValueError) as err:
            isla.get_spectra(target_name='J011705.1-732636', instrument='camera', epoch='0745_06340000001')
        assert 'This is not a valid value for instrument or band.' in err.value.args[0]

        # No correct epoch
        with pytest.raises(ValueError) as err:
            isla.get_spectra(target_name='J011705.1-732636', instrument='ibis', epoch='123456')
        assert 'Epoch 123456 is not available for this target and instrument/band.' in err.value.args[0]

        # No long term timeseries found
        with pytest.raises(ValueError) as err:
            isla.get_spectra(target_name='star', instrument='ibis', epoch='0745_06340000001')
        assert 'Epoch 0745_06340000001 is not available for this target and instrument/band.' in err.value.args[0]

    def test_get_mosaics(self):
        isla = IntegralClass()
        mosaics = isla.get_mosaic(epoch='0727_88601650001', instrument='ibis')

        assert len(mosaics) > 0
        assert 'fits' in mosaics[0]

        # No correct instrument or band
        with pytest.raises(ValueError) as err:
            isla.get_mosaic(epoch='0727_88601650001', instrument='camera')
        assert 'This is not a valid value for instrument or band.' in err.value.args[0]

        # No correct epoch
        with pytest.raises(ValueError) as err:
            isla.get_mosaic(epoch='123456', instrument='ibis')
        assert 'Epoch 123456 is not available for this target and instrument/band.' in err.value.args[0]

