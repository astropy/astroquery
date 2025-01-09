.. _astroquery.vizier:

************************************
VizieR Queries (`astroquery.vizier`)
************************************

Getting started
===============

This is a python interface for querying the VizieR web service. This supports
querying an object as well as querying a region around the target. For region
queries, the region dimensions may be specified either for a box or as a
radius. Similar to the VizieR web interface, the queries may be further
constrained by specifying a choice of catalogs, keywords as well as filters on
individual columns before retrieving the results.

.. note::
    In earlier versions of astroquery (<0.4.8), columns with special characters like 
    ``r'mag`` were renamed into ``r_mag`` and columns starting with a number like
    ``2MASS`` were prepended with an underscore ``_2MASS``.
    In astroquery >=0.4.8, the column names are the same in VizieR's webpages and in
    the tables received (for the two examples: you'll see ``r'mag`` and ``2MASS``).

Catalogs exploration
--------------------

If you want to search for a set of tables, e.g. based on author name or other keywords,
the :meth:`~astroquery.vizier.VizierClass.find_catalogs` tool can be used:

.. order is not deterministic
.. doctest-remote-data::

    >>> from astroquery.vizier import Vizier
    >>> vizier = Vizier() # this instantiates Vizier with its default parameters
    >>> catalog_list = vizier.find_catalogs('hot jupiter exoplanet transit')
    >>> for k, v in catalog_list.items(): # doctest: +IGNORE_OUTPUT
    ...     print(k, ":", v.description)
    J/A+A/635/A205 : Ultra-hot Jupiter WASP-121b transits (Bourrier+, 2020)
    J/ApJ/788/39 : Hot Jupiter exoplanets host stars EW and abundances (Teske+, 2014)
    J/AJ/157/217 : Transit times of five hot Jupiter WASP exoplanets (Bouma+, 2019)
    J/A+A/635/A122 : CoRoT-30b and CoRoT-31b radial velocity curves (Border+, 2020)

From this list, you can either get any catalog completely (all the lines) or make
sub-selections with :meth:`~astroquery.vizier.VizierClass.query_region`, 
or with additional criteria.

Get a whole catalog
-------------------

From the result of the precedent example, let's select ``J/ApJ/788/39``.
We call :meth:`~astroquery.vizier.VizierClass.get_catalogs`. Let's fix the number of
returned rows to 1 for now, to minimize the amount of data we download and speed up
exploration, while we inspect the result:

.. doctest-remote-data::
    
    >>> vizier.ROW_LIMIT = 1
    >>> exoplanets = vizier.get_catalogs("J/ApJ/788/39")
    >>> exoplanets
    TableList with 2 tables:
        '0:J/ApJ/788/39/stars' with 7 column(s) and 1 row(s)
        '1:J/ApJ/788/39/table4' with 48 column(s) and 1 row(s)

.. note::

    ``ROW_LIMIT`` is set to 50 per default.

We see that this catalog has two tables. One named ``J/ApJ/788/39/stars`` and the
other one is ``J/ApJ/788/39/table4``.

Let's look at the columns of ``J/ApJ/788/39/stars`` from the single row that we just
downloaded:

.. doctest-remote-data::

    >>> exoplanets[0]
    <Table length=1>
      Name    RAJ2000     DEJ2000     Vmag  Name1  lines Simbad
                                      mag                      
      str9     str11       str11    float32  str8   str5  str6 
    ------- ----------- ----------- ------- ------ ----- ------
    CoRoT-2 19 27 06.50 +01 23 01.4   12.57 COROT2 lines Simbad

.. note::

    The coordinates columns often have the information about the frame and epoch in
    their descriptions:

.. doctest-remote-data::

    >>> exoplanets[0]["RAJ2000"].description
    'Simbad Hour of Right Ascension (J2000)'

When we're ready to download the complete table, we can set the row limit to -1 (for 
infinity).

.. doctest-remote-data::

    >>> vizier.ROW_LIMIT = -1
    >>> stars = vizier.get_catalogs("J/ApJ/788/39/stars")
    >>> # stars is a TableList with only one table. Here is its first and only element
    >>> stars[0]
    <Table length=17>
       Name     RAJ2000     DEJ2000     Vmag   Name1   lines Simbad
                                        mag                        
       str9      str11       str11    float32   str8    str5  str6 
    --------- ----------- ----------- ------- -------- ----- ------
      CoRoT-2 19 27 06.50 +01 23 01.4   12.57   COROT2 lines Simbad
       TrES-4 17 53 13.06 +37 12 42.4   11.59    TRES4 lines Simbad
       TrES-2 19 07 14.04 +49 18 59.1   11.25    TRES2 lines Simbad
       WASP-2 20 30 54.13 +06 25 46.4   11.98    WASP2 lines Simbad
      WASP-12 06 30 32.79 +29 40 20.3   11.57   WASP12 lines Simbad
    HD 149026 16 30 29.62 +38 20 50.3    8.14 HD149026 lines Simbad
      HAT-P-1 22 57 46.84 +38 40 30.3   10.40    HATP1 lines Simbad
        XO-2S 07 48 07.48 +50 13 03.3   11.25     XO2S lines Simbad
        XO-2N 07 48 06.47 +50 13 33.0   11.25     XO2N lines Simbad
         XO-1 16 02 11.85 +28 10 10.4   11.25      XO1 lines Simbad
       TRES-3 17 52 07.02 +37 32 46.2   12.40    TRES3 lines Simbad
    HD 189733 20 00 43.71 +22 42 39.1    7.68 HD189733 lines Simbad
     HD 80606 09 22 37.58 +50 36 13.4    9.00  HD80606 lines Simbad
      HAT-P-7 19 28 59.35 +47 58 10.2   10.48    HATP7 lines Simbad
     HAT-P-13 08 39 31.81 +47 21 07.3   10.42   HATP13 lines Simbad
     HAT-P-16 00 38 17.56 +42 27 47.2   10.91   HATP16 lines Simbad
      WASP-32 00 15 50.81 +01 12 01.6   11.26   WASP32 lines Simbad


Alternatively, we could have downloaded all the catalogs from the results of 
:meth:`~astroquery.vizier.VizierClass.find_catalogs`.
Be careful when doing so, as this might be huge.

.. doctest-remote-data::

    >>> vizier.ROW_LIMIT = 50 # we reset to the default value
    >>> catalogs = vizier.get_catalogs(catalog_list.keys())
    >>> print(catalogs) # doctest: +IGNORE_OUTPUT
    TableList with 10 tables:
       '0:J/A+A/635/A205/20140119' with 7 column(s) and 50 row(s) 
       '1:J/A+A/635/A205/20140123' with 7 column(s) and 50 row(s) 
       '2:J/A+A/635/A205/20171231' with 7 column(s) and 50 row(s) 
       '3:J/A+A/635/A205/20180114' with 7 column(s) and 50 row(s) 
       '4:J/A+A/635/A205/ccf-mask' with 3 column(s) and 50 row(s) 
       '5:J/ApJ/788/39/stars' with 7 column(s) and 17 row(s) 
       '6:J/ApJ/788/39/table4' with 48 column(s) and 50 row(s) 
       '7:J/AJ/157/217/transits' with 8 column(s) and 50 row(s) 
       '8:J/A+A/635/A122/table2' with 4 column(s) and 18 row(s) 
       '9:J/A+A/635/A122/table3' with 4 column(s) and 17 row(s) 

We downloaded the 50 first rows of these 10 tables.

Get a catalog's associated metadata
-----------------------------------

The method `~astroquery.vizier.VizierClass.get_catalog_metadata` retrieves information
about VizieR's catalogs. It returns a table with the following columns:

- title
- authors
- abstract
- origin_article -- the bibcode of the associated article
- webpage -- a link to VizieR, contains more information about the catalog
- created -- date of creation of the catalog *in VizieR*
- updated -- date of the last modification applied to the entry, this is often about
  metadata, with no appearance in the history on the webpage but sometimes it is about
  a data erratum, which will appear in the history tab

  .. note::
     This value can be extra useful to check if you need to download some catalog
     again from VizieR or if you can work safely with a result you saved previously
     on disk. Also note that the VizieR team actively maintains the catalogs but if
     a published erratum was missed we'd gladly receive a notification from you!

- waveband
- doi -- the catalog doi when it exists

.. doctest-remote-data::

    >>> from astroquery.vizier import Vizier
    >>> Vizier(catalog="VII/74A").get_catalog_metadata()
    <Table length=1>
              title            authors  ... waveband  doi  
              object            object  ...  object  object
    -------------------------- -------- ... -------- ------
    Atlas of Peculiar Galaxies Arp H.C. ...  optical     --
      

Query an object
---------------


For instance to query Sirius across all catalogs:

.. doctest-remote-data::

    >>> from astroquery.vizier import Vizier
    >>> vizier = Vizier(row_limit=10)
    >>> result = vizier.query_object("sirius") # doctest: +IGNORE_WARNINGS
    >>> print(result)
    TableList with ... tables:
       '0:METAobj' with 5 column(s) and 7 row(s)
       '1:ReadMeObj' with 5 column(s) and 7 row(s) 
       '2:I/34/greenw2a' with 16 column(s) and 1 row(s) 
       ...

All the results are returned as a `~astroquery.utils.TableList` object. This
is a container for `~astropy.table.Table` objects. It is basically an
extension to `~collections.OrderedDict` for storing a `~astropy.table.Table`
against its name.

To access an individual table from the `~astroquery.utils.TableList` object:

.. doctest-remote-data::

    >>> interesting_table = result['IX/8/catalog']
    >>> print(interesting_table)
       2XRS     RAB1950      DEB1950    Xname ... Int   _RA.icrs     _DE.icrs   
                                              ... uJy                          
    --------- ------------ ------------ ----- ... --- ------------ ------------
    06429-166 06 42 54.000 -16 39 00.00       ...  -- 06 45 08.088 -16 42 11.29
    06429-166 06 42 54.000 -16 39 00.00       ...  -- 06 45 08.088 -16 42 11.29

To do some common processing to all the tables in the returned
`~astroquery.utils.TableList` object, do just what you would do for a python
dictionary:

.. doctest-remote-data::

    >>> for table_name in result.keys():
    ...     table = result[table_name]
    ...     # table is now an `astropy.table.Table` object
    ...     # some code to apply on table

Query a region
--------------


To query a region either the coordinates or the object name around which to
query should be specified along with the value for the radius (or height/width
for a box) of the region. For instance to query a large region around the
quasar 3C 273:

.. doctest-remote-data::

    >>> from astroquery.vizier import Vizier
    >>> from astropy.coordinates import Angle
    >>> vizier = Vizier()
    >>> result = vizier.query_region("3C 273", radius=Angle(0.1, "deg"), catalog='GSC')

Note that the radius may also be specified as a string in the format
expected by `~astropy.coordinates.Angle`. So the above query may also
be written as:

.. doctest-remote-data::

    >>> result = vizier.query_region("3C 273", radius="0d6m0s", catalog='GSC')

Or using angular units and quantities from `astropy.units`:

.. doctest-remote-data::

    >>> import astropy.units as u
    >>> result = vizier.query_region("3C 273", radius=0.1*u.deg, catalog='GSC')

To see the result:

.. doctest-remote-data::

    >>> print(result)
    TableList with 5 tables:
       '0:I/254/out' with 10 column(s) and 17 row(s) 
       '1:I/255/out' with 9 column(s) and 17 row(s) 
       '2:I/271/out' with 11 column(s) and 50 row(s) 
       '3:I/305/out' with 11 column(s) and 50 row(s) 
       '4:I/353/gsc242' with 35 column(s) and 50 row(s) 

As mentioned earlier, the region may also be mentioned by specifying the height
and width of a box. If only one of the height or width is mentioned, then the
region is treated to be a square having sides equal to the specified
dimension.

.. doctest-remote-data::

    >>> from astroquery.vizier import Vizier
    >>> import astropy.units as u
    >>> import astropy.coordinates as coord
    >>> vizier = Vizier()
    >>> result = vizier.query_region(coord.SkyCoord(ra=299.590, dec=35.201,
    ...                                             unit=(u.deg, u.deg),
    ...                                             frame='icrs'),
    ...                         width="30m",
    ...                         catalog=["NOMAD", "UCAC"])
    >>> print(result)
    TableList with 3 tables:
       '0:I/297/out' with 19 column(s) and 50 row(s) 
       '1:I/322A/out' with 24 column(s) and 50 row(s) 
       '2:I/340/ucac5' with 20 column(s) and 50 row(s)


One more thing to note in the above example is that the coordinates may be
specified by using the appropriate coordinate object from
`astropy.coordinates`. Especially for ICRS coordinates, some support
also exists for directly passing a properly formatted string as the
coordinate. Finally the ``catalog`` keyword argument may be passed in either
:meth:`~astroquery.vizier.VizierClass.query_object` or
:meth:`~astroquery.vizier.VizierClass.query_region` methods. This may be a string
(if only a single catalog) or a list of strings otherwise.

Last but not least, :meth:`~astroquery.vizier.VizierClass.query_region` also supports
constraints on the columns of the returned tables by mean of the ``column_filters`` keyword.

.. doctest-remote-data::

    >>> from astroquery.vizier import Vizier
    >>> import astropy.units as u
    >>> from astropy.coordinates import SkyCoord
    >>> vizier = Vizier()
    >>> result = vizier.query_region(SkyCoord.from_name('M81'),
    ...                              radius=10*u.arcmin,
    ...                              catalog='I/345/gaia2',
    ...                              column_filters={'Gmag': '<19'})
    >>> print(result[0]['Gmag'].max())
    18.9508

Specifying keywords, output columns and constraints on columns
--------------------------------------------------------------

To specify keywords on which to search as well as conditions on the output
columns, an instance of the `~astroquery.vizier.VizierClass` class specifying these must be first
created. All further queries may then be performed on this instance rather than
on the Vizier class.

.. doctest-remote-data::

    >>> vizier = Vizier(columns=['_RAJ2000', '_DEJ2000','B-V', 'Vmag', 'Plx'],
    ...            column_filters={"Vmag":">10"}, keywords=["optical", "xry"])  # doctest: +IGNORE_WARNINGS

Note that whenever an unknown keyword is specified (here ``xry``) a warning is emitted and
that keyword is discarded from further consideration. The behavior for
searching with these keywords is the same as defined for the web
interface (`for details see here`_). Now we call the different query methods on
this Vizier instance:

.. output can be in any order here
.. doctest-remote-data::

    >>> vizier = Vizier(columns=['_RAJ2000', '_DEJ2000','B-V', 'Vmag', 'Plx'],
    ...            column_filters={"Vmag":">10"}, keywords=["optical"])
    >>> result = vizier.query_object("HD 226868", catalog=["NOMAD", "UCAC"])
    >>> print(result)
    TableList with 3 tables:
       '0:I/297/out' with 3 column(s) and 50 row(s) 
       '1:I/322A/out' with 3 column(s) and 10 row(s) 
       '2:I/340/ucac5' with 2 column(s) and 26 row(s)
    >>> print(result['I/322A/out']) # doctest: +IGNORE_OUTPUT
       _RAJ2000      _DEJ2000    Vmag 
         deg           deg       mag  
    ------------- ------------- ------
    299.572418900  35.194234200 15.986
    299.580291200  35.176888900 13.274
    299.582571200  35.185225300 14.863
    299.594171800  35.179994800 14.690
    299.601402100  35.198107800 14.644
    299.617668600  35.186998700 14.394
    299.561497700  35.201692800 15.687
    299.570216500  35.225663400 14.878
    299.601080600  35.233337800 13.170
    299.617995000  35.205863700 13.946

When specifying the columns of the query, sorting of the returned table can be
requested by adding ``+`` (or ``-`` for reverse sorting order) in front of the column
name. In the following example, the standard (``"*"``) columns and the calculated
distance column (``"_r"``) of the 2MASS catalog (II/246) are queried, 20 arcsec
around HD 226868. The result is sorted in increasing distance, as requested with
the ``"+"`` in front of ``"_r"``.

.. doctest-remote-data::

    >>> vizier = Vizier(columns=["*", "+_r"], catalog="II/246")
    >>> result = vizier.query_region("HD 226868", radius="20s")
    >>> print(result[0])
      _r    RAJ2000    DEJ2000        2MASS        Jmag  ... Bflg Cflg Xflg Aflg
              deg        deg                       mag   ...                    
    ------ ---------- ---------- ---------------- ------ ... ---- ---- ---- ----
     0.134 299.590280  35.201599 19582166+3512057  6.872 ...  111  000    0    0
    10.135 299.587491  35.203217 19582099+3512115 10.285 ...  111  c00    0    0
    11.167 299.588599  35.198849 19582126+3511558 13.111 ...    2  00c    0    0
    12.288 299.586356  35.200542 19582072+3512019 14.553 ...  111  ccc    0    0
    17.691 299.586254  35.197994 19582070+3511527 16.413 ...  100  c00    0    0

Note: The special column ``"*"`` requests just the default columns of a
catalog; ``"**"`` would request all the columns.

Query with table
----------------

A `~astropy.table.Table` can also be used to specify the coordinates in a
region query *if* it contains the columns ``_RAJ2000`` and ``_DEJ2000``. The
following example starts by looking for AGNs in the Veron & Cety catalog with a
``Vmag`` between 10.0 and 11.0. Based on the result of this first query, guide
stars with a ``Kmag`` brighter than 9.0 are looked for, with a separation
between 2 and 30 arcsec. The column ``_q`` in the ``guide`` table is a 1-based
index to the ``agn`` table (not the 0-based python convention).

.. doctest-remote-data::

    >>> agn = Vizier(catalog="VII/258/vv10",
    ...              columns=['*', '_RAJ2000', '_DEJ2000']).query_constraints(Vmag="10.0..11.0")[0]
    >>> print(agn)
     _RAJ2000   _DEJ2000   Cl  nR      Name     ...  Sp  n_Vmag  Vmag  B-V  r_z 
       deg        deg                           ...              mag   mag      
    ---------- ---------- --- --- ------------- ... ---- ------ ----- ----- ----
     10.684583  41.269444   Q              M 31 ...   S2        10.57  1.08 1936
     60.277917 -16.110833   Q     NPM1G-16.0168 ...           R 10.16    --  988
     27.238750   5.906667   A   *      NGC  676 ...   S2        10.50    -- 1034
     40.669583  -0.013056   A          NGC 1068 ...  S1h        10.83  0.87   58
    139.759583  26.269722   A          NGC 2824 ...   S?        10.88    -- 2528
    147.592083  72.279167   A          NGC 2985 ... S1.9        10.61  0.76 1033
    173.144167  53.067778   A          NGC 3718 ...  S3b        10.61  0.74 1033
    184.960833  29.613889   A         UGC  7377 ...   S3        10.47  0.99 2500
    185.028750  29.280833   A          NGC 4278 ...  S3b        10.87  0.98 1033
    186.453750  33.546667   A          NGC 4395 ... S1.8        10.27  0.53 1033
    192.719583  41.119444   A          NGC 4736 ...    S        10.85  0.85 1032
    208.361250  40.283056   A          NGC 5353 ...   S?      R 10.91    --  368

.. doctest-remote-data::

    >>> guide = Vizier(catalog="II/246", column_filters={"Kmag":"<9.0"}).query_region(agn, radius="30s", inner_radius="2s")[0]
    >>> guide.pprint()
     _q  RAJ2000    DEJ2000        2MASS        Jmag  ... Rflg Bflg Cflg Xflg Aflg
           deg        deg                       mag   ...                         
    --- ---------- ---------- ---------------- ------ ... ---- ---- ---- ---- ----
      1  10.686015  41.269630 00424464+4116106  9.399 ...   20   20  0c0    2    0
      1  10.685657  41.269550 00424455+4116103 10.773 ...  200  200  c00    2    0
      1  10.685837  41.270599 00424460+4116141  9.880 ...   20   20  0c0    2    0
      1  10.683263  41.267456 00424398+4116028 12.136 ...  200  100  c00    2    0
      1  10.683465  41.269676 00424403+4116108 11.507 ...  200  100  c00    2    0
      3  27.238636   5.906066 01485727+0554218  8.961 ...  112  111  000    0    0
      4  40.669277  -0.014225 02424062-0000512 11.795 ...  200  100  c00    2    0
      4  40.668802  -0.013064 02424051-0000470 11.849 ...  200  100  c00    2    0
      4  40.669219  -0.012236 02424061-0000440 12.276 ...  200  100  c00    2    0
      4  40.670761  -0.012208 02424098-0000439 12.119 ...  200  100  c00    2    0
      4  40.670177  -0.012830 02424084-0000461 11.381 ...  200  100  c00    2    0
     11 192.721982  41.121040 12505327+4107157 10.822 ...  200  100  c00    2    0
     11 192.721179  41.120201 12505308+4107127  9.306 ...  222  111  000    2    0


Troubleshooting
===============

If you are repeatedly getting failed queries, or bad/out-of-date results, try clearing your cache:

.. code-block:: python

    >>> from astroquery.vizier import Vizier
    >>> Vizier.clear_cache()

If this function is unavailable, upgrade your version of astroquery. 
The ``clear_cache`` function was introduced in version 0.4.7.dev8479.

     
Reference/API
=============

.. automodapi:: astroquery.vizier
    :no-inheritance-diagram:

.. _for details see here: https://vizier.cds.unistra.fr/vizier/vizHelp/1.htx
