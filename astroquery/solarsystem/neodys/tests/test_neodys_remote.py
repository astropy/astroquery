import pytest

from astroquery.solarsystem.neodys import NEODyS


@pytest.mark.remote_data
def test_neodys_query():

    test_object = "2018VP1"

    res_kep_0 = NEODyS.query_object(test_object, orbital_element_type="ke", epoch_near_present=0)
    res_kep_1 = NEODyS.query_object(test_object, orbital_element_type="ke", epoch_near_present=1)
    res_eq_0 = NEODyS.query_object(test_object, orbital_element_type="eq", epoch_near_present=0)
    res_eq_1 = NEODyS.query_object(test_object, orbital_element_type="eq", epoch_near_present=1)

    assert len(res_kep_0['Keplerian State Vector']) == 6
    assert len(res_kep_0['Covariance Matrix']) == 21
    assert res_kep_0['Mean Julian Date'][0] != res_kep_1['Mean Julian Date'][0]
    assert len(res_eq_0['Equinoctial State Vector']) == 6
    assert len(res_eq_0['Covariance Matrix']) == 21
    assert len(res_eq_0['Keplerian Correlation Matrix']) == 0
    assert res_eq_0['Mean Julian Date'][0] != res_eq_1['Mean Julian Date'][0]
