.. doctest-skip-all

.. _astroquery_simbad:

************************************
SIMBAD Queries (`astroquery.simbad`)
************************************

Getting started
===============

This module can be used to query the Simbad service. Presented below are
examples that illustrate the different types of queries that can be
formulated. If successful all the queries will return the results in a
`~astropy.table.Table`.

A warning about big queries
---------------------------
The SIMBAD database has limited querying capacity.  If you spam the server with
queries, you may be temporary blacklisted.  The rate limit may vary, but you
should not submit more than ~5-10 queries per second.

If you want to perform large queries, we suggest using vectorized queries
when possible.  You can pass `~astroquery.simbad.SimbadClass.query_region`
a vector of coordinates or `~astroquery.simbad.SimbadClass.query_objects`
a list of object names, and SIMBAD will treat this submission as a single
query.  See :ref:`vectorized queries <vectorqueries>` below.

Different ways to access Simbad
-------------------------------

The Simbad tool described here provides a number of convenient methods that
internally creates a `script query
<http://simbad.u-strasbg.fr/simbad/sim-fscript>`__ to the Simbad server, which
is also how the `Simbad web interface <http://simbad.u-strasbg.fr/simbad/>`__
operates.

Simbad provides another way to access its database via `TAP
Service <http://simbad.u-strasbg.fr/simbad/sim-tap>`__. This may be better
suited for some usage. If you need a python client for TAP Services,
check out `pyvo <https://pyvo.readthedocs.io/en/latest/>`__.

Query an Identifier
-------------------


This is useful if you want to query a known identifier. For instance to query
the messier object M1:

.. code-block:: python

    >>> from astroquery.simbad import Simbad
    >>> result_table = Simbad.query_object("M1")
    >>> print(result_table)

    MAIN_ID      RA         DEC     RA_PREC DEC_PREC COO_ERR_MAJA COO_ERR_MINA COO_ERR_ANGLE COO_QUAL COO_WAVELENGTH     COO_BIBCODE
    ------- ----------- ----------- ------- -------- ------------ ------------ ------------- -------- -------------- -------------------
    M   1 05 34 31.94 +22 00 52.2       6        6          nan          nan             0        C              R 2011A&A...533A..10L

Wildcards are supported. So for instance to query messier objects from 1
through 9:

.. code-block:: python

    >>> from astroquery.simbad import Simbad
    >>> result_table = Simbad.query_object("m [1-9]", wildcard=True)
    >>> print(result_table)

    MAIN_ID      RA         DEC     RA_PREC DEC_PREC COO_ERR_MAJA COO_ERR_MINA COO_ERR_ANGLE COO_QUAL COO_WAVELENGTH     COO_BIBCODE
    ------- ----------- ----------- ------- -------- ------------ ------------ ------------- -------- -------------- -------------------
    M   1 05 34 31.94 +22 00 52.2       6        6          nan          nan             0        C              R 2011A&A...533A..10L
    M   2 21 33 27.02 -00 49 23.7       6        6      100.000      100.000             0        C              O 2010AJ....140.1830G
    M   3 13 42 11.62 +28 22 38.2       6        6      200.000      200.000             0        C              O 2010AJ....140.1830G
    M   4 16 23 35.22 -26 31 32.7       6        6      400.000      400.000             0        C              O 2010AJ....140.1830G
    M   5 15 18 33.22 +02 04 51.7       6        6          nan          nan             0        C              O 2010AJ....140.1830G
    M   6    17 40 20    -32 15.2       4        4          nan          nan             0        E              O 2009MNRAS.399.2146W
    M   7    17 53 51    -34 47.6       4        4          nan          nan             0        E              O 2009MNRAS.399.2146W
    M   8    18 03 37    -24 23.2       4        4    18000.000    18000.000           179        E
    M   9 17 19 11.78 -18 30 58.5       6        6          nan          nan             0        D                2002MNRAS.332..441F

Wildcards are supported by other queries as well - where this is the case,
examples are presented to this end. The wildcards that are supported and their
usage across all these queries is the same. To see the available wildcards and
their functions:

.. code-block:: python

    >>> from astroquery.simbad import Simbad
    >>> Simbad.list_wildcards()

    * : Any string of characters (including an empty one)

    [^0-9] : Any (one) character not in the list.

    ? : Any character (exactly one character)

    [abc] : Exactly one character taken in the list. Can also be defined by a range of characters: [A-Z]

Query a region
--------------


Queries that support a cone search with a specified radius - around an
identifier or given coordinates are also supported. If an identifier is used
then it will be resolved to coordinates using online name resolving services
available in Astropy.

.. code-block:: python

    >>> from astroquery.simbad import Simbad
    >>> result_table = Simbad.query_region("m81")
    >>> print(result_table)

                MAIN_ID                 RA           DEC      RA_PREC DEC_PREC ... COO_ERR_ANGLE COO_QUAL COO_WAVELENGTH     COO_BIBCODE
    -------------------------- ------------- ------------- ------- -------- ... ------------- -------- -------------- -------------------
    [VV2006c] J095534.0+043546 09 55 33.9854 +04 35 46.438       8        8 ...             0        B              O 2009A&A...505..385A
    ...

When no radius is specified, the radius defaults to 20 arcmin. A radius may
also be explicitly specified - it can be entered either as a string that is
acceptable by `~astropy.coordinates.Angle` or by using
the `~astropy.units.Quantity` object:

.. code-block:: python

    >>> from astroquery.simbad import Simbad
    >>> import astropy.units as u
    >>> result_table = Simbad.query_region("m81", radius=0.1 * u.deg)
    >>> # another way to specify the radius.
    >>> result_table = Simbad.query_region("m81", radius='0d6m0s')
    >>> print(result_table)

            MAIN_ID               RA      ...     COO_BIBCODE
    ----------------------- ------------- ... -------------------
                      M  81 09 55 33.1730 ... 2004AJ....127.3587F
              [SPZ2011] ML2   09 55 32.97 ... 2011ApJ...735...26S
                  [F88] X-5   09 55 33.32 ... 2001ApJ...554..202I
              [SPZ2011] 264  09 55 32.618 ... 2011ApJ...735...26S
              [SPZ2011] ML1   09 55 33.10 ... 2011ApJ...735...26S
              [SPZ2011] ML3   09 55 33.99 ... 2011ApJ...735...26S
              [SPZ2011] ML5   09 55 33.39 ... 2011ApJ...735...26S
              [SPZ2011] ML6   09 55 32.47 ... 2011ApJ...735...26S
                        ...           ... ...                 ...
              [MPC2001]   8   09 54 45.50 ... 2001A&A...379...90M
    2MASS J09561112+6859003   09 56 11.13 ... 2003yCat.2246....0C
               [PR95] 50721  09 56 36.460 ...
                    PSK  72    09 54 54.1 ...
                    PSK 353    09 56 03.7 ...
               [BBC91] S02S    09 56 07.1 ...
                    PSK 489   09 56 36.55 ... 2003AJ....126.1286L
                    PSK   7    09 54 37.0 ...




If coordinates are used, then they should be entered using an `astropy.coordinates.SkyCoord`
object.

.. code-block:: python

    >>> from astroquery.simbad import Simbad
    >>> import astropy.coordinates as coord
    >>> result_table = Simbad.query_region(coord.SkyCoord("05h35m17.3s -05h23m28s", frame='icrs'), radius='1d0m0s')
    >>> print(result_table)

            MAIN_ID               RA      ...     COO_BIBCODE
    ----------------------- ------------- ... -------------------
                  HD  38875 05 34 59.7297 ... 2007A&A...474..653V
             TYC 9390-799-1 05 33 58.2222 ... 1998A&A...335L..65H
             TYC 9390-646-1  05 35 02.830 ... 2000A&A...355L..27H
             TYC 9390-629-1  05 35 20.419 ... 2000A&A...355L..27H
             TYC 9390-857-1  05 30 58.989 ... 2000A&A...355L..27H
            TYC 9390-1171-1 05 37 35.9623 ... 1998A&A...335L..65H
             TYC 9390-654-1  05 35 27.395 ... 2000A&A...355L..27H
             TYC 9390-656-1  05 30 43.665 ... 2000A&A...355L..27H
                        ...           ... ...                 ...
             TYC 9373-779-1  05 11 57.788 ... 2000A&A...355L..27H
             TYC 9377-513-1 05 10 43.0669 ... 1998A&A...335L..65H
             TYC 9386-135-1  05 28 24.988 ... 2000A&A...355L..27H
            TYC 9390-1786-1  05 56 34.801 ... 2000A&A...355L..27H
    2MASS J05493730-8141270   05 49 37.30 ... 2003yCat.2246....0C
             TYC 9390-157-1  05 35 55.233 ... 2000A&A...355L..27H
             PKS J0557-8122   05 57 26.80 ... 2003MNRAS.342.1117M
               PKS 0602-813    05 57 30.7 ...


.. code-block:: python

    >>> from astroquery.simbad import Simbad
    >>> import astropy.coordinates as coord
    >>> import astropy.units as u
    >>> result_table = Simbad.query_region(coord.SkyCoord(31.0087, 14.0627,
    ...                                    unit=(u.deg, u.deg), frame='galactic'),
    ...                                    radius='0d0m2s')
    >>> print(result_table)

                MAIN_ID             RA      ... COO_WAVELENGTH     COO_BIBCODE
    ------------------- ------------- ... -------------- -------------------
    NAME Barnard's star 17 57 48.4980 ...              O 2007A&A...474..653V



Two other options can also be specified - the epoch and the equinox. If these
are not explicitly mentioned, then the epoch defaults to J2000 and the equinox
to 2000.0. So here is a query with all the options utilized:

.. code-block:: python

    >>> from astroquery.simbad import Simbad
    >>> import astropy.coordinates as coord
    >>> import astropy.units as u
    >>> result_table = Simbad.query_region(coord.SkyCoord(ra=11.70, dec=10.90,
    ...                                    unit=(u.deg, u.deg), frame='fk5'),
    ...                                    radius=0.5 * u.deg,
    ...                                    epoch='B1950',
    ...                                    equinox=1950)
    >>> print(result_table)

            MAIN_ID               RA      ...     COO_BIBCODE
    ----------------------- ------------- ... -------------------
                  PHL  6696       00 49.4 ...
                BD+10    97 00 49 25.4553 ... 2007A&A...474..653V
             TYC  607-238-1  00 48 53.302 ... 2000A&A...355L..27H
                  PHL  2998       00 49.3 ...
    2MASS J00492121+1121094  00 49 21.219 ... 2003yCat.2246....0C
            TYC  607-1135-1 00 48 46.5838 ... 1998A&A...335L..65H
    2MASX J00495215+1118527  00 49 52.154 ... 2006AJ....131.1163S
                BD+10    98 00 50 03.4124 ... 1998A&A...335L..65H
                        ...           ... ...                 ...
             TYC  607-971-1 00 47 38.0430 ... 1998A&A...335L..65H
             TYC  607-793-1  00 50 35.545 ... 2000A&A...355L..27H
    USNO-A2.0 0975-00169117  00 47 55.351 ... 2007ApJ...664...53A
             TYC  607-950-1  00 50 51.875 ... 2000A&A...355L..27H
                BD+10   100 00 51 15.0789 ... 1998A&A...335L..65H
              TYC  608-60-1  00 51 13.314 ... 2000A&A...355L..27H
             TYC  608-432-1  00 51 05.289 ... 2000A&A...355L..27H
             TYC  607-418-1  00 49 09.636 ... 2000A&A...355L..27H


Query a catalogue
-----------------

Queries can also be formulated to return all the objects from a catalogue. For
instance to query the ESO catalog:

.. code-block:: python

    >>> from astroquery.simbad import Simbad
    >>> limitedSimbad = Simbad()
    >>> limitedSimbad.ROW_LIMIT = 6
    >>> result_table = limitedSimbad.query_catalog('eso')
    >>> print(result_table)

    MAIN_ID              RA      ... COO_WAVELENGTH     COO_BIBCODE
    ----------------------- ------------ ... -------------- -------------------
    2MASS J08300740-4325465  08 30 07.41 ...              I 2003yCat.2246....0C
    NGC  2573 01 41 35.091 ...              I 2006AJ....131.1163S
    ESO   1-2   05 04 36.8 ...                1982ESO...C......0L
    ESO   1-3 05 22 36.509 ...              I 2006AJ....131.1163S
    ESO   1-4 07 49 28.813 ...              I 2006AJ....131.1163S
    ESO   1-5 08 53 05.006 ...              I 2006AJ....131.1163S


Query a bibcode
---------------


This retrieves the reference corresponding to a bibcode.

.. code-block:: python

    >>> from astroquery.simbad import Simbad
    >>> result_table = Simbad.query_bibcode('2005A&A.430.165F')
    >>> print(result_table)

    References
    ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    2005A&A...430..165F  --  ?
    Astron. Astrophys., 430, 165-186 (2005)
    FAMAEY B., JORISSEN A., LURI X., MAYOR M., UDRY S., DEJONGHE H. and TURON C.
    Local kinematics of K and M giants from CORAVEL/Hipparcos/Tycho-2 data. Revisiting the concept of  superclusters.
    Files: (abstract)
    Notes: <Available at CDS: tablea1.dat notes.dat>

Wildcards can be used in these queries as well. So to retrieve all the bibcodes
from a given journal in a given year:

.. code-block:: python

    >>> from astroquery.simbad import Simbad
    >>> result_table = Simbad.query_bibcode('2013A&A*', wildcard=True)
    >>> print(result_table)

    References
    -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    2013A&A...549A...1G  --  ?
    Astron. Astrophys., 549A, 1-1 (2013)
    GENTILE M., COURBIN F. and MEYLAN G.
    Interpolating point spread function anisotropy.
    Files: (abstract) (no object)

    2013A&A...549A...2L  --  ?
    Astron. Astrophys., 549A, 2-2 (2013)
    LEE B.-C., HAN I. and PARK M.-G.
    Planetary companions orbiting M giants HD 208527 and HD 220074.
    Files: (abstract)

    2013A&A...549A...3C  --  ?
    Astron. Astrophys., 549A, 3-3 (2013)
    COCCATO L., MORELLI L., PIZZELLA A., CORSINI E.M., BUSON L.M. and DALLA BONTA E.
    Spectroscopic evidence of distinct stellar populations in the  counter-rotating stellar disks of NGC 3593 and NGC 4550.
    Files: (abstract)

    2013A&A...549A...4S  --  ?
    Astron. Astrophys., 549A, 4-4 (2013)
    SCHAERER D., DE BARROS S. and SKLIAS P.
    Properties of z ~ 3-6 Lyman break galaxies. I. Testing star formation  histories and the SFR-mass relation with ALMA and near-IR spectroscopy.
    Files: (abstract)

    2013A&A...549A...5R  --  ?
    Astron. Astrophys., 549A, 5-5 (2013)
    RYGL K.L.J., WYROWSKI F., SCHULLER F. and MENTEN K.M.
    Initial phases of massive star formation in high infrared extinction  clouds. II. Infall and onset of star formation.
    Files: (abstract)

    2013A&A...549A...6K  --  ?
    Astron. Astrophys., 549A, 6-6 (2013)
    KAMINSKI T., SCHMIDT M.R. and MENTEN K.M.
    Aluminium oxide in the optical spectrum of VY Canis Majoris.
    Files: (abstract)

Query object identifiers
------------------------


These queries can be used to retrieve all of the names (identifiers)
associated with an object.

.. code-block:: python

    >>> from astroquery.simbad import Simbad
    >>> result_table = Simbad.query_objectids("Polaris")
    >>> print(result_table)
               ID
    -----------------------
               NAME Polaris
            NAME North Star
              NAME Lodestar
                   PLX  299
                    SBC9 76
                  *   1 UMi
                  * alf UMi
              AAVSO 0122+88
                ADS  1477 A
                 AG+89    4
                BD+88     8
          CCDM J02319+8915A
            CSI+88     8  1
                   FK5  907
                   GC  2243
                 GCRV  1037
                        ...
                 PPM    431
                  ROT  3491
                 SAO    308
                 SBC7    51
                 SKY#  3738
                  TD1   835
             TYC 4628-237-1
                UBV   21589
               UBV M   8201
                 V* alf UMi
                PLX  299.00
       WDS J02318+8916Aa,Ab
               ADS  1477 AP
                ** WRH   39
           WDS J02318+8916A
               ** STF   93A
    2MASS J02314822+8915503


Query a bibobj
--------------


These queries can be used to retrieve all the objects that are contained in the
article specified by the bibcode:

.. code-block:: python

    >>> from astroquery.simbad import Simbad
    >>> result_table = Simbad.query_bibobj('2006AJ....131.1163S')
    >>> print(result_table)

            MAIN_ID              RA          DEC      RA_PREC DEC_PREC ... COO_ERR_MINA COO_ERR_ANGLE COO_QUAL COO_WAVELENGTH     COO_BIBCODE
                              "h:m:s"      "d:m:s"                     ...     mas           deg
    ----------------------- ------------ ------------ ------- -------- ... ------------ ------------- -------- -------------- -------------------
                      M  32 00 42 41.825 +40 51 54.61       7        7 ...           --             0        B              I 2006AJ....131.1163S
                      M  31 00 42 44.330 +41 16 07.50       7        7 ...           --             0        B              I 2006AJ....131.1163S
                   NAME SMC   00 52 38.0    -72 48 01       5        5 ...           --             0        D              O 2003A&A...412...45P
            Cl Melotte   22     03 47 00     +24 07.0       4        4 ...           --             0        E              O 2009MNRAS.399.2146W
    2MASX J04504846-7531580 04 50 48.462 -75 31 58.08       7        7 ...           --             0        B              I 2006AJ....131.1163S
                   NAME LMC   05 23 34.6    -69 45 22       5        5 ...           --             0        D              O 2003A&A...412...45P
          NAME Lockman Hole   10 45 00.0    +58 00 00       5        5 ...           --             0        E                2011ApJ...734...99H
            NAME Gal Center  17 45 40.04  -29 00 28.1       6        6 ...           --             0        E


Query based on any criteria
----------------------------


Anything done in SIMBAD's `criteria interface`_ can be done via astroquery.
See that link for details of how these queries are formed.

.. code-block:: python

   >>> from astroquery.simbad import Simbad
   >>> result = Simbad.query_criteria('region(box, GAL, 0 +0, 3d 1d)', otype='SNR')
   >>> print(result)
          MAIN_ID             RA         DEC     RA_PREC DEC_PREC COO_ERR_MAJA COO_ERR_MINA COO_ERR_ANGLE COO_QUAL COO_WAVELENGTH     COO_BIBCODE
   --------------------- ----------- ----------- ------- -------- ------------ ------------ ------------- -------- -------------- -------------------
     EQ J174702.6-282733  17 47 02.6   -28 27 33       5        5          nan          nan             0        D                2002ApJ...565.1017S
   [L92] 174535.0-280410  17 48 44.4   -28 05 06       5        5     3000.000     3000.000             0        D
              [GWC93] 19  17 42 04.9   -30 04 04       5        5     3000.000     3000.000             1        D
         SNR G359.1-00.2    17 43 29    -29 45.9       4        4          nan          nan             0        E                2000AJ....119..207L
         SNR G000.1-00.2  17 48 42.5   -28 09 11       5        5          nan          nan             0        D                2008ApJS..177..255L
         SNR G359.9-00.9     17 45.8      -29 03       3        3          nan          nan             0
         SNR G359.4-00.1    17 44 37    -29 27.2       4        4    18000.000    18000.000             1        E
              NAME SGR D    17 48 42    -28 01.4       4        4    18000.000    18000.000             0        E
         SNR G359.1-00.5    17 45 25    -29 57.9       4        4    18000.000    18000.000             1        E
          NAME SGR D SNR     17 48.7      -28 07       3        3          nan          nan             0        E
       Suzaku J1747-2824    17 47 00    -28 24.5       4        4          nan          nan             0        E                2007ApJ...666..934C
         SNR G000.4+00.2 17 46 27.65 -28 36 05.6       6        6      300.000      300.000             1        D
         SNR G001.4-00.1  17 49 28.1   -27 47 45       5        5          nan          nan             0        D                1999ApJ...527..172Y
        GAL 000.61+00.01     17 47.0      -28 25       3        3          nan          nan             0        D
         SNR G000.9+00.1     17 47.3      -28 09       3        3          nan          nan             0        E              R 2009BASI...37...45G
         SNR G000.3+00.0  17 46 14.9   -28 37 15       5        5     3000.000     3000.000             1        D
         SNR G001.0-00.1     17 48.5      -28 09       3        3          nan          nan             0        E              R 2009BASI...37...45G
         NAME SGR A EAST    17 45 47    -29 00.2       4        4    18000.000    18000.000             1        E


.. _vectorqueries:

Vectorized Queries
------------------

You can query multiple regions at once using vectorized queries.
Each region must have the same radius.

.. code-block:: python

    >>> from astroquery.simbad import Simbad
    >>> import astropy.coordinates as coord
    >>> import astropy.units as u
    >>> result_table = Simbad.query_region(coord.SkyCoord(ra=[10, 11], dec=[10, 11],
    ...                                    unit=(u.deg, u.deg), frame='fk5'),
    ...                                    radius=0.1 * u.deg)
    >>> print(result_table)
             MAIN_ID                RA           DEC      RA_PREC DEC_PREC COO_ERR_MAJA COO_ERR_MINA COO_ERR_ANGLE COO_QUAL COO_WAVELENGTH     COO_BIBCODE
                                 "h:m:s"       "d:m:s"                         mas          mas           deg
    ------------------------- ------------- ------------- ------- -------- ------------ ------------ ------------- -------- -------------- -------------------
        PLCKECC G118.25-52.70    00 39 55.5     +10 03 42       5        5           --           --             0        E              m 2011A&A...536A...7P
              IRAS 00373+0947    00 39 55.6     +10 04 15       5        5    39000.000    29000.000            67        E              F 1988NASAR1190....1B
              IRAS 00371+0946    00 39 43.1     +10 03 21       5        5    88000.000    32000.000            67        E              F 1988NASAR1190....1B
                 LEDA 1387229    00 43 57.2     +10 58 54       5        5           --           --             0        D              O 2003A&A...412...45P
                 LEDA 1387610    00 43 50.3     +11 00 32       5        5           --           --             0        D              O 2003A&A...412...45P
                 LEDA 1386801    00 43 53.1     +10 56 59       5        5           --           --             0        D              O 2003A&A...412...45P
                 LEDA 1387466    00 43 41.3     +10 59 57       5        5           --           --             0        D              O 2003A&A...412...45P
          NVSS J004420+110010   00 44 20.74   +11 00 10.8       6        6     2800.000     1200.000            90        D                1996AJ....111.1945D
     SDSS J004340.18+105815.6 00 43 40.1841 +10 58 15.602      14       14        0.207        0.124            90        A              O 2018yCat.1345....0G
    GALEX 2675641789401008459  00 43 57.698  +10 54 46.15       7        7           --           --             0        D                2007ApJ...664...53A
     SDSS J004422.75+110104.3  00 44 22.753  +11 01 04.34       7        7           --           --             0        C              O 2017A&A...597A..79P
               TYC  607-628-1 00 44 05.6169 +11 05 41.195      14       14        0.047        0.033            90        A              O 2018yCat.1345....0G

You can do the same based on IDs.  If you add the votable field ``typed_id``, a
column showing your input identifier will be added:

.. code-block:: python

    >>> from astroquery.simbad import Simbad
    >>> Simbad.add_votable_fields('typed_id')
    >>> result_table = Simbad.query_objects(["M1", "M2", "M3", "M4"])
    >>> print(result_table)
    MAIN_ID      RA         DEC     RA_PREC DEC_PREC COO_ERR_MAJA COO_ERR_MINA COO_ERR_ANGLE COO_QUAL COO_WAVELENGTH     COO_BIBCODE     TYPED_ID
              "h:m:s"     "d:m:s"                        mas          mas           deg
    ------- ----------- ----------- ------- -------- ------------ ------------ ------------- -------- -------------- ------------------- --------
      M   1 05 34 31.94 +22 00 52.2       6        6           --           --             0        C              R 2011A&A...533A..10L       M1
      M   2 21 33 27.02 -00 49 23.7       6        6      100.000      100.000            90        C              O 2010AJ....140.1830G       M2
      M   3 13 42 11.62 +28 22 38.2       6        6      200.000      200.000            90        C              O 2010AJ....140.1830G       M3
      M   4 16 23 35.22 -26 31 32.7       6        6      400.000      400.000            90        C              O 2010AJ....140.1830G       M4

However, note that missing data will result in missing lines:

.. code-block:: python

    >>> from astroquery.simbad import Simbad
    >>> result_table = Simbad.query_objects(["M1", "notanobject", "m2", "m1000"])
    >>> print(result_table)
    UserWarning: Warning: The script line number 4 raised an error (recorded in the `errors` attribute of the result table): 'notanobject': No known catalog could be found
    (error.line, error.msg))
    MAIN_ID      RA         DEC     RA_PREC DEC_PREC COO_ERR_MAJA COO_ERR_MINA COO_ERR_ANGLE COO_QUAL COO_WAVELENGTH     COO_BIBCODE
              "h:m:s"     "d:m:s"                        mas          mas           deg
    ------- ----------- ----------- ------- -------- ------------ ------------ ------------- -------- -------------- -------------------
      M   1 05 34 31.94 +22 00 52.2       6        6           --           --             0        C              R 2011A&A...533A..10L
      M   2 21 33 27.02 -00 49 23.7       6        6      100.000      100.000            90        C              O 2010AJ....140.1830G

Only the results for M1 and M2 are included.  As of May 2019, there is a
feature request in place with SIMBAD to return blank rows with the queried
identifier indicated.

You can also stitch together region queries by writing a sophisticated script:

.. code-block:: python

   >>> from astroquery.simbad import Simbad
   >>> script = '(region(box, GAL, 0 +0, 0.5d 0.5d) | region(box, GAL, 43.3 -0.2, 0.25d 0.25d))'
   >>> result = Simbad.query_criteria(script, otype='SNR')
   >>> print(result)
   <Table masked=True length=4>
         MAIN_ID           RA          DEC      RA_PREC DEC_PREC COO_ERR_MAJA COO_ERR_MINA COO_ERR_ANGLE COO_QUAL COO_WAVELENGTH     COO_BIBCODE
                        "h:m:s"      "d:m:s"                         mas          mas           deg
          object         str13        str13      int16   int16     float32      float32        int16       str1        str1             object
    ----------------- ------------ ------------ ------- -------- ------------ ------------ ------------- -------- -------------- -------------------
      SNR G359.9-00.9      17 45.8       -29 03       3        3           --           --             0
      NAME Sgr A East     17 45 41     -29 00.8       4        4           --           --             0        D                2010ApJS..188..405A
                W 49b 19 11 09.000 +09 06 24.00       7        7           --           --             0        D                2015ApJS..217....2M
    SNR G000.13-00.12      17 46.4       -28 53       3        3           --           --             0        E                2013MNRAS.434.1339H



Customizing the default settings
================================

There may be times when you wish to change the defaults that have been set for
the Simbad queries.

Changing the row limit
----------------------


To fetch all the rows in the result, the row limit must be set to 0. However for some
queries, results are likely to be very large, in such cases it may be best to
limit the rows to a smaller number. If you want to do this only for the current
python session then:

.. code-block:: python

    >>> from astroquery.simbad import Simbad
    >>> Simbad.ROW_LIMIT = 15 # now any query fetches at most 15 rows

If you would like to make your choice persistent, then you can do this by
modifying the setting in the Astroquery configuration file.

Changing the timeout
--------------------


The timeout is the time limit in seconds for establishing connection with the
Simbad server and by default it is set to 100 seconds. You may want to modify
this - again you can do this at run-time if you want to adjust it only for the
current session. To make it persistent, you must modify the setting in the
Astroquery configuration file.

.. code-block:: python

    >>> from astroquery.simbad import Simbad
    >>> Simbad.TIMEOUT = 60 # sets the timeout to 60s

Specifying which VOTable fields to include in the result
--------------------------------------------------------


The VOTable fields that are currently returned in the result are set to
``main_id`` and ``coordinates``. However you can specify other fields that you
also want to be fetched in the result. To see the list of the fields:

.. code-block:: python

     >>> from astroquery.simbad import Simbad
     >>> Simbad.list_votable_fields()

              col0                   col1              col2
    ------------------------ -------------------- --------------
          bibcodelist(y1-y2) fluxdata(filtername)       plx_qual
                         cel                 gcrv             pm
                        cl.g                  gen     pm_bibcode
                    coo(opt)                   gj   pm_err_angle
                 coo_bibcode                 hbet    pm_err_maja
               coo_err_angle                hbet1    pm_err_mina
                coo_err_maja                 hgam        pm_qual


The above shows just a small snippet of the table that is returned and has all
the fields sorted lexicographically column-wise. For more information on a
particular field:

.. code-block:: python

    >>> from astroquery.simbad import Simbad
    >>> Simbad.get_field_description('ra_prec')

    right ascension precision code (0:1/10deg, ..., 8: 1/1000 arcsec)

To set additional fields to be returned in the VOTable:

.. code-block:: python

     >>> from astroquery.simbad import Simbad
     >>> customSimbad = Simbad()

     # see which fields are currently set

     >>> customSimbad.get_votable_fields()

     ['main_id', 'coordinates']

     # To set other fields

     >>> customSimbad.add_votable_fields('mk', 'rot', 'bibcodelist(1800-2014)')
     >>> customSimbad.get_votable_fields()

     ['main_id', 'coordinates', 'mk', 'rot', 'bibcodelist(1800-2014')]

You can also remove a field you have set or
:meth:`astroquery.simbad.SimbadClass.reset_votable_fields`.  Continuing from
the above example:

.. code-block:: python

    >>> customSimbad.remove_votable_fields('mk', 'coordinates')
    >>> customSimbad.get_votable_fields()

    ['main_id', 'rot', 'bibcodelist(1800-2014)']

    # reset back to defaults

    >>> customSimbad.reset_votable_fields()
    >>> customSimbad.get_votable_fields()

    ['main_id', 'coordinates']


Returning the queried name in the return table
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
You can include the name(s) queried in the output table by adding ``typed_id`` to
the votable fields.  This was also mentioned in :ref:`vectorized queries
<vectorqueries>` above, but we emphasize here that it works for all queries.

    >>> Simbad.add_votable_fields('typed_id')
    >>> Simbad.query_objects(['M31', 'Eta Carinae', 'Alpha Centauri'])
    <Table masked=True length=3>
     MAIN_ID        RA           DEC      RA_PREC DEC_PREC COO_ERR_MAJA COO_ERR_MINA COO_ERR_ANGLE COO_QUAL COO_WAVELENGTH     COO_BIBCODE        TYPED_ID
                "h:m:s"       "d:m:s"                         mas          mas           deg
      object      str13         str13      int16   int16     float32      float32        int16       str1        str1             object           object
    --------- ------------- ------------- ------- -------- ------------ ------------ ------------- -------- -------------- ------------------- --------------
        M  31  00 42 44.330  +41 16 07.50       7        7           --           --             0        C              I 2006AJ....131.1163S            M31
    + eta Car 10 45 03.5455 -59 41 03.951      11       11       11.000       10.000            90        B              O 2000A&A...355L..27H    Eta Carinae
    + alf Cen 14 39 29.7199 -60 49 55.999       9        9           --           --             0        C              O 2016A&A...589A.115S Alpha Centauri

    >>> Simbad.query_object('M31')
    <Table masked=True length=1>
     MAIN_ID      RA          DEC      RA_PREC DEC_PREC COO_ERR_MAJA COO_ERR_MINA COO_ERR_ANGLE COO_QUAL COO_WAVELENGTH     COO_BIBCODE     TYPED_ID
              "h:m:s"      "d:m:s"                         mas          mas           deg
     object    str13        str13      int16   int16     float32      float32        int16       str1        str1             object        object
    ------- ------------ ------------ ------- -------- ------------ ------------ ------------- -------- -------------- ------------------- --------
      M  31 00 42 44.330 +41 16 07.50       7        7           --           --             0        C              I 2006AJ....131.1163S      M31

Specifying the format of the included VOTable fields
----------------------------------------------------

The output for several of the VOTable fields can be formatted in many
different ways described in the help page of the SIMBAD query interface (see
Sect. 4.3 of `this page
<http://simbad.u-strasbg.fr/simbad/sim-help?Page=sim-fscript>`__). As an
example, the epoch and equinox for the Right Ascension and Declination can
be specified as follows (e.g. epoch of J2017.5 and equinox of 2000):

.. code-block:: python

    >>> customSimbad.add_votable_fields('ra(2;A;ICRS;J2017.5;2000)', 'dec(2;D;ICRS;J2017.5;2000)')
    >>> customSimbad.remove_votable_fields('coordinates')
    >>> customSimbad.query_object("HD189733")
    <Table masked=True length=1>
     MAIN_ID  RA_2_A_ICRS_J2017_5_2000 DEC_2_D_ICRS_2017_5_2000
                       "h:m:s"                  "d:m:s"
      object           str13                    str13
    --------- ------------------------ ------------------------
    HD 189733            20 00 43.7107            +22 42 39.064


Reference/API
=============

.. automodapi:: astroquery.simbad
    :no-inheritance-diagram:

.. _criteria interface: http://simbad.u-strasbg.fr/simbad/sim-fsam
