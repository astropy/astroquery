.. _astroquery_simbad:

************************************
SIMBAD Queries (`astroquery.simbad`)
************************************

Getting started
===============

This module can be used to query the SIMBAD service. Presented below are
examples that illustrate the different types of queries that can be
formulated. If successful all the queries will return the results in a
`~astropy.table.Table`.

A warning about query rate
--------------------------

The SIMBAD database is widely used and has to limit the rate of incoming queries.
If you spam the server with more that ~5-10 queries per second you will be
blacklisted for an hour. This can happen when a query method is called within a loop.
There is always a way to send the information in a bigger query. You can pass
`~astroquery.simbad.SimbadClass.query_region` a vector of coordinates or
`~astroquery.simbad.SimbadClass.query_objects` a list of object names,
and SIMBAD will treat this submission as a single query.

About deprecation warnings
--------------------------

The SIMBAD module has been rewritten with astroquery > 0.4.7. If you're here following a
deprecation warning, this is your go-to page:

.. toctree::
    :maxdepth: 2

    /simbad/simbad_evolution

Different ways to access SIMBAD
-------------------------------

The SIMBAD module described here provides methods that write pre-defined ADQL queries. These
methods are described in the next sections.

A more versatile option is to query SIMBAD directly with your own ADQL query via
Table Access Protocol (TAP) with the `~astroquery.simbad.SimbadClass.query_tap` method.
This is described in :ref:`query TAP <query-tap>`.

Query modes
===========

Objects queries
---------------

Query by an Identifier
^^^^^^^^^^^^^^^^^^^^^^

This is useful if you want to query a known identifier (name). For instance to query
the messier object M1:

.. doctest-remote-data::

    >>> from astroquery.simbad import Simbad
    >>> result_table = Simbad.query_object("m1")
    >>> print(result_table)
    main_id    ra     dec   ... coo_wavelength     coo_bibcode     matched_id
              deg     deg   ...                                              
    ------- ------- ------- ... -------------- ------------------- ----------
      M   1 83.6287 22.0147 ...              R 1995AuJPh..48..143S      M   1
    
Wildcards are supported, but they render the query case-sensitive. So for instance to query messier
objects from 1 through 9:

..
    The following example is very slow ~6s due to a current (early 2024) bug in
    the SIMBAD regexp. This should be removed from the skipped tests
    once the bug is fixed upstream.

.. doctest-remote-data::

    >>> from astroquery.simbad import Simbad
    >>> result_table = Simbad.query_object("M [1-9]", wildcard=True) # doctest: +SKIP
    >>> print(result_table) # doctest: +SKIP
     main_id          ra         ...     coo_bibcode     matched_id
                     deg         ...                               
    --------- ------------------ ... ------------------- ----------
        M   1            83.6287 ... 1995AuJPh..48..143S      M   1
        M   2 323.36258333333336 ... 2010AJ....140.1830G      M   2
        M   3  205.5484166666666 ... 2010AJ....140.1830G      M   3
    NGC  6475 268.44699999999995 ... 2021A&A...647A..19T      M   7
    NGC  6405 265.06899999999996 ... 2021A&A...647A..19T      M   6
        M   4 245.89675000000003 ... 2010AJ....140.1830G      M   4
        M   8 270.90416666666664 ...                          M   8
        M   9 259.79908333333333 ... 2002MNRAS.332..441F      M   9
        M   5 229.63841666666673 ... 2010AJ....140.1830G      M   5


We can see that the messier objects are indeed found. Their ``main_id`` is not necessarly
the one corresponding to the wildcard expression. The column ``matched_id`` will return which
identifier was matched. The wildcard parameter can often be replaced by a way faster query
done with `~astroquery.simbad.SimbadClass.query_objects`. 

Wildcards are supported by:
 - `~astroquery.simbad.SimbadClass.query_object`
 - `~astroquery.simbad.SimbadClass.query_objects`
 - `~astroquery.simbad.SimbadClass.query_bibcode`

The wildcards that are supported and their usage across all these queries is the same.
To see the available wildcards and their functions:

.. code-block:: python

    >>> from astroquery.simbad.utils import list_wildcards
    >>> list_wildcards()
    *: Any string of characters (including an empty one)
    ?: Any character (exactly one character)
    [abc]: Exactly one character taken in the list. Can also be defined by a range of characters: [A-Z]
    [^0-9]: Any (one) character not in the list.

Query to get all names (identifiers) of an object
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

These queries can be used to retrieve all of the names (identifiers)
associated with an object.

.. 
    This could change often (each time someone invents a new name for Polaris).

.. doctest-remote-data::

    >>> from astroquery.simbad import Simbad
    >>> result_table = Simbad.query_objectids("Polaris")
    >>> print(result_table)  # doctest: +IGNORE_OUTPUT
    <Table length=46>
               id          
             object        
    -----------------------
                  HIP 11767
              TIC 303256075
              NAME Lodestar
                   PLX  299
                    SBC9 76
                  *   1 UMi
                        ...
               ADS  1477 AP
                ** WRH   39
           WDS J02318+8916A
               ** STF   93A
    2MASS J02314822+8915503
            NAME North Star
                  WEB  2438


Query a region
^^^^^^^^^^^^^^

Query in a cone with a specified radius. The center can be a string with an
identifier, a string representing coordinates, or a `~astropy.coordinates.SkyCoord`.

.. doctest-remote-data::

    >>> from astroquery.simbad import Simbad
    >>> simbad = Simbad()
    >>> simbad.ROW_LIMIT = 10
    >>> result_table = simbad.query_region("m81", radius="0.5d")
    >>> print(result_table)   # doctest: +IGNORE_OUTPUT
                 main_id                       ra                dec        ... coo_err_angle coo_wavelength     coo_bibcode    
                                              deg                deg        ...      deg                                        
    ---------------------------------- ------------------ ----------------- ... ------------- -------------- -------------------
                          [PR95] 40298 149.14159166666667 69.19170000000001 ...            --                                   
                           [GTK91b] 19 149.03841666666668 69.21222222222222 ...            --                                   
                           [GTK91b] 15 149.26095833333332 69.22230555555556 ...            --                                   
                               PSK 212 148.86083333333332 69.15333333333334 ...            --                                   
                               PSK 210  148.8595833333333 69.20111111111112 ...            --                                   
                           [BBC91] N06 148.84166666666664 69.14222222222223 ...            --                                   
    [GKP2011] M81C J095534.66+691213.7 148.89441666666667 69.20380555555556 ...            --              O 2011ApJ...743..176G
                          [PR95] 51153 148.89568749999998  69.1995888888889 ...            --              O 2012ApJ...747...15K
                               PSK 300 148.96499999999997 69.16638888888889 ...            --                                   
                               PSK 234  148.9008333333333 69.19944444444445 ...            --                                   

When no radius is specified, the radius defaults to 2 arcmin. When the radius is
explicitly specified it can be either a string accepted by
`~astropy.coordinates.Angle` (ex: ``radius='0d6m0s'``)or directly a
`~astropy.units.Quantity` object.

If coordinates are used, then they should be entered using an `astropy.coordinates.SkyCoord`
object.

.. doctest-remote-data::

    >>> from astroquery.simbad import Simbad
    >>> from astropy.coordinates import SkyCoord
    >>> simbad = Simbad()
    >>> simbad.ROW_LIMIT = 10
    >>> coordinate = SkyCoord("05h35m17.3s -05h23m28s", frame='icrs')
    >>> simbad.query_region(coordinate, radius='1d0m0s')   # doctest: +IGNORE_OUTPUT
    <Table length=10>
              main_id                    ra               dec         ... coo_err_angle coo_wavelength     coo_bibcode    
                                        deg               deg         ...      deg                                        
               object                 float64           float64       ...     int16          str1             object      
    ---------------------------- ----------------- ------------------ ... ------------- -------------- -------------------
                 TYC 9390-1857-1 89.18327041666667 -81.31254972222223 ...            71              O 2016A&A...595A...2G
                    PKS 0602-813 89.37791666666668 -81.37027777777777 ...            --                                   
                 TYC 9390-1786-1    89.14477451271    -81.41309658604 ...            90              O 2020yCat.1350....0G
                 TYC 9390-1878-1    88.75276112064    -81.44513030144 ...            90              O 2020yCat.1350....0G
    Gaia DR3 4621434189736118144     89.2148880241    -81.42047989066 ...            90              O 2020yCat.1350....0G
    Gaia DR3 4621443844823809536 89.77428052292792 -81.21112425878056 ...            90              O 2020yCat.1350....0G
                     CD-81   190 89.17676879332167 -81.38640963209807 ...            90              O 2020yCat.1350....0G
                  PKS J0557-8122           89.3624           -81.3742 ...             0              R 2012MNRAS.422.1527M
                UCAC4 044-003417    89.50051776702    -81.21953460424 ...            90              O 2020yCat.1350....0G
                IRAS F05246-8120 80.00253626975339 -81.29356823821976 ...           100              F 1990IRASF.C......0M


.. doctest-remote-data::

    >>> from astroquery.simbad import Simbad
    >>> from astropy.coordinates import SkyCoord
    >>> import astropy.units as u
    >>> Simbad.query_region(SkyCoord(31.0087, 14.0627, unit=(u.deg, u.deg), frame='galactic'),
    ...                     radius=2 * u.arcsec)
    <Table length=2>
          main_id               ra        ... coo_wavelength     coo_bibcode    
                               deg        ...                                   
           object            float64      ...      str1             object      
    ------------------- ----------------- ... -------------- -------------------
               GJ 699 b 269.4520769586187 ...              O 2020yCat.1350....0G
    NAME Barnard's star 269.4520769586187 ...              O 2020yCat.1350....0G         

Calling `~astroquery.simbad.SimbadClass.query_region` within a loop is *very*
inefficient. If you need to query many regions, use a `~astropy.coordinates.SkyCoord`
with a list of centers and a list of radii. It looks like this:

.. doctest-remote-data::

    >>> from astroquery.simbad import Simbad
    >>> from astropy.coordinates import SkyCoord
    >>> import astropy.units as u
    >>> Simbad.query_region(SkyCoord(ra=[10, 11], dec=[10, 11],
    ...                     unit=(u.deg, u.deg), frame='fk5'),
    ...                     radius=[0.1 * u.deg, 2* u.arcmin])
    <Table length=6>
            main_id                  ra         ...     coo_bibcode    
                                    deg         ...                    
             object               float64       ...        object      
    ------------------------ ------------------ ... -------------------
    SDSS J004014.26+095527.0 10.059442999999998 ... 2020ApJS..250....8L
                LEDA 1387229 10.988333333333335 ... 2003A&A...412...45P
             IRAS 00371+0946   9.92962860161661 ... 1988NASAR1190....1B
             IRAS 00373+0947  9.981768085280164 ... 1988NASAR1190....1B
       PLCKECC G118.25-52.70  9.981250000000001 ... 2011A&A...536A...7P
      GALEX J004011.0+095752 10.045982309580001 ... 2020yCat.1350....0G

Query a catalogue
^^^^^^^^^^^^^^^^^

Queries can also be formulated to return all the objects from a catalogue. For
instance to query the ESO catalog:

.. doctest-remote-data::

    >>> from astroquery.simbad import Simbad
    >>> limitedSimbad = Simbad()
    >>> limitedSimbad.ROW_LIMIT = 6
    >>> limitedSimbad.query_catalog('ESO')
    <Table length=6>
     main_id          ra         ...     coo_bibcode     catalog_id
                     deg         ...                               
      object       float64       ...        object         object  
    --------- ------------------ ... ------------------- ----------
    NGC  2573     25.40834109527 ... 2020yCat.1350....0G  ESO   1-1
    ESO   1-2           76.15327 ... 2020MNRAS.494.1784A  ESO   1-2
    ESO   1-3  80.65212083333333 ... 2006AJ....131.1163S  ESO   1-3
    ESO   1-4 117.37006325383999 ... 2020yCat.1350....0G  ESO   1-4
    ESO   1-5  133.2708583333333 ... 2006AJ....131.1163S  ESO   1-5
    ESO   1-6    216.83122280179 ... 2020yCat.1350....0G  ESO   1-6

To see the available catalogues, you can write a custom ADQL query on the ``cat`` table. 
For example to get the 10 biggest catalogs in SIMBAD, it looks like this:

.. doctest-remote-data::

    >>> from astroquery.simbad import Simbad
    >>> Simbad.query_tap('SELECT TOP 10 cat_name, description FROM cat ORDER BY "size" DESC')
    <Table length=10>
    cat_name                           description                           
     object                               object                             
    -------- ----------------------------------------------------------------
        Gaia                                                             Gaia
       2MASS                               2 Micron Sky Survey, Point Sources
         TIC                                               TESS Input Catalog
        SDSS                                         Sloan Digital Sky Survey
         TYC                                                    Tycho mission
        OGLE                              Optical Gravitational Lensing Event
       UCAC4                               Fourth USNO CCD Astrograph Catalog
         GSC                                             Guide Star Catalogue
        WISE Wide-field Infrared Survey Explorer Final Release Source Catalog
        LEDA                              Lyon-Meudon Extragalactic DatabaseA


Bibliographic queries
---------------------

Query a bibcode
^^^^^^^^^^^^^^^

This retrieves the reference corresponding to a bibcode.

.. doctest-remote-data::

    >>> from astroquery.simbad import Simbad
    >>> Simbad.query_bibcode('2005A&A.430.165F')
    <Table length=1>
          bibcode                  doi             journal ... volume  year
           object                 object            object ... int32  int16
    ------------------- -------------------------- ------- ... ------ -----
    2005A&A...430..165F 10.1051/0004-6361:20041272     A&A ...    430  2005

The abstract of the article can also be added as an other column in the output by setting
the ``abstract`` parameter to ``True``.

Wildcards can be used in these queries as well. So to retrieve all the bibcodes
from a given journal in a given year:

.. doctest-remote-data::

    >>> from astroquery.simbad import Simbad
    >>> Simbad.query_bibcode('2013A&ARv.*', wildcard=True)  # doctest: +IGNORE_OUTPUT
        <Table length=9>
          bibcode                  doi            journal ... volume  year
           object                 object           object ... int32  int16
    ------------------- ------------------------- ------- ... ------ -----
    2013A&ARv..21...62D 10.1007/s00159-013-0062-7   A&ARv ...     21  2013
    2013A&ARv..21...59I 10.1007/s00159-013-0059-2   A&ARv ...     21  2013
    2013A&ARv..21...70B 10.1007/s00159-013-0070-7   A&ARv ...     21  2013
    2013A&ARv..21...69R 10.1007/s00159-013-0069-0   A&ARv ...     21  2013
    2013A&ARv..21...61R 10.1007/s00159-013-0061-8   A&ARv ...     21  2013
    2013A&ARv..21...64D 10.1007/s00159-013-0064-5   A&ARv ...     21  2013
    2013A&ARv..21...68G 10.1007/s00159-013-0068-1   A&ARv ...     21  2013
    2013A&ARv..21...63T 10.1007/s00159-013-0063-6   A&ARv ...     21  2013
    2013A&ARv..21...67B 10.1007/s00159-013-0067-2   A&ARv ...     21  2013

To look for articles published between 2010 and 2012 with a given keyword:

.. doctest-remote-data::

    >>> from astroquery.simbad import Simbad
    >>> simbad = Simbad()
    >>> simbad.ROW_LIMIT = 5
    >>> simbad.query_bibcode('20??A&A.*', wildcard=True,
    ...                      criteria=("\"year\" >= 2010 and \"year\" <= 2012"
    ...                                " and \"abstract\" like '%exoplanet%'"))
    <Table length=5>
          bibcode                   doi             journal ... volume  year
           object                  object            object ... int32  int16
    ------------------- --------------------------- ------- ... ------ -----
    2010A&A...509A..31G 10.1051/0004-6361/200912902     A&A ...    509  2010
    2010A&A...510A..21S 10.1051/0004-6361/200913675     A&A ...    510  2010
    2010A&A...510A.107M 10.1051/0004-6361/200912910     A&A ...    510  2010
    2010A&A...511A..36C 10.1051/0004-6361/200913629     A&A ...    511  2010
    2010A&A...511L...1M 10.1051/0004-6361/201014139     A&A ...    511  2010

As you can see, some wildcards can be replaced by a criteria (ex we could also
write: ``"journal" = 'A&A'`` in the criteria string). It is often faster to avoid
wildcards and use a criteria instead.

Query a bibobj
^^^^^^^^^^^^^^

These queries can be used to retrieve all the objects that are contained in the
article specified by the bibcode:

.. doctest-remote-data::

    >>> from astroquery.simbad import Simbad
    >>> Simbad.query_bibobj('2006AJ....131.1163S')
    <Table length=8>
            main_id                 ra         ...       bibcode       obj_freq
                                   deg         ...                             
             object              float64       ...        object        int16  
    ----------------------- ------------------ ... ------------------- --------
          NAME Lockman Hole             161.25 ... 2006AJ....131.1163S       --
            Cl Melotte   22  56.60099999999999 ... 2006AJ....131.1163S       --
                      M  32           10.67427 ... 2006AJ....131.1163S       --
                      M  31 10.684708333333333 ... 2006AJ....131.1163S       --
       NAME Galactic Center       266.41500889 ... 2006AJ....131.1163S       --
                   NAME LMC  80.89416666666666 ... 2006AJ....131.1163S       --
                   NAME SMC 13.158333333333333 ... 2006AJ....131.1163S       --
    2MASX J04504846-7531580          72.701925 ... 2006AJ....131.1163S       --

Customizing the default settings
================================

There may be times when you wish to change the defaults that have been set for
the Simbad queries.

Changing the row limit
----------------------

To fetch all the rows in the result, the row limit must be set to -1. However for some
queries, results are likely to be very large, in such cases it may be best to
limit the rows to a smaller number. If you want to do this only for the current
python session then:

.. code-block:: python

    >>> from astroquery.simbad import Simbad
    >>> Simbad.ROW_LIMIT = 15 # now any query except query_tap fetches at most 15 rows

If you would like to make your choice persistent, then you can do this by
modifying the setting in the Astroquery configuration file.

.. Note::

    `~astroquery.simbad.SimbadClass.query_tap` is an exception as the number
    of returned rows is fixed in the ADQL string with the ``TOP`` instruction.

Choosing the columns in the output tables
-----------------------------------------

.. Warning::

    Before astroquery v0.4.7, this was done with ``votable_fields``. This is not
    the case anymore. See :ref:`SIMBAD evolutions <simbad-evolutions>`.

Some query methods outputs can be customized. This is the case for:

- `~astroquery.simbad.DeprecatedSimbadClass.query_criteria`
- `~astroquery.simbad.SimbadClass.query_object`
- `~astroquery.simbad.SimbadClass.query_objects`
- `~astroquery.simbad.SimbadClass.query_region`
- `~astroquery.simbad.SimbadClass.query_bibobj`

Their default columns are:

- main_id
- ra
- dec
- coo_err_maj
- coo_err_min
- coo_err_angle
- coo_wavelength
- coo_bibcode'

This can be permanently changed in astroquery's configuration files. To do this within a session or
for a single query, use `~astroquery.simbad.SimbadClass.add_to_output`:

.. doctest-remote-data::

    >>> from astroquery.simbad import Simbad
    >>> simbad = Simbad()
    >>> simbad.add_to_output("otype")  # here we add a single column about object type

Some options add a single column and others add columns that are relevant for a theme (ex: fluxes,
proper motions...).
The list of possible options is printed with:

.. doctest-remote-data::

    >>> from astroquery.simbad import Simbad
    >>> Simbad.list_output_options()[["name", "description"]]
    <Table length=97>
          name      ...
         object     ...
    --------------- ...
                ids ...
           otypedef ...
              ident ...
               flux ...
          allfluxes ...
            has_ref ...
        mesDistance ...
        mesDiameter ...
            mesFe_h ...
             mesISO ...
                ... ...
           vlsr_min ...
    vlsr_wavelength ...
        coordinates ...
                dim ...
         dimensions ...
          morphtype ...
           parallax ...
      propermotions ...
                 sp ...
           velocity ...

Additional criteria
-------------------

.. Warning::

    Before astroquery v0.4.7, this was only possible within `~astroquery.simbad.DeprecatedSimbadClass.query_criteria`. This is not
    the case anymore, and a lot of query methods now admit criteria strings. See :ref:`SIMBAD evolutions <simbad-evolutions>`.

Some query methods take a ``criteria`` argument. They are listed here:

- `~astroquery.simbad.SimbadClass.query_object`
- `~astroquery.simbad.SimbadClass.query_objects`
- `~astroquery.simbad.SimbadClass.query_region`
- `~astroquery.simbad.SimbadClass.query_catalog`
- `~astroquery.simbad.SimbadClass.query_bibobj`
- `~astroquery.simbad.SimbadClass.query_bibcode`
- `~astroquery.simbad.SimbadClass.query_objectids`

A the criteria argument expect a string that fits in the ``WHERE`` clause of an ADQL query. Some examples can
be found in the `Simbad ADQL cheat sheet <http://simbad.cds.unistra.fr/simbad/tap/help/adqlHelp.html>`__. A way
of writing them is to first query a blank table to inspect the columns the method will return:

.. doctest-remote-data::

    >>> from astroquery.simbad import Simbad
    >>> simbad = Simbad()
    >>> simbad.ROW_LIMIT = 0  # get no lines, just the table structure
    >>> # add the table about proper motion measurements, and the object type column
    >>> simbad.add_to_output("mesPM", "otype")
    >>> peek = simbad.query_object("BD+30  2512") # a query on an object
    >>> peek.info
    <Table length=0>
            name         dtype    unit                                description                              
    ------------------- ------- -------- ----------------------------------------------------------------------
                main_id  object                                                   Main identifier for an object
                     ra float64      deg                                                        Right ascension
                    dec float64      deg                                                            Declination
            coo_err_maj float32      mas                                            Coordinate error major axis
            coo_err_min float32      mas                                            Coordinate error minor axis
          coo_err_angle   int16      deg                                                 Coordinate error angle
         coo_wavelength    str1                Wavelength class for the origin of the coordinates (R,I,V,U,X,G)
            coo_bibcode  object                                                            Coordinate reference
                  otype  object                                                                     Object type
          mespm.bibcode  object                                                             measurement bibcode
        mespm.coosystem  object                                                  coordinates system designation
           mespm.mespos   int16                             Position of a measurement in a list of measurements
             mespm.pmde float32 mas / yr                                                     Proper motion DEC.
         mespm.pmde_err float32 mas / yr                                                           sigma{pm-de}
    mespm.pmde_err_prec   int16          Precision (# of decimal positions) associated with the column pmde_err
        mespm.pmde_prec   int16              Precision (# of decimal positions) associated with the column pmde
             mespm.pmra float32 mas / yr                                                     Proper motion R.A.
         mespm.pmra_err float32 mas / yr                                                           sigma{pm-ra}
    mespm.pmra_err_prec   int16          Precision (# of decimal positions) associated with the column pmra_err
        mespm.pmra_prec   int16              Precision (# of decimal positions) associated with the column pmra
             matched_id  object                                                                      Identifier

With the information on the columns that will be returned by the query, it is now possible to write a criteria.
For example, to get only proper motions measurements more recent than 2000, we can add a constraint on the
first character of the bibcode (the first 4 digits of a bibcode are the year of publication of the article):

.. doctest-remote-data::

    >>> from astroquery.simbad import Simbad
    >>> criteria = "mespm.bibcode LIKE '2%'" # starts with 2, anything after
    >>> simbad = Simbad()
    >>> simbad.add_to_output("mesPM", "otype")
    >>> pm_measurements = simbad.query_object("BD+30  2512", criteria=criteria)
    >>> pm_measurements[["main_id", "mespm.pmra", "mespm.pmde", "mespm.bibcode"]]
    <Table length=6>
      main_id   mespm.pmra mespm.pmde    mespm.bibcode   
                 mas / yr   mas / yr                     
       object    float32    float32          object      
    ----------- ---------- ---------- -------------------
    BD+30  2512   -631.662   -308.469 2020yCat.1350....0G
    BD+30  2512     -631.6     -289.5 2016ApJS..224...36K
    BD+30  2512   -631.625   -308.495 2018yCat.1345....0G
    BD+30  2512    -631.36    -306.88 2007A&A...474..653V
    BD+30  2512     -631.0     -307.0 2005AJ....129.1483L
    BD+30  2512     -630.0     -306.0 2002ApJS..141..187B


.. _query-tap:

Query TAP
=========

.. include:: query_tap.rst



Troubleshooting
===============

If you are repeatedly getting failed queries, or bad/out-of-date results, try clearing your cache:

.. code-block:: python

    >>> from astroquery.simbad import Simbad
    >>> Simbad.clear_cache()

If this function is unavailable, upgrade your version of astroquery. 
The ``clear_cache`` function was introduced in version 0.4.7.dev8479.

    
Reference/API
=============

.. automodapi:: astroquery.simbad
    :no-inheritance-diagram:

.. _criteria interface: https://simbad.cds.unistra.fr/simbad/sim-fsam
