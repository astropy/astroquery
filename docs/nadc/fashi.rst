NADC FASHI Queries
======================

``astroquery.nadc.fashi`` provides a client for the FAST All Sky HI survey
catalog served by NADC.

FASHI is organized as a parent catalog with one main HI-source table and four
child catalogs for precomputed match/counterpart data products:

.. list-table::
   :header-rows: 1
   :widths: 32 48 20

   * - Catalog / table
     - Contents
     - Spatial columns
   * - ``FASHI`` / ``extragalactic_hi_source_catalog``
     - Extragalactic HI source measurements, including sky position,
       velocity/redshift, line widths, fluxes, SNR, distance, and HI mass.
     - ``ra,dec``
   * - ``alfalfa_crossmatch`` / ``alfalfa_crossmatch``
     - Precomputed FASHI/ALFALFA matches.
     - ``ra_fashi,dec_fashi`` or ``ra_alfalfa,dec_alfalfa``
   * - ``optical_counterparts_sdss_phot`` / ``optical_counterparts_sdss_phot``
     - SDSS photometric optical counterparts with match probability.
     - ``ra_fashi,dec_fashi`` or ``ra_sdss,dec_sdss``
   * - ``optical_counterparts_sdss_spec`` / ``optical_counterparts_sdss_spec``
     - SDSS spectroscopic optical counterparts.
     - ``ra_fashi,dec_fashi`` or ``ra_sdss,dec_sdss``
   * - ``optical_counterparts_sga`` / ``optical_counterparts_sga``
     - SGA optical counterparts.
     - ``ra_fashi,dec_fashi`` or ``ra_sga,dec_sga``

Configuration
-------------

The module follows the same authentication and server configuration pattern as
the other NADC catalog modules.

.. doctest::

  >>> from astroquery.nadc import conf as nadc_conf
  >>> from astroquery.nadc.fashi import conf
  >>> conf.supported_catalogs
  'FASHI,alfalfa_crossmatch,optical_counterparts_sdss_phot,optical_counterparts_sdss_spec,optical_counterparts_sga'
  >>> nadc_conf.token = ''  # optional shared NADC catalog-query token
  >>> conf.token = ''          # optional FASHI-specific override

Module-specific environment variables such as ``ASTROQUERY_FASHI_TOKEN`` take
precedence over the shared ``ASTROQUERY_NADC_TOKEN`` fallback. The legacy
``ASTROQUERY_CHINAVO_TOKEN`` name remains accepted for compatibility.

Catalog discovery
-----------------

``Fashi.list_catalogs`` returns the FASHI catalog subset
configured by ``conf.supported_catalogs`` and declared queryable by the service.
Pass ``queryable_only=False`` to include non-queryable module-supported catalogs
for diagnostics. Use ``Fashi.get_catalog_metadata`` to
inspect metadata and the normalized ``capabilities_summary`` for one catalog.

Common Queries
--------------

Use ``Fashi.query_hi_sources`` for the main FASHI HI
source catalog:

.. doctest::

  >>> import astropy.units as u
  >>> from astropy.coordinates import SkyCoord
  >>> from astroquery.nadc.fashi import Fashi
  >>> center = SkyCoord(125*u.deg, -6*u.deg)
  >>> payload = Fashi.query_hi_sources(
  ...     center,
  ...     5*u.arcmin,
  ...     cz_range=(1000, 8000),
  ...     snr_min=8,
  ...     columns=["id_fashi", "ra", "dec", "cz", "snr"],
  ...     get_query_payload=True,
  ... )
  >>> payload["submit"]["json"]["pos_group"]
  'ra,dec'
  >>> payload["submit"]["json"]["column_constraints"][0]["column_name"]
  'cz'

The match/counterpart helpers query the four precomputed related tables:

.. doctest::

  >>> match_payload = Fashi.query_alfalfa_matches(
  ...     agcnr_alfalfa=5951,
  ...     columns=["id_fashi", "agcnr_alfalfa", "cz_fashi", "cz_alfalfa"],
  ...     get_query_payload=True,
  ... )
  >>> match_payload["submit"]["url"].endswith(
  ...     "/query/openapi/catalogs/alfalfa_crossmatch/tables/alfalfa_crossmatch/query"
  ... )
  True

  >>> phot_payload = Fashi.query_sdss_phot_counterparts(
  ...     probability_min=0.8,
  ...     columns=["id_fashi", "objid_sdss", "probability_sdss"],
  ...     get_query_payload=True,
  ... )
  >>> phot_payload["submit"]["json"]["column_constraints"][0]["column_name"]
  'probability_sdss'

  >>> spec_payload = Fashi.query_sdss_spec_counterparts(
  ...     z_sdss_range=(0.01, 0.05),
  ...     get_query_payload=True,
  ... )
  >>> spec_payload["submit"]["json"]["column_constraints"][0]["column_name"]
  'z_sdss'

  >>> sga_payload = Fashi.query_sga_counterparts(
  ...     name_sga="PGC1035830",
  ...     get_query_payload=True,
  ... )
  >>> sga_payload["submit"]["json"]["column_constraints"][0]["column_name"]
  'name_sga'

Coordinate groups
-----------------

The match/counterpart tables contain both FASHI and external-catalog
coordinates. When using spatial constraints, the high-level methods default to
the FASHI coordinate pair ``"ra_fashi,dec_fashi"``. Pass ``pos_group`` when the
search should use the external-catalog coordinates:

.. doctest::

  >>> external_payload = Fashi.query_alfalfa_matches(
  ...     center,
  ...     5*u.arcmin,
  ...     pos_group="ra_alfalfa,dec_alfalfa",
  ...     get_query_payload=True,
  ... )
  >>> external_payload["submit"]["json"]["pos_group"]
  'ra_alfalfa,dec_alfalfa'

Advanced Queries
----------------

Use ``Fashi.query_table`` when a query needs custom column selection,
constraints, ordering, or explicit catalog/table binding:

.. doctest::

  >>> from astroquery.nadc import ColumnConstraint
  >>> table_payload = Fashi.query_table(
  ...     catalog="FASHI",
  ...     table="extragalactic_hi_source_catalog",
  ...     showcol=["id_fashi", "ra", "dec", "snr"],
  ...     column_constraints=[ColumnConstraint.greaterequal("snr", 10)],
  ...     max_rows=5,
  ...     get_query_payload=True,
  ... )
  >>> table_payload["submit"]["url"].endswith(
  ...     "/query/openapi/catalogs/FASHI/tables/extragalactic_hi_source_catalog/query"
  ... )
  True

Pass one of the child data-product catalog names to query counterpart tables:

.. doctest::

  >>> child_payload = Fashi.query_table(
  ...     catalog="alfalfa_crossmatch",
  ...     table="alfalfa_crossmatch",
  ...     showcol=["id_fashi", "agcnr_alfalfa", "cz_fashi", "cz_alfalfa"],
  ...     column_constraints=[ColumnConstraint.between("cz_fashi", 1000, 9000)],
  ...     max_rows=5,
  ...     get_query_payload=True,
  ... )
  >>> child_payload["submit"]["url"].endswith(
  ...     "/query/openapi/catalogs/alfalfa_crossmatch/tables/alfalfa_crossmatch/query"
  ... )
  True

Use ``Fashi.list_coordinate_groups`` to inspect valid
coordinate groups for any table before building low-level spatial queries.

Reference/API
=============

.. automodapi:: astroquery.nadc.fashi
    :no-inheritance-diagram:
    :inherited-members:
