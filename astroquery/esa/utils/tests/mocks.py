# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
=========================
ESA TAP Mocks for testing
=========================

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
        "table": ['ivoa.ObsCore', 'ivoa.siap'],
    }

    # Create an Astropy Table with the mock data
    astropy_table = Table(data)

    return DALResults(VOTableFile.from_table(astropy_table))


def get_empty_table():
    data = {
        "table": [],
    }

    # Create an Astropy Table with the mock data
    return Table(data)


def get_mock_response():
    error_message = "Mocked HTTP error"
    mock_response = Mock()
    mock_response.raise_for_status.side_effect = HTTPError(error_message)
    return mock_response
