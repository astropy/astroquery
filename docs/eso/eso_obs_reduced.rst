
*************************************
Observations - Query for Reduced Data
*************************************

In addition to raw observational files, the ESO Science Archive provides access to a wide range of **processed (reduced) data products**. These include science-ready images, spectra, and datacubes that have been validated by ESO (through the `ESO Phase 3 <https://www.eso.org/sci/observing/phase3.html>`_ process).

Available Surveys
=================

The list of available surveys can be obtained with :meth:`~astroquery.eso.EsoClass.list_surveys` as follows:

.. doctest-remote-data::

    >>> from astroquery.eso import Eso
    >>> eso = Eso()

.. doctest-remote-data::

    >>> surveys = eso.list_surveys()
    >>> surveys # doctest: +IGNORE_OUTPUT
    ['081.C-0827', '092.A-0472', '096.B-0054', '1100.A-0528', '1101.A-0127', '193.D-0232',
    '195.B-0283', '196.B-0578', '196.D-0214', '197.A-0384', '198.A-0708', '60.A-9284H',
    '60.A-9493', 'ADHOC', 'ALCOHOLS', 'ALLSMOG', 'ALMA', 'AMAZE', 'AMBRE', 'APEX-SciOps',
    'ARP_VST', 'ATLASGAL', 'CAFFEINE', 'ENTROPY', 'ePESSTOplus', 'ERIS-NIX',
    'ERIS-SPIFFIER', 'ESPRESSO', 'ESSENCE', 'FDS', 'FEROS', 'Fornax3D', 'FORS2-SPEC',
    'GAIAESO', 'GCAV', 'GIRAFFE', 'GOODS_FORS2', 'GOODS_ISAAC', 'GOODS_VIMOS_IMAG',
    'GOODS_VIMOS_SPEC', 'GW170817', 'HARPS', 'HAWKI', 'HUGS', 'INSPIRE', 'KIDS', 'KMOS',
    'LEGA-C', 'LESS', 'MAGIC', 'MUSE', 'MUSE-DEEP', 'MUSE-STD', 'MW-BULGE-PSFPHOT',
    'NGTS', 'NIRPS', 'OMEGACAM_INAF', 'PENELLOPE', 'PESSTO', 'PHANGS', 'PIONIER',
    'SHARKS', 'SPHERE', 'SUPER', 'UltraVISTA', 'UVES', 'UVES_SQUAD', 'VANDELS', 'VEGAS',
    'VEILS', 'VEXAS', 'VHS', 'VIDEO', 'VIKING', 'VIMOS', 'VINROUGE', 'VIPERS', 'VISIONS',
    'VMC', 'VPHASplus', 'VST-ATLAS', 'VVV', 'VVVX', 'XQ-100', 'XSGRB', 'XSHOOTER',
    'XShootU', 'XSL', 'ZCOSMOS']

Available Query Constraints
===========================

As before, list the possible columns in :meth:`~astroquery.eso.EsoClass.query_surveys` that can be queried with: 

.. doctest-remote-data::

    >>> eso.query_surveys(help=True) # get help on the ESO query
    INFO: 
    Columns present in the table ivoa.ObsCore:
        column_name     datatype    xtype     unit 
    ------------------- -------- ----------- ------
               abmaglim   double                mag
         access_estsize     long              kbyte
          access_format     char                   
             access_url     char                   
          bib_reference     char                   
            calib_level      int                                 
                    ...
            target_name     char                   
    Number of records present in the table ivoa.ObsCore:
    4559928
    [astroquery.eso.core]

.. note::
   Column names may differ between the tables returned by different query
   methods. Users are encouraged to inspect closely the available columns and supported
   filters using the ``help=True`` option. For example, for raw data queries
   (:meth:`~astroquery.eso.EsoClass.query_main` and
   :meth:`~astroquery.eso.EsoClass.query_instrument`), the target name is specified
   using the ``object`` column, whereas for reduced data queries
   (:meth:`~astroquery.eso.EsoClass.query_surveys`) the corresponding column is
   named ``target_name``.

Query with Constraints (Specific Survey)
========================================

Let's assume that we work with the `HARPS survey <https://www.eso.org/rm/api/v1/public/releaseDescriptions/72>`_. The archive can be queried as follows:

.. doctest-remote-data::

    >>> table = eso.query_surveys(surveys="HARPS")
    >>> table # doctest: +IGNORE_OUTPUT
    <Table length=1000>
    target_name     s_ra     s_dec              dp_id             proposal_id  abmaglim access_estsize ...   snr    strehl t_exptime     t_max          t_min      t_resolution t_xel
                    deg       deg                                                mag        kbyte      ...                     s           d              d             s            
    object     float64   float64             object               object    float64      int64      ... float64 float64  float64     float64        float64       float64    int64
    ------------ --------- --------- --------------------------- ------------- -------- -------------- ... ------- ------- --------- -------------- -------------- ------------ -----
        HD203608 321.61455 -65.36429 ADP.2014-09-16T11:03:30.940 077.D-0720(A)       --           5261 ...    60.9      --      33.0 53956.24265204 53956.24227009     33.00048    --
        HD114613  198.0129 -37.80367 ADP.2014-09-16T11:03:30.947 072.C-0488(E)       --           5261 ...   267.2      --   120.002 53765.36393677 53765.36254786   120.001824    --
        HIP5158  16.50838 -22.45455 ADP.2014-09-16T11:03:30.973 072.C-0488(E)       --           5261 ...    39.3      --   711.599 53946.33177006 53946.32353395   711.599904    --
            ...       ...       ...                         ...           ...      ...            ... ...     ...     ...       ...            ...            ...          ...   ...
        HD203608 321.60939 -65.36484 ADP.2014-09-16T11:03:45.713 077.D-0720(A)       --           5261 ...    45.0      --      33.0 53955.11202646 53955.11164451     33.00048    --

Suppose we want both `HARPS survey <https://www.eso.org/rm/api/v1/public/releaseDescriptions/72>`_ and `NIRPS survey <https://www.eso.org/rm/api/v1/public/releaseDescriptions/233>`_ data products.

.. doctest-remote-data::

    >>> table = eso.query_surveys(surveys=["HARPS", "NIRPS"])
    >>> table # doctest: +IGNORE_OUTPUT
    <Table length=1000>
    target_name     s_ra     s_dec              dp_id             proposal_id  abmaglim access_estsize ...   snr    strehl t_exptime     t_max          t_min      t_resolution t_xel
                    deg       deg                                                mag        kbyte      ...                     s           d              d             s            
    object     float64   float64             object               object    float64      int64      ... float64 float64  float64     float64        float64       float64    int64
    ------------ --------- --------- --------------------------- ------------- -------- -------------- ... ------- ------- --------- -------------- -------------- ------------ -----
        HD203608 321.61455 -65.36429 ADP.2014-09-16T11:03:30.940 077.D-0720(A)       --           5261 ...    60.9      --      33.0 53956.24265204 53956.24227009     33.00048    --
        HD114613  198.0129 -37.80367 ADP.2014-09-16T11:03:30.947 072.C-0488(E)       --           5261 ...   267.2      --   120.002 53765.36393677 53765.36254786   120.001824    --
        HIP5158  16.50838 -22.45455 ADP.2014-09-16T11:03:30.973 072.C-0488(E)       --           5261 ...    39.3      --   711.599 53946.33177006 53946.32353395   711.599904    --
            ...       ...       ...                         ...           ...      ...            ... ...     ...     ...       ...            ...            ...          ...   ...
        HD203608 321.60939 -65.36484 ADP.2014-09-16T11:03:45.713 077.D-0720(A)       --           5261 ...    45.0      --      33.0 53955.11202646 53955.11164451     33.00048    --

Now we see that this query is limited to 1000 results, so we can increase the row limit to retrieve all matching datasets and limit the columns returned:

.. doctest-remote-data::

    >>> eso.ROW_LIMIT = -1 # 0 or None to return all results without truncation
    >>> table = eso.query_surveys(surveys=["HARPS", "NIRPS"], 
    ...                          columns=["target_name", "s_ra", "s_dec", "dp_id", "proposal_id"])
    >>> table # doctest: +IGNORE_OUTPUT
    <Table length=376351>
    target_name      s_ra      s_dec              dp_id             proposal_id  
                    deg        deg                                              
        object      float64    float64             object               object    
    --------------- ---------- --------- --------------------------- --------------
            HD17051   40.64236 -50.80053 ADP.2014-09-16T11:03:41.583  078.D-0067(A)
            HD69830  124.59872  -12.6353 ADP.2014-09-16T11:03:41.610  072.C-0488(E)
            HD63077  116.39514 -34.17365 ADP.2014-09-16T11:03:41.617  076.D-0103(A)
                ...        ...       ...                         ...            ...
        TOI-2322 116.961088 -71.00243 ADP.2026-01-13T11:49:12.986   116.2974.001

The returned table has a ``dp_id`` column, which can be used to retrieve the datasets with
:meth:`~astroquery.eso.EsoClass.retrieve_data`: ``eso.retrieve_data(table["dp_id"])``.
Note that, in this example, there are 376,351 matching data products across both surveys so downloading
all of them may take a significant amount of time and disk space.
More details about this method are in the following section.

.. tip:: 
    
    As an example, making use of the TAP free query command, :meth:`~astroquery.eso.EsoClass.query_tap`, 
    you can also retrieve the documentation URL for every available collection with a query like:

    .. doctest-remote-data::

        >>> query = """
        ... SELECT DISTINCT obs_collection, release_description
        ... FROM ivoa.ObsCore
        ... WHERE release_description IS NOT NULL
        ... ORDER BY obs_collection, release_description
        ... """
        >>> table = eso.query_tap(query) # doctest: +SKIP
        >>> print(table[:5]) # doctest: +SKIP
        obs_collection                     release_description                    
        -------------- -----------------------------------------------------------
            081.C-0827 http://www.eso.org/rm/api/v1/public/releaseDescriptions/160
            092.A-0472 http://www.eso.org/rm/api/v1/public/releaseDescriptions/75
            096.B-0054 http://www.eso.org/rm/api/v1/public/releaseDescriptions/142
            108.2289   http://www.eso.org/rm/api/v1/public/releaseDescriptions/236
            110.23NK   http://www.eso.org/rm/api/v1/public/releaseDescriptions/239

Query with Constraints (Specific Instrument)
============================================

You can also query a specific instrument using the same method. For example, to retrieve **all** available HARPS data products regardless of the associated survey:

.. doctest-remote-data::

    >>> table = eso.query_surveys(column_filters={"instrument_name": "HARPS"})
    >>> table # doctest: +IGNORE_OUTPUT
    <Table length=1000>
    target_name     s_ra     s_dec              dp_id             proposal_id  abmaglim access_estsize ...   snr    strehl t_exptime     t_max          t_min      t_resolution t_xel
                    deg       deg                                                mag        kbyte      ...                     s           d              d             s            
    object     float64   float64             object               object    float64      int64      ... float64 float64  float64     float64        float64       float64    int64
    ------------ --------- --------- --------------------------- ------------- -------- -------------- ... ------- ------- --------- -------------- -------------- ------------ -----
        HD203608 321.61455 -65.36429 ADP.2014-09-16T11:03:30.940 077.D-0720(A)       --           5261 ...    60.9      --      33.0 53956.24265204 53956.24227009     33.00048    --
        HD114613  198.0129 -37.80367 ADP.2014-09-16T11:03:30.947 072.C-0488(E)       --           5261 ...   267.2      --   120.002 53765.36393677 53765.36254786   120.001824    --
        HIP5158  16.50838 -22.45455 ADP.2014-09-16T11:03:30.973 072.C-0488(E)       --           5261 ...    39.3      --   711.599 53946.33177006 53946.32353395   711.599904    --
            ...       ...       ...                         ...           ...      ...            ... ...     ...     ...       ...            ...            ...          ...   ...
        HD203608 321.60939 -65.36484 ADP.2014-09-16T11:03:45.713 077.D-0720(A)       --           5261 ...    45.0      --      33.0 53955.11202646 53955.11164451     33.00048    --

.. tip:: 

    Keep in mind that the definition of a ``survey`` (also referred to as a **collection** in the ESO Science Archive) is not the same as the definition of an **instrument**. The ``instrument_name`` refers to the actual hardware that acquired the data (e.g., ``HARPS``, ``MUSE``), whereas the ``obs_collection`` identifies the scientific programme, survey, or processing pipeline associated with the data product. In many cases, survey names match the instrument name (e.g., ``HARPS``, ``MUSE``, ``XSHOOTER``), which typically indicates **products processed and curated by ESO**. However, when the collection name differs (e.g., ``AMBRE``, ``GAIAESO``, ``PHANGS``), it usually denotes **community-contributed data** from large collaborations or specific science teams.

    So, for example, querying for ``eso.query_surveys(column_filters={"instrument_name": "HARPS"})`` will return all products taken with the HARPS instrument, across all programmes and collections. In contrast, filtering on ``eso.query_surveys(surveys="HARPS")`` will return only the `HARPS data reduced by ESO <https://doi.eso.org/10.18727/archive/33>`_. You can inspect the collection for each result via the ``obs_collection`` column in your results table.

Download Data
=============

To download the data returned by the query, you can use the :meth:`~astroquery.eso.EsoClass.retrieve_data` method. This method takes a list of data product IDs (``dp_id``) and downloads the corresponding files from the ESO archive.

.. doctest-remote-data::
    >>> eso.retrieve_data(table["dp_id"]) # doctest: +SKIP

The ``data_files`` list points to the decompressed dataset filenames that have been locally downloaded. The default location of the decompressed datasets can be adjusted by providing a ``destination`` keyword in the call to :meth:`~astroquery.eso.EsoClass.retrieve_data`.

.. doctest-remote-data::
    >>> data_files = eso.retrieve_data(table["dp_id"], destination="./eso_data/") # doctest: +SKIP
