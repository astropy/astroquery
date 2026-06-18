NADC Query Guide
================

NADC modules provide high-level methods for common queries plus direct methods
for custom catalog searches and data-product access. The exact advanced query
interface depends on the archive.

For CSTAR, FASHI, Legacy Plate, SCUSS, and SAGE, the recommended progression is:

1. High-level query methods for common use cases. Users provide parameters
   such as magnitude ranges, image quality limits,
   stellar-parameter ranges, or archive filters; the method selects the
   catalog/table and builds the request payload.
2. Direct catalog/table methods such as ``query_catalog`` and ``query_table``
   for advanced queries and service-level access. Use ``list_tables`` and
   ``list_columns`` to discover valid table and column names. Prefer
   ``ColumnConstraint`` over raw dictionaries when using these methods
   directly.

LAMOST uses a separate archive query interface. It provides high-level
spectral helpers plus direct methods such as ``query_sql`` and
``query_catalog``.

Legacy China-VO Import Paths
----------------------------

NADC modules can also be imported through matching ``astroquery.chinavo``
paths. These are compatibility aliases to the same objects, not separate
implementations:

.. doctest::

  >>> from astroquery.nadc.cstar import Cstar
  >>> from astroquery.chinavo.cstar import Cstar as ChinaVOCstar
  >>> Cstar is ChinaVOCstar
  True

The alias modules are ``chinavo.lamost``, ``chinavo.cstar``,
``chinavo.fashi``, ``chinavo.legacyplate``, ``chinavo.scuss``, and
``chinavo.sage``.

Recommended Query Methods
-------------------------

.. list-table::
   :header-rows: 1
   :widths: 18 32 30 20

   * - Module
     - Recommended high-level methods
     - Main use case
     - Advanced queries
   * - ``nadc.lamost``
     - ``query_spectra``; ``query_stellar_parameters``;
       ``query_repeat_observations``
     - Spectral catalog samples, stellar-parameter cuts, repeated observations
     - ``query_region``; ``query_ssap``; ``query_sql``; ``query_catalog``
   * - ``nadc.scuss``
     - ``query_sources``; ``query_images``; ``query_proper_motions``;
       ``query_sdss_matches``
     - Source photometry, image quality, proper motions, SDSS matches
     - ``query_table``; ``query_catalog``; ``list_tables``; ``list_columns``
   * - ``nadc.cstar``
     - ``query_sources``
     - CSTAR source photometry with magnitude and uncertainty filters
     - ``query_region``; ``query_catalog``; ``query_table``
   * - ``nadc.fashi``
     - ``query_hi_sources``; ``query_alfalfa_matches``;
       ``query_sdss_phot_counterparts``;
       ``query_sdss_spec_counterparts``; ``query_sga_counterparts``
     - FASHI HI sources and precomputed ALFALFA, SDSS, and SGA counterparts
     - ``query_table``; ``query_catalog``; ``list_coordinate_groups``
   * - ``nadc.legacyplate``
     - ``query_plates``; ``query_plate_images``
     - Plate archive discovery by year, observatory, telescope, target, and
       sky position
     - ``query_catalog*``; ``query_table``; ``query_siap``;
       download helpers
   * - ``nadc.sage``
     - ``query_uv_sources``; ``query_gri_sources``;
       ``query_stellar_parameters``
     - SAGE UV/gri photometry and stellar-parameter quality selection
     - ``query_table``; ``query_catalog``; ``list_tables``; ``list_columns``

Advanced Query Availability
---------------------------

Detailed examples belong in the module pages because each archive
has different catalog names, table names, spatial helpers, and data-product
endpoints. This page keeps only the compatibility map and one representative
example.

.. list-table::
   :header-rows: 1
   :widths: 18 22 38 22

   * - Module
     - Table-level queries
     - Advanced methods
     - Detailed examples
   * - ``nadc.lamost``
     - No
     - ``query_sql``; ``query_catalog``; ``query_region``; ``query_ssap``;
       metadata, spectrum, and image helpers
     - :doc:`lamost`
   * - ``nadc.cstar``
     - ``query_table``
     - ``query_catalog``; ``query_catalog_cone``; ``query_catalog_rectangle``;
       ``query_catalog_proximity``
     - :doc:`cstar`
   * - ``nadc.fashi``
     - ``query_table``
     - ``query_catalog``; ``list_coordinate_groups``
     - :doc:`fashi`
   * - ``nadc.legacyplate``
     - ``query_table``
     - ``query_catalog*``; ``query_table_cone``; ``query_siap``;
       download helpers
     - :doc:`legacyplate`
   * - ``nadc.scuss``
     - ``query_table``
     - ``query_catalog``
     - :doc:`scuss`
   * - ``nadc.sage``
     - ``query_table``
     - ``query_catalog``
     - :doc:`sage`

Shared Query Data Methods
-------------------------

The CSTAR, FASHI, Legacy Plate, SCUSS, and SAGE modules share the NADC Query
Data interface. These methods are inherited by each module's query class, but
individual catalogs can expose only a subset of the underlying service
capabilities.

.. list-table::
   :header-rows: 1
   :widths: 24 76

   * - Method group
     - Methods
   * - Discovery and schema
     - ``ping``; ``list_catalogs``; ``get_catalog_metadata``;
       ``list_tables``; ``list_columns``; ``list_schema``;
       ``describe_catalog``; ``list_coordinate_groups``;
       ``list_table_links``; ``list_docs``; ``get_doc``
   * - Spatial and direct query
     - ``query_region``; ``query_object``; ``conesearch``;
       ``query_siap``; ``query_catalog``; ``query_table``;
       ``query_catalog_cone``; ``query_catalog_rectangle``;
       ``query_catalog_proximity``; ``query_table_cone``;
       ``query_table_rectangle``; ``query_table_proximity``
   * - Submitted jobs and results
     - ``submit_query``; ``submit_table_query``; ``get_results``;
       ``get_count``
   * - Downloads
     - ``download_file``; ``batch_download``; ``download_products``

Download methods are available only for catalogs whose
``get_catalog_metadata`` response declares file-download support. Check the
metadata before using ``download_file``, ``batch_download``, or
``download_products`` against a new catalog.

Recommended Usage Pattern
-------------------------

Use high-level query methods first when the operation has a stable meaning and
represents a common query:

.. doctest::

  >>> import astropy.units as u
  >>> from astropy.coordinates import SkyCoord
  >>> from astroquery.nadc.cstar import Cstar
  >>> center = SkyCoord(1*u.deg, 2*u.deg)
  >>> payload = Cstar.query_sources(
  ...     center,
  ...     5*u.arcsec,
  ...     mag_range=(10, 13.5),
  ...     magerr_max=0.05,
  ...     columns=["id", "ra", "dec", "mag", "magerr"],
  ...     get_query_payload=True,
  ... )
  >>> payload["submit"]["json"]["column_constraints"][0]["column_name"]
  'mag'

Use direct catalog/table methods with ``ColumnConstraint`` for advanced queries
that need a custom combination of columns, constraints, sort order, and spatial
selection:

.. doctest::

  >>> from astroquery.nadc import ColumnConstraint
  >>> from astroquery.nadc.legacyplate import Legacyplate
  >>> payload = Legacyplate.query_table(
  ...     catalog="legacyplate-image",
  ...     table="image",
  ...     showcol=["id", "year", "observat"],
  ...     column_constraints=[
  ...         ColumnConstraint.greaterequal("year", 1950),
  ...         ColumnConstraint.equal("observat", "Naoc"),
  ...     ],
  ...     sort="year",
  ...     order="desc",
  ...     max_rows=10,
  ...     get_query_payload=True,
  ... )
  >>> payload["submit"]["json"]["column_constraints"][0]["column_name"]
  'year'

Long-running Query Data requests
--------------------------------

Query Data based modules use synchronous HTTP requests. Methods such as
``query_catalog*`` and ``query_table*`` submit a service-side query and then
immediately fetch result pages; astroquery does not run a separate background
polling loop for long server-side jobs.

For interactive work, keep catalog searches bounded with spatial constraints,
column constraints, explicit table selection, ``showcol``, and a small
``max_rows``. The default row limit comes from the module configuration
``conf.row_limit``; passing ``max_rows=-1`` requests all pages and can be slow
for large result sets.

For broad or reusable queries, submit the query first and keep the returned
``sqlid``:

.. doctest::

  >>> from astroquery.nadc.scuss import Scuss
  >>> job = Scuss.submit_query({"output.fmt": "html"}, catalog="scuss")  # doctest: +SKIP
  >>> sqlid = job["sqlid"]  # doctest: +SKIP
  >>> table = Scuss.get_results(sqlid, fmt="json", rows=100)  # doctest: +SKIP

The ``sqlid`` can also be passed to ``get_count`` and the download helpers when
the target catalog supports those operations. Counts and downloads still depend
on the size of the query represented by the ``sqlid``. Increasing
``conf.timeout`` can help when the service completes within the new per-request
timeout, but it does not guarantee that an unbounded or very broad query will
eventually return. Prefer constrained SQLIDs for smoke tests and examples.

For LAMOST advanced queries, use its direct query methods:

.. doctest::

  >>> from astroquery.nadc.lamost import Lamost
  >>> sql_payload = Lamost.query_sql(
  ...     "SELECT obsid, ra, dec FROM combined LIMIT 5",
  ...     get_query_payload=True,
  ... )
  >>> sql_payload["output.fmt"]
  'json'

Use direct query methods when a high-level method does not expose the needed
behavior, or when querying LAMOST-specific features.
