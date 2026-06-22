NADC CSTAR Queries
======================

``astroquery.nadc.cstar`` provides a thin, Astroquery-style client for the
CSTAR catalog in NADC.

Configuration
-------------

The service endpoint and authentication token are configurable:

.. doctest::

  >>> from astroquery.nadc import conf as nadc_conf
  >>> from astroquery.nadc.cstar import conf
  >>> conf.server  # doctest: +ELLIPSIS
  'http://.../'
  >>> # Optional shared NADC catalog-query token:
  >>> nadc_conf.token = ''  # set a real token in your astroquery.cfg
  >>> # Optional module-local override:
  >>> conf.token = ''
  >>> conf.auth_method = 'query'  # or 'bearer'

You can also provide the token through shared environment variables such as
``ASTROQUERY_NADC_TOKEN`` or module-specific variables such as
``ASTROQUERY_CSTAR_TOKEN``. The legacy ``ASTROQUERY_CHINAVO_TOKEN`` name
remains accepted for compatibility.

Catalog discovery is also configurable. ``conf.supported_catalogs`` controls
which catalogs are surfaced by
``Cstar.list_catalogs``. By default this method returns
only catalogs declared queryable by the service; pass ``queryable_only=False``
to include non-queryable module-supported catalogs for diagnostics. Use
``Cstar.get_catalog_metadata`` to inspect metadata and
the normalized ``capabilities_summary`` for a single catalog.

Basic usage
-----------

Use ``Cstar`` (a singleton instance) for quick queries.
The underlying service uses a two-step pattern (submit query -> fetch results);
the high-level methods hide this detail.

.. doctest::

  >>> import astropy.units as u
  >>> from astropy.coordinates import SkyCoord
  >>> from astroquery.nadc.cstar import Cstar
  >>> c = SkyCoord(ra=1*u.deg, dec=2*u.deg, frame="icrs")
  >>> # Build the request payload without hitting the network:
  >>> payload = Cstar.query_region(c, 5*u.arcsec, get_query_payload=True)
  >>> payload["params"]["output.fmt"]
  'votable'
  >>> payload["params"]["RA"], payload["params"]["DEC"]
  (1.0, 2.0)

Source queries
--------------

Use ``Cstar.query_sources`` for common source photometry
queries with common magnitude and uncertainty filters.  This method keeps users
away from the low-level ``column_constraints`` payload for the stable CSTAR
source-table query.

.. doctest::

  >>> payload = Cstar.query_sources(
  ...     c,
  ...     5*u.arcsec,
  ...     mag_range=(10, 13.5),
  ...     magerr_max=0.05,
  ...     columns=["id", "ra", "dec", "mag", "magerr"],
  ...     get_query_payload=True,
  ... )
  >>> payload["submit"]["json"]["column_constraints"][0]["column_name"]
  'mag'

Catalog metadata and downloads
------------------------------

Use ``Cstar.get_catalog_metadata`` to inspect catalog
capabilities such as downloadable file products:

.. doctest::

  >>> payload = Cstar.get_catalog_metadata(get_query_payload=True)
  >>> payload["url"].endswith("/query/openapi/catalogs/cstar")
  True

CSTAR file products can be downloaded individually by target ID and category,
or batched from a list of IDs or a query result table.  When
``get_query_payload=True`` is used, astroquery only builds the request payload;
metadata-based category validation is performed for real download requests.

.. doctest::

  >>> payload = Cstar.download_file(
  ...     "00001",
  ...     category="fits",
  ...     file_params={"category": "fits"},
  ...     get_query_payload=True,
  ... )
  >>> payload["url"].endswith("/query/openapi/catalogs/cstar/file")
  True
  >>> payload["params"]["category"]
  'fits'
  >>> batch_payload = Cstar.batch_download(
  ...     fmt="targz",
  ...     id_list=["00001", "00002"],
  ...     categories=["fits", "diurnal-fits"],
  ...     get_query_payload=True,
  ... )
  >>> batch_payload["json"]["categories"]
  ['fits', 'diurnal-fits']

Advanced Queries
----------------

For custom catalog searches,
``Cstar.query_catalog`` supports paging, sorting, and
column constraints. When ``get_query_payload=True`` is used, the returned
payload shows the submit request and the result retrieval request.

Use the explicit helpers when you want astroquery to build the request body for
the three supported spatial modes:

- ``Cstar.query_catalog_cone``
- ``Cstar.query_catalog_rectangle``
- ``Cstar.query_catalog_proximity``

.. doctest::

  >>> payload = Cstar.query_catalog_cone(c, 5*u.arcsec, get_query_payload=True)
  >>> payload["submit"]["method"]
  'POST'
  >>> payload["submit"]["json"]["pos_group"]
  'ra,dec'
  >>> rect_payload = Cstar.query_catalog_rectangle(0, 1, -1, 1, get_query_payload=True)
  >>> rect_payload["submit"]["json"]["pos"]["type"]
  'rect'
  >>> prox_payload = Cstar.query_catalog_proximity([(1, 2), (3, 4, 5)], get_query_payload=True)
  >>> prox_payload["submit"]["json"]["pos"]["type"]
  'proximity'
  >>> table = Cstar.query_catalog_cone(c, 5*u.arcsec, max_rows=10)  # doctest: +SKIP

Use ``Cstar.query_table`` when a query needs custom column selection, filters,
sorting, or limits beyond ``Cstar.query_sources``. Bind the table explicitly
when you want payload construction to stay fully offline:

.. doctest::

  >>> from astroquery.nadc import ColumnConstraint
  >>> table_payload = Cstar.query_table(
  ...     catalog="cstar",
  ...     table="catalog",
  ...     showcol=["ra", "dec"],
  ...     column_constraints=[ColumnConstraint.greaterequal("ra", 0)],
  ...     max_rows=3,
  ...     get_query_payload=True,
  ... )
  >>> table_payload["submit"]["json"]["column_constraints"][0]["column_name"]
  'ra'

Structured spatial queries default to ``conf.pos_group == "ra,dec"`` for the
``cstar`` catalog. Override ``pos_group=...`` if your deployment exposes a
different coordinate pair such as ``"ra_obs,dec_obs"``.

Use ``get_query_payload=True`` on ``Cstar.query_catalog``
or the explicit spatial helpers when you want to inspect the submit/results
requests without executing them.

Multiple catalogs
-----------------

The same service can expose multiple catalogs. To reuse the same implementation
for a different catalog, create a custom instance:

.. doctest::

  >>> from astroquery.nadc.cstar import CstarClass
  >>> other_catalog = CstarClass(catalog="some-other-catalog")  # doctest: +SKIP

The module-level ``Cstar.list_catalogs`` view is scoped
to queryable catalogs from ``conf.supported_catalogs``.

Choosing a query method
-----------------------

The CSTAR catalog provides source-level positions and photometric summary
columns such as ``mag`` and ``magerr``. Prefer
``Cstar.query_sources`` for that common task, then use
``Cstar.query_catalog``,
``Cstar.query_table``, or the explicit spatial helpers
when a query needs custom constraints beyond ``query_sources``.
See :doc:`query_guide` for a summary of NADC query methods.

Reference/API
=============

.. automodapi:: astroquery.nadc.cstar
    :no-inheritance-diagram:
    :inherited-members:
