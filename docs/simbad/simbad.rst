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
blacklisted for up to an hour. This can happen when a query method is called within a loop.
There is always a way to send the information in a bigger query rather than in a lot of
smaller ones. Frequent use cases are that you can pass a vector of coordinates to
`~astroquery.simbad.SimbadClass.query_region` or a list of names to
`~astroquery.simbad.SimbadClass.query_objects`, and SIMBAD will treat this submission as
a single query. If this does not fit your use case, then you'll need to either use
`Wildcards`_ or a custom :ref:`query TAP <query-tap>`.

Simbad Evolutions
-----------------

The SIMBAD module follows evolutions of the SIMBAD database.
Some of these changes are documented into more details here:

.. toctree::
    :maxdepth: 2

    /simbad/simbad_evolution

Different ways to access SIMBAD
-------------------------------

The SIMBAD module described here provides methods that write ADQL queries. These
methods are described in the next sections.

A more versatile option is to query SIMBAD directly with your own ADQL queries via
Table Access Protocol (TAP) with the `~astroquery.simbad.SimbadClass.query_tap` method.
This is described in this section: :ref:`query TAP <query-tap>`.

Query modes
===========

Objects queries
---------------

Query by an Identifier
^^^^^^^^^^^^^^^^^^^^^^

This is useful if you want to query an object by a known identifier (name). For instance
to query the messier object M1:

.. doctest-remote-data::

    >>> from astroquery.simbad import Simbad
    >>> result_table = Simbad.query_object("m1")
    >>> print(result_table)
    main_id    ra     dec   ... coo_wavelength     coo_bibcode     matched_id
              deg     deg   ...
    ------- ------- ------- ... -------------- ------------------- ----------
      M   1 83.6324 22.0174 ...              X 2022A&A...661A..38P      M   1

`Wildcards`_ are supported. Note that this makes the query case-sensitive.
This allows, for instance, to query messier objects from 1 through 9:

..
    The following example is very slow ~20s due to a current (2024) bug in
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


The messier objects from 1 to 9 are found. Their main identifier ``main_id`` is not
necessarily the one corresponding to the wildcard expression.
The column ``matched_id`` contains the identifier that was matched.

Note that in this example, the wildcard parameter could have been replaced by a way
faster query done with `~astroquery.simbad.SimbadClass.query_objects`.

Wildcards
"""""""""

Wildcards are supported in these methods:
 - `~astroquery.simbad.SimbadClass.query_object`
 - `~astroquery.simbad.SimbadClass.query_objects`
 - `~astroquery.simbad.SimbadClass.query_bibcode`

They allow to provide a pattern that the query will match. To see the available
wildcards and their meaning:

.. code-block:: python

    >>> from astroquery.simbad import Simbad
    >>> Simbad().list_wildcards()
    *: Any string of characters (including an empty one)
    ?: Any character (exactly one character)
    [abc]: Exactly one character taken in the list. Can also be defined by a range of characters: [A-Z]
    [^0-9]: Any (one) character not in the list.

Query to get all names (identifiers) of an object
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

These queries can be used to retrieve all of the names (identifiers)
associated with an object.

..
    This could change (each time someone invents a new name for Polaris).

.. doctest-remote-data::

    >>> from astroquery.simbad import Simbad
    >>> result_table = Simbad.query_objectids("Polaris")
    >>> result_table
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

Query hierarchy: to get all parents (or children, or siblings) of an object
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

SIMBAD also records hierarchy links between objects. For example, two galaxies in a pair
of galaxies are siblings, a cluster of stars is composed of stars: its children. This
information can be accessed with the `~astroquery.simbad.SimbadClass.query_hierarchy`
method.

Whenever available, membership probabilities are recorded in SIMBAD as given by
the authors, though rounded to an integer. When authors do not give a value but
assessments, they are translated in SIMBAD as follows:

+-------------------+------------------------+
| assessment        | membership certainty   |
+===================+========================+
| member            | 100                    |
+-------------------+------------------------+
| likely member     | 75                     |
+-------------------+------------------------+
| possible member   | 50                     |
+-------------------+------------------------+
| likely not member | 25                     |
+-------------------+------------------------+
| non member        | 0                      |
+-------------------+------------------------+

For gravitational lens systems, double stars, and blends (superposition of two
non-physically linked objects), the SIMBAD team does not assign a probability
value (this will be a ``None``).

You can find more details in the `hierarchy documentation 
<https://simbad.cds.unistra.fr/guide/dataHierarchy.htx>`_ of SIMBAD's webpages.

Let's find the galaxies composing the galaxy pair ``Mrk 116``:

.. doctest-remote-data::

    >>> from astroquery.simbad import Simbad
    >>> galaxies = Simbad.query_hierarchy("Mrk 116",
    ...                                   hierarchy="children", criteria="otype='G..'")
    >>> galaxies[["main_id", "ra", "dec", "membership_certainty"]]
    <Table length=2>
     main_id         ra            dec       membership_certainty
                    deg            deg             percent       
      object      float64        float64            int16        
    --------- --------------- -------------- --------------------
    Mrk  116A 143.50821525019 55.24105273196                   --
    Mrk  116B      143.509956      55.239762                   --

Alternatively, if we know one member of a group, we can find the others by asking for
``siblings``:

.. doctest-remote-data::

    >>> from astroquery.simbad import Simbad
    >>> galaxies = Simbad.query_hierarchy("Mrk 116A",
    ...                                   hierarchy="siblings", criteria="otype='G..'")
    >>> galaxies[["main_id", "ra", "dec", "membership_certainty"]]
    <Table length=2>
     main_id         ra            dec       membership_certainty
                    deg            deg             percent       
      object      float64        float64            int16        
    --------- --------------- -------------- --------------------
    Mrk  116A 143.50821525019 55.24105273196                   --
    Mrk  116B      143.509956      55.239762                   --

Note that if we had not added the criteria on the object type, we would also get
some stars that are part of these galaxies in the result.

And the other way around, let's find which cluster of stars contains
``2MASS J18511048-0615470``:

.. doctest-remote-data::

    >>> from astroquery.simbad import Simbad
    >>> cluster = Simbad.query_hierarchy("2MASS J18511048-0615470", 
    ...                                  hierarchy="parents", detailed_hierarchy=False)
    >>> cluster[["main_id", "ra", "dec"]]
    <Table length=1>
     main_id     ra     dec
                deg     deg
      object  float64 float64
    --------- ------- -------
    NGC  6705 282.766  -6.272

By default, we get a more detailed report with the two extra columns:
 - ``hierarchy_bibcode`` : the paper in which the hierarchy is established,
 - ``membership_certainty``: if present in the paper, a certainty index (100 meaning
   100% sure).

.. doctest-remote-data::

    >>> from astroquery.simbad import Simbad
    >>> cluster = Simbad.query_hierarchy("2MASS J18511048-0615470", 
    ...                                  hierarchy="parents",
    ...                                  detailed_hierarchy=True)
    >>> cluster[["main_id", "ra", "dec", "hierarchy_bibcode", "membership_certainty"]]
    <Table length=13>
     main_id     ra     dec    hierarchy_bibcode  membership_certainty
                deg     deg                             percent
      object  float64 float64        object              int16
    --------- ------- ------- ------------------- --------------------
    NGC  6705 282.766  -6.272 2014A&A...563A..44M                  100
    NGC  6705 282.766  -6.272 2015A&A...573A..55T                  100
    NGC  6705 282.766  -6.272 2016A&A...591A..37J                  100
    NGC  6705 282.766  -6.272 2018A&A...618A..93C                  100
    NGC  6705 282.766  -6.272 2020A&A...633A..99C                  100
    NGC  6705 282.766  -6.272 2020A&A...640A...1C                  100
    NGC  6705 282.766  -6.272 2020A&A...643A..71G                  100
    NGC  6705 282.766  -6.272 2020ApJ...903...55P                  100
    NGC  6705 282.766  -6.272 2020MNRAS.496.4701J                  100
    NGC  6705 282.766  -6.272 2021A&A...647A..19T                  100
    NGC  6705 282.766  -6.272 2021A&A...651A..84M                  100
    NGC  6705 282.766  -6.272 2021MNRAS.503.3279S                   99
    NGC  6705 282.766  -6.272 2022MNRAS.509.1664J                  100

Here, we see that the SIMBAD team found 13 papers mentioning the fact that 
``2MASS J18511048-0615470`` is a member of ``NGC  6705`` and that the authors of these
articles gave high confidence indices for this membership (``membership_certainty`` is
close to 100 for all bibcodes).

A note of caution on hierarchy
""""""""""""""""""""""""""""""

In some tricky cases, low membership values represent extremely important information.
Let's for example look at the star ``V* V787 Cep``:

.. doctest-remote-data::

    >>> from astroquery.simbad import Simbad
    >>> parents = Simbad.query_hierarchy("V* V787 Cep", 
    ...                                  hierarchy="parents",
    ...                                  detailed_hierarchy=True)
    >>> parents[["main_id", "ra", "dec", "hierarchy_bibcode", "membership_certainty"]]
    <Table length=4>
     main_id          ra           dec    hierarchy_bibcode  membership_certainty
                     deg           deg                             percent       
      object       float64       float64        object              int16
    --------- ------------------ ------- ------------------- --------------------
    NGC   188 11.797999999999998  85.244 2003AJ....126.2922P                   46
    NGC   188 11.797999999999998  85.244 2004PASP..116.1012S                   46
    NGC   188 11.797999999999998  85.244 2018A&A...616A..10G                  100
    NGC   188 11.797999999999998  85.244 2021MNRAS.503.3279S                    1

Here, we see that the link between ``V* V787 Cep`` and the open cluster ``NGC 188`` is
opened for debate: the only way to build an opinion is to read the four articles.
This information would be hidden if we did not print the detailed hierarchy report.

These somewhat contradictory results are an inherent part of SIMBAD, which simply
translates the literature into a database.

Query a region
^^^^^^^^^^^^^^

Query in a cone with a specified radius. The center can be a string with an
identifier, a string representing coordinates, or a `~astropy.coordinates.SkyCoord`.

..
    This output will also change often.

.. doctest-remote-data::

    >>> from astroquery.simbad import Simbad
    >>> # get 10 objects in a radius of 0.5° around M81
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
`~astropy.coordinates.Angle` (ex: ``radius='0d6m0s'``) or directly a
`~astropy.units.Quantity` object.

If the center is defined by coordinates, then the best solution is to use a
`astropy.coordinates.SkyCoord` object.

.. doctest-remote-data::

    >>> from astroquery.simbad import Simbad
    >>> from astropy.coordinates import SkyCoord
    >>> import astropy.units as u
    >>> Simbad.query_region(SkyCoord(31.0087, 14.0627, unit=(u.deg, u.deg),
    ...                     frame='galactic'), radius=2 * u.arcsec)
    <Table length=2>
           main_id                ra        ... coo_wavelength     coo_bibcode    
                                 deg        ...                                   
            object             float64      ...      str1             object      
    --------------------- ----------------- ... -------------- -------------------
    NAME Barnard's Star b 269.4520769586187 ...              O 2020yCat.1350....0G
      NAME Barnard's star 269.4520769586187 ...              O 2020yCat.1350....0G

.. Note::

    Calling `~astroquery.simbad.SimbadClass.query_region` within a loop is **very**
    inefficient. If you need to query many regions, use a multi-coordinate
    `~astropy.coordinates.SkyCoord` and a list of radii. It looks like this:

.. doctest-remote-data::

    >>> from astroquery.simbad import Simbad
    >>> from astropy.coordinates import SkyCoord
    >>> import astropy.units as u
    >>> Simbad.query_region(SkyCoord(ra=[10, 11], dec=[10, 11],
    ...                     unit=(u.deg, u.deg), frame='fk5'),
    ...                     radius=[0.1 * u.deg, 2* u.arcmin])   # doctest: +IGNORE_OUTPUT
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

If the radius is the same in every cone, you can also just give this single radius without
having to create the list (ex: ``radius = "5arcmin"``).

Query a catalogue
^^^^^^^^^^^^^^^^^

Queries can also return all the objects from a catalogue. For instance to query
the ESO catalog:

.. doctest-remote-data::

    >>> from astroquery.simbad import Simbad
    >>> simbad = Simbad(ROW_LIMIT=6)
    >>> simbad.query_catalog('ESO')
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

Note that the name in ``main_id`` is not necessarily from the queried catalog. This
information is in the ``catalog_id`` column.

To see the available catalogues, you can write a custom ADQL query
(see :ref:`query_tap <query-tap-documentation>`.) on the ``cat`` table.
For example to get the 10 biggest catalogs in SIMBAD, it looks like this:

..
    This changes quite often. Hence the doctest skip

.. doctest-remote-data::

    >>> from astroquery.simbad import Simbad
    >>> Simbad.query_tap('SELECT TOP 10 cat_name, description FROM cat ORDER BY "size" DESC')  # doctest: +IGNORE_OUTPUT
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
        WISE Wide-field Infrared Survey Explorer Final Release Source Catalog
         GSC                                             Guide Star Catalogue
        LEDA                              Lyon-Meudon Extragalactic DatabaseA

Where you can remove ``TOP 10`` to get **all** the catalogues (there's a lot of them).

.. warning::
    This method is case-sensitive since version 0.4.8 

Bibliographic queries
---------------------

Query a bibcode
^^^^^^^^^^^^^^^

This retrieves information about the article corresponding to a bibcode.

.. doctest-remote-data::

    >>> from astroquery.simbad import Simbad
    >>> Simbad.query_bibcode('2005A&A.430.165F')
    <Table length=1>
          bibcode                  doi             journal ... volume  year
           object                 object            object ... int32  int16
    ------------------- -------------------------- ------- ... ------ -----
    2005A&A...430..165F 10.1051/0004-6361:20041272     A&A ...    430  2005

The abstract of the reference can also be added as an other column in the output by
setting the ``abstract`` parameter to ``True``.

`Wildcards`_ can be used in these queries as well. This can be useful to retrieve all
the bibcodes from a given journal in a given year:

.. doctest-remote-data::

    >>> from astroquery.simbad import Simbad
    >>> biblio = Simbad.query_bibcode('2013A&ARv.*', wildcard=True)
    >>> biblio.sort("bibcode")
    >>> biblio
        <Table length=9>
          bibcode                  doi            journal ... volume  year
           object                 object           object ... int32  int16
    ------------------- ------------------------- ------- ... ------ -----
    2013A&ARv..21...59I 10.1007/s00159-013-0059-2   A&ARv ...     21  2013
    2013A&ARv..21...61R 10.1007/s00159-013-0061-8   A&ARv ...     21  2013
    2013A&ARv..21...62D 10.1007/s00159-013-0062-7   A&ARv ...     21  2013
    2013A&ARv..21...63T 10.1007/s00159-013-0063-6   A&ARv ...     21  2013
    2013A&ARv..21...64D 10.1007/s00159-013-0064-5   A&ARv ...     21  2013
    2013A&ARv..21...67B 10.1007/s00159-013-0067-2   A&ARv ...     21  2013
    2013A&ARv..21...68G 10.1007/s00159-013-0068-1   A&ARv ...     21  2013
    2013A&ARv..21...69R 10.1007/s00159-013-0069-0   A&ARv ...     21  2013
    2013A&ARv..21...70B 10.1007/s00159-013-0070-7   A&ARv ...     21  2013

or to look for articles published between 2010 and 2012 with a given keyword:

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

As you can see, some wildcards can be replaced by a criteria (ex: we could also
write: ``"journal" = 'A&A'`` in the criteria string). It is often faster to avoid
wildcards and use a criteria instead.

Query a bibobj
^^^^^^^^^^^^^^

These queries can be used to retrieve all the objects that are discussed in the
article specified by a bibcode:

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

This section describe how the default output for the SIMBAD queries can be changed.

Changing the row limit
----------------------

To fetch all the rows in the result, the row limit must be set to -1. This is the default
behavior. However if you're only interested in a certain number of objects, or if
the result would be too large, you can change this behavior.
If you want to do this only for the current python session then:

.. code-block:: python

    >>> from astroquery.simbad import Simbad
    >>> Simbad.ROW_LIMIT = 15 # now any query except query_tap fetches at most 15 rows

If you would like to make your choice persistent, then you can do this by
modifying the setting in the Astroquery configuration file.

.. Note::

    This works with every ``query_***`` method, except
    `~astroquery.simbad.SimbadClass.query_tap` as the number of returned rows is fixed
    in the ADQL string with the ``TOP`` instruction.

Choosing the columns in the output tables
-----------------------------------------

Some query methods outputs can be customized. This is the case for:

- `~astroquery.simbad.SimbadClass.query_object`
- `~astroquery.simbad.SimbadClass.query_objects`
- `~astroquery.simbad.SimbadClass.query_region`
- `~astroquery.simbad.SimbadClass.query_catalog`
- `~astroquery.simbad.SimbadClass.query_hierarchy`
- `~astroquery.simbad.SimbadClass.query_bibobj`

For these methods, the default columns in the output are:

- main_id
- ra
- dec
- coo_err_maj
- coo_err_min
- coo_err_angle
- coo_wavelength
- coo_bibcode

.. Note::

    The columns that will appear in the output can be printed with the
    `~astroquery.simbad.SimbadClass.get_votable_fields` method

    .. code-block:: python

        >>> from astroquery.simbad import Simbad
        >>> simbad = Simbad()
        >>> simbad.get_votable_fields()
        ['basic.main_id', 'basic.ra', 'basic.dec', 'basic.coo_err_maj', 'basic.coo_err_min', 'basic.coo_err_angle', 'basic.coo_wavelength', 'basic.coo_bibcode']

    Here we see the lists of columns that are selected per default. They are all from
    the table of basic information (``basic``).

This can be permanently changed in astroquery's configuration files. To do this within
a session or for a single query, use `~astroquery.simbad.SimbadClass.add_votable_fields`:

.. doctest-remote-data::

    >>> from astroquery.simbad import Simbad
    >>> simbad = Simbad()
    >>> simbad.add_votable_fields("otype")  # here we add a single column about the main object type

Some options add a single column and others add  a bunch of columns that are relevant
for a theme (ex: fluxes, proper motions...). The list of possible options is printed
with:

.. doctest-remote-data::

    >>> from astroquery.simbad import Simbad
    >>> Simbad.list_votable_fields()[["name", "description"]]
    <Table length=...>
        name                           description                       
       object                             object                         
    ----------- ---------------------------------------------------------
    mesDiameter                          Collection of stellar diameters.
          mesPM                             Collection of proper motions.
         mesISO           Infrared Space Observatory (ISO) observing log.
         mesSpT                             Collection of spectral types.
      allfluxes          all flux/magnitudes U,B,V,I,J,H,K,u_,g_,r_,i_,z_
          ident                     Identifiers of an astronomical object
           flux   Magnitude/Flux information about an astronomical object
       mesOtype Other object types associated with an object with origins
         mesPLX                   Collection of trigonometric parallaxes.
            ...                                                       ...
              K                                               Magnitude K
              u                                          Magnitude SDSS u
              g                                          Magnitude SDSS g
              r                                          Magnitude SDSS r
              i                                          Magnitude SDSS i
              z                                          Magnitude SDSS z
              G                                          Magnitude Gaia G
          F150W                                         JWST NIRCam F150W
          F200W                                         JWST NIRCam F200W
          F444W                                         JWST NIRCan F444W

You can also access a single field description with
`~astroquery.simbad.SimbadClass.get_field_description`

.. doctest-remote-data::

    >>> from astroquery.simbad import Simbad
    >>> Simbad.get_field_description("rvz_type")
    'Radial velocity / redshift type'

And the columns in the output can be reset to their default value with
`~astroquery.simbad.SimbadClass.reset_votable_fields`.

.. Note::

    A detailed description on the ways to add fluxes is available in the
    :ref:`optical filters` section.

Measurement fields vs. Basic fields
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Some field names start with ``mes``. These denote what SIMBAD calls a
"measurement table". These tables store the history on past measurements of a physical
parameter for each object.

Let's look at the star ``HD 200207`` with the parallax measurements table ``mesplx``:

.. doctest-remote-data::

    >>> from astroquery.simbad import Simbad
    >>> simbad = Simbad()
    >>> simbad.add_votable_fields("mesplx")
    >>> hd_200207 = simbad.query_object("HD 200207")
    >>> hd_200207[["main_id", "mesplx.plx", "mesplx.plx_err", "mesplx.bibcode"]]
    <Table length=5>
     main_id  mesplx.plx mesplx.plx_err    mesplx.bibcode
                 mas          mas
      object   float32      float32            object
    --------- ---------- -------------- -------------------
    HD 200207     3.4084         0.0195 2020yCat.1350....0G
    HD 200207     3.4552         0.0426 2018yCat.1345....0G
    HD 200207       3.35           0.76 1997A&A...323L..49P
    HD 200207       3.72           0.62 2007A&A...474..653V
    HD 200207       3.25           0.22 2016A&A...595A...2G

This field adds one line per parallax measurement: five articles have measured it
for this star.

If you are only interested in the most precise measure recorded by the SIMBAD team, some
measurements fields have an equivalent in the basic fields. These fields only give one
line per object with the most precise currently known value:

+-------------------+---------------+
| measurement field | basic field   |
+===================+===============+
| mesplx            | parallax      |
+-------------------+---------------+
| mespm             | propermotions |
+-------------------+---------------+
| messpt            | sp            |
+-------------------+---------------+
| mesvelocities     | velocity      |
+-------------------+---------------+

Here, ``mesplx`` has an equivalent in the basic fields so we could have done:

.. doctest-remote-data::

    >>> from astroquery.simbad import Simbad
    >>> simbad = Simbad()
    >>> simbad.add_votable_fields("parallax")
    >>> hd_200207 = simbad.query_object("HD 200207")
    >>> hd_200207[["main_id", "plx_value", "plx_err", "plx_bibcode"]]
    <Table length=1>
     main_id  plx_value plx_err     plx_bibcode
                 mas      mas
      object   float64  float32        object
    --------- --------- ------- -------------------
    HD 200207    3.4084  0.0195 2020yCat.1350....0G

And we only have one line per object with the value selected by SIMBAD's team.

Thus, choosing to add a measurement field or a basic field depends on your goal.

Additional criteria
-------------------

.. Warning::

    Before astroquery v0.4.8, criteria could only be used with the method ``query_criteria``.
    This method is now deprecated and is replaced by the criteria argument in every
    other methods. See :ref:`SIMBAD evolutions <simbad-evolutions>`.

Most query methods take a ``criteria`` argument. They are listed here:

- `~astroquery.simbad.SimbadClass.query_object`
- `~astroquery.simbad.SimbadClass.query_objects`
- `~astroquery.simbad.SimbadClass.query_region`
- `~astroquery.simbad.SimbadClass.query_catalog`
- `~astroquery.simbad.SimbadClass.query_hierarchy`
- `~astroquery.simbad.SimbadClass.query_bibobj`
- `~astroquery.simbad.SimbadClass.query_bibcode`
- `~astroquery.simbad.SimbadClass.query_objectids`

The criteria argument expect a string written in the syntax of the ``WHERE`` clause of
an ADQL query. Some examples can be found in the
`Simbad ADQL cheat sheet <http://simbad.cds.unistra.fr/simbad/tap/help/adqlHelp.html>`__.

To help writing criteria, a good tip is to inspect the columns that the query would
return by querying a blank table (of zero rows).
This allows to inspect the columns the method would return:

.. doctest-remote-data::

    >>> from astroquery.simbad import Simbad
    >>> simbad = Simbad()
    >>> simbad.ROW_LIMIT = 0  # get no lines, just the table structure
    >>> # add the table about proper motion measurements, and the object type column
    >>> simbad.add_votable_fields("mesPM", "otype")
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

Now that we know which columns will be returned by the query, we can edit the number of
returned rows and add a criteria.

For example, to get only proper motion measurements more recent than 2000, we can add a
constraint on the first character of the ``mespm.bibcode`` column
(the first 4 digits of a bibcode are the year of publication of the article):

.. doctest-remote-data::

    >>> from astroquery.simbad import Simbad
    >>> criteria = "mespm.bibcode LIKE '2%'" # starts with 2, anything after
    >>> simbad = Simbad()
    >>> simbad.add_votable_fields("mesPM", "otype")
    >>> pm_measurements = simbad.query_object("BD+30  2512", criteria=criteria)
    >>> pm_measurements[["main_id", "mespm.pmra", "mespm.pmde", "mespm.bibcode"]]
    <Table length=7>
      main_id   mespm.pmra mespm.pmde    mespm.bibcode
                 mas / yr   mas / yr
       object    float32    float32          object
    ----------- ---------- ---------- -------------------
    BD+30  2512     -631.6     -289.5 2016ApJ...817..112S
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

Longer queries
--------------

It can be useful to execute longer queries in asynchronous mode by setting the
``async_job`` argument to ``True``. This may take longer to start, depending on the
current number of other people using the asynchronous SIMBAD queue, but it is more
robust against transient errors. Asynchronous queries will take the ``timeout`` property
in account:

.. doctest-remote-data::

    >>> from astroquery.simbad import Simbad
    >>> simbad = Simbad(timeout=2000) # in seconds
    >>> simbad.query_tap("select otype, description from otypedef where otype = 'N*'",
    ...                  async_job=True)
    <Table length=1>
    otype  description
    object    object
    ------ ------------
        N* Neutron Star

Clearing the cache
------------------

If you are repeatedly getting failed queries, or bad/out-of-date results, try clearing
your cache:

.. code-block:: python

    >>> from astroquery.simbad import Simbad
    >>> Simbad.clear_cache()

If this function is unavailable, upgrade your version of astroquery.
The ``clear_cache`` function was introduced in version 0.4.7.dev8479.

Citation
========

If SIMBAD was useful for your research, you can
`read its acknowledgement page <https://cds.unistra.fr/help/acknowledgement/>`__.


Reference/API
=============

.. automodapi:: astroquery.simbad
    :no-inheritance-diagram:
