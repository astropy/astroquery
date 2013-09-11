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

**Table Discovery**

If you want to search for a set of tables, e.g. based on author name or other keywords,
the `~astroquery.vizier.Vizier.find_catalogs` tool can be used:

.. code-block:: python

    >>> from astroquery.vizier import Vizier
    >>> catalog_list = Vizier.find_catalogs('Kang W51')
    >>> print(catalog_list)
    {u'J/ApJ/706/83': <astropy.io.votable.tree.Resource at 0x108d4d490>,
     u'J/ApJS/191/232': <astropy.io.votable.tree.Resource at 0x108d50490>}
    >>> print({k:v.description for k,v in catalog_list.iteritems()})
    {u'J/ApJ/706/83': u'Embedded YSO candidates in W51 (Kang+, 2009)',
     u'J/ApJS/191/232': u'CO survey of W51 molecular cloud (Bieging+, 2010)'}

From this result, you could either get any of these as a complete catalog or
query them for individual objects or regions. 

**Get a whole catalog**

If you know the name of the catalog you wish to retrieve, e.g. from doing a
`~astroquery.vizier.Vizier.find_catalogs` search as above, you can then grab
the complete contents of those catalogs:

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

    >>> Vizier.ROW_LIMIT.set('999999999')
    >>> catalogs = Vizier.get_catalogs(catalog_list.keys())
    >>> print(catalogs)
    TableList with 3 tables:
       '0:J/ApJ/706/83/ysos' with 22 column(s) and 737 row(s) 
       '1:J/ApJS/191/232/table1' with 13 column(s) and 218 row(s) 
       '2:J/ApJS/191/232/map' with 2 column(s) and 2 row(s) 

**Query an object**

For instance to query Sirius across all catalogs:

.. code-block:: python

    >>> from astroquery.vizier import Vizier
    >>> result = Vizier.query_object("sirius")
    >>> print(result)
    TableList with 232 tables:
       '0:ReadMeObj' with 5 column(s) and 5 row(s) 
       '1:I/34/greenw2a' with 16 column(s) and 1 row(s) 
       '2:I/40/catalog' with 11 column(s) and 1 row(s) 
       ...

All the results are returned as a `TableList` object. This is a container for
`astropy.table.Table`_ objects. It is basically an extension to
`collections.OrderedDict` for storing an `astropy.table.Table`_ against its
name. 


To access an individual table from the `TableList` object

.. code-block:: python

    >>> interesting_table = result['IX/10A/cor_ros']
    >>> print(interesting_table)
         _1RXS       Rank        sourceID       RAJ2000  DEJ2000  Sep
    ---------------- ---- --------------------- -------- -------- ---
    J064509.3-164241    2 1RXH J064509.2-164242 101.2885 -16.7119   2
    J064509.3-164241   14 1RXP J0645 8.4-164302 101.2854 -16.7174  24
    J064509.3-164241   20 1RXH J064515.7-164402 101.3156 -16.7339 123

To do some common processing to all the tables in the returned `TableList`
object, do just what you would do for a python dictionary:

.. code-block:: python

    >>> for table_name in result:
            table = result[table_name]
            # table is now an `astropy.table.Table` object
            # some code to apply on table

**Query a region**

To query a region either the coordinates or the object name around which to
query should be specified along with the value for the radius (or height/width
for a box) of the region. For instance to query a large region around the
quasar 3C 273:

.. code-block:: python

    >>> from astroquery.vizier import Vizier
    >>> import astropy.units as u
    >>> result = Vizier.query_region("3C 273", radius=0.1 * u.deg, catalog='GSC')

Note that the radius may also be specified as a string in the format
expected by `astropy.coordinates.Angle`_. So the above query may also
be written as:

.. code-block:: python

    >>> result = Vizier.query_region("3C 273", radius="0d6m0s", catalog='GSC')

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
    >>> result = Vizier.query_region(coord.ICRSCoordinates(ra=299.590, dec=35.201, unit=(u.deg, u.deg)),
    ...                         width="0d30m0s", height="0d10m0s",
    ...                         catalog=["NOMAD", "UCAC"])
    >>> print(result)
    TableList with 3 tables:
       '0:I/297/out' with 19 column(s) and 50 row(s) 
       '1:I/289/out' with 13 column(s) and 50 row(s) 
       '2:I/322A/out' with 24 column(s) and 50 row(s) 


One more thing to note in the above example is that the coordinates may be
specified by using the appropriate coordinate object from
`astropy.coordinates`_. Especially for ICRS coordinates, some limited support
also exists for directly passing a properly formatted string as the
coordinate. Finally the `catalog` keyword argument may be passed in either
`Vizier.query_object` or `Vizier.query_region` methods. This may be a string
(if only a single catalog) or a list of strings otherwise.

**Specifying keywords, output columns and constraints on columns**

To specify keywords on which to search as well as conditions on the output
columns, an instance of the `Vizier` class specifying these must be first
created. All further queries may then be performed on this instance rather than
on the Vizier class. 

.. code-block:: python

    >>> v = Vizier(columns=['_RAJ2000', 'DEJ2000','B-V', 'Vmag', 'Plx'],
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
   TableList with 2 tables:
      '0:I/289/out' with 3 column(s) and 18 row(s) 
      '1:I/322A/out' with 4 column(s) and 10 row(s) 

    >>> print(result['I/322A/out'])
     _RAJ2000    DEJ2000    Vmag   _DEJ2000 
    ---------- ----------- ------ ----------
    299.572419  35.1942342 15.986  35.194234
    299.580291  35.1768889 13.274  35.176889
    299.582571  35.1852253 14.863  35.185225
    299.594172  35.1799948 14.690  35.179995
    299.601402  35.1981078 14.644  35.198108
    299.617669  35.1869987 14.394  35.186999
    299.561498  35.2016928 15.687  35.201693
    299.570217  35.2256634 14.878  35.225663
    299.601081  35.2333378 13.170  35.233338
    299.617995  35.2058637 13.946  35.205864

Note that the columns that appear in the `column_filters` are required to be a
subset of the output columns as specified via the `columns` keyword argument -
if this is not the case, an exception will be raised.

The constraints or keywords may be deleted at any time. So again continuing
from the above example:

.. code-block:: python

    >>> del v.column_filters
    >>> result = v.query_object("HD 226868", catalog=["NOMAD", "UCAC"])
    >>> print(result)
    TableList with 3 tables:
       '0:I/297/out' with 4 column(s) and 50 row(s) 
       '1:I/289/out' with 3 column(s) and 18 row(s) 
       '2:I/322A/out' with 4 column(s) and 28 row(s) 

As can be seen considerably more rows are returned. Just to check:

.. code-block:: python
    
    >>> print(result['I/322A/out'])
     _RAJ2000    DEJ2000    Vmag   _DEJ2000 
    ---------- ----------- ------ ----------
    299.560073  35.1847709    nan  35.184771
    299.572419  35.1942342 15.986  35.194234
    299.579956  35.1965673    nan  35.196567
    299.580291  35.1768889 13.274  35.176889
    299.582553  35.1801528    nan  35.180153
    299.582571  35.1852253 14.863  35.185225
    299.594172  35.1799948 14.690  35.179995
    299.601402  35.1981078 14.644  35.198108
    299.606413  35.1871734    nan  35.187173
    299.606698  35.1920009    nan  35.192001
    299.608171  35.1994889    nan  35.199489
    299.612142  35.1839075    nan  35.183908
    299.617669  35.1869987 14.394  35.186999
    299.561498  35.2016928 15.687  35.201693
    299.570217  35.2256634 14.878  35.225663
    299.587434  35.2032023    nan  35.203202
    299.589158  35.2301031    nan  35.230103
    299.590162  35.2168664  9.992  35.216866
    299.590315  35.2016062  8.996  35.201606
    299.590446  35.2153614    nan  35.215361
    299.592838  35.2291506    nan  35.229151
    299.597615  35.2271000    nan  35.227100
    299.597652  35.2342487    nan  35.234249
    299.601081  35.2333378 13.170  35.233338
    299.615751  35.2229892    nan  35.222989
    299.617995  35.2058637 13.946  35.205864
    299.620861  35.2124506    nan  35.212451
    299.623687  35.2105187    nan  35.210519

It is evident that the *Vmag* constraint no longer applies.
                 

Reference/API
=============

.. automodapi:: astroquery.vizier
    :no-inheritance-diagram:

.. _astropy.table.Table: http://docs.astropy.org/en/latest/table/index.html
.. _astropy.coordinates.Angle: http://docs.astropy.org/en/latest/_generated/astropy.coordinates.angles.Angle.html#astropy.coordinates.angles.Angle 
.. _astropy.units: http://docs.astropy.org/en/latest/units/index.html 
.. _astropy.coordinates: http://docs.astropy.org/en/latest/coordinates/index.html  
.. _for details see here: http://vizier.u-strasbg.fr/vizier/vizHelp/1.htx
