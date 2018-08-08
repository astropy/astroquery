from astroquery.simbad import Simbad

customSimbad = Simbad()
customSimbad.add_votable_fields('sptype')

result = customSimbad.query_object('g her')

result['MAIN_ID'][0]
# 'V* g Her'

result['SP_TYPE'][0]
# 'M6III'
