.. _astroquery.nadc.lamost:

LAMOST Queries (``astroquery.nadc.lamost``)
===========================================

``astroquery.nadc.lamost`` provides access to the LAMOST archive for catalog
queries, metadata lookups, and LRS/MRS spectrum downloads and reading.

The examples below run in order in one Python session. They use the public
DR10/v2.0 service unless another release is selected explicitly. Executing
queries and downloading data requires internet access; payload-only examples
do not execute the data query. Local processing also requires NumPy and
Astropy; the plotting example requires Matplotlib.

Run file-writing examples in a working directory reserved for this tutorial.
Examples with ``overwrite=True`` replace their named output files on reruns.

Configuration
-------------

The base URL, timeout in seconds, default data release, sub-version, and token
are read when a `~astroquery.nadc.lamost.LamostClass` instance is created.
The imported ``Lamost`` object is an instance created at import time. Changing
``conf`` does not update existing instances; create a new instance after
changing configuration:

.. doctest::

  >>> from astroquery.nadc.lamost import LamostClass, conf
  >>> with conf.set_temp('timeout', 120):
  ...     lamost = LamostClass(token='', data_release='dr10', sub_version='v2.0')
  >>> lamost.TIMEOUT
  120

``LamostClass`` resolves tokens in this order: an explicit ``token`` argument,
``conf.token``, environment variables such as
``ASTROQUERY_NADC_LAMOST_TOKEN``, and an explicitly requested pylamost-style
configuration file. Pass ``token=''`` to force anonymous access, including
when a token is configured elsewhere. An empty ``conf.token`` permits the
environment/config-file fallback; it does not force anonymous access.
``ASTROQUERY_NADC_LAMOST_TOKEN`` is the recommended environment variable.
Legacy aliases remain supported; ``ASTROQUERY_LAMOST_TOKEN`` is checked first
if both are set, so configure only one of these variables.

Configure a token using ``astroquery.cfg``, an environment variable, or
``conf`` before constructing the client. For example:

.. doctest::

  >>> conf.token = 'your-token'  # doctest: +SKIP
  >>> authenticated = LamostClass()  # doctest: +SKIP
  >>> configured = LamostClass(pylamost_config='~/pylamost.ini')  # doctest: +SKIP

The last example reads ``token=your-token`` from the named file only if no
higher-priority source supplied a token. The client does not search for this
file automatically. Authenticated requests disable response caching.
``conf.server`` must include the OpenAPI base path, for example
``https://www.lamost.org/openapi``. The timeout applies to queries and data
downloads.

Basic Usage
-----------

``query_region`` requests CSV by default. Some archive VOTable
responses declare string columns too short for their data; the client raises
`~astroquery.exceptions.TableParseError` instead of returning truncated
identifiers when VOTable is explicitly requested.

.. doctest::

  >>> import astropy.units as u
  >>> from astropy.coordinates import SkyCoord
  >>> coord = SkyCoord(10.0004738, 40.9952444, unit='deg', frame='icrs')
  >>> payload = lamost.query_region(
  ...     coord, radius=0.2*u.deg, output_format='csv', get_query_payload=True)
  >>> payload['ra'], payload['dec'], payload['output.fmt']
  (10.0004738, 40.9952444, 'csv')

.. doctest-remote-data::

  >>> matches = lamost.query_region(
  ...     coord, radius=0.2*u.deg, output_format='csv')
  >>> assert {'obsid', 'ra', 'dec'} <= set(matches.colnames)
  >>> assert matches['obsid'].dtype.kind in 'iu'
  >>> assert matches['ra'].dtype.kind == 'f'

Catalog query methods return `~astropy.table.Table` objects. Coordinates are
transformed to ICRS. Radii accept angular quantities such as ``5*u.arcsec``
and angle strings such as ``'5 arcsec'``. Bare numbers mean degrees for
``query_region`` and ``query_repeat_observations``; they mean
arcseconds for the structured ``query_spectra`` and
``query_stellar_parameters`` methods. Use explicit units to avoid ambiguity.
Invalid or non-angular radii raise `~astroquery.exceptions.InvalidQueryError`.

CSV avoids the known VOTable format problem on endpoints that honor the
format request. It does not establish that the service returned every match
for any release or search size. A single query
does not automatically retrieve additional pages.

SQL-style queries and structured catalog requests are also available:

.. doctest::

  >>> sql_payload = lamost.query_sql('SELECT * FROM combined LIMIT 5', get_query_payload=True)
  >>> sql_payload['output.fmt']
  'json'
  >>> catalog_payload = lamost.query_catalog(
  ...     'combined',
  ...     columns=['obsid', 'ra', 'dec'],
  ...     max_rows=5,
  ...     get_query_payload=True,
  ... )
  >>> catalog_payload['rows']
  5

``get_query_payload=True`` returns a request mapping with token values
redacted, without submitting the data query. SQL-backed structured queries
fetch field metadata to validate and compile the request first. The returned
mapping contains the actual SQL parameters, or ``json`` and ``params`` entries
for a structured POST. Pass explicit
coordinates, as above, to avoid online name resolution of an object name.

For ``query_catalog`` and its wrappers, ``max_rows`` limits a single page
(default: 100), and ``page`` selects the one-based page number. These methods
do not aggregate pages.

Data Release and Metadata
-------------------------

Use ``get_dr_versions`` to inspect available data-release and sub-version
combinations. The instance's ``data_release`` and ``sub_version`` select the
archive endpoint used by query and data-product methods.
``get_tables_metadata`` returns the available catalogs and their field
definitions. ``get_metadata(obsid)`` returns information about one observation.

Release and Format Boundaries
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The reference configuration is the public DR10/v2.0 service. A release listed
by ``get_dr_versions`` does not establish that every endpoint or output format
works for that release. Select both version components explicitly when
reproducing an observation; do not replace a historical release with a newer
one merely because its endpoint responds.

Legacy releases without ``/tables`` use SQL to read the visible database
relations and their column types. Ordinary observation queries and stellar
queries use their respective catalogs; a stellar-only subset is not used for
an ordinary field search. Units unavailable in old metadata remain unset.
SQL and structured queries choose JSON for modern configurations and CSV for legacy
configurations by default (``output_format=None``). An explicit format is
sent unchanged; some old SQL services return HTML for JSON requests.
For configurations without a verified default catalog mapping, inspect
``get_tables_metadata`` and use an explicit ``catalog_name`` or ``query_catalog``;
the client does not guess a population or select a different release.

DR3 uses verified native routes for SQL, cone search, spectrum metadata,
and FITS. DR3 and DR8 cone services can return VOTable even when CSV is
requested, with names such as ``catalogue_obsid`` or ``med_catalogue_obsid``.
The client retains these names and matches the known prefixes to catalog types.
A working native route for DR3 related-observation lookup is not established.

DR7--DR11 MRS v0 queries failed with the tested account because the backing
service could not read the MRS tables. The client does not turn these failures
into empty tables or switch releases. A listed release or visible schema does
not establish permission to read its data.

Format support in the parser is distinct from service availability. Supported
table inputs are JSON, CSV, tab-separated TXT, and valid VOTable. Historical
pipe-delimited text labelled as CSV is recognized from unquoted delimiters in
its header. Quoted commas, pipes, whitespace, and embedded newlines remain
field content, including blank lines and the original CR/LF line endings.
Mixed unquoted header delimiters, missing fields, duplicate or empty column
names, and broken quoting raise `~astroquery.exceptions.TableParseError`.
When a column name itself contains a delimiter, the service must quote it.
JSON record envelopes with ``rows`` and ``total`` preserve each record and
store ``total`` in table metadata. Unrecognized JSON objects raise
``TableParseError`` rather than becoming a single data row.

Executed ``query_catalog`` requests validate output, constraint, position, and
sort columns against ``get_tables_metadata`` before submitting the query.
Use ``cache=False`` to refresh cached metadata and query responses. The
returned table must also contain every requested output column.
Structured results record their source as ``table.meta['catalog']``. Catalog
names are specific to the LAMOST release; discover them from this metadata.

.. doctest::

  >>> versions = lamost.get_dr_versions()  # doctest: +SKIP
  >>> sorted({version['dr_version'] for version in versions})  # doctest: +SKIP
  >>> metadata = lamost.get_tables_metadata()  # doctest: +SKIP
  >>> "tables" in metadata  # doctest: +SKIP
  True

Column Types and Units
----------------------

``query_region``, ``query_catalog``, and its spectral-query wrappers use catalog metadata to
convert numeric columns and attach recognized units. For example, ``obsid``
is an integer when declared ``long``; character identifiers such as
``gaia_source_id`` remain strings, preserving leading zeros. Missing numeric
values are masked. Available schema information also determines the column
types of empty results.

``get_metadata`` also uses the selected resolution's catalog schema where a
default mapping is known. It preserves MRS band/exposure rows and fields
without type definitions. Unknown mappings retain raw parsing; failures to
retrieve a known schema remain errors. The verified DR10/v2.0 LRS and MRS
schemas provide no units; user-supplied ``column_schema`` units are supported.

``query_sql`` uses column definitions included in the response. Raw JSON
without these definitions preserves the service's types: a value such as
``teff='5770'`` remains a string. JSON null cells are masked; an all-null column
can retain object dtype without a schema. The client does not infer types from SQL
expressions or aliases. Supply ``column_schema`` using the actual result
column names when known types are required:

.. doctest::

  >>> column_schema = {
  ...     'obsid': {'datatype': 'long'},
  ...     'temperature': {'datatype': 'double', 'unit': 'K'},
  ...     'feh': {'datatype': 'double'},
  ...     'gaia_source_id': {'datatype': 'char'},
  ... }
  >>> stars = lamost.query_sql(  # doctest: +SKIP
  ...     'SELECT obsid, teff AS temperature, feh, gaia_source_id '
  ...     'FROM combined LIMIT 5', column_schema=column_schema)
  >>> hot_stars = stars[stars['temperature'] > 5500]  # doctest: +SKIP

The comparison above uses the column's numeric values in kelvin. The schema
must describe the returned expression, including any SQL unit conversion.
With ``column_schema``, CSV/TXT fields are read as strings before conversion;
columns without a declared datatype remain strings. This preserves character
identifiers such as ``'00123'``.
CSV character fields retain leading/trailing whitespace and embedded line
endings. Under a character schema, whitespace-only strings remain values;
empty fields are masked. Whitespace-only numeric fields remain masked.
Values that cannot be converted to their declared datatype raise
`~astroquery.exceptions.TableParseError`. Floating-point NaN and infinity
are preserved; conversion does not establish scientific validity. Check
column masks and ``numpy.isfinite`` when selecting numeric data for analysis.
A legacy VOTable can encode a missing integer as an empty ``TD`` cell.
The client masks empty scalar integer cells using their TABLEDATA positions,
preserving real zeros and existing masks. Ambiguous row/column mappings and
missing integer arrays raise ``TableParseError``. Malformed CSV and truncated
VOTable values remain errors.

Only client-generated SQL has an empty-body compatibility check: one separate
count confirms whether the same page is empty before a typed empty table is
returned. A failed count is still an error. Arbitrary ``query_sql`` statements
are never wrapped automatically.

To inspect or save SQL output before table parsing, use ``query_sql_async``:

.. code-block:: python

   from pathlib import Path

   with lamost.query_sql_async(
       'SELECT obsid, ra, dec FROM combined LIMIT 5', output_format='csv') as response:
       Path('lamost-response.csv').write_bytes(response.content)

This is a synchronous HTTP request returning ``requests.Response``, following
astroquery's ``_async`` naming convention. It checks HTTP, authentication and
explicit service errors, but leaves table parsing to the caller. Raw responses
may contain private data or credentials; diagnostic copies are redacted.
No file is saved automatically and no retry is added. SQL TXT may return a
service error; CSV and, on modern releases, JSON are the reference formats.

Temperature cuts use kelvin, ``logg`` cuts use the base-10 logarithm of surface
gravity in cm/s\ :sup:`2`, and ``feh`` cuts use [Fe/H] in dex. S/N thresholds
are dimensionless. Units are attached only when declared and recognized;
check ``table[column].unit`` before combining results from different sources.

Spectral Sample Queries
-----------------------

Use ``query_spectra`` to select spectral catalog records with common quality
cuts; use ``get_spectra`` to download their FITS data. It translates query
parameters such as SNR and stellar-parameter ranges into the structured
``query_catalog`` payload.

Position and physical constraints are applied together in the database.
``nearest_only=False`` returns the qualifying matches up to ``max_rows``;
``nearest_only=True`` selects one nearest qualifying row and requires
``page=1``. Without ``sort_by``, position results are ordered by angular
distance. Sorting and filtering do not download the entire candidate set to
the client. Rows at equal distances use stable secondary ordering; MRS
exposures sharing an ``obsid`` are not deduplicated.

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
  >>> stellar_payload["showcol"]
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
DR3 has no verified equivalent UID lookup. Its external-catalog matches may
be queried with SQL, but are not substituted for official target identities.

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

Catalog Pagination and Export
-----------------------------

Query methods return one page. To retrieve a larger sample, keep the selection,
page size, and sort order fixed while advancing ``page``. For example:

.. code-block:: python

   page = 1
   while True:
       matches = lamost.query_spectra(
           coord, '0.2 deg', columns=['obsid', 'ra', 'dec'],
           sort_by='obsid', max_rows=100, page=page)
       if len(matches) == 0:
           break
       matches.write(f'lamost-page-{page}.ecsv', format='ascii.ecsv', overwrite=True)
       page += 1

These are separate requests, not an atomic snapshot of a changing catalog.
Errors propagate instead of being treated as an empty final page. For a
single returned table, use ``Table.write`` with the desired local format;
the service's ``output_format`` controls transport rather than file saving.

Data Products
-------------

Use ``resolution='low'`` for LRS or ``resolution='medium'`` for MRS.
``get_metadata`` returns an observation table; ``get_spectra`` accepts one
observation ID and returns a list of `~astropy.io.fits.HDUList` objects.
The FITS retains its headers, inverse variance, masks, and spectral extensions.
To obtain its download URL without fetching the file, use ``get_spectrum_list``.
Authenticated URLs contain the token and must not be shared or logged;
``get_query_payload=True`` returns redacted parameters instead.

``get_spectra`` uses Astropy's ``verify='warn'`` by default. The caller must
close the returned HDU lists:

.. doctest::

  >>> spectra = lamost.get_spectra(176604010, resolution='low')  # doctest: +SKIP
  >>> try:  # doctest: +SKIP
  ...     obsid = spectra[0][0].header['OBSID']
  ...     spectra[0].writeto('lrs-spectrum.fits', overwrite=True, output_verify='fix')
  ... finally:
  ...     for spectrum in spectra:
  ...         spectrum.close()

The saved ``lrs-spectrum.fits`` is used in the LRS processing example below.
Astropy may fix structural header issues when writing; this is not a
byte-for-byte copy of the HTTP response.

For several observation IDs, repeat this operation and record any failures
before analyzing the sample. One MRS FITS can contain multiple exposures;
do not treat its ``obsid`` as a unique identifier for every exposure row.

``download_catalog`` retrieves a named catalog file and returns its local
path. It uses ``verify='exception'`` and publishes the file only after the
selected FITS verification succeeds. DR3 currently supports the verified
``download_catalog('plan')`` product, a gzip CSV validated as a table.
For DR10/v2.0 LRS, a verified product name is
``dr10_v2.0_LRS_plan.fits.gz``. Obtain file product names from the selected
release's download page; ``get_tables_metadata`` lists SQL relations, not
download products. HTTP 200 JSON errors and recognized login redirects are
checked before FITS validation, with text diagnostics limited to 1 MiB.
With ``overwrite=False``, an existing file is returned without revalidation;
the service is still contacted to resolve its name. A failed download leaves
an existing destination intact. Downloads do not resume partial files.

FITS verification checks structure, not scientific pixel quality. Inspect
warnings before changing ``verify``. Headers and pixels are preserved: a
DR4/v2 product has been observed with ``DATA_V=LAMOST DR5``; the client does
not relabel it or substitute another release.

Anonymous non-streaming requests use the inherited response cache, including
``get_spectra``. This is not a persistent spectrum library. Authenticated
requests and streaming catalog downloads bypass the cache.

Local Spectrum Processing
-------------------------

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

For example, export LRS arrays locally:

.. code-block:: python

   from astropy.table import Table
   from astroquery.nadc.lamost import parse_lrs_spectrum

   wavelength, flux = parse_lrs_spectrum('lrs-spectrum.fits')
   Table({'wavelength': wavelength, 'flux': flux}).write(
       'spectrum.csv', format='ascii.csv', overwrite=True)

Smoothing is a separate analysis choice. This seven-pixel median uses
zero-padded edges; setting ``window = 15`` selects a wider filter. Neither
result replaces the original flux:

.. code-block:: python

   import numpy as np

   window = 7
   samples = np.lib.stride_tricks.sliding_window_view(
       np.pad(flux, window // 2), window)
   smoothed_flux = np.median(samples, axis=-1)

MRS supports one-row ``FLUX``/``WAVELENGTH`` vectors and historical tables
with scalar ``FLUX``/``LOGLAM`` pixels. Logarithmic wavelengths are converted
with ``10**LOGLAM`` in double precision. Coadds and individual exposures keep
their extension names. The parser does not sort pixels, change the wavelength
frame, or apply velocity corrections. Invalid layouts, ambiguous wavelength
columns and duplicate extension names raise ``ValueError``. Wavelengths must
be finite and positive; conversion overflow and underflow to zero are rejected.
Errors identify the file, extension, and first invalid pixel. Flux quality
selection belongs to the analysis.

First download one MRS observation from the same DR10/v2.0 service:

.. code-block:: python

   mrs_files = lamost.get_spectra(1007903112, resolution='medium')
   try:
       mrs_files[0].writeto('mrs-spectrum.fits', overwrite=True, output_verify='fix')
   finally:
       for spectrum in mrs_files:
           spectrum.close()

For several local MRS files, retain each outcome so missing or invalid data
does not disappear from the sample. This example intentionally includes a
nonexistent filename to demonstrate the failure record:

.. code-block:: python

   from astropy.table import Table
   from astroquery.nadc.lamost import parse_mrs_spectrum

   spectra, rows = [], []
   for filename in ['mrs-spectrum.fits', 'missing-mrs.fits']:
       try:
           spectrum = parse_mrs_spectrum(filename)
       except (OSError, EOFError, ValueError) as error:
           spectra.append(None)
           rows.append((filename, 'ERROR', f'{type(error).__name__}: {error}'))
       else:
           spectra.append(spectrum)
           rows.append((filename, 'COMPLETE', ''))
   manifest = Table(rows=rows or None, names=('Local Path', 'Status', 'Message'),
                    dtype=(str, str, str))
   print(manifest['Local Path', 'Status', 'Message'])

This loop preserves input order, records expected file and validation errors,
and propagates unexpected exceptions. It does not repair or modify the files.

Plot a local MRS file with Matplotlib, retaining the extension labels:

.. code-block:: python

   import matplotlib.pyplot as plt
   from astroquery.nadc.lamost import parse_mrs_spectrum

   fig, ax = plt.subplots()
   for name, spectrum in parse_mrs_spectrum('mrs-spectrum.fits').items():
       ax.plot(spectrum['wavelength'], spectrum['flux'], label=name)
   ax.set(xlabel='Wavelength [Angstrom]', ylabel='Flux')
   ax.legend()
   fig.savefig('spectrum.png')
   plt.close(fig)

One-observation Activity Example
--------------------------------

The :download:`standalone example <lamost_activity.py>` selects DR7/v2.0,
retrieves metadata and a spectrum for observation 54901214, verifies the
metadata and FITS ``OBSID``, and computes the dimensionless Ca II H&K index
``S_L`` from `Zhang et al. (2022) <https://arxiv.org/abs/2209.15255>`_. It uses
only NumPy, Astropy, and astroquery. Configure authentication as described
above before running this example if anonymous access is rejected. DR7/v2.0
may require a valid token even when the DR10/v2.0 examples work anonymously.
The observed DR7 metadata and FITS endpoints are public, but ``get_metadata``
also uses SQL to obtain column types; that SQL request requires authentication.
For a standalone script, set ``ASTROQUERY_NADC_LAMOST_TOKEN`` in its
environment; a ``conf.token`` assignment in another Python process does not
carry over to the script.
``get_metadata`` normalizes the legacy DR7 response into a one-row table
with named fields. The example uses its observation ID and radial velocity.

Run the downloaded script to retrieve metadata and the spectrum:

.. code-block:: console

   $ python lamost_activity.py
   OBSID=54901214: S_L=0.180373854
   Published S_L=0.18038 +/- 0.003597

For an existing FITS file of the same observation (54901214), run without
networking:

.. code-block:: console

   $ python lamost_activity.py --filename 54901214.fits --rv -24.78

The archive RV is -24.78 km/s. The example divides the vacuum wavelengths by
``1 + RV/c`` before applying the paper's bands: 20-Angstrom rectangular
continua centered at 4002.20 and 3902.17 Angstroms, and triangular cores
centered at 3969.59 and 3934.78 Angstroms with FWHM 1.09 Angstroms. It uses
linear interpolation and trapezoidal weights, then evaluates
``S_L = (1.8 * 8 * 1.09 / 20) * (H + K) / (R + V)``.

The independently archived numerical result is ``0.1803738541038765``; the
script checks absolute agreement within ``1e-7``. This computational tolerance
is separate from the published measurement uncertainty ``0.003597``. The
published central value is ``0.18038``. This is a fixed-observation example,
not an uncertainty propagation or Mount Wilson calibration pipeline. It
requires finite positive flux for all pixels supporting each bandpass,
including neighbors outside the band edges that participate in interpolation.
An edge exactly on a wavelength sample needs no extra outside neighbor.
Invalid support pixels, RV, or nonfinite/nonpositive numerical results raise
``ValueError`` with a reason; support-pixel errors also identify the band and
pixel. Assess
archive pixel masks and scientific selection criteria for other targets.
The temporary FITS file is reserialized with Astropy header verification;
it is not claimed to preserve the original HTTP bytes. All HDU lists and
temporary files are closed or removed after use.

To process local observations independently, import ``measure_files`` from the
downloaded example. Supply the archive RV in km/s and expected integer OBSID
for each file; each identity is checked before computing its index:

.. code-block:: python

   from lamost_activity import measure_files

   manifest = measure_files([
       ('missing.fits', -24.78, 54901214),
       ('54901214.fits', -24.78, 54901214),
   ])
   print(manifest['Local Path', 'OBSID', 'Status', 'Message', 'S_L'])
   successful = manifest[manifest['Status'] == 'COMPLETE']

Like the MRS loop above, this returns one status row per input, continues
after file or validation errors, and propagates unexpected exceptions. Failed
``S_L`` values are masked and displayed as ``--``. No replacement index is
computed for a failed sample. Batch values are not compared to the fixed
observation's reference index; the script's original single-observation command
continues to perform that comparison.

Failures and Diagnostics
------------------------

Invalid query parameters or unknown catalog columns raise
`~astroquery.exceptions.InvalidQueryError`. Recognized authentication failures raise
`~astroquery.exceptions.LoginError`; configure a valid token and create a
new client as described above. Recognized cases include HTTP 401/403,
OAuth redirects, HTML META refresh to the verified login host, and service
errors asking to check a token. Other HTML pages remain parsing errors.
Other HTTP failures raise `requests.HTTPError`;
error payloads returned with HTTP success raise
`~astroquery.exceptions.RemoteServiceError`. Both preserve available, redacted
error details. A missing endpoint or unsupported release is a service/address
problem and does not by itself establish that a token is required.

Malformed responses, missing requested columns, failed datatype conversions,
and VOTables that would truncate data raise
`~astroquery.exceptions.TableParseError`. Query and JSON metadata endpoints
also reject empty bodies and HTML pages, including mislabeled HTML. A text
response with column headers and zero data rows is valid, as are supported
empty JSON and VOTable results.

When response parsing fails, ``lamost.response`` retains a redacted diagnostic
response. HTML and empty-body errors include the HTTP status, redacted URL,
content type, and body length. Payload inspection does not test authentication,
or data-query service availability. SQL-backed payload inspection validates
columns using metadata, but does not execute the data query.

Exceptions
----------

.. autoexception:: astroquery.exceptions.InvalidQueryError

.. autoexception:: astroquery.exceptions.LoginError

.. autoexception:: astroquery.exceptions.RemoteServiceError

.. autoexception:: astroquery.exceptions.TableParseError

Reference/API
=============

.. automodapi:: astroquery.nadc.lamost
    :no-inheritance-diagram:
