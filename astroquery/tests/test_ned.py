from astroquery import ned

def test_objname():
    result = ned.query_ned_by_objname()

def test_nearname():
    result = ned.query_ned_nearname()

def test_neariauname():
    result = ned.query_ned_neariauname()

def test_refcode():
    result = ned.query_ned_refcode()

def test_names():
    result = ned.query_ned_names()

def test_basic_posn():
    result = ned.query_ned_basic_posn()

def test_ned_external():
    result = ned.query_ned_external()

def test_ned_allsky():
    result = ned.query_ned_allsky()

def test_ned_photometry():
    result = ned.query_ned_photometry()

def test_ned_diameters():
    result = ned.query_ned_diameters()

def test_ned_redshifts():
    result = ned.query_ned_redshifts()

def test_ned_notes():
    result = ned.query_ned_ned_notes()

def test_ned_position():
    result = ned.query_ned_ned_position()

def test_ned_nearpos():
    result = ned.query_ned_ned_nearpos()

