import pytest

from ...neos import Neows

from astropy.table import Table


def test_observations_from_spk_id():
    result = Neows().from_spk_id(spk_id="2000433")
    assert isinstance(result, Table)


def test_name_from_spk_id():
    result = Neows().from_spk_id(spk_id="2000433")
    assert result[0][1] == "433 Eros (A898 PA)"


def test_name_gives_correct_spk_id():
    result = Neows()._spk_id_from_name(name="Eros")
    assert result == "2000433"
