.. doctest-skip-all

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

Table Discover
--------------

If you want to search for a set of tables, e.g. based on author name or other keywords,
the :meth:`~astroquery.vizier.VizierClass.find_catalogs` tool can be used:

.. code-block:: python

    >>> from astroquery.vizier import Vizier
    >>> catalog_list = Vizier.find_catalogs('Kang W51')
    >>> print({k:v.description for k,v in catalog_list.items()})
    {'J/ApJS/191/232': 'CO survey of W51 molecular cloud (Bieging+, 2010)',
     'J/ApJ/706/83': 'Embedded YSO candidates in W51 (Kang+, 2009)'}

From this result, you could either get any of these as a complete catalog or
query them for individual objects or regions.

Get a whole catalog
-------------------


If you know the name of the catalog you wish to retrieve, e.g. from doing a
:meth:`~astroquery.vizier.VizierClass.find_catalogs` search as above, you can then grab
the complete contents of those catalogs:

.. code-block:: python

    >>> catalogs = Vizier.get_catalogs(catalog_list.keys())
    >>> print(catalogs)
    TableList with 3 tables:
       '0:J/ApJ/706/83/ysos' with 22 column(s) and 50 row(s)
       '1:J/ApJS/191/232/table1' with 13 column(s) and 50 row(s)
       '2:J/ApJS/191/232/map' with 2 column(s) and 2 row(s)

Similarly, the ``Resource`` objects (the values of the dictionary resulting from
:meth:`~astroquery.vizier.VizierClass.find_catalogs`) can be used in the same
way:

.. code-block:: python

    >>> catalogs = Vizier.get_catalogs(catalog_list.values())
    >>> print(catalogs)
    TableList with 3 tables:
       '0:J/ApJ/706/83/ysos' with 22 column(s) and 50 row(s)
       '1:J/ApJS/191/232/table1' with 13 column(s) and 50 row(s)
       '2:J/ApJS/191/232/map' with 2 column(s) and 2 row(s)

.. code-block:: python

   >>> catalogs = Vizier.get_catalogs(catalog_list.keys())
   >>> print(catalogs)
   TableList with 3 tables:
      '0:J/ApJ/706/83/ysos' with 22 column(s) and 50 row(s)
      '1:J/ApJS/191/232/table1' with 13 column(s) and 50 row(s)
      '2:J/ApJS/191/232/map' with 2 column(s) and 2 row(s)

Note that the row limit is set to 50 by default, so if you want to get a truly
complete catalog, you need to change that:

.. code-block:: python

    >>> Vizier.ROW_LIMIT = -1
    >>> catalogs = Vizier.get_catalogs(catalog_list.keys())
    >>> print(catalogs)
    TableList with 3 tables:
       '0:J/ApJ/706/83/ysos' with 22 column(s) and 737 row(s)
       '1:J/ApJS/191/232/table1' with 13 column(s) and 218 row(s)
       '2:J/ApJS/191/232/map' with 2 column(s) and 2 row(s)
    >>> Vizier.ROW_LIMIT = 50

Query an object
---------------


For instance to query Sirius across all catalogs:

.. code-block:: python

    >>> from astroquery.vizier import Vizier
    >>> result = Vizier.query_object("sirius")
    >>> print(result)
    TableList with 275 tables:
       '0:METAobj' with 5 column(s) and 5 row(s)
       '1:ReadMeObj' with 5 column(s) and 5 row(s)
       '2:I/34/greenw2a' with 16 column(s) and 1 row(s)
       ...

All the results are returned as a `~astroquery.utils.TableList` object. This
is a container for `~astropy.table.Table` objects. It is basically an
extension to `~collections.OrderedDict` for storing a `~astropy.table.Table`
against its name.

To access an individual table from the `~astroquery.utils.TableList` object:

.. code-block:: python

    >>> interesting_table = result['IX/10A/cor_ros']
    >>> print(interesting_table)
         _1RXS       Rank        sourceID       RAJ2000  DEJ2000  Sep
                                                  deg      deg    arcs
    ---------------- ---- --------------------- -------- -------- ----
    J064509.3-164241    2 1RXH J064509.2-164242 101.2885 -16.7119    2
    J064509.3-164241   14 1RXP J0645 8.4-164302 101.2854 -16.7174   24
    J064509.3-164241   20 1RXH J064515.7-164402 101.3156 -16.7339  123

To do some common processing to all the tables in the returned
`~astroquery.utils.TableList` object, do just what you would do for a python
dictionary:

.. code-block:: python

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

.. code-block:: python

    >>> from astroquery.vizier import Vizier
    >>> from astropy.coordinates import Angle
    >>> result = Vizier.query_region("3C 273", radius=Angle(0.1, "deg"), catalog='GSC')

Note that the radius may also be specified as a string in the format
expected by `~astropy.coordinates.Angle`. So the above query may also
be written as:

.. code-block:: python

    >>> result = Vizier.query_region("3C 273", radius="0d6m0s", catalog='GSC')

Or using angular units and quantities from `astropy.units`:

.. code-block:: python

    >>> import astropy.units as u
    >>> result = Vizier.query_region("3C 273", radius=0.1*u.deg, catalog='GSC')

To see the result:

.. code-block:: python

    >>> print(result)
    TableList with 3 tables:
       '0:I/254/out' with 10 column(s) and 17 row(s)
       '1:I/271/out' with 11 column(s) and 50 row(s)
       '2:I/305/out' with 11 column(s) and 50 row(s)

As mentioned earlier, the region may also be mentioned by specifying the height
and width of a box. If only one of the height or width is mentioned, then the
region is treated to be a square having sides equal to the specified
dimension.

.. code-block:: python

    >>> from astroquery.vizier import Vizier
    >>> import astropy.units as u
    >>> import astropy.coordinates as coord
    >>> result = Vizier.query_region(coord.SkyCoord(ra=299.590, dec=35.201,
    ...                                             unit=(u.deg, u.deg),
    ...                                             frame='icrs'),
    ...                         width="30m",
    ...                         catalog=["NOMAD", "UCAC"])
    >>> print(result)
    TableList with 3 tables:
       '0:I/297/out' with 19 column(s) and 50 row(s)
       '1:I/289/out' with 13 column(s) and 50 row(s)
       '2:I/322A/out' with 24 column(s) and 50 row(s)


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

.. code-block:: python

    >>> from astroquery.vizier import Vizier
    >>> import astropy.units as u
    >>> from astropy.coordinates import SkyCoord
    >>> result = Vizier.query_region(SkyCoord.from_name('M81'),
                                     radius=10*u.arcmin,
                                     catalog='I/345/gaia2',
                                     column_filters={'Gmag': '<19'})
    >>> print(result[0]['Gmag'].max())
    18.9508

Specifying keywords, output columns and constraints on columns
--------------------------------------------------------------

To specify keywords on which to search as well as conditions on the output
columns, an instance of the `~astroquery.vizier.VizierClass` class specifying these must be first
created. All further queries may then be performed on this instance rather than
on the Vizier class.

.. code-block:: python

    >>> v = Vizier(columns=['_RAJ2000', '_DEJ2000','B-V', 'Vmag', 'Plx'],
    ...            column_filters={"Vmag":">10"}, keywords=["optical", "xry"])

    WARNING: xry : No such keyword [astroquery.vizier.core]

Note that whenever an unknown keyword is specified, a warning is emitted and
that keyword is discarded from further consideration. The behavior for
searching with these keywords is the same as defined for the web
interface (`for details see here`_). Now we call the different query methods on
this Vizier instance:

.. code-block:: python

    >>> result = v.query_object("HD 226868", catalog=["NOMAD", "UCAC"])
    >>> print(result)
    TableList with 3 tables:
        '0:I/297/out' with 3 column(s) and 50 row(s)
        '1:I/289/out' with 3 column(s) and 18 row(s)
        '2:I/322A/out' with 3 column(s) and 10 row(s)

    >>> print(result['I/322A/out'])
     _RAJ2000   _DEJ2000   Vmag
       deg        deg      mag
    ---------- ---------- ------
    299.572419  35.194234 15.986
    299.580291  35.176889 13.274
    299.582571  35.185225 14.863
    299.594172  35.179995 14.690
    299.601402  35.198108 14.644
    299.617669  35.186999 14.394
    299.561498  35.201693 15.687
    299.570217  35.225663 14.878
    299.601081  35.233338 13.170
    299.617995  35.205864 13.946

When specifying the columns of the query, sorting of the returned table can be
requested by adding ``+`` (or ``-`` for reverse sorting order) in front of the column
name. In the following example, the standard (``"*"``) columns and the calculated
distance column (``"_r"``) of the 2MASS catalog (II/246) are queried, 20 arcsec
around HD 226868. The result is sorted in increasing distance, as requested with
the ``"+"`` in front of ``"_r"``.

.. code-block:: python

    >>> v = Vizier(columns=["*", "+_r"], catalog="II/246")
    >>> result = v.query_region("HD 226868", radius="20s")
    >>> print(result[0])
      _r    RAJ2000    DEJ2000        _2MASS       Jmag  ... Bflg Cflg Xflg Aflg
     arcs     deg        deg                       mag   ...
    ------ ---------- ---------- ---------------- ------ ... ---- ---- ---- ----
     0.134 299.590280  35.201599 19582166+3512057  6.872 ...  111  000    0    0
    10.141 299.587491  35.203217 19582099+3512115 10.285 ...  111  c00    0    0
    11.163 299.588599  35.198849 19582126+3511558 13.111 ...  002  00c    0    0
    12.289 299.586356  35.200542 19582072+3512019 14.553 ...  111  ccc    0    0
    17.688 299.586254  35.197994 19582070+3511527 16.413 ...  100  c00    0    0

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

.. code-block:: python

    >>> agn = Vizier(catalog="VII/258/vv10",
    ...              columns=['*', '_RAJ2000', '_DEJ2000']).query_constraints(Vmag="10.0..11.0")[0]
    >>> print(agn)
    _RAJ2000 _DEJ2000  Cl  nR      Name     ...  Sp  n_Vmag  Vmag  B-V  r_z
      deg      deg                          ...              mag   mag
    -------- -------- --- --- ------------- ... ---- ------ ----- ----- ----
     10.6846  41.2694   Q              M 31 ...   S2        10.57  1.08 1936
     60.2779 -16.1108   Q     NPM1G-16.0168 ...           R 10.16    --  988
     27.2387   5.9067   A   *      NGC  676 ...   S2        10.50    -- 1034
     40.6696  -0.0131   A          NGC 1068 ...  S1h        10.83  0.87   58
    139.7596  26.2697   A          NGC 2824 ...   S?        10.88    -- 2528
    147.5921  72.2792   A          NGC 2985 ... S1.9        10.61  0.76 1033
    173.1442  53.0678   A          NGC 3718 ...  S3b        10.61  0.74 1033
    184.9608  29.6139   A         UGC  7377 ...   S3        10.47  0.99 2500
    185.0287  29.2808   A          NGC 4278 ...  S3b        10.87  0.98 1033
    186.4537  33.5467   A          NGC 4395 ... S1.8        10.27  0.53 1033
    192.7196  41.1194   A          NGC 4736 ...    S        10.85  0.85 1032
    208.3612  40.2831   A          NGC 5353 ...   S?      R 10.91    --  368

    >>> guide = Vizier(catalog="II/246", column_filters={"Kmag":"<9.0"}).query_region(agn, radius="30s", inner_radius="2s")[0]
    >>> guide.pprint()
     _q  RAJ2000    DEJ2000        _2MASS       Jmag  ... Rflg Bflg Cflg Xflg Aflg
           deg        deg                       mag   ...
    --- ---------- ---------- ---------------- ------ ... ---- ---- ---- ---- ----
      1  10.686015  41.269630 00424464+4116106  9.399 ...  020  020  0c0    2    0
      1  10.685657  41.269550 00424455+4116103 10.773 ...  200  200  c00    2    0
      1  10.685837  41.270599 00424460+4116141  9.880 ...  020  020  0c0    2    0
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

Reference/API
=============

.. automodapi:: astroquery.vizier
    :no-inheritance-diagram:

.. _for details see here: http://vizier.u-strasbg.fr/vizier/vizHelp/1.htx
