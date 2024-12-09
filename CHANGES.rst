0.4.8 (unreleased)
==================

New Tools and Services
----------------------

esa.neocc
^^^^^^^^^

- New module to provide access too the ESA near-earth objects coordination centre. [#2254]


Service fixes and enhancements
------------------------------

astrometry_net
^^^^^^^^^^^^^^

- Remove photutils from Astroquery astrometry.net [#3067]

- Reduce the number of API calls when polling for job status [#3079]

alma
^^^^

- Added method to return quantities instead of values and regions footprint in alma [#2855]

- Added support for frequency_resolution in KHz [#3035]

- Added support for temporary upload tables in query_tap [#3118]

- Changed the way galactic ranges are used in queries [#3105]

casda
^^^^^

- Support jobs which are in the SUSPENDED state (used when copying data) [#3134]

ehst
^^^^

- Include warning in get_datalabs_path method for ehst when the data volume is not mounted in DataLabs [#3059]

gama
^^^^

- Change URL to https and thus making the module functional again. [#3056]

esa.jwst
^^^^^^^^

- get_obs_products method supports product_type parameter as string or list [#2995]

- Add download_files_from_program method to get all products by program id [#3073]

mpc
^^^

- Parse star catalog information when querying observations database [#2957]

- Parse ephemeris with sky motion with three digit precision [#3026]

- Raise EmptyResponseError when empty ephemeris response is returned [#3026]

- Deprecate ``get_raw_response`` parameter from ``MPC.get_observations``. The
  raw response may be retrieved from the _async() method. [#3089]

- Remove ``get_raw_response`` parameter from ``MPC.get_ephemeris`` and
  ``MPC.get_observatory_codes`` without deprecation as the parameters were
  ignored and had no effect. [#3089]

- Fix bug in ``MPC.get_ephemeris`` that caused the ``cache`` keyword parameter
  to be ignored. [#3089]

- Remove ``comettype`` parameter from ``MPC.get_observations`` without
  deprecation: it was undocumented, ignored, and had no effect.  [#3089]

linelists.cdms
^^^^^^^^^^^^^^

- Fix result parsing incompatibility with astropy 6.1 on Windows systems. [#3008]

ogle
^^^^

- Change URL to https and thus making the module functional again. [#3048]


splatalogue
^^^^^^^^^^^

- Fix incompatibilities with the major changes made to the Splatalogue's upstream server in March 2024. [#2960]

vizier
^^^^^^

- Change the type of raised error when the catalog is not found in ``Vizier.get_catalog_metadata``
  from ``IndexError`` to ``EmptyResponseError`` [#2980]

sdss
^^^^

- Support new SDSS-V DR18 access URLs. [#3017]

simbad
^^^^^^

- The ``ROW_LIMIT`` value to have the maximum number of rows is now -1.
  Use ``ROW_LIMIT = 0`` to retrieve the output's meta-data. [#2954]

- ``ROW_LIMIT`` can now be set at instantiation
  (e.g.: ``simbad = Simbad(ROW_LIMIT=10))``). [#2954]

- ``list_votable_fields`` now return an astropy Table with added fields
  information instead of a list of strings. [#2954]

- ``list_votable_fields`` is now queried directly from SIMBAD instead of reading
  a file in astroquery. This prevents it from being outdated. [#2954]

- ``get_votable_fields`` now prints the table name and column name instead of
  just the column name. [#2954]

- The ``verbose`` and ``cache`` kwargs have been deprecated from all methods
  as they have no effect with with the new query interface. [#2954]

- ``get_adql`` is deprecated and replaced by ``get_query_payload`` in
  ``list_columns`` and ``list_table``.
  The payload output contains the ADQL under the ``QUERY`` key. [#2954]

- all query methods except ``query_tap`` and ``query_criteria`` now accept a
  ``criteria`` argument to restrict the results with custom criteria. [#2954]

- ``query_objects`` outputs now have an additional column ``user_specified_id``
  containing the objects' name as specified by the user.
  The ``votable_field`` option ``typed_id`` is removed. [#2954]

- The ``equinox`` and ``epoch`` kwargs are deprecated in ``query_region``,
  use astropy.coordinates.SkyCoord directly instead. [#2954]

- ``query_bibcode`` has a new option ``abstract`` that allows to also
  retrieve the article's abstract. [#2954]

- ``query_bibcode`` output is now in an astropy Table with distinct columns
  instead of a single one in which all the information was a string. [#2954]

- ``query_criteria`` is now deprecated and should be replaced by either custom
  TAP queries or by the ``criteria`` argument added in the other query methods.
  A helper method was added ``astroquery.simbad.utils.CriteriaTranslator`` to
  translate between the sim-script syntax and the TAP/ADQL syntax. [#2954]

skyview
^^^^^^^

- Overlay arguments ``lut``, ``grid``, and ``gridlabel`` are removed, as they
  only apply to output types not returned by Astroquery [#2979]

vsa
^^^

- Updating base URL to fix 404 responses. [#3033]


Infrastructure, Utility and Other Changes and Additions
-------------------------------------------------------

- Versions of astropy <5.0 and numpy <1.20 are no longer supported. [#2966]

- Versions of Python <3.9 are no longer supported. [#2966]

- Versions of PyVO <1.5 are no longer supported. [#3002]

- Dropped ``setuptools`` as a runtime dependency. [#3071]

utils.tap
^^^^^^^^^

- ``TapPlus.upload_table`` should not allow table names to contain a
  dot. ``ValueError`` is now raised for such cases. [#2971]

- Fix method read_http_response to retrieve json files. This fixes the previous PR #2947. [#2990]

gaia
^^^^

- Include table size in the class TapTableMeta returned by the functions load_tables and load_table, in the class Tap.
  [#2970]

- For the functions that return files in FITS/ECSV format, the files are now provided as uncompressed files.
  [#2983]

- New parameter USE_NAMES_OVER_IDS that gives preference to ``name`` over ID attributes of columns as the names of
  columns in the `astropy.table.Table` instance. By default, value True is set, that gives name preference.  [#2967]

- Fix method search_async_jobs in the class TapPlus. [#2967]

- Change the signature of the function load_data: the parameter output_file that defined the file where the results were
  saved, is replaced by boolean parameter dump_to_file, that in case it is true, a compressed directory named "datalink_output.zip" with
  all the DataLink files is made. So the users cannot specified the output file anymore  [#3014]

- New retrieval types for datalink (Gaia DR4 release). [#3110]

- The output file name built by the method load_data, includes microsecond resolution. This is based on the previous PR [#3014]. [#3130]


jplhorizons
^^^^^^^^^^^

- Add missing column definitions, especially for ``refraction=True`` and ``extra_precision=True``. [#2986]

mast
^^^^

- Fix bug in which the ``local_path`` parameter for the ``mast.observations.download_file`` method does not accept a directory. [#3016]

- Optimize remote test suite to improve performance and reduce execution time. [#3036]

- Add ``verbose`` parameter to modulate output in ``mast.observations.download_products`` method. [#3031]

- Fix bug in ``Catalogs.query_criteria()`` to use ``page`` and ``pagesize`` parameters correctly. [#3065]

- Modify ``mast.Observations.get_cloud_uris`` to also accept query criteria and data product filters. [#3064]

- Increased the speed of ``mast.Observations.get_cloud_uris`` by obtaining multiple
  URIs from MAST at once. [#3064]

- Present users with an error rather than a warning when nonexistent query criteria are used in ``mast.Observations.query_criteria``
  and ``mast.Catalogs.query_criteria``. [#3084]

- Support for case-insensitive criteria keyword arguments in ``mast.Observations.query_criteria`` and
  ``mast.Catalogs.query_criteria``. [#3087]

- Added function ``mast.Observations.get_unique_product_list`` to return the unique data products associated with
  given observations. [#3096]

- Deprecated ``enable_cloud_dataset`` and ``disable_cloud_dataset`` in classes where they
  are non-operational. They will be removed in a future release. [#3113]

- Present users with an error when nonexistent query criteria are used in ``mast.MastMissions`` query functions. [#3126]

- Present users with an error when nonexistent query criteria are used in ``mast.Catalogs.query_region`` and
  ``mast.Catalogs.query_object``. [#3126]

- Handle HLSP data products in ``Observations.get_cloud_uris``. [#3126]

mpc
^^^

- Rename ``MPC.get_mpc_object_endpoint`` to ``MPC._get_mpc_object_endpoint`` to
  indicate that it is a private method. [#3089]

xmatch
^^^^^^

- Fix xmatch query for two local tables. The second table was written over the first one,
  resulting in a confusing "missing cat1" error. [#3116]


0.4.7 (2024-03-08)
==================

New Tools and Services
----------------------

esa.hsa
^^^^^^^

- New module to access the ESA Herschel mission. [#2122]

ipac.irsa
^^^^^^^^^

- New class, ``Most``, to access the Moving Object Search Tool (MOST) is
  added. [#2660]

mocserver
^^^^^^^^^

- ``mocserver`` is the new name of the ``cds`` module allowing access to the
  CDS MOC server [#2766]

solarsystem.neodys
^^^^^^^^^^^^^^^^^^

- New module to access the NEODyS web interface. [#2618]

solarsystem.pds
^^^^^^^^^^^^^^^

- New module to access the Planetary Data System's Ring Node System. [#2358]


Service fixes and enhancements
------------------------------

alfalfa
^^^^^^^

- Removal of the non-functional ``get_spectrym`` method as that service has
  disappeared. [#2578]

alma
^^^^

- Fixed a regression to handle arrays of string input for the ``query``
  methods. [#2457]

- Throws an error when an unsupported ``kwargs`` (or argument) is passed in
  to a function. [#2475]

- New DataLink API handling. [#2493]

- Fixed bug in which blank URLs were being sent to the downloader. [#2490]

- Removed deprecated broken functions from ``alma.utils``. [#2331]

- Fixed a bug in slicing of ALMA regions. [#2810]

- Added support for ALMA OIDC (OpenID Connect) auth service, Keycloak. [#2712]

- Fixed bug to use the timeout set in the configuration. [#2535]

astrometry_net
^^^^^^^^^^^^^^

- Added a ``verbose=`` keyword argument to ``AstrometryNet`` to control
  whether or not to show any information during solving. [#2484]

- Fixed a bug which caused ``solve_timeout`` to not be respected when an image
  was solved by constructing a source list internally before sending data to
  astrometry.net. [#2484]

- Avoid duplicated warnings about API key and raise an error only when API key
  is needed but not set. [#2483]

- Added ``return_submission_id`` keyword argument to
  ``monitor_submission()``. [#2685]

- Fixed off-by-one error in the reference pixel of the WCS solution when the
  solution is found using sources detected by photutils. After this fix the
  solution from astrometry.net will be the same when the input is an image
  regardless of whether the image is uploaded or sources are detected
  locally. [#2752]

atomic
^^^^^^

- Fixed infitine caching loop. [#2339]

- Change URL and improve error handling. [#2769]

cadc
^^^^

- Deprecated keywords and ``run_query`` method have been removed. [#2389]

- Added the ability to pass longer that filename Path objects as
  ``output_file``. [#2541]

casda
^^^^^

- Add the ability to produce 2D and 3D cutouts from ASKAP images and cubes.
  [#2366]

- Use the standard ``login`` method for authenticating, which supports the
  system keyring. [#2386]

cds
^^^

- The ``cds`` module has been renamed ``mocserver`` and issues a deprecation
  warning when imported. [#2766]

esa.hubble
^^^^^^^^^^

- Refactored ``query_criteria`` to make the query a lot faster. [#2524]

- Method ``query_hst_tap`` has been renamed ``query_tap``. [#2597]

- Product types in ``download_product`` have been modified to:
  'PRODUCT', 'SCIENCE_PRODUCT', or 'POSTCARD'. [#2597]

- Added ``proposal`` keyword argument to several methods now allows to
  filter by Proposal ID. [#2797]

- Update to TAP url to query data and download files, aligned with the new
  eHST Science Archive. [#2567, #2597]

- Status and maintenance messages from eHST TAP when the module is
  instantiated. Use ``get_status_messages`` to retrieve them. [#2597]

- New methods to download single files ``download_file`` and download FITS
  associated to an observation ``download_fits_files``. [#2797]

- New function to retrieve all the files associated to an observation
  ``get_associated_files``. [#2797]

- New methods to retrieve metadata (``get_observations_from_program``) and
  files (``download_files_from_program``) associated to a proposal. [#2910]

- New method ``get_datalabs_path`` to return the complete path of a file in
  datalabs by combining the datalabs volume path with the path of the file
  in the table ehst.artifact [#2998, #3010]

esa.jwst
^^^^^^^^

- Fixes in ``login`` and ``set_token`` methods. [#2807]

esa.xmm_newton
^^^^^^^^^^^^^^
- New version of RMF matrices (v21). [#2910, #2932]

eso
^^^

- Authenticate with ESO using APIs and tokens instead of HTML forms. [#2681]

- Discontinue usage of old Request Handler for dataset retrieval in favor of
  new dataportal API. [#2681]

- Local reimplementation of astroquery's ``_download_file`` to fix some issues
  and avoid sending a HEAD request just to get the original filename. [#1580]

- Restore support for .Z files. [#1818]

exoplanet_orbit_database
^^^^^^^^^^^^^^^^^^^^^^^^

- The module has been deprecated due to the retirement of its upstream
  website. The database hasn't been updated since 2018, users are encouraged
  to use the ``ipac.nexsci.nasa_exoplanet_archive`` module instead. [#2792]

gaia
^^^^

- TAP notifications service is now available for Gaia. [#2376]

- Datalink can be used with the new parameter ``linking_parameter``.
  It provides an additional meaning to the source identifiers:
  'source_id', 'transit_id', and 'image_id'. [#2859, #2936]

- Added support for output formats:
  votable, votable_gzip (which is now the default), and ecsv. [#2907]

- For the functions ``cone_search``, ``cone_search_async``, ``launch_job``,
  and ``launch_job_async`` the data can be retrieved for the json
  ``output_format``. [#2927, #2947]

- Method ``load_data`` now has the parameter ``valid_data`` to control the
  epoch photometry service to return all data associated to a given source.
  [#2376]

- New retrieval types for datalink (Gaia DR4 release). [#3110]

- Default Gaia catalog updated to DR3. [#2596]

heasarc
^^^^^^^

- Fix issue in which blank tables raised exceptions. [#2624]

ipac.irsa
^^^^^^^^^

- The IRSA module's backend has been refactored to favour VO services and to
  run the queries through TAP rather than Gator.
  New method ``query_tap`` is added to enable ADQL queries, async-named
  methods have been removed. The ``selcols`` kwarg has been renamed to
  ``columns``, and the ``cache`` and ``verbose`` kwargs have been
  deprecated as they have no effect. [#2823]

- Method to run SIAv2 VO queries, ``query_sia``, is added. [#2837]

- Method to list available collections for SIA queries,
  ``list_collections``, is added. [#2952]

- Deprecation of the module ``ipac.irsa.sha`` due to upstream API changes
  and in favour of recommending using ``ipac.irsa`` instead. [#2924]

ipac.nexsci.nasa_exoplanet_archive
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- Removed deprecated methods ``query_planet`` and ``query_star``. [#2431]

- Stability improvements to ``query_aliases`` to address bug that made
  method retrieve no aliases for multiple star systems. [#2506]

- Fix unit inconsistency in ``pl_trandur`` from day(s) to hour(s). [#3137]

jplhorizons
^^^^^^^^^^^

- Deprecate ``get_raw_response`` parameter in query methods.
  The raw response may be retrieved from the _async() methods. [#2418]

- Adding ``optional_setting`` parameter to the ephemerides methods to allow
  passing additional settings. [#1802]

- Topocentric coordinates can now be specified for both center and target in
  observer and vector queries. [#2625]

- Updated returned table columns to match Horizons's updates. [#2794]

- Assign units to ``"hour_angle"``, ``"solartime"``, and ``"siderealtime"``
  columns. [#2794]

- Allow using units in locations specified as coordinates. [#2746]

jplsbdb
^^^^^^^

- Fix a bug for jplsdbd query when the returned physical quantity contains
  a unit with exponential. [#2377]

jplspec
^^^^^^^

- Fix a bug in lookup-table generation when using ``parse_name_locally``
  option. [#2945]

linelists.cdms
^^^^^^^^^^^^^^

- Fix issues with the line name parser and the line data parser; the original
  implementation was incomplete and upstream was not fully
  documented. [#2385, #2411]

- Added new line list reader and enabled reading line list from remote
  server.[#2760]

- Updated local version of line list to include some change in column names.
  [#2760]

mast
^^^^

- Cull duplicate downloads for the same dataURI in
  ``Observations.download_products()`` and duplicate URIs in
  ``Observations.get_cloud_uris``. [#2497]

- Fixed ``Observations.get_product_list`` to handle input lists of
  obsids. [#2504]

- Add a ``flat`` option to ``Observation.download_products()`` to turn off the
  automatic creation and organizing of products into subdirectories. [#2511]

- Expanding ``Cutouts`` functionality to support making Hubble Advanced
  Product (HAP) cutouts via HAPCut. [#2613]

- Expanding ``Cutouts`` functionality to support TICA HLSPs now available
  through ``TesscutClass``. [#2668]

- Resolved issue making PANSTARRS catalog queries when columns and sorting
  is specified. [#2727]

- Bug fix in ``Observations.query_criteria()`` to use ``page`` and
  ``pagesize`` parameters [#2915]

- Added ``mast_query`` to ``MastClass`` to handle the creation of parameter
  dictionaries for MAST Service queries. [#2785]

- PanSTARRS data is now available to download anonymously from the public
  STScI S3 buckets. [#2893]

- Changed warning to error for authentication failure. [#1874]

nist
^^^^

- Vectorized ``linename`` option to query multiple spectral lines with one call
  of ``Nist.query``. [#2678]

- Fix wavelength keywords, which were changed upstream. [#2918]

- Fetch statistical weight (g) from the database. [#2955]

oac
^^^

- Fix bug in parsing events that contain html tags (e.g. in their alias
  field). [#2423]

sdss
^^^^

- ``query_region()`` can perform cone search or a rectangular
  search around the specified coordinates. [#2477, #2663]

- The default data release has been changed to DR17. [#2478]

- Switching to https to avoid issues originating in relying on server side
  redirects. [#2654]

- Fix bug to have object IDs as unsigned integers, on Windows, too.
  [#2800, #2806, #2880]

simbad
^^^^^^

- new ``query_tap`` method to access SIMBAD. This comes with additional
  methods to explore SIMBAD's tables and their links:
  ``list_tables``, ``list_columns``, and ``list_linked_tables``. [#2856]

- It is now possible to specify multiple coordinates together with a single
  radius as a string in ``query_region()`` and ``query_region_async()``.
  [#2494]

- ``ROW_LIMIT`` is now respected when running region queries; previously, it
  was ignored for region queries but respected for all others.  A new warning,
  ``BlankResponseWarning``, is introduced for use when one or more query terms
  result in a blank or missing row; previously, only a generic warning was
  issued. [#2637]

skyview
^^^^^^^

- Fix bug for ``radius`` parameter to not behave as diameter. [#2601]

- Fix bug in ``height`` and ``width`` input validation. [#2757]

svo_fps
^^^^^^^

- The wavelength limits in ``get_filter_index`` can now be specified using any
  length unit, not just angstroms. [#2444]

- Queries with invalid parameter names now raise an ``InvalidQueryError``.
  [#2446]

- The default wavelength range used by ``get_filter_index`` was far too
  large. The user must now always specify both upper and lower limits. [#2509]

vizier
^^^^^^

- Fix parsing vizier generated tsv returns. [#2611]

- New method ``get_catalog_metadata`` allows to retrieve information about
  VizieR catalogs such as origin_article, description, or last modified
  date. [#2878]

xmatch
^^^^^^

- The reason for query errors, as parsed from the returned VOTable is now
  exposed as part of the traceback. [#2608]

- Minor internal change to use VOTable as the response format that include
  units, too. [#1375]


Infrastructure, Utility and Other Changes and Additions
-------------------------------------------------------

- Optional keyword arguments are now keyword only.
  [#1802, #2339, #2477, #2532, #2597, #2601, #2609, #2610, #2655, #2656, #2661, #2671, #2690, #2703]

- New function, ``utils.cleanup_downloads.cleanup_saved_downloads``, is
  added to help the testcleanup narrative in narrative documentations. [#2384]

- Adding new ``BaseVOQuery`` baseclass for modules using VO tools. [#2836]

- Adding more system and package information to User-Agent. [#2762, #2836]

- Refactoring caching. [#1634]

- Removal of the non-functional ``nrao`` module as it was completely
  incompatible with the refactored upstream API. [#2546]

- Removal of the non-functional ``noirlab`` module because the current module
  is incompatible with the new upstream API. [#2579]

- Removed deprecated function ``utils.commons.send_request()``. [#2583]

- Removed deprecated function ``utils.download_list_of_fitsfiles()``. [#2594]

- Versions of astropy <4.2.1 and numpy <1.18 are no longer supported. [#2602]

utils.tap
^^^^^^^^^

- Add support for ``MAXREC`` parameter. [#1584]

- Data downloads are now executed in streaming mode. [#2910]


0.4.6 (2022-03-22)
==================

Service fixes and enhancements
------------------------------

alma
^^^^

- Added ``verify_only`` option to check if data downloaded with correct file
  size. [#2263]

- Deprecated keywords and ``stage_data`` method has been removed. [#2309]

- Deprecate broken functions from ``alma.utils``. [#2332]

- Optional keyword arguments are now keyword only. [#2309]

casda
^^^^^

- Simplify file names produced by ``download_files`` to avoid filename too
  long errors. [#2308]

esa.hubble
^^^^^^^^^^

- Changed ``query_target`` method to use TAP instead of AIO. [#2268]


- Added new method ``get_hap_hst_link`` and ``get_member_observations`` to
  get related observations. [#2268]

esa.xmm_newton
^^^^^^^^^^^^^^

- Add option to download proprietary data. [#2251]

gaia
^^^^

- The ``query_object()`` and ``query_object_async()`` methods of
  ``astroquery.gaia.Gaia`` no longer ignore their ``columns`` argument when
  ``radius`` is specified. [#2249]

- Enhanced methods ``launch_job`` and ``launch_job_async`` to avoid issues with
  the name provided by the user for the output file when the results are
  returned by the TAP in compressed format. [#2077]

ipac.nexsci.nasa_exoplanet_archive
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- Fixes to alias query, and regularize keyword removed from deprecated
  ``query_star`` method. [#2264]

mast
^^^^

- Adding moving target functionality to ``Tesscut`` [#2121]

- Adding ``MastMissions`` class to provide mission-specific metadata query
  functionalities. [#2095]

- GALEX data is now available to download anonymously from the public
  STScI S3 buckets. [#2261]

- Adding the All-Sky PLATO Input Catalog ('plato') as a catalog option for
  methods of ``Catalogs``. [#2279]

- Optional keyword arguments are now keyword only. [#2317]

sdss
^^^^

- Fix ``query_crossid`` for spectral data and DR17. [#2258, #2304]

- Fix ``query_crossid`` to be able to query larger list of coordinates. [#2305]

- Fix ``query_crossid`` for very old data releases (< DR10). [#2318]


Infrastructure, Utility and Other Changes and Additions
-------------------------------------------------------

- Remove obsolete testing tools. [#2287]

- Callback hooks are deleted before caching. Potentially all cached queries
  prior to this PR will be rendered invalid. [#2295]

utils.tap
^^^^^^^^^

- The modules that make use of the ``astroquery.utils.tap.model.job.Job`` class
  (e.g. Gaia) no longer print messages about where the results of async queries
  were written if the ``verbose`` setting is ``False``. [#2299]

- New method, ``rename_table``, which allows the user to rename table and
  column names. [#2077]



0.4.5 (2021-12-24)
==================

New Tools and Services
----------------------

esa.jwst
^^^^^^^^^^

- New module to provide access to eJWST Science Archive metadata and datasets. [#2140, #2238]


Service fixes and enhancements
------------------------------

eso
^^^

- Add option to retrieve_data from an earlier archive query. [#1614]

jplhorizons
^^^^^^^^^^^

- Fix result parsing issues by disabling caching of failed queries. [#2253]

sdss
^^^^

- Fix URL for individual spectrum file download in recent data releases. [#2214]

Infrastructure, Utility and Other Changes and Additions
-------------------------------------------------------

- Adding ``--alma-site`` pytest option for testing to have a control over
  which specific site to test. [#2224]

- The function ``astroquery.utils.download_list_of_fitsfiles()`` has been
  deprecated. [#2247]

utils.tap
^^^^^^^^^

- Changing the default verbosity of TapPlus to False. [#2228]


0.4.4 (2021-11-17)
==================

New Tools and Services
----------------------

esa.esasky
^^^^^^^^^^

- Added Solar System Object functionality. [#2106]

- Added support for eROSITA downloads. [#3111]

ipac
^^^^

- New namespace for IPAC services. [#2131]

linelists.cdms
^^^^^^^^^^^^^^
- Molecular line catalog query tool provides an interface to the
  Cologne Database for Molecular Spectroscopy. [#2143]


Service fixes and enhancements
------------------------------

casda
^^^^^^

- Add ability to stage and download non image data which have been found
  through the CASDA obscore table. [#2158]

gaia
^^^^

- The bug which caused changing the ``MAIN_GAIA_TABLE`` option to have no
  effect has been fixed. [#2153]

ipac.ned
^^^^^^^^

- Keyword 'file_format' is added to ``get_image_list`` to enable obtaining
  links to non-fits file formats, too. [#2217]

jplhorizons
^^^^^^^^^^^

- Updated to use v1.0 of the new JPL Horizons API released 2021-09-15.
  Included in this update, the default reference system is changed from
  J2000 to ICRF, following API documentation. [#2154]

- Query ``id_type`` behavior has changed:
    * ``'majorbody'`` and ``'id'`` have been removed and the equivalent
      functionality replaced with ``None``.  ``None`` implements the Horizons
      default, which is to search for major bodies first, then fall back to a
      small body search when no matches are found. Horizons does not have a
      major body only search. [#2161]
    * The default value was ``'smallbody'`` but it is now ``None``, which
      follows Horizons's default behavior. [#2161]

- Fix changes in column names that resulted KeyErrors. [#2202]

jplspec
^^^^^^^

- JPLSpec now raises an EmptyResponseError if the returned result is empty.
  The API for JPLspec's ``lookup_table.find`` function returns a dictionary
  instead of values (for compatibility w/CDMS).  [#2144]

simbad
^^^^^^

- Fix result parsing issues by disabling caching of failed queries. [#2187]

- Fix parsing of non-ascii bibcode responses. [#2200]

splatalogue
^^^^^^^^^^^

- Splatalogue table merging can now handle unmasked columns. [#2136]

vizier
^^^^^^

- It is now possible to specify 'galatic' centers in region queries to
  have box queries oriented along the galactic axes. [#2152]


Infrastructure, Utility and Other Changes and Additions
-------------------------------------------------------

- Versions of astropy <4 and numpy <1.16 are no longer supported. [#2163]

ipac
^^^^

- As part of the namespace restructure, now modules for the IPAC archives are
  avalable as: ``ipac.irsa``, ``ipac.ned``, and ``ipac.nexsci``.
  Additional services have also been moved to their parent organisations'
  namespace. Acces from the top namespace have been deprecated for the
  following modules: ``ibe``, ``irsa``, ``irsa_dust``,
  ``nasa_exoplanet_archive``, ``ned``, ``sha``. [#2131]


0.4.3 (2021-07-07)
==================

New Tools and Services
----------------------

esa.esasky
^^^^^^^^^^

- Download by observation id or source name. [#2078]

- Added custom ADQL and TAP+ functionality. [#2078]

- Enabled download of INTEGRAL data products. [#2105]

esa.hubble
^^^^^^^^^^

- Module added to perform a cone search based on a set of criteria. [#1855]

esa.xmm_newton
^^^^^^^^^^^^^^

- Adding the extraction epic light curves and spectra. [#2017]

heasarc
^^^^^^^

- Add alternative instance of HEASARC Server, maintained by
  INTEGRAL Science Data Center. [#1988]

nasa_exoplanet_archive
^^^^^^^^^^^^^^^^^^^^^^

- Making module compatible with the NASA Exoplanet Archive 2.0 using TAP.
  release. Support for querying old tables (exoplanets, compositepars, and
  exomultpars) has been dropped. [#2067]


Service fixes and enhancements
------------------------------

atomic
^^^^^^

- Change URL to https. [#2088]

esa.xmm_newton
^^^^^^^^^^^^^^

- Fixed the generation of files with wrong extension. [#2017]

- Use astroquery downloader tool to get progressbar, caching, and prevent
  memory leaks. [#2087]

gaia
^^^^

- Changed default of Gaia TAP Plus interface to instantiate silently. [#2085]

heasarc
^^^^^^^

- Added posibility to query limited time range. [#1988]

ibe
^^^

- Doubling default timeout to 120 seconds. [#2108]

- Change URL to https. [#2108]

irsa
^^^^

- Adding ``cache`` kwarg to the class methods to be able to control the use
  of local cache. [#2092]

- Making optional kwargs keyword only. [#2092]

sha
^^^

- Change URL to https. [#2108]

- A ``NoResultsWarning`` is now returned when there is return of any empty
  table. [#1837]


Infrastructure, Utility and Other Changes and Additions
-------------------------------------------------------

- Fixed progressbar download to report the correct downloaded amount. [#2091]

- Dropping Python 3.6 support. [#2102]


0.4.2 (2021-05-14)
==================

New Tools and Services
----------------------

cds.hips2fits
^^^^^^^^^^^^^

- New module HIPS2fits to provide access to fits/jpg/png image cutouts from a
  HiPS + a WCS. [#1734]

esa.iso
^^^^^^^

- New module to access ESA ISO mission. [#1914]

esa.xmm_newton
^^^^^^^^^^^^^^

- New method ``get_epic_images`` is added to extract EPIC images from
  tarballs. [#1759]

- New method ``get_epic_metadata`` is added to download EPIC sources
  metadata. [#1814]

mast
^^^^

- Added Zcut functionality to astroquery [#1911]

svo_fps
^^^^^^^

- New module to access the Spanish Virtual Observatory Filter Profile List. [#1498]


Service fixes and enhancements
------------------------------

alma
^^^^

- The archive query interface has been deprecated in favour of
  VirtualObservatory (VO) services such as TAP, ObsCore etc. The alma
  library has been updated accordingly. [#1689]

- ALMA queries using string representations will now convert to appropriate
  coordinates before being sent to the server; previously they were treated as
  whatever unit they were presented in.  [#1867]

- Download mechanism uses the ALMA Datalink service that allows exploring and
  downloading entire tarball package files or just part of their
  content. [#1820]

- Fixed bug in ``get_data_info`` to ensure relevant fields are strings. [#2022]

esa.esasky
^^^^^^^^^^

- All ESASky spectra now accessible. [#1909]

- Updated ESASky module for version 3.5 of ESASky backend. [#1858]

- Added row limit parameter for map queries. [#1858]

esa.hubble
^^^^^^^^^^

- Module added to query eHST TAP based on a set of specific criteria and
  asynchronous jobs are now supported. [#1723]

gaia
^^^^
- Fixed RA/dec table edit capability. [#1784]

- Changed file names handling when downloading data. [#1784]

- Improved code to handle bit data type. [#1784]

- Prepared code to handle new datalink products. [#1784]

gemini
^^^^^^

- ``login()`` method to support authenticated sessions to the GOA. [#1780]

- ``get_file()`` to support downloading files. [#1780]

- fix syntax error in ``query_criteria()`` [#1823]

- If QA and/or engineering parameters are explicitly passed, remove the
  defaults of ``notengineering`` and/or ``NotFail``. [#2000]

- Smarter defaulting of radius to None unless coordinates are specified, in
  which case defaults to 0.3 degrees. [#1998]

heasarc
^^^^^^^

- A ``NoResultsWarning`` is now returned when there is no matching rows were
  found in query. [#1829]

irsa
^^^^

- Used more specific exceptions in IRSA. [#1854]

jplsbdb
^^^^^^^

- Returns astropy quantities, rather than scaled units. [#2011]

lcogt
^^^^^

- Module has been removed after having been defunct due to upstream API
  refactoring a few years ago. [#2071]

mast
^^^^

- Added ``Observations.download_file`` method to download a single file from
  MAST given an input data URI. [#1825]

- Added case for passing a row to ``Observations.download_file``. [#1881]

- Removed deprecated methods: ``Observations.get_hst_s3_uris()``,
  ``Observations.get_hst_s3_uri()``, ``Core.get_token()``,
  ``Core.enable_s3_hst_dataset()``, ``Core.disable_s3_hst_dataset()``; and
  parameters: ``obstype`` and ``silent``. [#1884]

- Fixed error causing empty products passed to ``Observations.get_product_list()``
  to yeild a non-empty result. [#1921]

- Changed AWS cloud access from RequesterPays to anonymous acces. [#1980]

- Fixed error with download of Spitzer data. [#1994]

sdss
^^^^

- Fix validation of field names. [#1790]

splatalogue
^^^^^^^^^^^

- The Splatalogue ID querying is now properly cached in the astropy cache
  directory. The scraping function has also been updated to reflect
  the Splatalogue webpage. [#1772]

- The splatalogue URL has changed to https://splatalogue.online, as the old site
  stopped functioning in September 2020 [#1817]

ukidss
^^^^^^

- Updated to ``UKIDSSDR11PLUS`` as the default data release. [#1767]

vamdc
^^^^^

- Deprecate module due to upstream library dependence and compability
  issues. [#2070]

vizier
^^^^^^

- Refactor module to support list of coordinates as well as several fixes to
  follow changes in upstream API. [#2012]


Infrastructure, Utility and Other Changes and Additions
-------------------------------------------------------

- HTTP requests and responses can now be logged when the astropy
  logger is set to level "DEBUG" and "TRACE" respectively. [#1992]

- Astroquery and all its modules now uses a logger similar to Astropy's. [#1992]


0.4.1 (2020-06-19)
==================

New Tools and Services
----------------------

esa.xmm_newton
^^^^^^^^^^^^^^

- A new ESA archive service for XMM-Newton access. [#1557]

image_cutouts.first
^^^^^^^^^^^^^^^^^^^

- Module added to access FIRST survey radio images. [#1733]

noirlab
^^^^^^^

- Module added to access the NOIRLab (formally NOAO) archive. [#1638]


Service fixes and enhancements
------------------------------

alma
^^^^

- A new API was deployed in late February / early March 2020, requiring a
  refactor.  The user-facing API should remain mostly the same, but some
  service interruption may have occurred.  Note that the ``stage_data`` column
  ``uid`` has been renamed ``mous_uid``, which is a technical correction, and
  several columns have been added. [#1644, #1665, #1683]

- The contents of tarfiles can be shown with the ``expand_tarfiles`` keyword
  to ``stage_data``. [#1683]

- Bugfix: when accessing private data, auth credentials were not being passed
  to the HEAD request used to acquire header data. [#1698]

casda
^^^^^

- Add ability to stage and download ASKAP data. [#1706]

cadc
^^^^

- Fixed authentication and enabled listing of async jobs. [#1712]

eso
^^^

- New ``unzip`` parameter to control uncompressing the retrieved data. [#1642]

gaia
^^^^
- Allow for setting row limits in query submissions through class
  attribute. [#1641]

gemini
^^^^^^

- Allow for additional search terms to be sent to query_criteria and passed to
  the raw web query against the Gemini Archive. [#1659]

jplhorizons
^^^^^^^^^^^

- Fix for changes in HORIZONS return results after their 2020 Feb 12
  update. [#1650]

nasa_exoplanet_archive
^^^^^^^^^^^^^^^^^^^^^^

- Update the NASA Exoplanet Archive interface to support all tables available
  through the API. The standard astroquery interface is now implemented via the
  ``query_*[_async]`` methods. [#1700]

nrao
^^^^

- Fixed passing ``project_code`` to the query [#1720]

vizier
^^^^^^

- It is now possible to specify constraints to ``query_region()``
  with the ``column_filters`` keyword. [#1702]


Infrastructure, Utility and Other Changes and Additions
-------------------------------------------------------

- Versions of astropy <3.1 are no longer supported. [#1649]

- Fixed a bug that would prevent the TOP statement from being properly added
  to a TAP query containing valid '\n'. The bug was revealed by changes to
  the gaia module, introduced in version 0.4. [#1680]

- Added new ``json`` keyword to BaseQuery requests. [#1657]


0.4 (2020-01-24)
================

New Tools and Services
----------------------

casda
^^^^^

- Module added to access data from the CSIRO ASKAP Science Data Archive.  [#1505]

dace
^^^^

- Added DACE Service. See https://dace.unige.ch/ for details. [#1370]

gemini
^^^^^^

- Module added to access the Gemini archive. [#1596]


Service fixes and enhancements
------------------------------

gaia
^^^^
- Add optional 'columns' parameter to select specific columns. [#1548]

imcce
^^^^^

- Fix Skybot return for unumbered asteroids. [#1598]

jplhorizons
^^^^^^^^^^^

- Fix for changes in HORIZONS return results after their 2020 Jan 21 update. [#1620]

mast
^^^^

- Add Kepler to missions with cloud support,
  Update ``get_cloud_uri`` so that if a file is not found it produces a warning
  and returns None rather than throwing an exception. [#1561]

nasa_exoplanet_archive
^^^^^^^^^^^^^^^^^^^^^^
- Redefined the query API so as to prevent downloading of the whole database.
  Added two functions ``query_planet`` (to query for a specific exoplanet), and
  ``query_star`` (to query for all exoplanets under a specific stellar system) [#1606]



splatalogue
^^^^^^^^^^^

- Added new 'only_astronomically_observed' option. [#1600]

vo_conesearch
^^^^^^^^^^^^^

- ``query_region()`` now accepts ``service_url`` keyword and uses
  ``conf.pedantic`` and ``conf.timeout`` directly. As a result, ``URL``,
  ``PEDANTIC``, and ``TIMEOUT`` class attributes are no longer needed, so
  they are removed from ``ConeSearchClass`` and ``ConeSearch``. [#1528]

- The classic API ``conesearch()`` no longer takes ``timeout`` and ``pedantic``
  keywords. It uses ``conf.pedantic`` and ``conf.timeout`` directly. [#1528]

- Null result now emits warning instead of exception. [#1528]

- Result is now returned as ``astropy.table.Table`` by default. [#1528]


Infrastructure, Utility and Other Changes and Additions
-------------------------------------------------------

utils
^^^^^

- Added timer functions. [#1508]


0.3.10 (2019-09-19)
===================

New Tools and Services
----------------------

astrometry_net
^^^^^^^^^^^^^^

- Module added to interface to astrometry.net plate-solving service. [#1163]

cadc
^^^^

- Module added to access data at the Canadian Astronomy Data Centre. [#1354, #1486]

esa
^^^

- Module added ``hubble`` for accessing the ESA Hubble Archive. [#1373, #1534]

gaia
^^^^

- Added tables sharing, tables edition, upload from pytable and job results,
  cross match, data access and datalink access. [#1266]

imcce
^^^^^

- Service ``miriade`` added, querying asteroid and comets ephemerides. [#1353]

- Service ``skybot`` added, identifying Solar System objects in a given
  field at a given epoch. [#1353]

mast
^^^^

- Addition of observation metadata query. [#1473]

- Addition of catalogs.MAST PanSTARRS catalog queries. [#1473]

mpc
^^^

- Functionality added to query observations database. [#1350]


Service fixes and enhancements
------------------------------

alma
^^^^

- Fix some broken VOtable returns and a broken login URL. [#1369]

- ``get_project_metadata()`` is added to query project metadata. [#1147]

- Add access to the ``member_ous_id`` attribute. [#1316]

cds
^^^

- Apply MOCPy v0.5.* API changes. [#1343]

eso
^^^

- Try to re-authenticate when logged out from the ESO server. [#1315]

heasarc
^^^^^^^

- Fixing error handling to filter out only the query errors. [#1338]

jplhorizons
^^^^^^^^^^^

- Add ``refplane`` keyword to ``vectors_async`` to return data for different
  available reference planes. [#1335]

- Vector queries provide different aberrations, ephemerides queries provide
  extra precision option. [#1478]

- Fix crash when precision to the second on epoch is requested. [#1488]

- Fix for missing H, G values. [#1333]

jplsbdb
^^^^^^^

- Fix for missing values. [#1333]

mast
^^^^

- Update query_criteria keyword obstype->intentType. [#1366]

- Remove deprecated authorization code, fix unit tests, general code cleanup,
  documentation additions. [#1409]

- TIC catalog search update. [#1483]

- Add search by object name to Tesscut, make resolver_object public, minor bugfixes. [#1499]

- Add option to query TESS Candidate Target List (CTL) Catalog. [#1503]

- Add verbose keyword for option to silence logger info and warning about S3
  in enable_cloud_dataset(). [#1536]

nasa_ads
^^^^^^^^

- Fix an error in one of the default keys, citations->citation. [#1337]

nist
^^^^

- Fixed an upstream issue where js was included in returned data. [#1359]

- Unescape raw HTML codes in returned data back into Unicode equivalents to
  stop them silently breaking Table parsing. [#1431]

nrao
^^^^

- Fix parameter validation allowing for hybrid telescope configuration. [#1283]

sdss
^^^^

- Update to SDSS-IV URLs and general clean-up. [#1308]

vizier
^^^^^^

- Support using the output values of ``find_catalog`` in ``get_catalog``. [#603]

- Fix to ensure to fall back on the default catalog when it's not provided as
  part of the query method. [#1328]

- Fix swapped width and length parameters. [#1406]

xmatch
^^^^^^

- Add parameter ``area`` to restrict sky  region considered. [#1476]


Infrastructure, Utility and Other Changes and Additions
-------------------------------------------------------

- HTTP user-agent now has the string ``_testrun`` in the version number of astroquery,
  for queries triggered by testing. [#1307]

- Adding deprecation decorators to ``utils`` from astropy to be used while we
  support astropy <v3.1.2. [#1435]

- Added tables sharing, tables edition, upload from pytable and job results,
  data access and datalink access to ``utils.tap``. [#1266]

- Added a new ``astroquery.__citation__`` and ``astroquery.__bibtex__``
  attributes which give a citation for astroquery in bibtex format. [#1391]



0.3.9 (2018-12-06)
==================

- New tool: MPC module can now request comet and asteroid ephemerides from the
  Minor Planet Ephemeris Service, and return a table of observatory codes and
  coordinates. [#1177]
- New tool ``CDS``:  module to query the MOCServer, a CDS tool providing MOCs
  and meta data of various data-sets. [#1111]
- New tool ``JPLSDB``: New module for querying JPL's Small Body Database
  Browser [#1214]

- ATOMIC: fix several bugs for using Quantities for the range parameters.
  [#1187]
- CADC: added the get_collections method. [#1482]
- ESASKY: get_maps() accepts dict or list of (name, Table) pairs as input
  table list. [#1167]
- ESO: Catch exception on login when keyring fails to get a valid storage.
  [#1198]
- ESO: Add option to retrieve calibrations associated to data. [#1184]
- FERMI: Switch to HTTPS [#1241]
- IRSA: Added ``selcols`` keyword. [#1296]
- JPLHorizons: Fix for missing total absolute magnitude or phase coefficient
  for comets [#1151]
- JPLHorizons: Fix queries for major solar system bodies when sub-observer or
  sub-solar positions are requested. [#1268]
- JPLHorizons: Fix bug with airmass column. [#1284]
- JPLSpec: New query service for JPL Molecular Spectral Catalog. [#1170]
- JPLHorizons: JPL server protocol and epoch range bug fixes, user-defined
  location and additional ephemerides information added [#1207]
- HITRAN: use class-based API [#1028]
- MAST: Enable converting list of products into S3 uris [#1126]
- MAST: Adding Tesscut interface for accessing TESS cutouts. [#1264]
- MAST: Add functionality for switching to auth.mast when it goes live [#1256]
- MAST: Support downloading data from multiple missions from the cloud [#1275]
- MAST: Updating HSC and Gaia catalog calls (bugfix) [#1203]
- MAST: Fixing bug in catalog criteria queries, and updating remote tests.
  [#1223]
- MAST: Fixing mrp_only but and changing default to False [#1238]
- MAST: TESS input catalog bugfix [#1297]
- NASA_ADS: Use new API [#1162]
- Nasa Exoplanet Arhive: Add option to return all columns. [#1183]
- SPLATALOGUE: Minor - utils & tests updated to match upstream change [#1236]
- utils.tap: Fix Gaia units. [#1161]
- VO_CONESEARCH: Service validator now uses new STScI VAO TAP registry. [#1114]
- WFAU: Added QSL constraints parameter [#1259]
- XMATCH: default timeout has changed from 60s to 300s. [#1137]

- Re-enable sandboxing / preventing internet access during non-remote tests,
  which has been unintentionally disabled for a potentially long time.  [#1274]
- File download progress bar no longer displays when Astropy log level is set
  to "WARNING", "ERROR", or "CRITICAL". [#1188]
- utils: fix bug in ``parse_coordinates``, now strings that can be interpreted
  as coordinates are not sent through Sesame. When unit is not provided,
  degrees is now explicitely assumed. [#1252]
- JPLHorizons: fix for #1201 issue in elements() and vectors(), test added
- JPLHorizons: fix for missing H, G values [#1332]
- JPLHorizons: warn if URI is longer than 2000 chars, docs updated
- JPLSBDB: fix for missing value, test added


0.3.8 (2018-04-27)
==================

- New tool ``jplhorizons``: JPL Horizons service to obtain ephemerides,
  orbital elements, and state vectors for Solar System objects. [#1023]
- New tool ``mpc``: MPC Module to query the Minor Planet Center web service.
  [#1064, #1077]
- New tool ``oac``: Open Astronomy Catalog API to obtain data products on
  supernovae, TDEs, and kilonovae. [#1053]
- New tool ``wfau`` and ``vsa``: Refactor of the UKIDSS query tool add full
  WFAU support.  [#984]
- ALMA: Adding support for band and polarization selection. [#1108]
- HEASARC: Add additional functionality and expand query capabilities. [#1047]
- GAIA: Default URL switched to DR2 and made configurable. [#1112]
- IRSA: Raise exceptions for exceeding output table size limit. [#1032]
- IRSA_DUST: Call over https. [#1069]
- LAMDA: Fix writer for Windows on Python 3. [#1059]
- MAST: Removing filesize checking due to unreliable filesize reporting in
  the database. [#1050]
- MAST: Added Catalogs class. [#1049]
- MAST: Enable downloading MAST HST data from S3. [#1040]
- SPLATALOGUE: Move to https as old HTTP post requests were broken. [#1076]
- UKIDSS: Update to DR10 as default database. [#984]
- utils.TAP: Add tool to check for phase of background job. [#1073]
- utils.TAP: Added redirect handling to sync jobs. [#1099]
- utils.TAP: Fix jobsIDs assignment. [#1105]
- VO_CONESEARCH: URL for validated services have changed. Old URL should still
  redirect but it is deprecated. [#1033]

0.3.7 (2018-01-25)
==================

- New tool: Exoplanet Orbit Catalog, NASA Exoplanet Archive [#771]
- ESO: The upstream API changed.  We have adapted.  [#970]
- ESO: Added 'destination' keyword to Eso.retrieve_data(), to download files
  to a specific location (other than the cache). [#976]
- ESO: Fixed Eso.query_instrument() to use instrument specific query forms
  (it was using the main form before). [#976]
- ESO: Implemented Eso.query_main() to query all instruments with the main form
  (even the ones without a specific form). [#976]
- ESO: Disabled caching for all Eso.retrieve_data() operations. [#976]
- ESO: Removed deprecated Eso.data_retrieval() and Eso.query_survey().
  Please use Eso.retrieve_data() and Eso.query_surveys() instead. [#1019]
- ESO: Added configurable URL. [#1017]
- ESO: Fixed string related bugs. [#981]
- MAST: Added convenience function to list available missions. [#947]
- MAST: Added login capabilities [#982]
- MAST: Updated download functionality [#1004]
- MAST: Fixed no results bug [#1003]
- utils.tap: Made tkinter optional dependency. [#983]
- utils.tap: Fixed a bug in load_tables. [#990]
- vo_conesearch: Fixed bad query for service that cannot accept '&&'
  in URL. [#993]
- vo_conesearch: Removed broken services from default list. [#997, #1002]
- IRSA Dust: fix units in extinction by band table. [#1016]
- IRSA: Updated links that switched to use https. [#1010]
- NRAO: Allow multiple configurations, telescopes in queries [#1020]
- SIMBAD: adding 'get_query_payload' kwarg to all public methods to return
  the request parameters. [#962]
- CosmoSim: Fixed login service. [#999]
- utils: upgrade ``prepend_docstr_noreturns`` to work with multiple
  sections, and thus rename it to ``prepend_docstr_nosections``. [#988]
- Vizier: find_catalogs will now respect UCD specifications [#1000]
- ATOMIC: Added ability to select which rows are returned from the atomic
  line database. [#1006]
- ESASKY: Added Windows support, various bugfixes. [#1001, #977]
- GAMA: Updated to use the newer DR3 release. [#1005]

0.3.6 (2017-07-03)
==================

- New tool: MAST - added module to access the Barbara A. Mikulski Archive
  for Space Telescopes. [#920, #937]
- LAMDA: Add function to write LAMDA-formatted Tables to a datafile. [#887]
- ALMA: Fix to queries and tests that were broken by changes in the archive.
  Note that as of April 2017, the archive is significantly broken and missing
  many data sets. [#888]
- SIMBAD: "dist" is now available as a valid votable field. [#849]
  Additional minor fixes. [#932,#892]
- SHA: fix bug with the coordinate handling. [#885]
- ``turn_off_internet`` and ``turn_on_internet`` is not available any more
  from the main ``utils`` namespace, use them directly from
  ``utils.testing_tools``. [#940]
- Added the 'verify' kwarg to ``Astroquery.request`` to provide a workaround
  for services that have HTTPS URLs but missing certificates. [#928]

0.3.5 (2017-03-29)
==================

- New tool: Gaia - added module to access the European Space Agency Gaia
  Archive. [#836]
- New tool: VO Cone Search - added module to access Virtual Observatory's
  Simple Cone Search. This is ported from ``astropy.vo``. [#859]
- New utility: TAP/TAP+ - added Table Access Protocol utility and the ESAC
  Science Data Centre (ESDC) extension. [#836]
- Fix VizieR to respect specification to return default columns only [#792]
- SIMBAD queries allow multiple configurable parameters [#820]
- Add a capability to resume partially-completed downloads for services that
  support the http 'range' keyword.  Currently applied to ESO and ALMA
  [#812,#876]
- SIMBAD now supports vectorized region queries.  A list of coordinates can be
  sent to SIMBAD simultaneously.  Users will also be warned if they submit
  queries with >10000 entries, which is the SIMBAD-recommended upper limit.
  Also, SIMBAD support has noted that any IP submitting >6 queries/second
  will be soft-banned, so we have added a warning to this effect in the
  documentation [#833]
- ALMA: Fix to always use https as the archive now requires it. [#814, #828]
- ESASky: Fix various issues related to remote API changes. [#805, #817]
- ESASky: Corrected Herschel filter indexing. [#844]
- ESO: Fix picking issue with simple ``query_survey()`` queries. [#801]
- ESO: Fix FEROS and HARPS instrument queries. [#840]
- NRAO: Change default radius from 1 degree to 1 arcmin. [#813]

0.3.4 (2016-11-21)
==================

- New tool: basic HITRAN queries support [#617]
- Fix #737, an issue with broken ALMA archive tables, via a hack [#775]
- Correct HEASARC tool, which was sending incorrect data to the server [#774]
- Fix NIST issue #714 which led to badly-parsed tables [#773]
- NRAO archive tool allows user logins and HTML-based queries [#767, #780]
- ALMA allows kwargs as input, and various small fixes [#785, #790, #782]
- XMatch caching bug fixed [#789]
- Various fixes to ESASky [#779, #772, #770]
- New tool: VAMDC-cdms interface [#658]
- Fix issue with exclude keyword in Splatalogue queries [#616]

0.3.3 (2016-10-11)
==================

- Option to toggle the display of the download bar [#734]
- ESASKY - added new module for querying the ESASKY archive [#758, #763, #765]
- Refactor Splatalogue and XMatch to use the caching [#747, #751]
- Minor data updates to Splatalogue [#746, #754, #760]
- Fix parsing bug for ``_parse_radius`` in Simbad [#753]
- Multiple fixes to ensure Windows compatibility [#709, #726]
- Minor fixes to ESO to match upstream form changes [#729]

0.3.2 (2016-06-10)
==================

- Update ESO tool to work with new web API [#696]
- Added new instruments for ESO: ``ambient_paranal`` and ``meteo_paranal``
  [#657]
- Fix problem with listed votable fields being truncated in SIMBAD [#654]
- SDSS remote API fixes [#690]
- ALMA file downloader will skip over, rather than crashing on, access denied
  (HTTP 401) errors [#687]
- Continued minor ALMA fixes [#655,#672,#687,#688]
- Splatalogue export limit bugfix [#673]
- SIMBAD flux_quality flag corrected to flux_qual [#680]
- VIZIER add a flag to return the query payload for debugging [#668]

0.3.1 (2016-01-19)
==================

- Fix bug in xmatch service that required astropy tables to have exactly 2
  columns on input [#641]
- Fix NASA ADS, which had an internal syntax error [#602]
- Bugfix in NRAO queries: telescope config was parsed incorrectly [#629]
- IBE - added new module for locating data from PTF, WISE, and 2MASS from IRSA.
  See <http://irsa.ipac.caltech.edu/ibe/> for more information about IBE and
  <http://www.ptf.caltech.edu/page/ibe> for more information about PTF survey
  data in particular. [#450]

0.3.0 (2015-10-26)
==================

- Fix ESO APEX project ID keyword [#591]
- Fix ALMA queries when accessing private data [#601]
- Allow data downloads to use the cache [#601]

0.2.6 (2015-07-23)
==================

- ESO bugfixes for handling radio buttons [#560]
- ESO: added SPHERE to list [#551]
- ESO/ALMA test cleanup [#553]
- Allow ALMA project view [#554]
- Fix Splatalogue version keyword [#557]

0.2.4 (2015-03-27)
==================

- Bugfix for ``utils.commons.send_request()``: Raise exception if error status
  is returned in the response. [#491]
- Update for ALMA Cycle 3 API change [#500]
- Added LCOGT Archive support [#537]
- Refactored LAMDA to match the standard API and added a critical density
  calculation utility [#546]

0.2.3 (2014-09-30)
==================


- AstroResponse has been removed, which means that all cached objects will have
  new hashes.  You should clear your cache: for most users, that means
  ``rm -r ~/.astropy/cache/astroquery/`` [#418]
- In ESO and ALMA, default to *not* storing your password.  New keyword
  ``store_password=False``.  [#415]
- In ESO, fixed a form activation issue triggered in ESO ``retrieve_data()``,
  updated file download link triggered by server side change.
  More interesting, made ``username`` optional in ``login()``:
  instead, you can now configure your preferred ``username``.
  Finally, automatic login is now used by ``retrieve_data()``, if configured. [#420, #427]
- Bugfix for UKIDSS: Login now uses the correct session to retrieve the data
  [#425]
- ALMA - many new features, including selective file retrieval.  Fixes many errors that
  were unnoticed in the previous version [#433]
- ALMA - add ``help`` method and pass payload keywords on correctly.  Validate
  the payload before querying. [#438]

0.2.2 (2014-09-10)
==================

- Support direct transmission of SQL queries to the SDSS server [#410]
- Added email/text job completion alert [#407] to the CosmoSim tool [#267].
- ESO archive now supports HARPS/FEROS reprocessed data queries [#412]
- IPython notebook checker in the ESO tool is now compatible with regular
  python [#413]
- Added new tool: ALMA archive query tool. [#411]
- setup script and installation fixes

0.2 (2014-08-17)
================

- New tools: ESO, GAMA, xmatch, skyview, OEC
- Consistent with astropy 0.4 API for coordinates
- Now uses the astropy affiliated template
- Python 3 compatibility dramatically improved
- Caching added and enhanced: the default cache directory is
  ``~/.astropy/cache/astroquery/[service_name]``
- Services with separate login pages can be accessed


0.1 (2013-09-19)
================

- Initial release.  Includes features!
