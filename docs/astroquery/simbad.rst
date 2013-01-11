.. _astroquery.simbad:

************************************
SIMBAD Queries (`astroquery.simbad`)
************************************

Getting started
===============

The following example illustrates a SIMBAD query.

.. code-block:: python
    >>> from astroquery import simbad
    >>> r = simbad.QueryAroundId('m31', radius='0.5s').execute()
    >>> print r.table

               MAIN_ID                 RA          DEC      RA_PREC DEC_PREC COO_ERR_MAJA COO_ERR_MINA COO_ERR_ANGLE COO_QUAL COO_WAVELENGTH     COO_BIBCODE    
    ----------------------------- ------------ ------------ ------- -------- ------------ ------------ ------------- -------- -------------- -------------------
                            M  31 00 42 44.330 +41 16 07.50       7        7          nan          nan             0        B              I 2006AJ....131.1163S
    [BFS98] J004244.344+411607.70 00 42 44.344 +41 16 07.70       7        7          nan          nan             0        D                1998ApJ...504..113B
      [K2002] J004244.37+411607.6 00 42 44.365 +41 16 07.65       7        7         30.0         30.0            10        D                2002ApJ...577..738K
    [BFS98] J004244.362+411607.20 00 42 44.362 +41 16 07.20       7        7          nan          nan             0        D                1998ApJ...504..113B
    [BFS98] J004244.303+411607.14 00 42 44.303 +41 16 07.14       7        7          nan          nan             0        D                1998ApJ...504..113B

Reference/API
=============

.. automodapi:: astroquery.simbad
    :no-inheritance-diagram:
