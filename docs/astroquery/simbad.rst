.. _astroquery.simbad:

*****************************************
SIMBAD Queries (`astroquery.simbad`)
*****************************************

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

Multi-query example:

.. code-block:: python

    >>> from astroquery import simbad
    >>> targets = ['m31','m51','omc1','notatarget']
    >>> queries = [simbad.QueryId(x) for x in targets]
    >>> result = simbad.QueryMulti(queries).execute(mirror='harvard')
    >>> print result.table

     MAIN_ID        RA          DEC      RA_PREC DEC_PREC COO_ERR_MAJA COO_ERR_MINA COO_ERR_ANGLE COO_QUAL COO_WAVELENGTH     COO_BIBCODE    
    ---------- ------------ ------------ ------- -------- ------------ ------------ ------------- -------- -------------- -------------------
         M  31 00 42 44.330 +41 16 07.50       7        7           --           --             0        B              I 2006AJ....131.1163S
         M  51 13 29 52.698 +47 11 42.93       7        7           --           --             0        B              I 2006AJ....131.1163S
    NAME OMC-1     05 35 14     -05 22.4       4        4      18000.0      18000.0           175        E                             
 

Advanced example: Get all flux data available for a given object.

.. code-block:: python

    >>> from astroquery import simbad
    >>> from astroquery.simbad import VoTableDef
    >>> bands = 'UBVRIJHKugriz'
    >>> votabledef = VoTableDef("main_id, coordinates, "+", ".join(["Flux({})".format(x) for x in bands]))
    >>> r = simbad.QueryId('HD 163629').execute(votabledef=votabledef)
    >>> print r.table

    [ ('HD 163629', '17 57 51.2369', '-17 07 54.600', 8, 8, 34.279998779296875, 27.34000015258789, 0, 'B', '', '1998A&A...335L..65H', --, 10.59000015258789, 9.819999694824219, --, --, 8.251999855041504, 7.940999984741211, 7.76200008392334, --, --, --, --, --)]

Reference/API
=============

.. automodapi:: astroquery.simbad
    :no-inheritance-diagram:
