========================================
Accessing Online Astronomical Data
========================================

Astrodata is an affiliated package that contains a collection of classes 
and functions to access online Astronomical data. Each web service has 
its own sub-package. For example, to interface with the IRSA website, 
use the ``irsa`` sub-package:

    from astroquery import irsa

    from astroquery import simbad
    theta1c = astroquery.simbad.QueryId('tet01 Ori C').execute()
    theta1c.table.pprint()



    MAIN_ID          RA           DEC      RA_PREC DEC_PREC COO_ERR_MAJA COO_ERR_MINA COO_ERR_ANGLE COO_QUAL COO_WAVELENGTH     COO_BIBCODE    
    
    ------------- ------------- ------------- ------- -------- ------------ ------------ ------------- -------- -------------- -------------------
    
    * tet01 Ori C 05 35 16.4637 -05 23 22.848       9        9        42.09         28.6            90        A              O 2007A&A...474..653V