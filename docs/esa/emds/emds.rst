.. _astroquery.esa.emds:

**********************************************************************
ESDC Multi-Mission Data Services (EMDS) (`astroquery.esa.emds`)
**********************************************************************

The ESAC Science Data Center (ESDC) develops and operates science archives for ESA missions, providing the community
with access to Planetary, Heliophysics, and Astronomy data collections. As many mission archives transition into a
legacy phase, operating multiple independent archives becomes increasingly resource-intensive and can lead to software
obsolescence, limited standardization, reduced interoperability, and fragmented long-term evolution.

The ESDC Multi-Mission Data Services (EMDS) initiative addresses these challenges by integrating stand-alone mission
archives into a unified and scalable backend system. EMDS promotes cross-disciplinary data discovery and access through
standardized interoperability mechanisms, including the IVOA Table Access Protocol (TAP), and by harmonizing interfaces
across scientific domains. This approach improves maintainability and scalability, supports the migration of existing
archives, and provides a common foundation for future missions and shared user interfaces.

========
Examples
========

---------------
1. Login/Logout
---------------
Some tables and data require authentication to access proprietary or advanced data. Authentication is managed
through the ``login()`` and ``logout()`` methods provided by the EMDS Astroquery module.

.. doctest-remote-data::

  >>> from astroquery.esa.emds import EmdsClass
  >>> emds = EmdsClass()
  >>> emds.login() # doctest: +IGNORE_OUTPUT
  >>> emds.logout() # doctest: +IGNORE_OUTPUT

-----------------------------------
2. Get available tables and columns
-----------------------------------

EMDS Astroquery module allows users to explore the data structure of the TAP by listing available
tables and their columns. This is useful for understanding what data is accessible before running ADQL queries.

  >>> from astroquery.esa.emds import EmdsClass
  >>> emds = EmdsClass()
  >>> emds.get_tables()
  [<VODataServiceTable name="ivoa.ObsCore">... 30 columns ...</VODataServiceTable>]

  >>> obscore_table = emds.get_table(table='ivoa.ObsCore')
  >>> obscore_table.columns
  [<BaseParam name="access_estsize"/>, <BaseParam name="access_format"/>, <BaseParam name="access_url"/>, <BaseParam name="calib_level"/>, <BaseParam name="dataproduct_type"/>, <BaseParam name="em_max"/>, <BaseParam name="em_min"/>, <BaseParam name="em_res_power"/>, <BaseParam name="em_xel"/>, <BaseParam name="facility_name"/>, <BaseParam name="instrument_name"/>, <BaseParam name="o_ucd"/>, <BaseParam name="obs_collection"/>, <BaseParam name="obs_id"/>, <BaseParam name="obs_publisher_did"/>, <BaseParam name="pol_states"/>, <BaseParam name="pol_xel"/>, <BaseParam name="s_dec"/>, <BaseParam name="s_fov"/>, <BaseParam name="s_ra"/>, <BaseParam name="s_region"/>, <BaseParam name="s_resolution"/>, <BaseParam name="s_xel1"/>, <BaseParam name="s_xel2"/>, <BaseParam name="t_exptime"/>, <BaseParam name="t_max"/>, <BaseParam name="t_min"/>, <BaseParam name="t_resolution"/>, <BaseParam name="t_xel"/>, <BaseParam name="target_name"/>]

-------------------------
3. Get available missions
-------------------------

The EMDS TAP service is a *multi-mission* archive: multiple missions and data collections are exposed through a single
TAP endpoint. Each mission typically appears as a distinct value in the ``obs_collection`` field of the EMDS global
ObsCore view.

   >>> from astroquery.esa.emds import EmdsClass
   >>> emds = EmdsClass()
   >>> emds.get_emds_missions()
    <Table length=1>
    obs_collection
        object
    --------------
              EPSA

----------------------------
4. ADQL Queries to EMDS TAP
----------------------------

The Query TAP functionality facilitates the execution of custom Table Access Protocol (TAP) queries within the EMDS.
Results can be exported to a specified file in the chosen format, and queries may be executed asynchronously.

.. doctest-remote-data::

  >>> from astroquery.esa.emds import EmdsClass
  >>> emds = EmdsClass()
  >>> emds.query_tap(
  ...     query=(
  ...         "SELECT dataproduct_type, obs_collection, target_name, obs_id, s_ra, s_dec "
  ...         "FROM ivoa.ObsCore "
  ...         "ORDER BY target_name DESC"
  ...     )
  ... )  # doctest: +IGNORE_OUTPUT

    <Table length=12298>
    dataproduct_type obs_collection target_name    obs_id          s_ra             s_dec
                                                                   deg               deg
         object          object        object      object        float64           float64
    ---------------- -------------- ----------- ----------- ----------------- ------------------
                 arf           EPSA             10202076929                --                 --
                 png           EPSA             11900006256                --                 --
                 png           EPSA             11900006200                --                 --
                 rmf           EPSA             11900012239                --                 --
                 ...            ...         ...         ...               ...                ...
                 img           EPSA   * 111 Tau 11900008319 81.12383618253855  17.41749240154885
               event           EPSA   * 111 Tau 11900008319 81.12383618253855  17.41749240154885
                  lc           EPSA   * 111 Tau 11900008319 81.12383618253855  17.41749240154885
                 pha           EPSA   * 111 Tau 11900008319 81.12383621375398 17.417492453817907

-------------------------------------
5. Filtering the Obs Core Catalogue
-------------------------------------

The EMDS TAP service exposes an ObsCore-compliant catalogue (``ivoa.ObsCore``) that contains observation-level metadata
(e.g. sky position, time coverage, instrument/collection identifiers, and access information). Depending on the mission
and instrument, the catalogue can contain a large number of rows and many columns, so it is not recommended to retrieve
all columns and all rows by default.

Instead, users should filter the catalogue by selecting only the columns required for their use case and applying
constraints (for example by sky region, observation collection, instrument, data product type, or other ObsCore fields).

This module provides a dedicated method to query the EMDS ObsCore view and apply filters based on any available column.

To check the columns available in this catalogue, the following method can be executed using ``get_metadata=True``:

.. doctest-remote-data::

  >>> from astroquery.esa.emds import EmdsClass
  >>> emds = EmdsClass()
  >>> emds.get_observations(get_metadata=True)  # doctest: +IGNORE_OUTPUT

    <Table masked=True length=30>
        Column                   Description                Unit  Data Type           UCD                                   UType
        str17                       object                 object    str6            object                                 object
    -------------- --------------------------------------- ------ --------- ----------------------- ------------------------------------------------------
    access_estsize Estimated size of dataset: in kilobytes  kbyte      long     phys.size;meta.file                                    obscore:Access.size
     access_format           Content format of the dataset   None      char          meta.code.mime                                  obscore:Access.format
        access_url              URL used to access dataset   None      char            meta.ref.url                               obscore:Access.reference
               ...                                     ...    ...       ...                     ...                                                    ...
             t_min                       Start time in MJD      d    double time.start;obs.exposure obscore:Char.TimeAxis.Coverage.Bounds.Limits.StartTime
      t_resolution                Temporal resolution FWHM      s    double         time.resolution          obscore:Char.TimeAxis.Resolution.Refval.value
             t_xel  Number of elements along the time axis   None      long             meta.number                          obscore:Char.TimeAxis.numBins
       target_name                      Object of interest   None      char             meta.id;src                                    obscore:Target.name

Once the columns of interest have been extracted, it is possible to execute the same function with the following
options, that can be combined to extract the required data:

+ Define the reference target or coordinates where a cone search will be executed.

.. doctest-remote-data::

  >>> from astroquery.esa.emds import EmdsClass
  >>> emds = EmdsClass()
  >>> emds.get_observations(target_name='V1589 Cyg')  # doctest: +IGNORE_OUTPUT

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

  >>> from astroquery.esa.emds import EmdsClass
  >>> emds = EmdsClass()
  >>> emds.get_observations(target_name='V1589 Cyg', columns=['s_ra', 's_dec', 'obs_id', 's_xel1'])  # doctest: +IGNORE_OUTPUT

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

  >>> from astroquery.esa.emds import EmdsClass
  >>> emds = EmdsClass()
  >>> emds.get_observations(target_name='V1589 Cyg', columns=['s_ra', 's_dec', 'obs_id', 's_xel1'], s_xel1=('>', 100))  # doctest: +IGNORE_OUTPUT

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

  >>> emds.get_observations(
  ...     columns=["dataproduct_type", "obs_collection", "target_name", "obs_id",
  ...              "s_ra", "s_dec", "instrument_name"]
  ... )  # doctest: +IGNORE_OUTPUT

  >>> emds.get_observations(
  ...     columns=["obs_id", "obs_collection", "instrument_name", "dataproduct_type"],
  ...     obs_collection="EPSA",
  ...     instrument_name="FXT",
  ... )  # doctest: +IGNORE_OUTPUT

  >>> emds.get_observations(
  ...     columns=["obs_id", "target_name"],
  ...     target_name="V1589 Cyg",
  ... )  # doctest: +IGNORE_OUTPUT

  >>> emds.get_observations(
  ...     columns=["obs_id", "dataproduct_type"],
  ...     dataproduct_type=["img", "pha"],
  ... )  # doctest: +IGNORE_OUTPUT

  >>> emds.get_observations(
  ...     columns=["obs_id", "t_min", "t_max"],
  ...     t_min=(">", 60000),
  ... )  # doctest: +IGNORE_OUTPUT

  >>> emds.get_observations(
  ...     columns=["obs_id", "s_ra", "s_dec"],
  ...     s_ra=(80, 82),
  ...     s_dec=(16, 18),
  ... )  # doctest: +IGNORE_OUTPUT

  >>> emds.get_observations(
  ...     coordinates="81.1238 17.4175",
  ...     radius=0.1,
  ...     columns=["obs_id", "s_ra", "s_dec", "instrument_name"],
  ... )  # doctest: +IGNORE_OUTPUT

  >>> emds.get_observations(
  ...     target_name="V1589 Cyg",
  ...     radius=0.1,
  ...     columns=["obs_id", "s_ra", "s_dec", "target_name"],
  ... )  # doctest: +IGNORE_OUTPUT

  >>> emds.get_observations(
  ...     columns=["dataproduct_type", "obs_collection", "target_name", "obs_id",
  ...              "s_ra", "s_dec", "instrument_name"],
  ...     obs_collection="EPSA",
  ...     dataproduct_type=["img", "pha"],
  ...     instrument_name="FXT",
  ... )  # doctest: +IGNORE_OUTPUT


Reference/API
=============

.. automodapi:: astroquery.esa.emds
    :no-inheritance-diagram:
