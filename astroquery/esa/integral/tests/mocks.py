# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
================
ISLA Mocks tests
================

European Space Astronomy Centre (ESAC)
European Space Agency (ESA)

"""
from unittest.mock import Mock
from requests import HTTPError

from pyvo.dal import DALResults
from astropy.io.votable.tree import VOTableFile
from astropy.table import Table

instruments_value = ["i1"]
bands_value = ["b1"]
instrument_band_mock_value = {"i1": {'instrument_oid': 'id1', 'band_oid': 'id2'},
                              "b1": {'instrument_oid': 'id3', 'band_oid': 'id4'}}


def get_instrument_bands():
    return instruments_value, bands_value, instrument_band_mock_value


def get_dal_table():
    data = {
        "source_id": [123456789012345, 234567890123456, 345678901234567],
        "ra": [266.404997, 266.424512, 266.439127],
        "dec": [-28.936173, -28.925636, -28.917813]
    }

    # Create an Astropy Table with the mock data
    astropy_table = Table(data)

    return DALResults(VOTableFile.from_table(astropy_table))


def get_empty_table():
    data = {
        "source_id": [],
    }

    # Create an Astropy Table with the mock data
    return Table(data)


def get_sources_table():
    data = {
        "name": ['Crab'],
        "ra": [83.63320922851562],
        "dec": [22.01447105407715],
        "source_id": ['J053432.0+220052']
    }

    # Create an Astropy Table with the mock data
    astropy_table = Table(data)

    return DALResults(VOTableFile.from_table(astropy_table))


def get_mock_timeline():
    return {'totalItems': 1,
            'data': {
                'fraFC': 1,
                'totEffExpo': 1,
                'scwExpo': [1, 2],
                'scwRevs': [1, 2],
                'scwTimes': [1, 2],
                'scwOffAxis': [1, 2]
            }}


def get_mock_timeseries():
    return {'aggregationValue': 1,
            'aggregationUnit': 'm',
            'detectors': ['d1', 'd2'],
            'sourceId': 'target',
            'totalItems': 2,
            'time': [['2024-12-18T12:00:00', '2024-12-19T12:00:00'], ['2024-12-20T12:00:00', '2024-12-18T21:00:00']],
            'rates': [[1, 2], [3, 4]],
            'ratesError': [[1, 2], [3, 4]]
            }


def get_mock_spectra():
    return [{'spectraOid': 1,
             'fileName': 'm',
             'detector': ['d1', 'd2'],
             'metadata': 'meta',
             'dateStart': 'target',
             'dateStop': 2,
             'time': ['2024-12-18T12:00:00', '2024-12-19T12:00:00', '2024-12-20T12:00:00', '2024-12-18T21:00:00'],
             'energy': [1, 2, 3, 4],
             'energyError': [1, 2, 3, 4],
             'rate': [1, 2, 3, 4],
             'rateError': [1, 2, 3, 4]
             }]


def get_mock_mosaic():
    return [{'mosaicOid': 1,
             'fileName': 'm',
             'height': 2,
             'width': 2,
             'minZScale': 1,
             'maxZScale': 3,
             'ra': [[1, 2], [3, 4]],
             'dec': [[1, 2], [3, 4]],
             'data': [[1, 2], [3, 4]]
             }]


def get_mock_response():
    error_message = "Mocked HTTP error"
    mock_response = Mock()
    mock_response.raise_for_status.side_effect = HTTPError(error_message)
    return mock_response
