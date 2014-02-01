from ... import eso


def test_SgrAstar():

    instruments = eso.Eso.list_instruments()
    results = [eso.Eso.query_instrument(ins, target='Sgr A*') for ins in instruments]
    
