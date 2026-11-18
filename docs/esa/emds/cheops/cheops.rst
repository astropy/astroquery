.. _astroquery.esa.emds.cheops:

************************************************************
CHEOPS Space Archive (CHEOPS) (`astroquery.esa.emds.cheops`)
************************************************************

CHEOPS (CHaracterising ExOPlanet Satellite) is ESA's first space mission dedicated
to the characterisation of known exoplanets orbiting bright, nearby stars. It performs
high-precision photometric observations of exoplanet transits to accurately measure
planetary radii and help determine their physical properties.

CHEOPS data are originally hosted by the CHEOPS Mission Archive at Geneva Observatory.
The ESA Multi-Mission Data Services (EMDS) provides access to a mirror of this archive,
allowing CHEOPS programmes, observations, visits, and data products to be queried and
downloaded through the common EMDS interface.

The typical workflow is to identify observations either directly, by sky
position, or through a CHEOPS programme. The corresponding visits and data
products can then be retrieved and downloaded.

========
Examples
========

---------------
1. Login/Logout
---------------
Authentication is available, to access to the benefits of registered users.
The Astroquery EMDS interface provides :meth:`~astroquery.esa.utils.EsaTap.login` and
:meth:`~astroquery.esa.utils.EsaTap.logout` for this purpose.

CHEOPS data accessed through this module are public and do not require authentication, but the methods are
available for consistency and are inherited from the base EMDS interface.

.. doctest-remote-data::

  >>> from astroquery.esa.emds.cheops import CheopsClass
  >>> cheops = CheopsClass()
  >>> cheops.login() # doctest: +SKIP
  >>> cheops.logout() # doctest: +SKIP

-----------------------------------
2. Get available tables and columns
-----------------------------------

The CHEOPS Astroquery module allows users to explore the data structure of the TAP by listing available
tables and their columns. This is useful for understanding what data is accessible before running ADQL queries.

.. doctest-remote-data::

  >>> from astroquery.esa.emds.cheops import CheopsClass
  >>> cheops = CheopsClass()
  >>> cheops.get_tables()
  [<VODataServiceTable name="cheops.data_product">... 9 columns ...</VODataServiceTable>, <VODataServiceTable name="cheops.data_type">... 3 columns ...</VODataServiceTable>, <VODataServiceTable name="cheops.gaia_id">... 4 columns ...</VODataServiceTable>, <VODataServiceTable name="cheops.observation_request">... 10 columns ...</VODataServiceTable>, <VODataServiceTable name="cheops.pi_tbl">... 3 columns ...</VODataServiceTable>, <VODataServiceTable name="cheops.programme">... 4 columns ...</VODataServiceTable>, <VODataServiceTable name="cheops.programme_info">... 4 columns ...</VODataServiceTable>, <VODataServiceTable name="cheops.v_data_product">... 8 columns ...</VODataServiceTable>, <VODataServiceTable name="cheops.v_doi_generation">... 13 columns ...</VODataServiceTable>, <VODataServiceTable name="cheops.visit">... 9 columns ...</VODataServiceTable>]


By default, ``get_tables()`` returns table objects with metadata. If ``only_names=True`` is provided, the method returns
only the table names as strings. This is useful when you only need to inspect or display the available tables without
accessing their full metadata.

.. doctest-remote-data::

  >>> cheops.get_tables(only_names=True)
  ['cheops.data_product', 'cheops.data_type', 'cheops.gaia_id', 'cheops.observation_request', 'cheops.pi_tbl', 'cheops.programme', 'cheops.programme_info', 'cheops.v_data_product', 'cheops.v_doi_generation', 'cheops.visit']

Once a specific table is selected using ``get_table()``, the returned object provides access to the table metadata,
including its columns.

.. doctest-remote-data::

  >>> observation_table = cheops.get_table('cheops.observation_request')
  >>> observation_table.columns
  [<BaseParam name="dec"/>, <BaseParam name="obs_cat"/>, <BaseParam name="observation_request_oid"/>, <BaseParam name="programme_oid"/>, <BaseParam name="ra"/>, <BaseParam name="request_id"/>, <BaseParam name="target_mag_cheops"/>, <BaseParam name="target_mag_gaia"/>, <BaseParam name="target_name"/>, <BaseParam name="target_temp"/>]

----------------------------
3. ADQL Queries to EMDS TAP
----------------------------

The Query TAP functionality facilitates the execution of custom Table Access Protocol (TAP)
queries within the EMDS service. Queries can be executed synchronously or asynchronously,
and results may be exported in different output formats.

When using the CHEOPS client, ADQL queries are executed against the EMDS TAP service.
Mission-specific tables are exposed under their corresponding TAP schemas (e.g. ``cheops``),
and can be queried directly using fully-qualified table names.

.. doctest-remote-data::

  >>> from astroquery.esa.emds.cheops import CheopsClass
  >>> cheops = CheopsClass()
  >>> cheops.query_tap(query=("SELECT * FROM cheops.observation_request"))  # doctest: +IGNORE_OUTPUT
  <Table length=2867>
         dec             obs_cat      observation_request_oid programme_oid        ra        request_id target_mag_cheops target_mag_gaia  target_name   target_temp
       float64            str255               int64              int64         float64        int64         float64          float64         str255        int64
  ----------------- ----------------- ----------------------- ------------- ---------------- ---------- ----------------- --------------- -------------- -----------
   28.0261988888889  flux sensitivity                       1             1      116.3289575 3000500001  1.14855874762684            1.14         Pollux        4620
          -12.45523  flux sensitivity                       2             2       161.197133 3000050005  11.9871310391184          11.979 TYC5502-1037-1        4750
   -25.797420501709  flux sensitivity                       3             2 152.281753540039 3000050001  8.98015862713381           8.973        HD88111        5330
  -9.39902611111111 reference transit                       4             3 161.707250416667 3000240001  7.83824890123086          7.8311       KELT-11b        5340
   28.0261988888889  flux sensitivity                       5             1      116.3289575 3000500001  1.13678166379684            1.14         Pollux        4620
   -25.797420501709  flux sensitivity                       6             2 152.281753540039 3000050001  8.96688817819056           8.973        HD88111        5330
  -9.39902611111111 reference transit                       7             3 161.707250416667 3000240001  7.82498192100376          7.8311       KELT-11b        5340
          -12.45523  flux sensitivity                       8             2       161.197133 3000050005  11.9747879488508          11.979 TYC5502-1037-1        4750
  -51.3628372222222 reference transit                       9             4 186.574548333333 3000460001  9.09705130039859            9.09 TESS_260647166        5720
                ...               ...                     ...           ...              ...        ...               ...             ...            ...         ...
   35.1717910766602     time critical                    2876           177  178.04655456543 1500990078  11.7662813972883          11.771        TOI1803        4830
    1.8938399553299     time critical                    2877           101 72.6605911254883 1490020017  9.89313592584892           9.898      WASP-82 b        6510
  -32.2108917236328     time critical                    2878           130 41.1885070800781 1400730060  11.2103094408661          11.212 TESS_122613513        4450
  -39.2294807434082 non time critical                    2879           181 245.890991210937 1500960003  11.0612554255802            11.0    WD 1620-391       25980
  -39.2294807434082 non time critical                    2880           183 245.890991210937 1500960035  11.0612554255802            11.0    WD 1620-391       25980
   20.1571006774902     time critical                    2881           166 61.3316307067871 2500330014  10.0640924810582           10.07      V1298 Tau        5170
  -37.5527305603027     time critical                    2882           205 178.576629638672 2500020006  10.7511591702076           10.74        TOI-776        3680
   39.7904281616211     time critical                    2883           206 217.392684936523 2500360010   8.9039319209556            8.91       TOI-2076        5280
   39.7904281616211     time critical                    2884           206 217.392684936523 2500360008   8.9039319209556            8.91       TOI-2076        5280

-------------------------------
4. Querying CHEOPS observations
-------------------------------

The ``get_observations()`` method provides direct access to the CHEOPS observation request catalogue.

To inspect the available columns that can be queried or used as filters,
``get_metadata=True`` can be used:

.. doctest-remote-data::

    >>> from astroquery.esa.emds.cheops import CheopsClass
    >>> cheops = CheopsClass()
    >>> cheops.get_observations(get_metadata=True)  # doctest: +IGNORE_OUTPUT

A subset of columns can be requested using the ``columns`` argument:

.. doctest-remote-data::

    >>> cheops.get_observations(columns=["obs_cat", "ra", "dec"])  # doctest: +IGNORE_OUTPUT

Additional constraints can be supplied as keyword arguments. The keyword
corresponds to a column in the CHEOPS observation table and its value defines
the filter.

For example, an observation request can be selected using its magnitude according to Gaia catalogue:

.. doctest-remote-data::

    >>> cheops.get_observations(target_mag_gaia=(">", 10))  # doctest: +IGNORE_OUTPUT
    Executed query:SELECT * FROM cheops.observation_request  WHERE target_mag_gaia > 10
    <Table length=1463>
           dec             obs_cat      observation_request_oid programme_oid         ra        request_id target_mag_cheops target_mag_gaia         target_name          target_temp
         float64            str255               int64              int64          float64        int64         float64          float64                str255               int64
    ----------------- ----------------- ----------------------- ------------- ----------------- ---------- ----------------- --------------- ---------------------------- -----------
            -12.45523  flux sensitivity                       2             2        161.197133 3000050005  11.9871310391184          11.979               TYC5502-1037-1        4750
            -12.45523  flux sensitivity                       8             2        161.197133 3000050005  11.9747879488508          11.979               TYC5502-1037-1        4750
            -47.15672     time critical                      18             6         153.71574 1000410004  12.1469241062368          12.138                      GJ 1132        3200
             29.79953 non time critical                      23             7        174.271266 2100070005   12.472784296066          12.509                  WD 1134+300       22000
             -21.3992 non time critical                      24             8        195.136324 1000020089  13.4492918323654          13.522                EC 12578-2107       31000
            -11.69257 non time critical                      25             8        196.596167 1000020064  13.5565483978104          13.633                   PG1303-114       31900
               9.1436 non time critical                      26             8        263.931474 1000020093  12.6192918323654          12.692                  LS IV +09 2       31000
              6.42167 non time critical                      30             8         188.34667 1000020075  13.0532918323654          13.126                  PG 1230+067       31000
             -10.4468 non time critical                      32             8        206.533229 1000020087  13.6299885078869          13.694                  PG 1343-102       28900
                  ...               ...                     ...           ...               ...        ...               ...             ...                          ...         ...
    -1.25950002670288 non time critical                    2873           204 0.550068020820618 4500250005  14.7977672635234            14.8 Gaia DR3 2449616081671057024        4500
    -1.25950002670288     time critical                    2874           204 0.550068020820618 4500250002  14.7877672635234           14.79 Gaia DR3 2449616081671057024        4500
     35.1717910766602     time critical                    2875           177   178.04655456543 1500990080  11.7662813972883          11.771                      TOI1803        4830
     35.1717910766602     time critical                    2876           177   178.04655456543 1500990078  11.7662813972883          11.771                      TOI1803        4830
    -32.2108917236328     time critical                    2878           130  41.1885070800781 1400730060  11.2103094408661          11.212               TESS_122613513        4450
    -39.2294807434082 non time critical                    2879           181  245.890991210937 1500960003  11.0612554255802            11.0                  WD 1620-391       25980
    -39.2294807434082 non time critical                    2880           183  245.890991210937 1500960035  11.0612554255802            11.0                  WD 1620-391       25980
     20.1571006774902     time critical                    2881           166  61.3316307067871 2500330014  10.0640924810582           10.07                    V1298 Tau        5170
    -37.5527305603027     time critical                    2882           205  178.576629638672 2500020006  10.7511591702076           10.74                      TOI-776        3680

These filters are converted by the EMDS query interface into the corresponding ADQL constraints.

As it can be observed in the previous examples, additional constraints can be provided
using the ``**filters`` syntax, where the keyword corresponds to an ObsCore column name
and the value defines the filter to be applied. The method translates these filters
into the corresponding ADQL constraints executed by the TAP service.

Some examples and their corresponding ADQL transformations are provided below:

+ Exact match (string):
    - ``obs_cat="flux sensitivity"`` → ``obs_cat = 'flux sensitivity'``

+ Wildcards (string):
    - ``obs_cat="flux%"`` → ``obs_cat ILIKE 'flux%'``

+ ``coordinates`` and ``radius``.

+ String list:
    - ``obs_cat=["flux sensitivity", "time critical"]`` → ``obs_cat = 'flux sensitivity' OR obs_Cat = 'time critical'``

+ Numeric comparison:
    - ``target_mag_cheops=(">", 5)`` -> ``target_mag_cheops > 5``

+ Filter by numeric interval:
    - ``target_mag_cheops=(5, 10)`` -> ``target_mag_cheops >= 5 AND target_mag_cheops <= 10``

+ Combined filters: Multiple keyword filters are combined with ``AND``.
    - ``obs_cat="flux sensitivity", target_mag_cheops=("<", 12)`` → ``obs_cat = 'flux sensitivity' AND target_mag_cheops < 12>``

----------------
5. Cone searches
----------------

CHEOPS observations can be selected by sky position using either coordinates
or a target name. A coordinate-based cone search can be performed by supplying coordinates and
a search radius:

.. doctest-remote-data::

    >>> cheops.get_observations(coordinates="81.1238 17.4175", radius=0.1)  # doctest: +IGNORE_OUTPUT

The coordinates are converted into an ADQL cone-search condition using the ``ra`` and ``dec`` columns of the CHEOPS observation catalogue.

A target name can also be supplied. The target is first resolved into sky coordinates and the resulting position is used for the cone search:

.. doctest-remote-data::

    >>> cheops.get_observations(target_name="M31", radius=0.1)  # doctest: +IGNORE_OUTPUT

The ``target_name`` and ``coordinates`` arguments are mutually exclusive and
must not be provided together.

-----------------------------
6. Querying CHEOPS programmes
-----------------------------

CHEOPS observations can be associated with observing programmes. The
``get_programmes()`` method provides access to programme information using
one of three selectors:

* Programme key
* Programme title
* Principal investigator (PI) name

Only one selector can be provided in each call.

A programme can be retrieved using its programme key:

.. doctest-remote-data::

    >>> cheops.get_programmes(programme_key="PR300050")  # doctest: +IGNORE_OUTPUT

A programme can also be searched by title:

.. doctest-remote-data::

    >>> cheops.get_programmes(title="very bright star")  # doctest: +IGNORE_OUTPUT

Title searches are performed as partial matches. The supplied title is internally surrounded by ``%`` wildcard characters,
to include the titles containing the defined text.

Programmes can also be searched using the name of their principal investigator:

.. doctest-remote-data::

    >>> cheops.get_programmes(pi_name="Smith")  # doctest: +IGNORE_OUTPUT

The returned programme information includes the programme key, title and
abstract, together with the PI name and the internal programme identifier
needed to associate programmes with observations.

----------------------------------------
7. Getting observations from a programme
----------------------------------------

Once a programme has been identified, its observations can be retrieved
directly with ``get_observations_from_programme()``.

Using a programme key:

.. doctest-remote-data::

    >>> observations = cheops.get_observations_from_programme(programme_key="PR300050")  # doctest: +IGNORE_OUTPUT

The programme can alternatively be identified from its title:

.. doctest-remote-data::

    >>> observations = cheops.get_observations_from_programme(title="very bright star")  # doctest: +IGNORE_OUTPUT

or from its PI:

.. doctest-remote-data::

    >>> observations = cheops.get_observations_from_programme(pi_name="Smith")  # doctest: +IGNORE_OUTPUT

Internally, the method first identifies the corresponding programme and then
uses its programme identifier to query the CHEOPS observation catalogue.

-----------------------------------
8. Getting visits from observations
-----------------------------------

CHEOPS observations are associated with their correspondent visits. The
``get_visit_from_observation()`` method allows the visits associated with an
observation to be retrieved.

If an observation has already been obtained through ``get_observations()``,
the corresponding table row can be supplied directly:

.. doctest-remote-data::

    >>> observations = cheops.get_observations(observation_request_oid=1) # doctest: +IGNORE_OUTPUT
    >>> visit = cheops.get_visit_from_observation(observations[0])  # doctest: +IGNORE_OUTPUT

Alternatively, the value of the ``observation_request_oid`` column can be
provided directly:

.. doctest-remote-data::

    >>> visit = cheops.get_visit_from_observation(observation=1)  # doctest: +SKIP

The method accepts either an Astropy ``Row`` representing an observation or a
number containing the observation request identifier.

-------------------------------
9. Getting CHEOPS data products
-------------------------------

CHEOPS data products can be retrieved using several different starting points:

* Target name or coordinates
* Observation
* Visit
* Programme

These methods return tables containing the data products corresponding to the
specified selection.

Product queries can optionally be restricted by processing level using the
``level`` parameter. Supported values include ``EXT``, ``L0.5``, ``L1`` and
``L2``.

----------------------------------------------
10. Get products by target name or coordinates
----------------------------------------------

To obtain the products associated with observations around a target:

.. doctest-remote-data::

    >>> products = cheops.get_products_from_targets_or_coordinates(target_name="Pollux",radius=1.0)  # doctest: +IGNORE_OUTPUT

The same operation can be performed with explicit coordinates:

.. doctest-remote-data::

    >>> products = cheops.get_products_from_targets_or_coordinates(coordinates="116.3289575 28.0261988888889", radius=0.1)  # doctest: +IGNORE_OUTPUT

Products can also be restricted by calibration level:

.. doctest-remote-data::

    >>> products = cheops.get_products_from_targets_or_coordinates(coordinates="116.3289575 28.0261988888889", radius=0.1, level="L2")  # doctest: +IGNORE_OUTPUT

The method first retrieves the matching observations, identifies their visits,
and then returns the products associated with those visits. Duplicate visits
are processed only once.

------------------------------------
11. Get products from an observation
------------------------------------

Products associated with a particular observation can be obtained directly:

.. doctest-remote-data::

    >>> observations = cheops.get_observations(observation_request_oid=1) # doctest: +IGNORE_OUTPUT
    >>> products = cheops.get_products_from_observation(observations[0])  # doctest: +IGNORE_OUTPUT

A processing level can also be specified:

.. doctest-remote-data::

    >>> products = cheops.get_products_from_observation(observations[0], level="L0.5")  # doctest: +IGNORE_OUTPUT

The value of ``observation_request_oid`` may also be supplied directly as an integer.

-----------------------------
12. Get products from a visit
-----------------------------

If a CHEOPS visit is already known or provided through the previous methods, its products can be retrieved using
``get_products_from_visit()``.

An Astropy row returned from a visit query can be supplied:

.. doctest-remote-data::

    >>> observations = cheops.get_observations(observation_request_oid=1) # doctest: +IGNORE_OUTPUT
    >>> visit = cheops.get_visit_from_observation(observations[0]) # doctest: +IGNORE_OUTPUT
    >>> products = cheops.get_products_from_visit(visit[0])  # doctest: +IGNORE_OUTPUT

Alternatively, a visit identifier can be used directly:

.. doctest-remote-data::

    >>> products = cheops.get_products_from_visit(visit=250033000901, level="L2")  # doctest: +SKIP

---------------------------------
13. Get products from a programme
---------------------------------

All products corresponding to observations from a CHEOPS programme can be
retrieved using ``get_products_from_programme()``.

For example:

.. doctest-remote-data::

    >>> products = cheops.get_products_from_programme(programme_key="PR300050")  # doctest: +IGNORE_OUTPUT

The product selection can also be restricted by processing level:

.. doctest-remote-data::

    >>> products = cheops.get_products_from_programme(programme_key="PR300050", level="L2")  # doctest: +IGNORE_OUTPUT

The programme can also be selected using ``title`` or ``pi_name``.

-----------------------------
14. Download a single product
-----------------------------

Once a data product has been identified, it can be downloaded using its
filename with ``download_product()``.

For example:

.. doctest-remote-data::

    >>> products = cheops.get_products_from_programme(programme_key="PR300050", level="L2") # doctest: +IGNORE_OUTPUT
    >>> filename = products["filename"][0] # doctest: +IGNORE_OUTPUT
    >>> cheops.download_product(filename=filename)  # doctest: +SKIP

By default, the original archive filename is used. A different local filename
can be specified with ``output_filename``:

.. doctest-remote-data::

    >>> cheops.download_product(filename=filename, output_filename="cheops_product.fits")  # doctest: +SKIP

A destination directory can also be provided:

.. doctest-remote-data::

    >>> cheops.download_product(filename=filename, path="cheops_data")  # doctest: +SKIP

If the requested directory does not exist, it is created automatically.

---------------------------------------
15. Download products from a sky region
---------------------------------------

All products associated with observations in a sky region can be downloaded
using ``download_products_from_targets_or_coordinates()``.

For example, using a target name:

.. doctest-remote-data::

    >>> cheops.download_products_from_targets_or_coordinates(target_name="M31", radius=1.0, level="L2", path="cheops_data")  # doctest: +SKIP

or explicit coordinates:

.. doctest-remote-data::

    >>> cheops.download_products_from_targets_or_coordinates(coordinates="116.3289575 28.0261988888889", radius=0.1, level="L2", path="cheops_data")  # doctest: +SKIP

The method identifies the corresponding observations and visits, retrieves the
product list, and downloads each product into the specified directory.

-----------------------------------------
16. Download products from an observation
-----------------------------------------

All products associated with an observation can be downloaded with
``download_products_from_observation()``.

For example:

.. doctest-remote-data::

    >>> observations = cheops.get_observations(coordinates='116.3289575 28.0261988888889') # doctest: +IGNORE_OUTPUT
    >>> cheops.download_products_from_observation(observations[0], level="L2", path="cheops_data")  # doctest: +SKIP

The ``observation_request_oid`` value can also be supplied instead of the
Astropy table row.

----------------------------------
17. Download products from a visit
----------------------------------

Products belonging to an individual visit can be downloaded using
``download_products_from_visit()``:

.. doctest-remote-data::

    >>> observations = cheops.get_observations(observation_request_oid=1) # doctest: +IGNORE_OUTPUT
    >>> visit = cheops.get_visit_from_observation(observations[0]) # doctest: +IGNORE_OUTPUT
    >>> cheops.download_products_from_visit(visit[0], level="L2", path="cheops_data")  # doctest: +SKIP

A visit identifier can also be supplied directly.

--------------------------------------
18. Download products from a programme
--------------------------------------

All products associated with a CHEOPS programme can be downloaded with
``download_products_from_programme()``.

For example:

.. doctest-remote-data::

    >>> cheops.download_products_from_programme(programme_key="PR010023", level="L2", path="cheops_data")  # doctest: +SKIP

The programme can alternatively be located using its title:

.. doctest-remote-data::

    >>> cheops.download_products_from_programme(title="very bright star", level="L2", path="cheops_data")  # doctest: +SKIP

or its PI name:

.. doctest-remote-data::

    >>> cheops.download_products_from_programme(pi_name="Smith", level="L2", path="cheops_data")  # doctest: +SKIP

For bulk downloads, the destination directory is created automatically when
it does not already exist.


Reference/API
=============

.. automodapi:: astroquery.esa.emds.cheops
    :no-inheritance-diagram:
    :inherited-members: