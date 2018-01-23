from astroquery.astrocats import OACAPI

test_table = OACAPI.query_object(object_name=['GW170817' , 'SN2014J'],
                                 quantity_name='photometry',
                                 attribute_name=['time', 'magnitude', 'e_magnitude'],
                                 verbose=True)

print(test_table)