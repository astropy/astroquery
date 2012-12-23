import astroquery.irsa
import pytest

def test_trivial():
    """ just make sure it doesn't raise anything 
    takes about 3-5 seconds"""
    tbl = astroquery.irsa.query_gator_box('pt_src_cat','83.808 -5.391',300)

    assert len(tbl) == 100 # at least, that's what I got...
    return tbl
