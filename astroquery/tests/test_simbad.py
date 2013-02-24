from astroquery import simbad

def simbad_test():
    r = simbad.QueryAroundId('m31', radius='0.5s').execute()
    print r.table


def multitest():
    result = simbad.QueryMulti(
            [simbad.QueryId('m31'),
             simbad.QueryId('m51')])
    table = result.execute().table
    assert "M  31" in table
    assert "M  51" in table

