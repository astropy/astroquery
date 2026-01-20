.. _astroquery.esa.emds.einsteinprobe:

*****************************************************************************
EinsteinProbe Space Archive (EPSA) (`astroquery.esa.emds.einsteinprobe`)
*****************************************************************************

Einstein Probe is an X-ray astronomy mission led by the Chinese Academy of Sciences (CAS),
with international collaboration from the European Space Agency (ESA) and the Max Planck
Institute for Extraterrestrial Physics (MPE). The Einstein Probe data are distributed
through the EMDS archive, which provides access to multiple missions via a single service.

The mission is designed to monitor the X-ray sky and discover transient and variable
phenomena across the Universe. It carries two main scientific instruments: the Wide-field
X-ray Telescope (WXT), which provides a very large field of view for sky monitoring, and
the Follow-up X-ray Telescope (FXT), which enables more detailed observations of selected
sources.

Using its wide field of view, the mission performs a systematic survey of the X-ray sky and
can monitor a large fraction of the Universe simultaneously. This allows the detection of
X-ray emission from a wide range of astrophysical sources, including accreting compact
objects such as black holes and neutron stars, gamma-ray bursts, supernovae, stellar
flares, and transient events within the Solar System, such as X-ray emission from comets.

The mission also searches for tidal disruption events, in which stars are torn apart by the
strong gravitational field of supermassive black holes that are otherwise dormant and
difficult to detect. In addition, it plays an important role in multi-messenger astronomy
by detecting X-ray counterparts of gravitational-wave events, such as mergers of neutron
stars or neutron stars and black holes, helping to localize these events and study their
physical properties.

========
Examples
========

---------------
1. Login/Logout
---------------
Some tables and data require authentication to access proprietary or advanced data. Authentication is managed
through the ``login()`` and ``logout()`` methods provided by the EMDS Astroquery module.

.. doctest-remote-data::

  >>> from astroquery.esa.emds.einsteinprobe import EinsteinProbeClass
  >>> epsa = EinsteinProbeClass()
  >>> epsa.login() # doctest: +IGNORE_OUTPUT
  >>> epsa.logout() # doctest: +IGNORE_OUTPUT

-----------------------------------
2. Get available tables and columns
-----------------------------------

Einstein Probe Astroquery module allows users to explore the data structure of the TAP by listing available
tables and their columns. This is useful for understanding what data is accessible before running ADQL queries.

  >>> from astroquery.esa.emds.einsteinprobe import EinsteinProbeClass
  >>> epsa = EinsteinProbeClass()
  >>> epsa.get_tables()
  [<VODataServiceTable name="einsteinprobe.fxt_product">... 24 columns ...</VODataServiceTable>, <VODataServiceTable name="einsteinprobe.obscore">... 30 columns ...</VODataServiceTable>, <VODataServiceTable name="einsteinprobe.obscore_extended">... 34 columns ...</VODataServiceTable>, <VODataServiceTable name="einsteinprobe.preview_products">... 2 columns ...</VODataServiceTable>, <VODataServiceTable name="einsteinprobe.wxt_product">... 22 columns ...</VODataServiceTable>]

By default, ``get_tables()`` returns table objects with metadata. If ``only_names=True`` is provided, the method returns
only the table names as strings. This is useful when you only need to inspect or display the available tables without
accessing their full metadata.

.. doctest-remote-data::

  >>> epsa.get_tables(only_names=True)
  ['einsteinprobe.fxt_product', 'einsteinprobe.obscore', 'einsteinprobe.obscore_extended', 'einsteinprobe.preview_products', 'einsteinprobe.wxt_product']

Once a specific table is selected using ``get_table()``, the returned object provides access to the table metadata,
including its columns.

.. doctest-remote-data::

  >>> obscore_table = epsa.get_table('einsteinprobe.obscore_extended')
  >>> obscore_table.columns
  [<BaseParam name="access_estsize"/>, <BaseParam name="access_format"/>, <BaseParam name="access_url"/>, <BaseParam name="calib_level"/>, <BaseParam name="dataproduct_type"/>, <BaseParam name="em_max"/>, <BaseParam name="em_min"/>, <BaseParam name="em_res_power"/>, <BaseParam name="em_xel"/>, <BaseParam name="facility_name"/>, <BaseParam name="filename"/>, <BaseParam name="filepath"/>, <BaseParam name="has_preview"/>, <BaseParam name="instrument_name"/>, <BaseParam name="o_ucd"/>, <BaseParam name="obs_collection"/>, <BaseParam name="obs_id"/>, <BaseParam name="obs_publisher_did"/>, <BaseParam name="pol_states"/>, <BaseParam name="pol_xel"/>, <BaseParam name="preview"/>, <BaseParam name="s_dec"/>, <BaseParam name="s_fov"/>, <BaseParam name="s_ra"/>, <BaseParam name="s_region"/>, <BaseParam name="s_resolution"/>, <BaseParam name="s_xel1"/>, <BaseParam name="s_xel2"/>, <BaseParam name="t_exptime"/>, <BaseParam name="t_max"/>, <BaseParam name="t_min"/>, <BaseParam name="t_resolution"/>, <BaseParam name="t_xel"/>, <BaseParam name="target_name"/>]

----------------------------
3. ADQL Queries to EMDS TAP
----------------------------

The Query TAP functionality facilitates the execution of custom Table Access Protocol (TAP)
queries within the EMDS service. Queries can be executed synchronously or asynchronously,
and results may be exported in different output formats.

When using the Einstein Probe client, ADQL queries are executed against the EMDS TAP service.
Mission-specific tables are exposed under their corresponding TAP schemas (e.g. ``einsteinprobe``),
and can be queried directly using fully-qualified table names.

.. doctest-remote-data::

  >>> from astroquery.esa.emds.einsteinprobe import EinsteinProbeClass
  >>> epsa = EinsteinProbeClass()
  >>> epsa.query_tap(
  ...     query=(
  ...         "SELECT dataproduct_type, obs_collection, target_name, obs_id, s_ra, s_dec "
  ...         "FROM einsteinprobe.obscore_extended "
  ...         "ORDER BY target_name DESC"
  ...     )
  ... )  # doctest: +IGNORE_OUTPUT

    <Table length=12298>
    dataproduct_type obs_collection target_name    obs_id           s_ra             s_dec
         object          object        object      object         float64           float64
    ---------------- -------------- ----------- ------------ ----------------- ------------------
                 arf           EPSA              10202076929                --                 --
                 png           EPSA              11900006256                --                 --
                 ...            ...         ...          ...               ...                ...
                  lc           EPSA   * 111 Tau  11900008319 81.12383618253855  17.41749240154885
                 pha           EPSA   * 111 Tau  11900008319 81.12383621375398 17.417492453817907


-------------------------------------
4. Filtering the Obs Core Catalogue
-------------------------------------

The EMDS TAP service provides a catalogue with observation-level information, such as sky
position, time coverage, instrument details, and data product identifiers. Since EMDS is a
multi-mission archive, each mission exposes its own observation catalogue.

When using the Einstein Probe client, queries are performed on the Einstein Probe catalogue,
which is exposed under a mission-specific schema.

These catalogues can be large, so it is usually not practical to retrieve all rows and
columns at once. Instead, users are encouraged to select only the columns they need and
apply filters, for example by sky position, data product type, or observation collection.

The ``get_observations`` method provides a convenient way to query the Einstein Probe
observation catalogue and apply such filters.

To inspect the available columns in the catalogue, the following method can be executed
using ``get_metadata=True``:

.. doctest-remote-data::

  >>> from astroquery.esa.emds.einsteinprobe import EinsteinProbeClass
  >>> epsa = EinsteinProbeClass()
  >>> epsa.get_observations(get_metadata=True)  # doctest: +IGNORE_OUTPUT

    <Table masked=True length=34>
        Column     Description  Unit  Data Type  UCD   UType
        str17         object   object    str7   object object
    -------------- ----------- ------ --------- ------ ------
    access_estsize        None   None      long   None   None
     access_format        None   None      char   None   None
               ...         ...    ...       ...    ...    ...
      t_resolution        None   None    double   None   None
             t_xel        None   None    double   None   None
       target_name        None   None      char   None   None

Once the columns of interest have been extracted, it is possible to execute the same function with the following
options, that can be combined to extract the required data:

+ Define the reference target or coordinates where a cone search will be executed.

.. doctest-remote-data::

  >>> from astroquery.esa.emds.einsteinprobe import EinsteinProbeClass
  >>> epsa = EinsteinProbeClass()
  >>> epsa.get_observations(target_name='V1589 Cyg')  # doctest: +IGNORE_OUTPUT

    Executed query:SELECT * FROM ivoa.ObsCore WHERE 1=CONTAINS(POINT('ICRS', s_ra, s_dec),CIRCLE('ICRS', 310.7048109, 41.3833259, 1.0))
    <Table length=12>
    access_estsize        access_format        ... t_xel target_name
        kbyte                                  ...
        int64                 object           ... int64    object
    -------------- --------------------------- ... ----- -----------
            463680 application/x-fits-bintable ... 19233   V1589 Cyg
           2888640 application/x-fits-bintable ...    --           0
             51840 application/x-fits-bintable ...   961   V1589 Cyg
            745920 application/x-fits-bintable ... 19233   V1589 Cyg
               ...                         ... ...   ...         ...
           2888640 application/x-fits-bintable ...    --           0
           1465920 application/x-fits-bintable ... 19234   V1589 Cyg
            362880 application/x-fits-bintable ... 19234   V1589 Cyg
           1465920 application/x-fits-bintable ... 19233   V1589 Cyg

+ Retrieve only a specific set of columns.

.. doctest-remote-data::

  >>> from astroquery.esa.emds.einsteinprobe import EinsteinProbeClass
  >>> epsa = EinsteinProbeClass()
  >>> epsa.get_observations(target_name='V1589 Cyg', columns=['s_ra', 's_dec', 'obs_id', 's_xel1'])  # doctest: +IGNORE_OUTPUT

    Executed query:SELECT s_ra, s_dec, obs_id, s_xel1 FROM ivoa.ObsCore WHERE 1=CONTAINS(POINT('ICRS', s_ra, s_dec),CIRCLE('ICRS', 310.7048109, 41.3833259, 1.0))
    <Table length=12>
           s_ra             s_dec           obs_id   s_xel1
           deg               deg
         float64           float64          object   int64
    ----------------- ------------------ ----------- ------
    310.6757640621578 41.351414087733275 11900012239     95
    310.6755985583337 41.351202980612555 11900012239    600
    310.6755985583337 41.351202980612555 11900012239     20
    310.6755985583337 41.351202980612555 11900012239    418
                  ...                ...         ...    ...
    310.6755985583337 41.351202980612555 11900012239    600
    310.6756375374491 41.351278441170614 11900012239    600
    310.6756375374491 41.351278441170614 11900012239     95
    310.6757640621578 41.351414087733275 11900012239    600

+ Filter by any other column available in the previous method.

.. doctest-remote-data::

  >>> from astroquery.esa.emds.einsteinprobe import EinsteinProbeClass
  >>> epsa = EinsteinProbeClass()
  >>> epsa.get_observations(target_name='V1589 Cyg', columns=['s_ra', 's_dec', 'obs_id', 's_xel1'], s_xel1=('>', 100))  # doctest: +IGNORE_OUTPUT

    Executed query:SELECT s_ra, s_dec, obs_id, s_xel1 FROM ivoa.ObsCore  WHERE s_xel1 > 100 AND 1=CONTAINS(POINT('ICRS', s_ra, s_dec),CIRCLE('ICRS', 310.7048109, 41.3833259, 1.0))
    <Table length=8>
           s_ra             s_dec           obs_id   s_xel1
           deg               deg
         float64           float64          object   int64
    ----------------- ------------------ ----------- ------
    310.6755985583337 41.351202980612555 11900012239    600
    310.6755985583337 41.351202980612555 11900012239    418
    310.6755993340324  41.35120289084306 11900012239    600
    310.6755993340324  41.35120289084306 11900012239    600
    310.6755993340324  41.35120289084306 11900012239    418
    310.6755985583337 41.351202980612555 11900012239    600
    310.6756375374491 41.351278441170614 11900012239    600
    310.6757640621578 41.351414087733275 11900012239    600

As it can be observed in the previous examples, additional constraints can be provided using the ``**filters`` syntax,
where the keyword corresponds to an ObsCore column name and the value defines the filter to be applied. The method
translates these filters into the corresponding ADQL constraints executed by the TAP service.

Some examples and their corresponding ADQL transformations are provided below:

+ Exact match (string): ``obs_collection="EPSA"`` -> ``obs_collection = 'EPSA'``

+ Exact match (string): ``instrument_name="FXT"`` -> ``instrument_name = 'FXT'``

+ Wildcards (string): ``target_name="AT 2023%"`` -> ``target_name ILIKE 'AT 2023%'``
  (``*`` may also be accepted as an alias for ``%`` depending on the backend configuration)

+ String list: ``dataproduct_type=["img", "pha"]`` -> ``dataproduct_type = 'img' OR dataproduct_type = 'pha'``
  (some TAP services may translate this to an equivalent ``IN ('img','pha')`` clause)

+ Numeric comparison: ``t_min=(">", 60000)`` -> ``t_min > 60000``

+ Filter by numeric interval: ``s_ra=(80, 82)`` -> ``s_ra >= 80 AND s_ra <= 82``

+ Combined filters: ``obs_collection="EPSA", instrument_name="FXT"`` -> ``obs_collection = 'EPSA' AND instrument_name = 'FXT'``

  >>> epsa.get_observations(
  ...     columns=["dataproduct_type", "obs_collection", "target_name", "obs_id",
  ...              "s_ra", "s_dec", "instrument_name"]
  ... )  # doctest: +IGNORE_OUTPUT

  >>> epsa.get_observations(
  ...     columns=["obs_id", "obs_collection", "instrument_name", "dataproduct_type"],
  ...     obs_collection="EPSA",
  ...     instrument_name="FXT",
  ... )  # doctest: +IGNORE_OUTPUT

  >>> epsa.get_observations(
  ...     columns=["obs_id", "target_name"],
  ...     target_name="V1589 Cyg",
  ... )  # doctest: +IGNORE_OUTPUT

  >>> epsa.get_observations(
  ...     columns=["obs_id", "dataproduct_type"],
  ...     dataproduct_type=["img", "pha"],
  ... )  # doctest: +IGNORE_OUTPUT

  >>> epsa.get_observations(
  ...     columns=["obs_id", "t_min", "t_max"],
  ...     t_min=(">", 60000),
  ... )  # doctest: +IGNORE_OUTPUT

  >>> epsa.get_observations(
  ...     columns=["obs_id", "s_ra", "s_dec"],
  ...     s_ra=(80, 82),
  ...     s_dec=(16, 18),
  ... )  # doctest: +IGNORE_OUTPUT

  >>> epsa.get_observations(
  ...     coordinates="81.1238 17.4175",
  ...     radius=0.1,
  ...     columns=["obs_id", "s_ra", "s_dec", "instrument_name"],
  ... )  # doctest: +IGNORE_OUTPUT

  >>> epsa.get_observations(
  ...     target_name="V1589 Cyg",
  ...     radius=0.1,
  ...     columns=["obs_id", "s_ra", "s_dec", "target_name"],
  ... )  # doctest: +IGNORE_OUTPUT

  >>> epsa.get_observations(
  ...     columns=["dataproduct_type", "obs_collection", "target_name", "obs_id",
  ...              "s_ra", "s_dec", "instrument_name"],
  ...     obs_collection="EPSA",
  ...     dataproduct_type=["img", "pha"],
  ...     instrument_name="FXT",
  ... )  # doctest: +IGNORE_OUTPUT

-------------------------
5. Download file product
-------------------------

Observations in the Einstein Probe catalogue are associated with one or more data products,
such as science files or preview images. These products are stored as files on the EMDS
data service and can be accessed once the corresponding observation or product identifiers
are known.

Typically, users first query the observation catalogue to identify the observations of
interest and inspect the available metadata (for example product type, filename, or file
path). Based on this information, individual products can then be downloaded.

This module provides helper methods to retrieve product information and to download
individual files directly from the EMDS data service.

.. doctest-remote-data::

  >>> from astroquery.esa.emds.einsteinprobe import EinsteinProbeClass
  >>> epsa = EinsteinProbeClass()
  >>> epsa.get_products(obs_id=' 11900008319') # doctest: +IGNORE_OUTPUT

    Executed query:SELECT obs_id, filename, filepath FROM einsteinprobe.obscore_extended WHERE obs_id = ' 11900008319'
    <Table length=20>
       obs_id                    filename                              filepath
       object                     object                                object
    ------------ --------------------------------------- -----------------------------------
     11900008319  fxt_b_11900008319_ff_01_po_cl_3ac.fits /epsa/repo/11900008319/fxt/products
     11900008319      fxt_b_11900008319_ff_01_po_3ac.pha /epsa/repo/11900008319/fxt/products
             ...                                     ...                                 ...
     11900008319 fxt_a_11900008319_ff_01_po_gti_3bb.fits /epsa/repo/11900008319/fxt/products
     11900008319      fxt_b_11900008319_ff_01_po_3bb.arf /epsa/repo/11900008319/fxt/products
     11900008319      fxt_b_11900008319_ff_01_po_3bb.rmf /epsa/repo/11900008319/fxt/products

The following example shows how to download a single data product using its filename.
By default, the file is downloaded to the current working directory.

.. doctest-remote-data::

    >>> from astroquery.esa.emds.einsteinprobe import EinsteinProbeClass
    >>> epsa.download_product(filename='fxt_b_11900008319_ff_01_po_3bb.rmf') # doctest: +IGNORE_OUTPUT
    'fxt_b_11900008319_ff_01_po_3bb.rmf'

Product downloads return the files as stored in the archive. No output format needs to be
specified when downloading data products.


Reference/API
=============

.. automodapi:: astroquery.esa.emds.einsteinprobe
    :no-inheritance-diagram: