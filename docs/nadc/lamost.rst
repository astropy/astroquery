.. _astroquery.nadc.lamost:

*****************************************
LAMOST Queries (`astroquery.nadc.lamost`)
*****************************************

``astroquery.nadc.lamost`` provides access to the LAMOST archive for catalog
queries, metadata lookups, and LRS/MRS spectrum downloads and reading.

Examples use the public DR10/v2.0 service unless another release is specified.
Executing queries and downloading data requires internet access; payload-only
examples do not execute the data query.

Examples with ``overwrite=True`` replace existing output files.

Configuration
=============

Set configuration options before creating a
`~astroquery.nadc.lamost.LamostClass` instance. For example, to set the timeout
in seconds:

.. doctest::

  >>> from astroquery.nadc.lamost import LamostClass, conf
  >>> with conf.set_temp('timeout', 120):
  ...     lamost = LamostClass(token='', data_release='dr10', sub_version='v2.0')
  >>> lamost.TIMEOUT
  120

For authenticated access, set ``ASTROQUERY_NADC_LAMOST_TOKEN`` or configure
``conf.token`` before creating the client:

.. doctest::

  >>> conf.token = 'your-token'  # doctest: +SKIP
  >>> authenticated = LamostClass()  # doctest: +SKIP
  >>> configured = LamostClass(pylamost_config='~/pylamost.ini')  # doctest: +SKIP

Pass ``token=''`` to force anonymous access. The optional ``pylamost_config``
path expands ``~`` and is read only when explicitly supplied. See
`~astroquery.nadc.lamost.LamostClass` for token precedence and legacy
environment-variable support.

Basic Usage
===========

Use ``query_region`` to find observations around a position:

.. doctest::

  >>> import astropy.units as u
  >>> from astropy.coordinates import SkyCoord
  >>> coord = SkyCoord(10.0004738, 40.9952444, unit='deg', frame='icrs')

.. doctest-remote-data::

  >>> matches = lamost.query_region(coord, radius=0.2*u.deg)
  >>> print(matches['obsid', 'ra', 'dec'][:5])  # doctest: +IGNORE_OUTPUT

Catalog query methods return `~astropy.table.Table` objects. Coordinates are
transformed to ICRS. Radii accept angular quantities such as ``5*u.arcsec``
and angle strings such as ``'5 arcsec'``. Bare numbers mean degrees for
``query_region`` and ``query_repeat_observations``; they mean
arcseconds for the structured ``query_spectra`` and
``query_stellar_parameters`` methods. Use explicit units to avoid ambiguity.
Invalid or non-angular radii raise ``InvalidQueryError``.

.. note::

   ``query_region`` requests CSV by default, but some LAMOST endpoints return
   VOTable regardless of the requested format. Some of these responses declare
   string fields shorter than their values. The client widens affected
   fixed-length string fields in TABLEDATA before parsing, preserving complete identifiers.
   This workaround is needed until the service supplies correct field lengths;
   unsupported cases that would truncate strings still raise ``TableParseError``.

SQL-style queries and structured catalog requests are also available:

.. doctest-remote-data::

  >>> sql_results = lamost.query_sql('SELECT obsid, ra, dec FROM combined LIMIT 5')
  >>> print(sql_results)  # doctest: +IGNORE_OUTPUT
  >>> catalog_results = lamost.query_catalog(
  ...     'combined', columns=['obsid', 'ra', 'dec'], max_rows=5)
  >>> print(catalog_results)  # doctest: +IGNORE_OUTPUT

For page sizes and retrieving further results, see :ref:`lamost-pagination`.

Use ``get_query_payload=True`` to inspect request parameters without executing
the data query, with credentials redacted; see
`~astroquery.nadc.lamost.LamostClass.query_catalog` for the return format.

Data Release and Metadata
=========================

Use ``get_dr_versions`` to inspect available data-release and sub-version
combinations. The instance's ``data_release`` and ``sub_version`` select the
archive endpoint used by query and data-product methods.
``get_tables_metadata`` returns the available catalogs and their field
definitions. ``get_metadata(obsid)`` returns information about one observation.

Known Limitations
-----------------

Available endpoints and formats vary by release. Select both ``data_release``
and ``sub_version`` when reproducing an observation.

- Legacy metadata lookups may require authentication even when observation
  metadata and FITS downloads are public, as in DR7/v2.0.
- Where no default catalog mapping is available, use ``get_tables_metadata``
  to select a catalog and pass ``catalog_name`` explicitly.
- ``output_format=None`` selects JSON for modern configurations and CSV for
  legacy ones. Some older services do not support every requested format.
- Related-observation lookup is not supported for DR3.

Results from ``query_catalog`` identify their catalog in
``table.meta['catalog']``. Use ``cache=False`` to refresh cached metadata and
query responses.

.. doctest-remote-data::

  >>> versions = lamost.get_dr_versions()
  >>> sorted({version['dr_version'] for version in versions})  # doctest: +IGNORE_OUTPUT
  >>> metadata = lamost.get_tables_metadata()
  >>> "tables" in metadata
  True

Column Types and Units
======================

``query_region``, ``query_catalog``, and its spectral-query wrappers use catalog metadata to
convert numeric columns and attach recognized units. For example, ``obsid``
is an integer when declared ``long``; character identifiers such as
``gaia_source_id`` remain strings, preserving leading zeros. Missing numeric
values are masked. Available schema information also determines the column
types of empty results.

``get_metadata`` preserves MRS band/exposure rows. The DR10/v2.0 LRS and MRS
schemas provide no units; check the returned units before using the values in
calculations.

``query_sql`` uses column definitions supplied with the response. Without
them, values retain the service's types: ``teff='5770'`` can remain a string.
For SQL aliases or expressions, use ``column_schema`` to specify result types
and units:

.. doctest-remote-data::

  >>> column_schema = {
  ...     'obsid': {'datatype': 'long'},
  ...     'temperature': {'datatype': 'double', 'unit': 'K'},
  ...     'feh': {'datatype': 'double'},
  ...     'gaia_source_id': {'datatype': 'char'},
  ... }
  >>> stars = lamost.query_sql(
  ...     'SELECT obsid, teff AS temperature, feh, gaia_source_id '
  ...     'FROM combined LIMIT 5', column_schema=column_schema)
  >>> hot_stars = stars[stars['temperature'] > 5500]
  >>> stars['temperature'].unit
  Unit("K")

Schema names and units must match the returned columns, including any SQL
unit conversion. Character identifiers retain leading zeros. Missing values
are masked; NaN and infinity are preserved, so check masks and finite values
before analysis. See `~astroquery.nadc.lamost.LamostClass.query_sql` for the
complete ``column_schema`` behavior.

To inspect or save SQL output before table parsing, use ``query_sql_async``:

.. code-block:: python

   from pathlib import Path

   with lamost.query_sql_async(
       'SELECT obsid, ra, dec FROM combined LIMIT 5', output_format='csv') as response:
       Path('lamost-response.csv').write_bytes(response.content)

This follows astroquery's ``_async`` convention: it returns a
``requests.Response`` from a synchronous request, leaving table parsing to
the caller. Raw responses may contain credentials; use the redacted diagnostic
response described below when reporting an error.

Temperature cuts use kelvin, ``logg`` cuts use the base-10 logarithm of surface
gravity in cm/s\ :sup:`2`, and ``feh`` cuts use [Fe/H] in dex. S/N thresholds
are dimensionless. Units are attached only when declared and recognized;
check ``table[column].unit`` before combining results from different sources.

Spectral Sample Queries
=======================

Use ``query_spectra`` to select spectral catalog records with common quality
cuts; use ``get_spectra`` to download their FITS data.

Position and physical constraints are applied together in the database.
``nearest_only=False`` returns the qualifying matches up to ``max_rows``;
``nearest_only=True`` selects one nearest qualifying row and requires
``page=1``. Without ``sort_by``, position results are ordered by angular
distance, with stable secondary ordering for ties. MRS exposures sharing an
``obsid`` remain separate rows.

.. code-block:: python

   matches = lamost.query_stellar_parameters(
       coord, '0.2 deg', teff_range=(4500, 6500),
       logg_range=(3.5, 5), feh_range=(-1, 0.5), snr_min=30,
       max_rows=1000)
   nearest = lamost.query_stellar_parameters(
       coord, '0.2 deg', teff_range=(4500, 6500),
       logg_range=(3.5, 5), feh_range=(-1, 0.5), snr_min=30,
       nearest_only=True)

For direct ``query_catalog`` batch positions, use a ``proximity`` constraint:

.. code-block:: python

   matches = lamost.query_catalog(
       'combined', columns=['obsid', 'ra', 'dec'], max_rows=1000,
       position_constraints={'proximity': {
           'radecTextarea': '10.0004738,40.9952444,720\n10.008848,40.969976,5',
           'proximity_nearestonly': False}})

Radii in that text are arcseconds. ``inputobjs_input_line`` preserves the
original one-based text line number (including skipped comments/header lines),
so repeated positions and overlapping matches remain distinguishable.
``inputobjs_dist_arcsec`` gives the angular separation in arcseconds.
For batch nearest matching, one qualifying row is selected per input;
``max_rows`` then limits the complete output page, not each input separately.

On SQL-backed paths, ``contains`` uses case-insensitive ``ILIKE`` patterns:
``%`` and ``_`` act as wildcards. Equivalence with the native structured
endpoint's matching rules has not been verified.

Use ``query_stellar_parameters`` when the
desired output is focused on stellar atmospheric parameters.  The default
columns are ``obsid``, ``ra``, ``dec``, ``teff``, ``logg``, ``feh``, and the
selected SNR column for LRS. The default LRS S/N field is ``snrg``; callers can
select ``snru``, ``snrr``, ``snri``, or ``snrz`` explicitly with
``snr_column``. MRS uses ``snr``, ``teff_lasp``, ``logg_lasp``, and
``feh_lasp``. Early MRS configurations use the verified ``teff``,
``logg``, and ``feh`` names instead; the public range parameters are unchanged.

.. doctest::

  >>> stellar_payload = lamost.query_stellar_parameters(
  ...     teff_range=(4500, 6500),
  ...     snr_min=30,
  ...     get_query_payload=True,
  ... )
  >>> stellar_payload["json"]["showcol"]
  ['obsid', 'ra', 'dec', 'teff', 'logg', 'feh', 'snrg']

Use ``query_repeat_observations`` to resolve one observation ID, or one
position and radius, to related observations. These two input forms are
mutually exclusive. Its return value is a dictionary containing
``unique_id``, ``related_obsids``, ``related_obsids_low``, and
``related_obsids_medium``; the latter lists distinguish LRS and MRS IDs.
An unmatched target has ``unique_id=None`` and empty lists. The convenience
``related_obsids`` union has no resolution labels; use the separate lists to
choose the download resolution, since the two ID spaces can overlap.
Associations follow the selected release's target identity rules. Use an
``obsid`` from that release when available; a cone query instead returns
nearby observations without asserting that they belong to one target.

.. code-block:: python

   related = lamost.query_repeat_observations(obsid=176604010)
   print(related['related_obsids_low'])

.. doctest::

  >>> repeat_payload = lamost.query_repeat_observations(
  ...     coordinates=coord,
  ...     radius=3*u.arcsec,
  ...     get_query_payload=True,
  ... )
  >>> repeat_payload["ra"], repeat_payload["dec"]
  (10.0004738, 40.9952444)

.. _lamost-pagination:

Catalog Pagination
==================

``query_catalog``, ``query_spectra``, and ``query_stellar_parameters`` return
one page per call, with a default ``max_rows=100`` and one-based ``page``.
This is a client default to limit data transfer, not a general 100-row limit
of the LAMOST service. These methods do not automatically fetch all matches.
To request another page, keep the selection, page size, and sort order fixed:

.. code-block:: python

   matches = lamost.query_spectra(
       coord, '0.2 deg', columns=['obsid', 'ra', 'dec'],
       sort_by='obsid', max_rows=100, page=2)

An empty table marks the end of the results. Pages are separate requests,
not an atomic snapshot of a changing catalog. Errors propagate instead of
being treated as an empty final page.

Data Products
=============

Use ``resolution='low'`` for LRS or ``resolution='medium'`` for MRS.
``get_metadata`` returns an observation table; ``get_spectra`` accepts one
observation ID and returns a list of `~astropy.io.fits.HDUList` objects.
The FITS retains its headers, inverse variance, masks, and spectral extensions.
To obtain its download URL without fetching the file, use ``get_spectrum_list``.
Authenticated URLs contain the token and must not be shared or logged;
``get_query_payload=True`` returns redacted parameters instead.

``get_spectra`` uses Astropy's ``verify='warn'`` by default. This example
uses ``silentfix`` to repair structural FITS header issues in the selected
product. Close the returned HDU lists after use:

.. doctest-remote-data::

  >>> spectra = lamost.get_spectra(176604010, resolution='low', verify='silentfix')
  >>> try:
  ...     obsid = spectra[0][0].header['OBSID']
  ...     spectra[0].writeto('lrs-spectrum.fits', overwrite=True, output_verify='silentfix')
  ... finally:
  ...     for spectrum in spectra:
  ...         spectrum.close()
  >>> obsid
  176604010

Astropy may fix structural header issues when writing; this is not a
byte-for-byte copy of the HTTP response.

One MRS FITS can contain multiple exposures;
do not treat its ``obsid`` as a unique identifier for every exposure row.

``download_catalog`` saves a named catalog product and returns its local
path. For example:

.. code-block:: python

   path = lamost.download_catalog('dr10_v2.0_LRS_plan.fits.gz')

Find product names on the selected release's download page;
``get_tables_metadata`` lists queryable tables instead. DR3 supports the
``'plan'`` product, a gzip CSV. FITS catalog downloads use
``verify='exception'`` by default. Existing files are reused unless
``overwrite=True``; failed downloads leave an existing file intact.

FITS verification checks file structure. Inspect warnings before changing
``verify`` and assess pixel quality separately. Catalog downloads bypass the
response cache and do not resume partial files.

Reading Local Spectra
=====================

``parse_lrs_spectrum`` reads the supported single-HDU image or two-HDU table
layout and returns two arrays: wavelength and flux. It preserves flux values
and precision without smoothing. Unsupported layouts raise ``ValueError``.
LRS parsing does not reject nonfinite or nonpositive wavelength/flux values;
apply scientific quality checks before analysis.

``parse_mrs_spectrum`` returns a dictionary keyed by extension name, each
containing ``wavelength`` and ``flux``. Both readers return wavelengths in
angstroms and retain the archive flux units and normalization. Consult the
FITS headers before interpreting them as calibrated flux. The simplified
arrays do not include inverse variance or quality masks; read those from the
original FITS when selecting pixels or propagating errors.

For existing local LRS and MRS FITS files:

.. code-block:: python

   from astroquery.nadc.lamost import parse_lrs_spectrum, parse_mrs_spectrum

   wavelength, flux = parse_lrs_spectrum('lrs-spectrum.fits')
   exposures = parse_mrs_spectrum('mrs-spectrum.fits')

MRS readers support modern wavelength columns and legacy logarithmic
wavelengths. Coadds and individual exposures retain their extension names.
Wavelengths must be finite and positive; unsupported or ambiguous layouts
raise ``ValueError``. Neither reader applies a velocity correction or
scientific pixel selection.

Tutorials and Analysis Examples
===============================

The `astroquery NADC LAMOST examples repository
<https://github.com/china-vo/astroquery-nadc-lamost-examples>`_ contains complete
workflows for catalog pagination and export, LRS export and smoothing,
MRS batch reading and plotting, and a Ca II H&K activity-index calculation.
The repository includes installation instructions, a standalone activity
script, and offline test data.

Failures and Diagnostics
========================

``InvalidQueryError``
    Check parameter values and catalog column names using
    ``get_tables_metadata``.
``LoginError``
    Check the token and its access permissions, then create a new client.
``requests.HTTPError`` or ``RemoteServiceError``
    Check service availability and the selected release. A missing endpoint
    does not necessarily mean authentication is required.
``TableParseError``
    The response could not be read safely. Inspect ``lamost.response``, which
    retains a diagnostic copy with credentials redacted. Include the selected
    release and query parameters when reporting the problem.

Reference/API
=============

.. automodapi:: astroquery.nadc.lamost
    :no-inheritance-diagram:
