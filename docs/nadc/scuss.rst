NADC SCUSS Queries
======================

``astroquery.nadc.scuss`` provides a thin client for the SCUSS catalog family
in NADC.

The currently verified service catalogs are:

- ``scuss``
- ``scuss-cat``
- ``scuss-image``
- ``scuss-proper-motion``

Configuration
-------------

The module follows the same authentication and server configuration pattern as
the other NADC catalog modules.

.. doctest::

  >>> from astroquery.nadc import conf as nadc_conf
  >>> from astroquery.nadc.scuss import conf
  >>> conf.supported_catalogs
  'scuss,scuss-cat,scuss-image,scuss-proper-motion'
  >>> nadc_conf.token = ''  # optional shared NADC catalog-query token
  >>> conf.token = ''

Module-specific environment variables such as ``ASTROQUERY_SCUSS_TOKEN`` take
precedence over the shared ``ASTROQUERY_NADC_TOKEN`` fallback. The legacy
``ASTROQUERY_CHINAVO_TOKEN`` name remains accepted for compatibility.

Catalog Discovery
-----------------

``Scuss`` inherits the shared NADC Query Data
discovery methods. Use ``Scuss.list_catalogs`` to view
the SCUSS-specific catalog subset configured by ``conf.supported_catalogs`` and
declared queryable by the service. Pass ``queryable_only=False`` to include
non-queryable module-supported catalogs for diagnostics. Use
``Scuss.get_catalog_metadata`` for metadata, normalized
``capabilities_summary``, and query-status reason for one catalog. Use
``Scuss.list_tables`` and
``Scuss.list_columns`` to inspect the tables and columns
for a selected catalog.

.. doctest::

  >>> from astroquery.nadc.scuss import Scuss
  >>> payload = Scuss.list_tables(catalog="scuss", get_query_payload=True)
  >>> payload["url"].endswith("/query/openapi/catalogs/scuss/tables")
  True

Common Queries
--------------

Use the high-level SCUSS query methods for common use cases. These methods
select the appropriate catalog and table internally, so users do not need to
know whether a product is stored under ``scuss.catalogue``, ``scuss.sdss10``,
``scuss-image.image``, or ``scuss-proper-motion.proper_motion``.
See :doc:`query_guide` for a summary of NADC query methods.

.. doctest::

  >>> import astropy.units as u
  >>> from astropy.coordinates import SkyCoord
  >>> from astroquery.nadc.scuss import Scuss
  >>> center = SkyCoord(180*u.deg, 30*u.deg)
  >>> sources = Scuss.query_sources(  # doctest: +SKIP
  ...     center,
  ...     radius=5*u.arcmin,
  ...     mag_range=(14, 22),
  ...     magerr_max=0.1,
  ...     columns=["id", "ra", "dec", "psfmag", "psferr"],
  ...     max_rows=100,
  ... )

Query image metadata with seeing constraints. The default output format is
``"json"`` for this method because some SCUSS image VOTable responses are not
currently parsed reliably by Astropy.

.. doctest::

  >>> images = Scuss.query_images(  # doctest: +SKIP
  ...     center,
  ...     radius=0.2*u.deg,
  ...     seeing_max=2.0,
  ...     columns=["filename", "cra", "cdec", "seeing"],
  ...     max_rows=20,
  ... )

Query proper-motion measurements without binding the underlying
``proper_motion`` table explicitly.

.. doctest::

  >>> motions = Scuss.query_proper_motions(  # doctest: +SKIP
  ...     center,
  ...     radius=10*u.arcmin,
  ...     pmra_range=(-50, 50),
  ...     pmdec_range=(-50, 50),
  ...     obsused_min=3,
  ...     max_rows=100,
  ... )

Query the SDSS DR10 match table through the same high-level query style.

.. doctest::

  >>> matches = Scuss.query_sdss_matches(  # doctest: +SKIP
  ...     center,
  ...     radius=5*u.arcmin,
  ...     match_error_max=1.0,
  ...     columns=["sdssobjid", "match_err", "psfmag_u", "psfmag_g"],
  ...     max_rows=100,
  ... )

Advanced Queries
----------------

Use the high-level query methods first for common use cases, and use
``Scuss.query_table`` when you need custom column selection, constraints,
ordering, or table binding.

The root ``scuss`` catalog currently exposes two tables, so bind a table name
explicitly:

.. doctest::

  >>> from astroquery.nadc import ColumnConstraint
  >>> from astroquery.nadc.scuss import Scuss
  >>> payload = Scuss.query_table(
  ...     catalog="scuss",
  ...     table="catalogue",
  ...     showcol=["id", "ra", "dec"],
  ...     column_constraints=[ColumnConstraint.greaterequal("ra", 120)],
  ...     max_rows=5,
  ...     get_query_payload=True,
  ... )
  >>> payload["submit"]["url"].endswith(
  ...     "/query/openapi/catalogs/scuss/tables/catalogue/query"
  ... )
  True
  >>> payload["submit"]["json"]["column_constraints"][0]["column_name"]
  'ra'

Single-table catalogs such as ``scuss-image`` and ``scuss-proper-motion`` can
also be queried with ``Scuss.query_table``. Bind the
table explicitly in offline payload examples; a live service can also resolve
single-table catalogs through discovery.

.. doctest::

  >>> image_payload = Scuss.query_table(
  ...     catalog="scuss-image",
  ...     table="image",
  ...     showcol=["id", "filename", "cra"],
  ...     max_rows=5,
  ...     get_query_payload=True,
  ... )
  >>> image_payload["submit"]["url"].endswith(
  ...     "/query/openapi/catalogs/scuss-image/tables/image/query"
  ... )
  True

Catalog metadata and downloads
------------------------------

Use ``Scuss.get_catalog_metadata`` to inspect whether a
SCUSS catalog declares downloadable file products:

.. doctest::

  >>> metadata_payload = Scuss.get_catalog_metadata(
  ...     catalog="scuss-image",
  ...     get_query_payload=True,
  ... )
  >>> metadata_payload["url"].endswith("/query/openapi/catalogs/scuss-image")
  True

For real downloads, astroquery reads the catalog metadata and maps the selected
category to the service-specific query parameters.  For example, ``png`` files
in ``scuss-image`` are requested with the ``path=png`` and ``ext=png`` service
parameters, but users only need to provide the category:

.. doctest::

  >>> payload = Scuss.download_file(
  ...     "1",
  ...     catalog="scuss-image",
  ...     category="png",
  ...     file_params={"path": "png", "ext": "png"},
  ...     get_query_payload=True,
  ... )
  >>> payload["url"].endswith("/query/openapi/catalogs/scuss-image/file")
  True
  >>> payload["params"]["path"], payload["params"]["ext"]
  ('png', 'png')

The ``scuss-cat`` catalog currently exposes no table metadata via the discovery
API. Check ``Scuss.get_catalog_metadata`` before using
low-level query methods against it, because query support is declared by the
service metadata.

Reference/API
=============

.. automodapi:: astroquery.nadc.scuss
    :no-inheritance-diagram:
    :inherited-members:
