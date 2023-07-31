import os.path

from astropy.table import Table

from ...atomic import AtomicLineList, Transition, AtomicTransition, MultiTransition
from ...atomic.utils import is_valid_transitions_param


class MockResponseAtomicLineList:
    def __init__(self, is_empty):
        if is_empty:
            self.filename = data_path('empty_results.html')
        else:
            self.filename = data_path('default_params_result.html')

    @property
    def text(self):
        with open(self.filename) as f:
            return f.read()


def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)


def test_parse_result_empty():
    alist = AtomicLineList()
    response = MockResponseAtomicLineList(True)
    table = alist._parse_result(response)
    assert isinstance(table, Table)
    assert not table
    assert len(table) == 0


def test_parse_result_non_empty():
    alist = AtomicLineList()
    response = MockResponseAtomicLineList(False)
    table = alist._parse_result(response)
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


def test_transitions():
    assert isinstance(Transition.all, AtomicTransition)
    assert isinstance(Transition.nebular, AtomicTransition)
    assert isinstance(Transition.IC, MultiTransition)
    assert isinstance(Transition.E1, MultiTransition)
    assert isinstance(Transition.E2, MultiTransition)
    assert isinstance(Transition.M1, MultiTransition)
    assert len(Transition.IC | Transition.M1) == 2
    # associativity
    assert ((Transition.IC | Transition.M1) | Transition.E1
            == Transition.IC | (Transition.M1 | Transition.E1))
    # commutativity
    assert Transition.IC | Transition.M1 == Transition.M1 | Transition.IC
    assert str((Transition.IC | Transition.M1)) == 'IC,M1'


def test_validate_transitions():
    assert is_valid_transitions_param(Transition.all)
    assert is_valid_transitions_param(Transition.nebular)
    assert is_valid_transitions_param(Transition.E1)
    assert is_valid_transitions_param(Transition.IC | Transition.E2)
    assert is_valid_transitions_param(
        Transition.IC | Transition.E2 | Transition.M1)
    assert not is_valid_transitions_param(Transition.all | Transition.IC)
    assert not is_valid_transitions_param(Transition.IC | Transition.all)
    assert not is_valid_transitions_param(Transition.nebular | Transition.IC)
    assert not is_valid_transitions_param(Transition.IC | Transition.nebular)
