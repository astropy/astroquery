from astroquery.simbad import Simbad

s = Simbad()
# bibcodelist(date1-date2) lists the number of bibliography
# items referring to each object over that date range
s.add_votable_fields('bibcodelist(2003-2013)')
r = s.query_object('m31')
r.pprint()

"""
MAIN_ID      RA          DEC      RA_PREC DEC_PREC COO_ERR_MAJA COO_ERR_MINA COO_ERR_ANGLE COO_QUAL COO_WAVELENGTH     COO_BIBCODE     BIBLIST_2003_2013
------- ------------ ------------ ------- -------- ------------ ------------ ------------- -------- -------------- ------------------- -----------------
  M  31 00 42 44.330 +41 16 07.50       7        7          nan          nan             0        B              I 2006AJ....131.1163S              3758
"""
