A Gallery of Queries
====================

A series of queries folks have performed for research or for kicks.  

Example 1:

.. code-block:: python

    >>> from astroquery.vizier import Vizier
    >>> # Vizier accepts keywords indicating wavelength & object type
    >>> # You can create a Vizier query object that respects these kws
    >>> V = Vizier(keywords=['stars:white_dwarf'])
    >>> # use astropy coordinates to set a (highly arbitrary) target
    >>> from astropy import coordinates as coord
    >>> C = coord.ICRSCoordinates(0,0,unit=('deg','deg'))
    >>> result = V.query_region(C, radius='2 degrees')
    >>> print len(result)
    31
    >>> result[0].pprint()
       LP    Rem Name  RA1950   DE1950  Rmag l_Pmag Pmag u_Pmag spClass   pm   pmPA _RA.icrs _DE.icrs
    -------- --- ---- -------- -------- ---- ------ ---- ------ ------- ------ ---- -------- --------
    584-0063          00 03 23 +00 01.8 18.1        18.3              f  0.219   93 00 05 57 +00 18.7
    643-0083          23 50 40 +00 33.4 15.9        17.0              k  0.197   93 23 53 14 +00 50.3
    584-0030          23 54 05 -01 32.3 16.6        17.7              k  0.199  193 23 56 39 -01 15.4
    

Example 2:

.. code-block:: python

    >>> from astroquery.simbad import Simbad
    >>> S = Simbad()
    >>> # You can add new output fields to queries
    >>> # see Simbad.list_votable_fields()
    >>> # bibcodelist(date1-date2) lists the number of bibliography
    >>> # items referring to each object over that date range
    >>> S.VOTABLE_FIELDS.append('bibcodelist(2003-2013)')
    >>> r = S.query_object('m31')
    >>> r.pprint()
    MAIN_ID      RA          DEC      RA_PREC DEC_PREC COO_ERR_MAJA COO_ERR_MINA COO_ERR_ANGLE COO_QUAL COO_WAVELENGTH     COO_BIBCODE     BIBLIST_2003_2013
    ------- ------------ ------------ ------- -------- ------------ ------------ ------------- -------- -------------- ------------------- -----------------
      M  31 00 42 44.330 +41 16 07.50       7        7          nan          nan             0        B              I 2006AJ....131.1163S              3758
    

Example 3:

.. code-block:: python

    >>> from astroquery import simbad
    >>> S = simbad.Simbad()
    >>> # We've seen errors where ra_prec was NAN, but it's an int: that's a problem
    >>> # this is a workaround we adapted
    >>> S.VOTABLE_FIELDS = ['main_id','ra(d)','dec(d)']
    >>> result[:5].pprint()
         MAIN_ID           RA_d        DEC_d
    ------------------ ------------ ------------
      [AU88] 5.95-37.9  11.88896000 -25.28775000
       SNR G315.0-02.3 220.76700000 -62.46200000
             [DD88] 14 192.71670000  41.12110000
            [U2000] 22  11.92991700 -25.26106400
    [MF97] NGC 5585  3 214.96500000  56.73920000
    

