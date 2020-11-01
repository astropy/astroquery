0.4.2 (unreleased)
==================

Service fixes and enhancements
------------------------------

ESASky
^^^^

- Updated ESASky module for version 3.5 of ESASky backend. [#1858]

- Added row limit parameter for map queries. [#1858]


irsa
^^^^

- Used more specific exceptions in IRSA. [#1854]


mast
^^^^

- Added ``Observations.download_file`` method to download a single file from MAST given an input
  data URI. [#1825]

esa/hubble
^^^^^^^^^^

- Module added to query eHST TAP based on a set of specific criteria and
  asynchronous jobs are now supported. [#1723]

esa/xmm_newton
^^^^^^^^^^^^^^

- new method ``get_epic_images`` is added to extract EPIC images from
  tarballs. [#1759]

esasky
^^^^^^

- Converted unittest styled tests to pytest. [#1862]


Gemini
^^^^^^

- login() support for authenticated sessions to the GOA [#1778]
- get_file() support for downloading files [#1778]
- fix syntax error in query_criteria() [#1823]


heasarc
^^^^^^^

- A ``NoResultsWarning`` is now returned when there is no matching rows were
  found in query. [#1829]


SVO FPS
^^^^^^^

- Module added to access the Spanish Virtual Observatory Filter Profile List [#1498]

Splatalogue
^^^^^^^^^^^

- The Splatalogue ID querying is now properly cached in the `astropy` cache
  directory (Issue [#423]) The scraping function has also been updated to reflect
  the Splatalogue webpage. [#1772]

- The splatalogue URL has changed to https://splatalogue.online, as the old site
  stopped functioning in September 2020 [#1817]

UKIDSS
^^^^^^

- Updated to ``UKIDSSDR11PLUS`` as the default version [#1767]

utils/tap
^^^^^^

- Converted unittest styled tests to pytest. [#1862]

alma
^^^^

- The archive query interface has been deprecated in favour of
  VirtualObservatory (VO) services such as TAP, ObsCore etc. The alma
  library has been updated accordingly. [#1689]

gaia
^^^^
- Fixed RA/dec table edit capability. [#1784]
- Changed file names handling when downloading data. [#1784]
- Improved code to handle bit data type. [#1784]
- Prepared code to handle new datalink products. [#1784]


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
  Archive. (#836)
- New tool: VO Cone Search - added module to access Virtual Observatory's
  Simple Cone Search. This is ported from ``astropy.vo``. (#859)
- New utility: TAP/TAP+ - added Table Access Protocol utility and the ESAC
  Science Data Centre (ESDC) extension. (#836)
- Fix VizieR to respect specification to return default columns only (#792)
- SIMBAD queries allow multiple configurable parameters (#820)
- Add a capability to resume partially-completed downloads for services that
  support the http 'range' keyword.  Currently applied to ESO and ALMA
  (#812,#876)
- SIMBAD now supports vectorized region queries.  A list of coordinates can be
  sent to SIMBAD simultaneously.  Users will also be warned if they submit
  queries with >10000 entries, which is the SIMBAD-recommended upper limit.
  Also, SIMBAD support has noted that any IP submitting >6 queries/second
  will be soft-banned, so we have added a warning to this effect in the
  documentation (#833)
- ALMA: Fix to always use https as the archive now requires it. (#814, #828)
- ESASky: Fix various issues related to remote API changes. (#805, #817)
- ESASky: Corrected Herschel filter indexing. (#844)
- ESO: Fix picking issue with simple ``query_survey()`` queries. (#801)
- ESO: Fix FEROS and HARPS instrument queries. (#840)
- NRAO: Change default radius from 1 degree to 1 arcmin. (#813)

0.3.4 (2016-11-21)
==================

- New tool: basic HITRAN queries support (#617)
- Fix #737, an issue with broken ALMA archive tables, via a hack (#775)
- Correct HEASARC tool, which was sending incorrect data to the server (#774)
- Fix NIST issue #714 which led to badly-parsed tables (#773)
- NRAO archive tool allows user logins and HTML-based queries (#767, #780)
- ALMA allows kwargs as input, and various small fixes (#785, #790, #782)
- XMatch caching bug fixed (#789)
- Various fixes to ESASky (#779, #772, #770)
- New tool: VAMDC-cdms interface (#658)
- Fix issue with exclude keyword in Splatalogue queries (#616)

0.3.3 (2016-10-11)
==================

- Option to toggle the display of the download bar (#734)
- ESASKY - added new module for querying the ESASKY archive (#758, #763, #765)
- Refactor Splatalogue and XMatch to use the caching (#747, #751)
- Minor data updates to Splatalogue (#746, #754, #760)
- Fix parsing bug for ``_parse_radius`` in Simbad (#753)
- Multiple fixes to ensure Windows compatibility (#709, #726)
- Minor fixes to ESO to match upstream form changes (#729)

0.3.2 (2016-06-10)
==================

- Update ESO tool to work with new web API (#696)
- Added new instruments for ESO: ``ambient_paranal`` and ``meteo_paranal``
  (#657)
- Fix problem with listed votable fields being truncated in SIMBAD (#654)
- SDSS remote API fixes (#690)
- ALMA file downloader will skip over, rather than crashing on, access denied
  (HTTP 401) errors (#687)
- Continued minor ALMA fixes (#655,#672,#687,#688)
- Splatalogue export limit bugfix (#673)
- SIMBAD flux_quality flag corrected to flux_qual (#680)
- VIZIER add a flag to return the query payload for debugging (#668)

0.3.1 (2016-01-19)
==================

- Fix bug in xmatch service that required astropy tables to have exactly 2
  columns on input (#641)
- Fix NASA ADS, which had an internal syntax error (#602)
- Bugfix in NRAO queries: telescope config was parsed incorrectly (#629)
- IBE - added new module for locating data from PTF, WISE, and 2MASS from IRSA.
  See <http://irsa.ipac.caltech.edu/ibe/> for more information about IBE and
  <http://www.ptf.caltech.edu/page/ibe> for more information about PTF survey
  data in particular. (#450)

0.3.0 (2015-10-26)
==================

- Fix ESO APEX project ID keyword (#591)
- Fix ALMA queries when accessing private data (#601)
- Allow data downloads to use the cache (#601)

0.2.6 (2015-07-23)
==================

- ESO bugfixes for handling radio buttons (#560)
- ESO: added SPHERE to list (#551)
- ESO/ALMA test cleanup (#553)
- Allow ALMA project view (#554)
- Fix Splatalogue version keyword (#557)

0.2.4 (2015-03-27)
==================

- Bugfix for ``utils.commons.send_request()``: Raise exception if error status
  is returned in the response. (#491)
- Update for ALMA Cycle 3 API change (#500)
- Added LCOGT Archive support (#537)
- Refactored LAMDA to match the standard API and added a critical density
  calculation utility (#546)

0.2.3 (2014-09-30)
==================


- AstroResponse has been removed, which means that all cached objects will have
  new hashes.  You should clear your cache: for most users, that means
  ``rm -r ~/.astropy/cache/astroquery/`` (#418)
- In ESO and ALMA, default to *not* storing your password.  New keyword
  ``store_password=False``.  (#415)
- In ESO, fixed a form activation issue triggered in ESO ``retrieve_data()``,
  updated file download link triggered by server side change.
  More interesting, made ``username`` optional in ``login()``:
  instead, you can now configure your preferred ``username``.
  Finally, automatic login is now used by ``retrieve_data()``, if configured. (#420, #427)
- Bugfix for UKIDSS: Login now uses the correct session to retrieve the data
  (#425)
- ALMA - many new features, including selective file retrieval.  Fixes many errors that
  were unnoticed in the previous version (#433)
- ALMA - add ``help`` method and pass payload keywords on correctly.  Validate
  the payload before querying. (#438)

0.2.2 (2014-09-10)
==================

- Support direct transmission of SQL queries to the SDSS server (#410)
- Added email/text job completion alert (#407) to the CosmoSim tool (#267).
- ESO archive now supports HARPS/FEROS reprocessed data queries (#412)
- IPython notebook checker in the ESO tool is now compatible with regular
  python (#413)
- Added new tool: ALMA archive query tool
  http://astroquery.readthedocs.io/en/latest/alma/alma.html
  (#411)
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
