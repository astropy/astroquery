from ... import ogle

from astropy import coordinates as coord
from astropy import units as u

def test_ogle_single():
    """
    Test a single pointing using an astropy coordinate instance
    """
    co = coord.GalacticCoordinates(0, 3, unit=(u.degree, u.degree))
    ogle.query(coord=co)
    return

def test_ogle_list():
    """
    Test multiple pointings using a list of astropy coordinate instances
    """
    co = coord.GalacticCoordinates(0, 3, unit=(u.degree, u.degree))
    co_list = [co, co, co]
    ogle.query(coord=co_list)
    return

def test_ogle_list():
    """
    Test multiple pointings using a list of astropy coordinate instances
    """
    co_list = [[0, 0, 0], [3, 3, 3]]
    ogle.query(coord=co_list)
    return

if __name__ == '__main__':
    test_ogle_single()
    test_ogle_list()
    test_ogle_list_values()


