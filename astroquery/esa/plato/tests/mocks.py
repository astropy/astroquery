# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
=================
PLATO Mocks tests
=================

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


def get_mock_response():
    error_message = "Mocked HTTP error"
    mock_response = Mock()
    mock_response.raise_for_status.side_effect = HTTPError(error_message)
    return mock_response
