
***************************
Query using the TAP Service
***************************

The ESO `TAP service <https://archive.eso.org/programmatic/#TAP>`_ allows users to
submit custom `ADQL <https://www.ivoa.net/documents/ADQL/>`_ (Astronomical Data
Query Language) queries against the archive metadata, providing fine-grained
control over complex searches. TAP queries can be executed against different
tables depending on the type of data required:

- ``ivoa.ObsCore``: standardized metadata for **fully calibrated (Phase 3) data
  products** corresponding to high-level queries, such as available via
  :meth:`~astroquery.eso.EsoClass.query_surveys`.

- ``dbo.raw``: metadata for **raw observational data** across all ESO
  instruments, such as available via :meth:`~astroquery.eso.EsoClass.query_main`.

- ``ist.<instrument_name>`` (e.g. ``ist.muse``, ``ist.midi``): **instrument-specific
  raw metadata** tables, such as available via
  :meth:`~astroquery.eso.EsoClass.query_instrument`.

While these query modes are covered by the high-level ``astroquery.eso`` API,
direct use of ADQL through TAP provides additional flexibility for constructing
advanced queries that combine constraints across multiple metadata fields or
tables. For more information about the TAP and how to write ADQL queries, refer to the following resources:

- `ESO TAP documentation <https://archive.eso.org/programmatic/>`_: Describes ESO's implementation of TAP and the available services.
- `IVOA TAP standard <https://www.ivoa.net/documents/TAP/>`_: The official specification from the International Virtual Observatory Alliance.
- `ADQL specification <https://www.ivoa.net/documents/cover/ADQL-20081030.html>`_: Defines the query language used to interact with TAP services.

Query for Raw Data (Generic)
============================

The following example demonstrates how to query the ``dbo.raw`` table for raw data products from the ``MUSE`` instrument:

.. doctest-remote-data::

    >>> query = """
    ...         SELECT *
    ...         FROM dbo.raw
    ...             AND instrument = 'MUSE'
    ...          """
    >>> table = eso.query_tap(query)

Query for Raw Data (Instrument-Specific)
========================================

The following example demonstrates how to query the ``ist.muse`` table for raw
data products from the ``MUSE`` instrument, selecting observations taken at
night with a Moon illumination below 30%, an LST range between 0 and 6 hours,
an average seeing (FWHM) below 1.0 arcsec, and an exposure time greater than
100 seconds:

.. doctest-remote-data::

    >>> query = """
    ...         SELECT *
    ...         FROM ist.muse
    ...         WHERE night_flag = 'NIGHT'
    ...             AND moon_illu < 30
    ...             AND dimm_fwhm_avg < 1.0
    ...             AND exptime > 100
    ...             AND lst between 0 and 6
    ...          """
    >>> table = eso.query_tap(query)

Query for Reduced Data Products
===============================

The following examples query the ``ivoa.ObsCore`` table to find enhanced data
products and perform common spatial selections using dataset footprints. Using
the TAP service directly allows access to functionality beyond what is available
via the high-level :meth:`~astroquery.eso.EsoClass.query_surveys` interface, such
as complex spatial constraints, joins, aggregations, and more flexible filtering
on ObsCore metadata.

The same general approach applies when querying raw data products as described
above: while the specific metadata fields may differ, the use of TAP enables the
same general functionality as demonstrated in the examples below.

List Release Documentation URLs for Data Collections
----------------------------------------------------

Firstly, this example retrieves the release documentation URL associated with
each published data collection exposed through ``ivoa.ObsCore``.


.. doctest-remote-data::
    >>> query = """
    ... SELECT DISTINCT obs_collection, release_description
    ... FROM ivoa.ObsCore
    ... WHERE release_description IS NOT NULL
    ... ORDER BY obs_collection, release_description
    ... """
    >>> table = eso.query_tap(query)
    >>> print(table[:5])
    obs_collection                     release_description                    
    -------------- -----------------------------------------------------------
        081.C-0827 http://www.eso.org/rm/api/v1/public/releaseDescriptions/160
        092.A-0472 http://www.eso.org/rm/api/v1/public/releaseDescriptions/75
        096.B-0054 http://www.eso.org/rm/api/v1/public/releaseDescriptions/142
        108.2289   http://www.eso.org/rm/api/v1/public/releaseDescriptions/236
        110.23NK   http://www.eso.org/rm/api/v1/public/releaseDescriptions/239

Constrained query
-----------------

The following example queries to find enhanced data products
(``calib_level = 3``; e.g. mosaics, resampled/drizzled images, or other heavily
processed survey fields) from the ``SPHERE`` survey. The query further restricts
the selection to multi-OB observations (``multi_ob = 'M'``) with spatial pixel
scales smaller than 0.2 arcsec:

.. doctest-remote-data::

    >>> query = """
    ...          SELECT obs_collection, calib_level, multi_ob, filter,
    ...                 s_pixel_scale, instrument_name
    ...          FROM ivoa.ObsCore
    ...          WHERE obs_collection = 'SPHERE'
    ...              AND calib_level = 3
    ...              AND multi_ob = 'M'
    ...              AND s_pixel_scale < 0.2
    ...          """
    >>> table = eso.query_tap(query)
    >>> table
    <Table length=15>
    obs_collection calib_level multi_ob filter s_pixel_scale instrument_name
                                                arcsec
        object        int32     object  object    float64         object
    -------------- ----------- -------- ------ ------------- ---------------
            SPHERE           3        M    K12        0.0122          SPHERE
            SPHERE           3        M    K12        0.0122          SPHERE
            ...
            SPHERE           3        M      H        0.0122          SPHERE

Cone search
-----------

We can also use the TAP service to perform spatial queries based on dataset
footprints. Suppose you are looking for datasets closer than *2.5 arcmin* from *NGC 4666*.
Either you know the equatorial coordinates of your object, or you rely on a name
resolver such as SESAME (CDS) to obtain them. In the end you define a search
circle by three quantities: RA, Dec, and radius, all expressed in degrees.

The cone-search constraint is typically implemented using the ADQL
``INTERSECTS`` operator, which takes two spatial footprints as input and returns
``1`` if they intersect in at least one point (and ``0`` otherwise). In a cone
search, one footprint is the input circle, while the other is the ``s_region``
column, which represents the sky footprint of each dataset.

.. doctest-remote-data::

    >>> from astropy.coordinates import SkyCoord
    >>> target = "NGC 4666"
    >>> pos = SkyCoord.from_name(target)
    >>> r = 2.5/60.  # search radius of 2.5 arcmin, expressed in degrees
    >>> query = """SELECT *
    ...             FROM ivoa.ObsCore
    ...             WHERE INTERSECTS(s_region, CIRCLE('', {ra:.6f}, {dec:.6f}, {r:.6f}))=1
    ...         """.format(ra=pos.ra.degree, dec=pos.dec.degree, r=r)

.. doctest-remote-data::

    >>> table = eso.query_tap(query=query)
    >>> print("Num matching datasets: %d" % (len(table)))
    Num matching datasets: 219

.. note::
   **Cone search:** ``INTERSECTS`` or ``CONTAINS``?

   If you are looking specifically for spectra (whose footprint is typically a
   point), you could use the stricter ``CONTAINS`` operator to ensure that only
   footprints entirely contained within the defined circle are returned.
   Remember: ``INTERSECTS`` is commutative, but the order of the operands in
   ``CONTAINS`` matters and is defined as::

       CONTAINS(contained, container) = 1

   Try repeating the cone-search query after replacing ``INTERSECTS`` with
   ``CONTAINS`` to see the difference. In practice, images (and measurements
   derived from those images) may disappear from the results because their
   footprints are larger than the 2.5 arcmin circle.


Point in footprint
------------------

Suppose you are interested in finding extended datasets that cover a specific
point on the sky (for example, datasets that could have imaged the progenitor of
a supernova). “Extended” here means datasets with a non-zero footprint area, excluding spectra
and visibilities whose footprint is effectively a single point.

To find datasets that include a given sky position, you can use either
``INTERSECTS`` or ``CONTAINS``; for a point there is no practical difference.
Here we use ``CONTAINS`` and restrict the results to images and cubes.

.. doctest-remote-data::

    >>> query = """SELECT t_min, abmaglim, dataproduct_type as type, dp_id, obs_release_date
    ...             FROM ivoa.ObsCore
    ...             WHERE CONTAINS(POINT('', 193.815, 0.099819), s_region)=1
    ...             AND dataproduct_type IN ('image', 'cube')
    ...             ORDER BY t_min ASC
    ...         """
    >>> table = eso.query_tap(query=query)
    >>> table
    <Table length=32>
          t_min             abmaglim      ...     obs_release_date    
            d                 mag         ...                         
        float64            float64       ...          object         
    ------------------ ------------------ ... ------------------------
        56402.18240388             21.629 ... 2017-09-20T20:02:58.453Z
        56402.18240388             21.536 ... 2017-09-20T20:02:58.453Z
        56402.18390705             21.374 ... 2017-09-20T20:02:58.453Z
                   ...               ...  ...                      ...
    58787.638966122686 14.437809060706662 ...     2021-04-22T16:00:18Z
        58884.23649998             22.653 ... 2021-02-05T06:16:18.783Z


Region in footprint
-------------------

If you want to ensure that matching datasets contain an entire region, you must
use ``CONTAINS``. The first operand is the region you want to be covered, and
the second operand is the dataset footprint in ``s_region``. The covered region
may be a simple circle or a more complex shape (e.g. a polygon). Here we show a
circle around NGC 253 and restrict to images and cubes.

.. doctest-remote-data::

    >>> query = """SELECT t_min, s_fov, dataproduct_type as type, dp_id, obs_release_date
    ...             FROM ivoa.ObsCore
    ...             WHERE CONTAINS(CIRCLE('', 11.888002, -25.288220, 0.21), s_region)=1
    ...             AND dataproduct_type IN ('image', 'cube')
    ...             ORDER BY t_min ASC
    ...         """
    >>> table = eso.query_tap(query=query)
    >>> table
    <Table length=7>
        t_min          s_fov      type             dp_id                obs_release_date    
          d             deg                                                                 
      float64        float64    object            object                    object         
    -------------- ------------- ------ --------------------------- ------------------------
    55864.21418374 1.15908954416  image ADP.2019-04-29T06:50:17.911 2019-04-29T13:08:36.937Z
    55893.13608187 1.45520652527  image ADP.2015-06-17T12:56:53.853 2015-06-18T11:00:50.587Z
    55897.15708812 1.45500126333  image ADP.2015-06-17T12:57:54.060 2015-06-18T05:46:38.167Z
    55927.08420409 1.15896704055  image ADP.2019-04-29T06:50:21.403 2019-04-29T18:06:01.943Z
    56132.3041874 1.15909942583  image ADP.2019-04-29T07:01:36.683 2019-05-02T17:40:17.620Z
    56147.27356555 1.15886452083  image ADP.2019-04-29T07:01:36.979 2019-05-02T17:40:17.620Z
    56180.34451683 1.15887357333  image ADP.2019-04-29T07:01:38.569 2019-05-02T18:00:17.460Z

The above lists datasets whose footprints are large enough to entirely contain
the provided circular region.

Search by polygon
-----------------

You can also search for datasets intersecting a polygon. This is useful, for
example, when looking for optical/infrared/radio counterparts of a gravitational
wave (GW) event. GW spatial probability maps (e.g. via LIGO/Virgo skymaps) can be
converted into confidence contours at a given probability level, resulting in a
counterclockwise polygon suitable for ADQL spatial queries.

The following example uses a polygon constructed for the GW170817 event and
returns matching datasets ordered by ``t_min``.

.. doctest-remote-data::

    >>> query = """SELECT t_min, snr, abmaglim, dataproduct_type as type, dp_id
    ...             FROM ivoa.ObsCore
    ...             WHERE INTERSECTS(
    ...             s_region,
    ...             POLYGON('J2000',
    ...               196.8311,-23.5212, 196.7432,-23.3586, 196.6553,-23.1962,
    ...               196.4795,-23.0339, 196.3916,-22.8719, 196.3037,-22.7100,
    ...               196.2158,-22.5484, 196.1279,-22.3869, 196.0400,-22.2257,
    ...               195.9521,-22.0646, 195.8643,-21.9037, 195.7764,-21.7429,
    ...               195.7764,-21.5824, 195.6885,-21.4220, 195.6006,-21.2618,
    ...               195.5127,-21.1018, 195.4248,-20.9420, 195.3369,-20.7823,
    ...               195.3369,-20.6228, 195.2490,-20.4634, 195.1611,-20.3043,
    ...               195.1611,-20.1452, 195.0732,-19.9864, 194.9854,-19.8277,
    ...               194.8975,-19.6692, 194.8975,-19.5108, 194.8096,-19.3526,
    ...               194.7217,-19.1945, 194.6338,-19.0366, 194.6338,-18.8788,
    ...               194.5459,-18.7212, 194.4580,-18.5637, 194.4580,-18.4064,
    ...               194.3701,-18.2492, 194.4580,-18.0922, 194.4580,-17.9353,
    ...               194.6338,-18.0137, 194.8096,-18.1707, 194.9854,-18.3278,
    ...               195.0732,-18.4851, 195.1611,-18.6425, 195.2490,-18.8000,
    ...               195.3369,-18.9577, 195.4248,-19.1155, 195.5127,-19.2735,
    ...               195.6006,-19.4317, 195.6885,-19.5900, 195.8643,-19.7484,
    ...               195.9521,-19.9070, 196.1279,-20.0658, 196.2158,-20.2247,
    ...               196.3916,-20.3838, 196.4795,-20.5431, 196.5674,-20.7025,
    ...               196.6553,-20.8621, 196.7432,-21.0219, 196.8311,-21.1818,
    ...               196.9189,-21.3419, 196.9189,-21.5022, 197.0068,-21.6626,
    ...               197.0947,-21.8233, 197.1826,-21.9841, 197.2705,-22.1451,
    ...               197.3584,-22.3063, 197.4463,-22.4676, 197.5342,-22.6292,
    ...               197.6221,-22.7909, 197.7100,-22.9529, 197.7979,-23.1150,
    ...               197.7979,-23.2773, 197.8857,-23.4399, 197.9736,-23.6026,
    ...               196.9189,-23.6026
    ...             ))=1
    ...             ORDER BY t_min ASC
    ...      """
    >>> table = eso.query_tap(query=query)
    >>> table
    <Table length=1415>
        t_min        snr   abmaglim     type                dp_id           
          d                  mag                                            
      float64     float64 float64     object               object          
    -------------- ------- -------- ------------ ---------------------------
    52769.18223732    41.5       --     spectrum ADP.2020-08-04T16:44:55.149
    53070.29890813    79.4       --     spectrum ADP.2016-09-20T08:08:13.622
    53071.17154411    86.0       --     spectrum ADP.2016-09-20T08:08:12.820
    53373.36714808   170.9       --     spectrum ADP.2016-09-21T07:05:31.370
    54514.36343016    74.2       --     spectrum ADP.2020-06-28T16:34:31.221
    54514.36347455    14.3       --     spectrum ADP.2020-06-28T16:34:31.235
              ...     ...      ...          ...                         ...
    59355.20396096     6.9       --     spectrum ADP.2021-06-08T11:54:53.878
    59759.00758508      --       --   visibility ADP.2025-12-18T13:15:42.554

Spatial joins
-------------

Are you interested in finding images in different bands of the same sky region,
for photometric studies? The following example shows how to compose a spatial
join to find HAWKI source tables:

* within 10 degrees from the Galactic plane,
* taken in the J and H bands (selected by wavelength constraints),
* where the J and H footprints overlap, and
* ensuring that the overlap covers at least 80% of the J-band footprint area.

.. doctest-remote-data::

    >>> query = """SELECT J.* FROM
    ...             (SELECT * FROM ivoa.ObsCore
    ...               WHERE dataproduct_subtype = 'srctbl'
    ...                 AND obs_collection = 'HAWKI'
    ...                 AND gal_lat < 10 AND gal_lat > -10
    ...                 AND em_min < 1.265E-6 AND em_max > 1.265E-6) J,
    ...
    ...             (SELECT * FROM ivoa.ObsCore
    ...               WHERE dataproduct_subtype = 'srctbl'
    ...                 AND obs_collection = 'HAWKI'
    ...                 AND gal_lat < 10 AND gal_lat > -10
    ...                 AND em_min < 1.66E-6 AND em_max > 1.66E-6) H
    ...
    ...             WHERE INTERSECTS(J.s_region, H.s_region)=1
    ...             AND ESO_INTERSECTION(J.s_region, H.s_region) > 0.8 * AREA(J.s_region)
    ...         """
    >>> table = eso.query_tap(query=query)
    >>> table
    <Table length=4224>
    abmaglim access_estsize               access_format                ... t_resolution t_xel target_name
    float64      int64                        object                   ...   float64    int64    object  
    -------- -------------- ------------------------------------------ ... ------------ ----- -----------
      23.029           2255 application/x-votable+xml;content=datalink ...  3580.209504    -- Lupus3-East
      23.054           2004 application/x-votable+xml;content=datalink ...  3580.209504    -- Lupus3-East
      23.035           1990 application/x-votable+xml;content=datalink ...   3580.94736    -- Lupus3-East
      23.01           2217 application/x-votable+xml;content=datalink ...   3580.94736    -- Lupus3-East
        ...            ...                                        ... ...          ...   ...         ...
      25.468           3081 application/x-votable+xml;content=datalink ...   280.788768    --     V U Car
      25.408           3093 application/x-votable+xml;content=datalink ...   280.788768    --     V U Car

Notice the ``J.*`` in the ``SELECT`` clause: this returns only the metadata for
the J-band datasets. You can repeat the query selecting ``H.*`` to retrieve the
H-band metadata. This is useful, for example, when visualising results in tools
such as Aladin using different colours for different bands. Alternatively, you
can return both sets in one query (``SELECT *``) or select specific columns from
each side, e.g. ``SELECT J.dp_id, H.dp_id, ...``.


Query by wavelengths
--------------------

The IVOA ObsCore standard stores wavelengths in meters. You can rescale them in
the ``SELECT`` clause to display other units (e.g. nanometers), but you should
use meters when setting constraints on the ``em_min`` and ``em_max`` columns.
This applies even when the underlying data are naturally described in frequency
(e.g. radio observations), enabling uniform queries across observatories.

.. doctest-remote-data::

    >>> query = """SELECT obs_collection AS collection,
    ...                   dataproduct_type AS type,
    ...                   dataproduct_subtype AS subtype,
    ...                   em_min*1E9 AS min_wavel_nm,
    ...                   em_max*1E9 AS max_wavel_nm,
    ...                   em_res_power
    ...            FROM ivoa.ObsCore
    ...            WHERE target_name = 'a370'
    ...              AND em_res_power < 3000"""
    >>> table = eso.query_tap(query=query)
    >>> table
    <Table length=89>
    collection     type     subtype     min_wavel_nm    max_wavel_nm em_res_power
      object      object     object       float64         float64      float64   
    ---------- ------------ -------- ------------------ ------------ ------------
    092.A-0472        image          1981.9999999999998       2307.0       6.5985
        HAWKI measurements   srctbl             1181.0       1335.0       8.1688
        HAWKI        image pawprint             1181.0       1335.0       8.1688
        HAWKI        image     tile             1181.0       1335.0       8.1688
          ...          ...      ...                ...          ...          ...
        HAWKI        image     tile             1181.0       1335.0       8.1688

Query ESO Archive Stats
=======================

The ESO TAP service can also be used to retrieve high-level statistics about the
contents of the ESO Science Archive. 
The example below queries the total number of entries in the
``ivoa.ObsCore`` table, corresponding to the total number of data products
currently exposed through the ESO TAP service.

.. doctest-remote-data::

    >>> query = "SELECT COUNT(*) FROM ivoa.ObsCore"
    >>> table = eso.query_tap(query)
    >>> table
    <Table length=1>
    COUNT_ALL
      int32  
    ---------
      4731624

More detailed statistics can be obtained by grouping on selected metadata
columns. The following example groups all data products by
``dataproduct_type`` and returns both the number of products in each category
and the total estimated archive volume, computed from the
``access_estsize`` column. The results are ordered by decreasing total data
volume.

.. doctest-remote-data::

    >>> query = """SELECT dataproduct_type, 
    ...             COUNT(*) NumProducts, 
    ...             SUM(access_estsize)/1000000000. TB 
    ...             FROM ivoa.ObsCore 
    ...             GROUP BY dataproduct_type 
    ...             ORDER BY 3 DESC 
    ...         """
    >>> table = eso.query_tap(query)
    >>> table
    <Table length=5>
    dataproduct_type numproducts      tb     
        object         int32      float64   
    ---------------- ----------- ------------
                cube      690736  98.60936855
              image      969281 82.775606369
        measurements      675811 50.197075129
            spectrum     2377000  5.434112666
          visibility       18796  0.254378068

These are just some of the many possible ways to query for ESO Science Archive statistics
using the TAP service. For more examples on the available queries,
refer to the `TAP service <https://archive.eso.org/programmatic/#TAP>`_.

Download Data
=============

As with the other functionality, to download the data returned by the above data queries (i.e. not the stats queries), you can use the :meth:`~astroquery.eso.EsoClass.retrieve_data` method. This method takes a list of data product IDs (``dp_id``) and downloads the corresponding files from the ESO archive.

.. doctest-remote-data::
    >>> eso.retrieve_data(table["dp_id"])

The ``data_files`` list points to the decompressed dataset filenames that have been locally downloaded. The default location of the decompressed datasets can be adjusted by providing a ``destination`` keyword in the call to :meth:`~astroquery.eso.EsoClass.retrieve_data`.

.. doctest-skip::
    >>> data_files = eso.retrieve_data(table["dp_id"], destination="./eso_data/")
