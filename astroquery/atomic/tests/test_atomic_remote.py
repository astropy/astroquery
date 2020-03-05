import numpy as np
import pytest
from bs4 import BeautifulSoup
from astropy import units as u
from astropy.table import Table

from ...atomic import AtomicLineList


@pytest.mark.remote_data
def test_default_form_values():
    default_response = AtomicLineList._request(
        method="GET", url=AtomicLineList.FORM_URL,
        data={}, timeout=AtomicLineList.TIMEOUT)
    bs = BeautifulSoup(default_response.text)
    form = bs.find('form')

    default_form_values = AtomicLineList._get_default_form_values(form)
    assert default_form_values == {
        'air': u'Vacuum',
        'auto': u'Suppress',
        'ener': u'cm^-1',
        'form': [u'spec', u'type', u'term', u'angm', u'ener'],
        'hydr': u'Suppress',
        'jval': u'usej',
        'mode': u'Plain',
        'type': u'All',
        'wave': u'Angstrom'}


@pytest.mark.remote_data
def test_query_with_default_params():
    table = AtomicLineList.query_object()
    assert isinstance(table, Table)
    assert len(table) == 500
    assert str(table[:5]) == '''
LAMBDA VAC ANG SPECTRUM  TT CONFIGURATION TERM  J J    A_ki   LEVEL ENERGY  CM 1
-------------- -------- --- ------------- ---- ----- -------- ------------------
      1.010799   Zn XXX  E1        1*-10* 1-10 1/2-* 1.02E+11 0.00 - 98933890.00
      1.013182   Zn XXX  E1         1*-9*  1-9 1/2-* 1.74E+11 0.00 - 98701900.00
      1.016534   Zn XXX  E1         1*-8*  1-8 1/2-* 3.14E+11 0.00 - 98377600.00
       1.02146   Zn XXX  E1         1*-7*  1-7 1/2-* 6.13E+11 0.00 - 97904300.00
       1.02916   Zn XXX  E1         1*-6*  1-6 1/2-* 1.33E+12 0.00 - 97174700.00'''.strip()


@pytest.mark.remote_data
def test_query_with_wavelength_params():
    result = AtomicLineList.query_object(
        wavelength_range=(15 * u.nm, 200 * u.Angstrom),
        wavelength_type='Air',
        wavelength_accuracy=20,
        element_spectrum='C II-IV')
    assert isinstance(result, Table)
    assert result.colnames == ['LAMBDA VAC ANG', 'SPECTRUM', 'TT',
                              'CONFIGURATION', 'TERM', 'J J', 'A_ki',
                              'LEVEL ENERGY  CM 1']
    assert np.all(result['LAMBDA VAC ANG'] ==
                  np.array([196.8874, 197.7992, 199.0122]))
    assert np.all(result['SPECTRUM'] == np.array(['C IV', 'C IV', 'C IV']))
    assert np.all(result['TT'] == np.array(['E1', 'E1', 'E1']))
    assert np.all(result['TERM'] == np.array(['2S-2Po', '2S-2Po', '2S-2Po']))
    assert np.all(result['J J'] == np.array(['1/2-*', '1/2-*', '1/2-*']))
    assert np.all(result['LEVEL ENERGY  CM 1'] ==
                  np.array(['0.00 -   507904.40', '0.00 -   505563.30',
                            '0.00 -   502481.80']))


@pytest.mark.remote_data
def test_empty_result_set():
    result = AtomicLineList.query_object(wavelength_accuracy=0)
    assert isinstance(result, Table)
    assert not result
    assert len(result) == 0


@pytest.mark.remote_data
def test_lower_upper_ranges():
    result = AtomicLineList.query_object(
        lower_level_energy_range=u.Quantity((600 * u.cm**(-1), 1000 * u.cm**(-1))),
        upper_level_energy_range=u.Quantity((15000 * u.cm**(-1), 100000 * u.cm**(-1))),
        element_spectrum='Ne III')
    assert isinstance(result, Table)

    assert np.all(result['LAMBDA VAC ANG'] ==
                  np.array([1814.73, 3968.91, 4013.14]))
