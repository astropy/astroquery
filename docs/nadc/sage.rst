NADC SAGE Queries
=====================

``astroquery.nadc.sage`` provides a thin, Astroquery-style client for the
SAGE-related NADC catalogs that are currently verified in this repository.

Verified service catalogs
-------------------------

The SAGE client currently exposes two verified service catalogs:

- ``SAGES-DR1``
- ``SAGES-StellarParameters``

No third SAGE-prefixed catalog is exposed by the current module configuration.

The public NADC resource page for DOI ``10.12149/100876`` describes the data
release as DR1 plus DR1s data products, but those data products are not exposed
as additional NADC catalog names in the current module configuration.

Configuration
-------------

The service endpoint and authentication token are configurable:

.. doctest::

  >>> from astroquery.nadc import conf as nadc_conf
  >>> from astroquery.nadc.sage import conf
  >>> conf.server  # doctest: +ELLIPSIS
  'https://.../'
  >>> nadc_conf.token = ''
  >>> conf.token = ''
  >>> conf.auth_method = 'query'  # or 'bearer'

You can also provide the token through environment variables. The resolution
order is intentionally unified with the other NADC catalog modules:
module-specific variables such as ``ASTROQUERY_SAGE_TOKEN`` take precedence,
and the shared fallback then checks ``ASTROQUERY_NADC_TOKEN``. The legacy
``ASTROQUERY_CHINAVO_TOKEN`` name remains accepted for compatibility.

Basic usage
-----------

Catalog discovery starts with ``Sage.list_catalogs``, which returns the SAGE
catalog subset configured by ``conf.supported_catalogs`` and declared queryable
by the service. Pass ``queryable_only=False`` to include non-queryable
module-supported catalogs for diagnostics. Use ``Sage.get_catalog_metadata`` to
inspect metadata and the normalized ``capabilities_summary`` for one catalog.

.. doctest::

  >>> from astroquery.nadc.sage import Sage
  >>> payload = Sage.list_catalogs(get_query_payload=True)
  >>> payload["method"]
  'GET'
  >>> "get_catalogs" in payload["url"]
  True

Use ``Sage.list_tables`` and
``Sage.list_columns`` to inspect the tables and columns
for a selected catalog before building custom table queries.

Common Queries
--------------

Use the high-level query methods for the verified SAGE data products:

- ``Sage.query_uv_sources`` for ``SAGES-DR1.dr1_uv``
- ``Sage.query_gri_sources`` for ``SAGES-DR1.dr1s_gri``
- ``Sage.query_stellar_parameters`` for
  ``SAGES-StellarParameters.catalog``

.. doctest::

  >>> import astropy.units as u
  >>> from astropy.coordinates import SkyCoord
  >>> from astroquery.nadc.sage import Sage
  >>> center = SkyCoord(180*u.deg, 30*u.deg)
  >>> payload = Sage.query_uv_sources(
  ...     center,
  ...     2*u.arcsec,
  ...     mag_u_range=(14, 21),
  ...     err_u_max=0.1,
  ...     flag_u=0,
  ...     columns=["sage_id", "ra", "dec", "mag_u", "err_u"],
  ...     get_query_payload=True,
  ... )
  >>> payload["submit"]["json"]["column_constraints"][0]["column_name"]
  'mag_u'

.. doctest::

  >>> stellar_payload = Sage.query_stellar_parameters(
  ...     teff_range=(4500, 6500),
  ...     feh_range=(-1.0, 0.5),
  ...     err_teff_max=150,
  ...     ruwe_max=1.4,
  ...     columns=["sourceid", "teff", "feh", "ruwe"],
  ...     get_query_payload=True,
  ... )
  >>> stellar_payload["submit"]["url"].endswith(
  ...     "/query/openapi/catalogs/SAGES-StellarParameters/tables/sages_param/query"
  ... )
  True

Advanced Queries
----------------

Use ``Sage.query_table`` when you need custom column selection, constraints,
ordering, or explicit table binding.

.. doctest::

  >>> from astroquery.nadc import ColumnConstraint
  >>> from astroquery.nadc.sage import Sage
  >>> payload = Sage.query_table(
  ...     catalog="SAGES-DR1",
  ...     table="dr1_uv",
  ...     showcol=["ra", "dec"],
  ...     column_constraints=[ColumnConstraint.greaterequal("ra", 120)],
  ...     max_rows=10,
  ...     get_query_payload=True,
  ...     cache=False,
  ... )
  >>> payload["submit"]["method"]
  'POST'
  >>> payload["submit"]["json"]["column_constraints"][0]["column_name"]
  'ra'

Reference/API
=============

.. automodapi:: astroquery.nadc.sage
    :no-inheritance-diagram:
    :inherited-members:
