from astroquery import simbad

def simbad_test():
    r = simbad.QueryAroundId('m31', radius='0.5s').execute()
    print r.table

