import numpy as np
from bs4 import BeautifulSoup
from astropy import units as u
from astropy.table import Table
from astropy.tests.helper import remote_data
from astropy.tests.helper import pytest

from ...utils import commons
from ...atomic import AtomicLineList


@pytest.fixture(scope='module')
def form():
    response = commons.send_request(AtomicLineList.FORM_URL, {},
                                    AtomicLineList.TIMEOUT, 'GET')
    bs = BeautifulSoup(response.text)
    return bs.find('form')


@remote_data
def test_default_form_values(form):
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


@remote_data
def test_query_with_default_params():
    table = AtomicLineList.query_object()
    assert isinstance(table, Table)
    assert len(table) == 500
    assert str(table[:5]) == '''
LAMBDA VAC ANG SPECTRUM  TT TERM  J J  LEVEL ENERGY  CM 1
-------------- -------- --- ---- ----- ------------------
      1.010799   Zn XXX  E1 1-10 1/2-* 0.00 - 98933890.00
      1.013182   Zn XXX  E1  1-9 1/2-* 0.00 - 98701900.00
      1.016534   Zn XXX  E1  1-8 1/2-* 0.00 - 98377600.00
       1.02146   Zn XXX  E1  1-7 1/2-* 0.00 - 97904300.00
       1.02916   Zn XXX  E1  1-6 1/2-* 0.00 - 97174700.00'''.strip()


@remote_data
def test_query_with_params():
    table = AtomicLineList.query_object(
        wavelength_range=(15 * u.nm, 200 * u.Angstrom),
        wavelength_type='Air',
        wavelength_accuracy=20,
        element_spectrum='C II-IV')
    assert isinstance(table, Table)
    assert table.colnames == ['LAMBDA VAC ANG', 'SPECTRUM', 'TT', 'TERM',
                              'J J', 'LEVEL ENERGY  CM 1']
    assert np.all(table['LAMBDA VAC ANG'] ==
                  np.array([196.8874, 197.7992, 199.0122]))
    assert np.all(table['SPECTRUM'] == np.array(['C IV', 'C IV', 'C IV']))
    assert np.all(table['TT'] == np.array(['E1', 'E1', 'E1']))
    assert np.all(table['TERM'] == np.array(['2S-2Po', '2S-2Po', '2S-2Po']))
    assert np.all(table['J J'] == np.array(['1/2-*', '1/2-*', '1/2-*']))
    assert np.all(table['LEVEL ENERGY  CM 1'] ==
                  np.array(['0.00 -   507904.40', '0.00 -   505563.30',
                            '0.00 -   502481.80']))


@remote_data
def test_empty_result_set():
    table = AtomicLineList.query_object(wavelength_accuracy=0)
    assert isinstance(table, Table)
    assert not table
    assert len(table) == 0
