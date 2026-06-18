NADC LAMOST Queries
=======================

``astroquery.nadc.lamost`` provides access to the LAMOST archive for catalog
queries, metadata lookups, and spectrum-related utilities. The legacy import
path ``astroquery.chinavo.lamost`` is kept as an alias to the same module.

Configuration
-------------

The base URL, default data release, sub-version, and token are configurable:

.. doctest::

  >>> from astroquery.nadc.lamost import conf
  >>> conf.server  # doctest: +ELLIPSIS
  'https://...'
  >>> conf.data_release
  'dr10'
  >>> conf.sub_version
  'v2.0'
  >>> conf.token = ''  # set a real token in astroquery.cfg when needed

``LamostClass`` resolves tokens in this order: an explicit ``token`` argument,
``astroquery.nadc.lamost.conf.token``, environment variables such as
``ASTROQUERY_NADC_LAMOST_TOKEN``. To read an existing pylamost-style config
file explicitly, pass its path to ``pylamost_config``:

.. doctest::

  >>> from astroquery.nadc.lamost import LamostClass
  >>> lamost = LamostClass(pylamost_config="~/pylamost.ini")  # doctest: +SKIP

Basic Usage
-----------

Use ``Lamost`` for quick queries:

.. doctest::

  >>> import astropy.units as u
  >>> from astropy.coordinates import SkyCoord
  >>> from astroquery.nadc.lamost import Lamost
  >>> Lamost.token = None
  >>> coord = SkyCoord(10.0, 40.0, unit='deg', frame='icrs')
  >>> payload = Lamost.query_region(coord, radius=0.2*u.deg, get_query_payload=True)
  >>> payload['ra'], payload['dec'], payload['output.fmt']
  (10.0, 40.0, 'votable')

SQL-style queries and structured catalog requests are also available:

.. doctest::

  >>> sql_payload = Lamost.query_sql('SELECT * FROM combined LIMIT 5', get_query_payload=True)
  >>> sql_payload['output.fmt']
  'json'
  >>> catalog_payload = Lamost.query_catalog(
  ...     'combined',
  ...     columns=['obsid', 'ra', 'dec'],
  ...     max_rows=5,
  ...     get_query_payload=True,
  ... )
  >>> catalog_payload['rows']
  5

For request introspection and debugging, prefer ``get_query_payload=True`` on
these public sync methods instead of relying on raw-response helper APIs.

LAMOST uses its own archive query interface rather than the NADC Query Data
catalog/table endpoints used by CSTAR, FASHI, Legacy Plate, SCUSS, and SAGE.

Data Release and Metadata
-------------------------

Use ``Lamost.get_dr_versions`` to inspect available data-release and
sub-version combinations. The configured ``conf.data_release`` and
``conf.sub_version`` values select the default archive endpoint used by query
and data-product methods. ``Lamost.get_tables_metadata``,
``Lamost.get_tap_url``, and ``Lamost.get_footprint`` expose archive metadata
for schema discovery, TAP clients, and footprint inspection.

.. doctest::

  >>> versions = Lamost.get_dr_versions()  # doctest: +SKIP
  >>> versions[0]["dr_version"]  # doctest: +SKIP
  'dr10'
  >>> metadata = Lamost.get_tables_metadata()  # doctest: +SKIP
  >>> "tables" in metadata  # doctest: +SKIP
  True

Spectral Sample Queries
-----------------------

Use ``Lamost.query_spectra`` when the task is to build
a LAMOST spectral sample with common quality cuts.  It translates query
parameters such as SNR and stellar-parameter ranges into the structured
``query_catalog`` payload.

.. doctest::

  >>> spectral_payload = Lamost.query_spectra(
  ...     coord,
  ...     5*u.arcsec,
  ...     snr_min=20,
  ...     teff_range=(4500, 6500),
  ...     logg_range=(3.5, 5.0),
  ...     feh_range=(-1.0, 0.5),
  ...     columns=["obsid", "ra", "dec", "snr", "teff", "logg", "feh"],
  ...     get_query_payload=True,
  ... )
  >>> spectral_payload["column_constraints"][0]["column_name"]
  'snr'

Use ``Lamost.query_stellar_parameters`` when the
desired output is focused on stellar atmospheric parameters.  The default
columns are ``obsid``, ``ra``, ``dec``, ``teff``, ``logg``, ``feh``, and the
selected SNR column.

.. doctest::

  >>> stellar_payload = Lamost.query_stellar_parameters(
  ...     teff_range=(4500, 6500),
  ...     snr_min=30,
  ...     get_query_payload=True,
  ... )
  >>> stellar_payload["showcol"]
  ['obsid', 'ra', 'dec', 'teff', 'logg', 'feh', 'snr']

Use ``Lamost.query_repeat_observations`` for the
common repeated-observation lookup task:

.. doctest::

  >>> repeat_payload = Lamost.query_repeat_observations(
  ...     coordinates=coord,
  ...     radius=3*u.arcsec,
  ...     get_query_payload=True,
  ... )
  >>> repeat_payload["ra"], repeat_payload["dec"]
  (10.0, 40.0)

Paged Query Results
-------------------

LAMOST SQL and structured catalog queries can return a server-side ``sqlid``.
Use ``get_query_result_count`` and ``get_query_result_by_page`` for explicit
pagination, or ``get_query_result`` to fetch all pages with a fixed
``page_size``. ``download_query_result`` writes the complete result set to a
local file.

.. doctest::

  >>> count = Lamost.get_query_result_count(12345)  # doctest: +SKIP
  >>> page = Lamost.get_query_result_by_page(  # doctest: +SKIP
  ...     12345, count, rows=1000, page=1, output_format="json"
  ... )
  >>> results = Lamost.get_query_result(  # doctest: +SKIP
  ...     12345, output_format="json", page_size=1000
  ... )
  >>> path = Lamost.download_query_result(  # doctest: +SKIP
  ...     12345, "lamost-results.csv", output_format="csv"
  ... )

Data Products
-------------

The module also provides helpers for LAMOST spectra and images:

- ``Lamost.get_metadata``
- ``Lamost.get_spectrum_list``
- ``Lamost.get_image_list``
- ``Lamost.get_fits_csv``
- ``parse_lrs_spectrum``
- ``parse_mrs_spectrum``

Example:

.. doctest::

  >>> urls = Lamost.get_spectrum_list('686112127', resolution='low')  # doctest: +SKIP
  >>> len(urls) > 0  # doctest: +SKIP
  True

Reference/API
=============

.. automodapi:: astroquery.nadc.lamost
    :no-inheritance-diagram:
