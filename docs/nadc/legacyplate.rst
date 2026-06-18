NADC Legacy Plate Queries
=============================

``astroquery.nadc.legacyplate`` provides a thin client for legacy plate
catalogs exposed through NADC.
It shares the same protocol as ``astroquery.nadc.cstar``, but defaults to the
``legacyplate`` catalog family.

Configuration
-------------

The service endpoint, token, default catalog, and surfaced catalog list are
configurable:

.. doctest::

  >>> from astroquery.nadc import conf as nadc_conf
  >>> from astroquery.nadc.legacyplate import conf
  >>> conf.catalog
  'legacyplate'
  >>> conf.supported_catalogs
  'legacyplate,legacyplateedr,legacyplate-cat,legacyplate-image'
  >>> nadc_conf.token = ''  # shared NADC catalog-query token
  >>> conf.token = ''  # optional module-local override

You can also provide the token through shared environment variables such as
``ASTROQUERY_NADC_TOKEN`` or module-specific variables such as
``ASTROQUERY_LEGACYPLATE_TOKEN``. The legacy ``ASTROQUERY_CHINAVO_TOKEN`` name
remains accepted for compatibility.

Catalog discovery
-----------------

``Legacyplate`` inherits the shared NADC Query
Data discovery methods.
``Legacyplate.list_catalogs`` returns the legacy
plate catalog subset configured by ``conf.supported_catalogs`` and declared
queryable by the service. Pass ``queryable_only=False`` to include
non-queryable module-supported catalogs for diagnostics. Use
``Legacyplate.get_catalog_metadata`` to inspect
metadata, normalized ``capabilities_summary``, and query-status reason for one
catalog. Use
``Legacyplate.list_tables`` and
``Legacyplate.list_columns`` to inspect table and
column metadata for a selected catalog.

.. doctest::

  >>> from astroquery.nadc.legacyplate import Legacyplate
  >>> payload = Legacyplate.list_catalogs(get_query_payload=True)
  >>> payload["url"].endswith("/query/openapi/get_catalogs")
  True
  >>> payload = Legacyplate.get_catalog_metadata(
  ...     catalog="legacyplate-image",
  ...     get_query_payload=True,
  ... )
  >>> payload["url"].endswith("/query/openapi/catalogs/legacyplate-image")
  True

Archive queries
---------------

Use ``Legacyplate.query_plates`` for metadata discovery by sky position,
observation year,
observatory, telescope, and target name.  Use
``Legacyplate.query_plate_images`` for the same
archive filters against the image-metadata catalog.

.. doctest::

  >>> import astropy.units as u
  >>> from astropy.coordinates import SkyCoord
  >>> coord = SkyCoord(ra=1*u.deg, dec=2*u.deg, frame="icrs")
  >>> payload = Legacyplate.query_plates(
  ...     coord,
  ...     5*u.arcsec,
  ...     year_range=(1950, 1970),
  ...     observatory="Shao",
  ...     object_name="M31",
  ...     columns=["id", "year", "observat", "object"],
  ...     get_query_payload=True,
  ... )
  >>> payload["submit"]["json"]["column_constraints"][0]["column_name"]
  'year'

.. doctest::

  >>> image_payload = Legacyplate.query_plate_images(
  ...     observatory="Naoc",
  ...     columns=["filename", "year", "observat"],
  ...     get_query_payload=True,
  ... )
  >>> image_payload["submit"]["url"].endswith(
  ...     "/query/openapi/catalogs/legacyplate-image/query"
  ... )
  True

Advanced Queries
----------------

Legacy plate queries reuse the same structured-query helpers as CSTAR. Use
``query_catalog`` and ``query_table`` when a query needs custom fields,
sorting, spatial modes, or constraints. The
``column_constraints`` parameter follows the ``ColumnConstraint`` schema, where
each constraint dict requires ``column_name`` and ``operation``, with
``constraint`` for single-value operations.

Available operations: ``equal``, ``notequal``, ``less``, ``lessequal``,
``greater``, ``greaterequal``, ``between`` (uses ``min``/``max``),
``contains``, ``in`` (uses ``textarea``).

Filtering by observatory and year
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The legacy plate catalogs expose business-specific fields that can be filtered
through ``column_constraints``.  Commonly used columns include:

- ``year`` — observation year (integer)
- ``observat`` — observatory code: ``Naoc`` (国家天文台), ``Pmo`` (紫金山天文台),
  ``Qdo`` (青岛观象台), ``Shao`` (上海天文台), ``Ynao`` (云南天文台)
- ``telescop`` — telescope aperture (cm)
- ``object`` — target name
- ``date_o`` — observation date (e.g. ``1981-11-07``)

Use ``Legacyplate.list_columns`` to discover all
available columns for a catalog.

.. doctest::

  >>> import astropy.units as u
  >>> from astropy.coordinates import SkyCoord
  >>> coord = SkyCoord(ra=1*u.deg, dec=2*u.deg, frame="icrs")
  >>> payload = Legacyplate.query_catalog_cone(
  ...     coord,
  ...     5*u.arcsec,
  ...     column_constraints=[
  ...         {"column_name": "year", "operation": "greaterequal",
  ...          "constraint": "1900"},
  ...         {"column_name": "observat", "operation": "equal",
  ...          "constraint": "Naoc"},
  ...     ],
  ...     sort="year",
  ...     order="desc",
  ...     get_query_payload=True,
  ... )
  >>> payload["submit"]["json"]["column_constraints"][0]["column_name"]
  'year'
  >>> payload["submit"]["json"]["column_constraints"][0]["operation"]
  'greaterequal'
  >>> payload["results"]["params"]["sort"]
  'year'

Filtering without a position constraint (catalog-wide search):

.. doctest::

  >>> payload = Legacyplate.query_catalog(
  ...     catalog="legacyplateedr",
  ...     column_constraints=[
  ...         {"column_name": "year", "operation": "between",
  ...          "min": 1950, "max": 1970},
  ...         {"column_name": "observat", "operation": "equal",
  ...          "constraint": "Shao"},
  ...     ],
  ...     sort="year",
  ...     order="asc",
  ...     max_rows=10,
  ...     get_query_payload=True,
  ... )
  >>> payload["submit"]["json"]["column_constraints"][1]["constraint"]
  'Shao'

As with CSTAR, ``Legacyplate.query_region``
remains a ConeSearch-style convenience method and does not expose generic field
filters or sorting.

Table-level spatial queries
---------------------------

The catalog query service also provides table-level cone search and
coordinate-group discovery endpoints. These are useful when a catalog may
contain multiple tables, or when you want to discover valid coordinate-group
IDs instead of manually typing strings such as ``"ra,dec"``.

Use ``Legacyplate.list_coordinate_groups`` to
inspect available groups for a table:

.. doctest::

  >>> payload = Legacyplate.list_coordinate_groups(
  ...     table="images",
  ...     catalog="legacyplateedr",
  ...     get_query_payload=True,
  ... )
  >>> payload["url"].endswith(
  ...     "/query/openapi/catalogs/legacyplateedr/tables/images/coordinate_groups"
  ... )
  True

Then pass one of the returned ``groups[].id`` values to
``Legacyplate.query_table_cone``:

.. doctest::

  >>> payload = Legacyplate.query_table_cone(
  ...     coord,
  ...     5*u.arcsec,
  ...     table="images",
  ...     catalog="legacyplateedr",
  ...     coordinate_group="ra,dec",
  ...     get_query_payload=True,
  ... )
  >>> payload["url"].endswith(
  ...     "/query/openapi/catalogs/legacyplateedr/tables/images/vo/conesearch"
  ... )
  True
  >>> payload["params"]["coordinate_group"]
  'ra,dec'

``query_catalog*`` and ``query_table_cone`` use different parameter names on the
wire:

- ``pos_group`` is part of the structured query request used by
  ``query_catalog``, ``query_catalog_cone``, ``query_catalog_rectangle``, and
  ``query_catalog_proximity``
- ``coordinate_group`` is a query parameter used only by the table-level cone
  search endpoint

SIAP image discovery
--------------------

For image-oriented catalogs such as ``legacyplate-image``, the service also
exposes the IVOA Simple Image Access Protocol (SIAP) endpoint.

.. doctest::

  >>> siap_payload = Legacyplate.query_siap(
  ...     coord,
  ...     0.5,
  ...     catalog="legacyplate-image",
  ...     get_query_payload=True,
  ... )
  >>> siap_payload["url"].endswith("/query/openapi/vo/legacyplate-image/siap")
  True
  >>> siap_payload["params"]["POS"]
  '1.0,2.0'
  >>> siap_payload["params"]["SIZE"]
  0.5

Unlike cone-search helpers where plain floats are interpreted as arcseconds,
``Legacyplate.query_siap`` follows the SIAP
convention and interprets plain floats as **degrees**.  You can also pass an
angular `~astropy.units.Quantity`.

Column discovery and constraints
--------------------------------

Use ``Legacyplate.list_columns`` to discover
column names for ``showcol``, ``sort``, and ``column_constraints``. Use
``ColumnConstraint`` factory methods for structured filters.

.. doctest::

  >>> from astroquery.nadc import ColumnConstraint
  >>> ColumnConstraint.greaterequal("year", 1950).to_dict()
  {'column_name': 'year', 'operation': 'greaterequal', 'constraint': '1950'}

Catalog documents and downloads
-------------------------------

The legacyplate client now exposes catalog documentation pages and file download
endpoints.

List and retrieve documentation pages:

.. doctest::

  >>> payload = Legacyplate.list_docs(catalog="legacyplate", get_query_payload=True)
  >>> payload["url"].endswith("/query/openapi/catalogs/legacyplate/docs")
  True
  >>> payload = Legacyplate.get_doc("intro", catalog="legacyplate", get_query_payload=True)
  >>> payload["url"].endswith("/query/openapi/catalogs/legacyplate/docs/intro")
  True

Inspect catalog metadata before choosing a file product:

.. doctest::

  >>> metadata_payload = Legacyplate.get_catalog_metadata(
  ...     catalog="legacyplate-image",
  ...     get_query_payload=True,
  ... )
  >>> metadata_payload["url"].endswith("/query/openapi/catalogs/legacyplate-image")
  True

Prepare a single-file download request:

.. doctest::

  >>> payload = Legacyplate.download_file(
  ...     "plate-1",
  ...     catalog="legacyplate-image",
  ...     category="fits",
  ...     file_params={"category": "fits"},
  ...     get_query_payload=True,
  ... )
  >>> payload["url"].endswith("/query/openapi/catalogs/legacyplate-image/file")
  True
  >>> payload["params"]["category"]
  'fits'
  >>> payload["stream"]
  True

Prepare a batch download request:

.. doctest::

  >>> payload = Legacyplate.batch_download(
  ...     catalog="legacyplate-image",
  ...     fmt="urllist",
  ...     id_list=["1", "2"],
  ...     categories=["fits"],
  ...     get_query_payload=True,
  ... )
  >>> payload["url"].endswith("/query/openapi/catalogs/legacyplate-image/download")
  True
  >>> payload["json"]["fmt"]
  'urllist'
  >>> payload["json"]["categories"]
  ['fits']

Batch downloads can also be built from a query result table.  Astroquery reads
the file identifier from the catalog metadata ``file_download.id_source`` and
submits it to the same service-side batch download endpoint. For
``legacyplate-image``, query results expose the file identifier as
``image_filename`` even though the download endpoint parameter is named ``id``.
For payload-only examples, pass ``id_column`` explicitly to avoid a metadata
request; real downloads can omit it when the service metadata declares
``id_source``:

.. doctest::

  >>> from astropy.table import Table
  >>> products = Table({"image_filename": ["SH9701CL97006001"]})
  >>> payload = Legacyplate.download_products(
  ...     products,
  ...     catalog="legacyplate-image",
  ...     fmt="urllist",
  ...     categories=["fits"],
  ...     id_column="image_filename",
  ...     get_query_payload=True,
  ... )
  >>> payload["json"]["id_list"]
  ['SH9701CL97006001']

When ``out_path`` is omitted, ``download_file`` and ``batch_download`` save files
under the astroquery cache directory for this module.

Reference/API
=============

.. automodapi:: astroquery.nadc.legacyplate
    :no-inheritance-diagram:
    :inherited-members:
