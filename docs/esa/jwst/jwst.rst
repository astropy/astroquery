.. _astroquery.esa.jwst:

****************************************
ESA JWST Archive (`astroquery.esa.jwst`)
****************************************

The James Webb Space Telescope (JWST) is a collaborative project between NASA,
ESA, and the Canadian Space Agency (CSA). Although radically different in
design, and emphasizing the infrared part of the electromagnetic spectrum,
JWST is widely seen as the successor to the Hubble Space Telescope (HST).
The JWST observatory consist of a deployable 6.6 meter passively cooled
telescope optimized for infrared wavelengths, and is operated in deep
space at the anti-Sun Earth-Sun Lagrangian point (L2). It carries four
scientific instruments: a near-infrared camera (NIRCam), a
near-infrared multi-object spectrograph (NIRSpec) covering the 0.6 - 5 μm
spectral region, a near-infrared slit-less spectrograph (NIRISS), and a
combined mid-infrared camera/spectrograph (MIRI) covering 5 - 28 μm. The JWST
focal plane (see image to the right) contains apertures for the science
instruments and the Fine Guidance Sensor (FGS).

The scientific goals of the JWST mission can be sorted into four broad themes:
The birth of stars and proto-planetary systems Planetary systems and the
origins of life

* The end of the dark ages: first light and re-ionization.
* The assembly of galaxies.
* The birth of stars and proto-planetary systems.
* Planetary systems and the origins of life.

This package provides access to the metadata and datasets provided by the
European Space Agency JWST Archive using a TAP+ REST service. TAP+ is an
extension of Table Access Protocol (TAP: http://www.ivoa.net/documents/TAP/)
specified by the International Virtual Observatory Alliance (IVOA: http://www.ivoa.net).

The TAP query language is Astronomical Data Query Language
(ADQL: http://www.ivoa.net/documents/ADQL), which is similar
to Structured Query Language (SQL), widely used to query databases.

TAP provides two operation modes: Synchronous and Asynchronous:

* Synchronous: the response to the request will be generated as soon as the
  request received by the server.
  (Do not use this method for queries that generate a big amount of results.)
* Asynchronous: the server starts a job that will execute the request.
  The first response to the request is the required information (a link)
  to obtain the job status.
  Once the job is finished, the results can be retrieved.

This module can use these two modes, usinc the 'async_job=False/True' tag in different functions.

ESA JWST TAP+ server provides two access mode: public and authenticated:

* Public: this is the standard TAP access. A user can execute ADQL queries and
  upload tables to be used in a query 'on-the-fly' (these tables will be removed
  once the query is executed). The results are available to any other user and
  they will remain in the server for a limited space of time.

* Authenticated: some functionalities are restricted to authenticated users only.
  The results are saved in a private user space and they will remain in the
  server for ever (they can be removed by the user).

  * ADQL queries and results are saved in a user private area.

  * Cross-match operations: a catalog cross-match operation can be executed.
    Cross-match operations results are saved in a user private area.

  * Persistence of uploaded tables: a user can upload a table in a private space.
    These tables can be used in queries as well as in cross-matches operations.


This python module provides an Astroquery API access.


========
Examples
========

It is highly recommended checking the status of JWST TAP before executing this module. To do this:

.. doctest-remote-data::

  >>> from astroquery.esa.jwst import Jwst
  >>> Jwst.get_status_messages()

This method will retrieve the same warning messages shown in JWST Science Archive with information about
service degradation.

---------------------------
1. Non authenticated access
---------------------------

1.1. Query region
~~~~~~~~~~~~~~~~~

.. doctest-remote-data::

  >>> import astropy.units as u
  >>> from astropy.coordinates import SkyCoord
  >>> from astroquery.esa.jwst import Jwst
  >>>
  >>> coord = SkyCoord(ra=53, dec=-27, unit=(u.degree, u.degree), frame='icrs')
  >>> width = u.Quantity(1, u.deg)
  >>> height = u.Quantity(1, u.deg)
  >>> result = Jwst.query_region(coordinate=coord, width=width, height=height)
  >>> result  # doctest: +IGNORE_OUTPUT
  <Table length=2>
         dist                observationid          calibrationlevel public dataproducttype instrument_name energy_bandpassname target_name targetposition_coordinates_cval1 targetposition_coordinates_cval2                                                                     position_bounds_spoly
                                                                                                                                                          deg                              deg
       float64                   str256                  int32        bool       str64           str64             str64           str64                float64                          float64                                                                                          object
  ------------------ ------------------------------ ---------------- ------ --------------- --------------- ------------------- ----------- -------------------------------- -------------------------------- --------------------------------------------------------------------------------------------------------------------------------------------------------------
  0.5067292953603689 jw01488027001_01201_00001_nrs2                2   True           image         NIRSPEC       OPAQUE;MIRROR     UNKNOWN               53.222453933619164                -27.4665362333739 Polygon 53.20094994600003 -27.504268390999997 53.18004140700001 -27.449039869999986 53.24354427599998 -27.42825785399999 53.26482467600001 -27.484746299999987
  0.5067292953603689 jw01488027001_01201_00001_nrs2                1   True           image         NIRSPEC       OPAQUE;MIRROR     UNKNOWN               53.222453933619164                -27.4665362333739 Polygon 53.20094994600003 -27.504268390999997 53.18004140700001 -27.449039869999986 53.24354427599998 -27.42825785399999 53.26482467600001 -27.484746299999987


1.2. Cone search
~~~~~~~~~~~~~~~~

.. doctest-remote-data::

  >>> import astropy.units as u
  >>> from astropy.coordinates import SkyCoord
  >>> from astroquery.esa.jwst import Jwst
  >>>
  >>> coord = SkyCoord(ra=53, dec=-27, unit=(u.degree, u.degree), frame='icrs')
  >>> radius = u.Quantity(1.0, u.deg)
  >>> result = Jwst.cone_search(coordinate=coord, radius=radius, async_job=True)
  >>> result  # doctest: +IGNORE_OUTPUT
  <Table length=90213>
                 observationid                 calibrationlevel public dataproducttype ...          target_name           targetposition_coordinates_cval1 targetposition_coordinates_cval2                                                                                                        position_bounds_spoly
                                                                                       ...                                              deg                              deg
                     str256                         int32        bool       str64      ...             str64                          float64                          float64                                                                                                                             object
  -------------------------------------------- ---------------- ------ --------------- ... ------------------------------ -------------------------------- -------------------------------- -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
  hlsp_jems_jwst_niriss_goods-s_f430m_v1.0_drz                4   True           image ...                    GOODS-South                53.13978654458929              -27.900186014457034                                                                                     Polygon 53.143803 -27.927580000000003 53.109126 -27.903765000000032 53.13575099999998 -27.872764999999983 53.17046199999999 -27.896657000000015
  hlsp_jems_jwst_nircam_goods-s_f210m_v1.0_drz                4   True           image ...                    GOODS-South               53.143638298315224              -27.801618346014052         Polygon 53.096915 -27.824334000000007 53.122494000000025 -27.794125 53.15620000000001 -27.75595300000002 53.190561000000024 -27.778544000000018 53.16450600000003 -27.809449000000026 53.13050300000002 -27.847565000000017
  hlsp_jems_jwst_nircam_goods-s_f480m_v1.0_drz                4   True           image ...                    GOODS-South               53.143437544017296              -27.801695104861977 Polygon 53.09720799999998 -27.824191999999996 53.12226799999999 -27.794775000000005 53.15615300000003 -27.756444000000002 53.189827 -27.77872799999998 53.16437400000002 -27.808874000000024 53.130314999999996 -27.847223999999976
  hlsp_jems_jwst_nircam_goods-s_f182m_v1.0_drz                4   True           image ...                    GOODS-South                53.14363713303235               -27.80161768929551 Polygon 53.096915 -27.824334000000007 53.122494000000025 -27.79411700000001 53.15620000000001 -27.75595300000002 53.190561000000024 -27.778544000000018 53.16450600000003 -27.809449000000026 53.13050300000002 -27.847565000000017
  hlsp_jems_jwst_nircam_goods-s_f430m_v1.0_drz                4   True           image ...                    GOODS-South                53.14343758237035              -27.801708096392474  Polygon 53.09722600000002 -27.82435900000001 53.12227700000001 -27.794765999999985 53.15615300000003 -27.756444000000002 53.189827 -27.77872799999998 53.16437400000002 -27.808874000000024 53.130314999999996 -27.847223999999976
  hlsp_jems_jwst_nircam_goods-s_f460m_v1.0_drz                4   True           image ...                    GOODS-South               53.143440120302536              -27.801707446703716 Polygon 53.09723600000001 -27.824366999999995 53.12227700000001 -27.794775000000005 53.15615300000003 -27.756444000000002 53.189827 -27.77872799999998 53.16437400000002 -27.808865999999973 53.130314999999996 -27.847223999999976
  hlsp_jems_jwst_niriss_goods-s_f480m_v1.0_drz                4   True           image ...                    GOODS-South                53.13978632823965              -27.900183039523228                                                                                     Polygon 53.143803 -27.927580000000003 53.109126 -27.903765000000032 53.13575099999998 -27.872756000000024 53.17046199999999 -27.896657000000015
                                           ...              ...    ...             ... ...                            ...                              ...                              ...                                                                                                                                                                                                                                 ...
             jw09947005001_xx102_00002_nirspec               -1  False        spectrum ...       PANO_j033224m2756_hzmask                53.05677244086242              -27.991837786812724                                                                            Polygon 53.096969928409976 -28.01611837930999 53.02950963081 -28.027253231710016 53.01652523938 -27.96799365591003 53.083769109779986 -27.95602420377999
             jw07208043001_xx102_00002_nirspec               -1  False        spectrum ... panoramic_j033224m2756_id48361               52.967296645552835               -27.91594920163261                                                                    Polygon 52.96726340586999 -27.916570782990007 52.966603101559976 -27.915900119979998 52.967329862730026 -27.915327690959998 52.96799020715001 -27.91599813632998
             jw12577010001_xx108_00001_nirspec               -1  False        spectrum ...              MPT_input_P2_v0.1                53.18150426082802              -27.788964910220372                                                                      Polygon 53.14066196510001 -27.81228690420001 53.15511898750003 -27.75306849454997 53.22188803278999 -27.765402558849996 53.208412411089995 -27.824806072489967
              jw12537018001_xx104_00004_nircam               -1  False           image ...                         C26202                53.13706305814418              -27.863345866648146                                                                       Polygon 53.137841297059985 -27.864035186479992 53.13628697504 -27.864035125519973 53.13628547561999 -27.862656598209984 53.13783826878002 -27.862656105589984
             jw12577008001_xx102_00001_nirspec               -1  False        spectrum ...              MPT_input_P2_v0.1                53.18101100892586              -27.788873798924087                                                                                    Polygon 53.14016864170001 -27.81219564789 53.15462592045 -27.752977289580016 53.22139485402998 -27.76531159096 53.20791897390998 -27.82471505678
             jw07081002001_xx103_00003_nirspec               -1  False        spectrum ...              Highz-CNO-Targets                53.14603497119161               -27.78278614388954                                                                         Polygon 53.125203002309995 -27.82163964418002 53.10224041494998 -27.76456272203999 53.166341358630014 -27.743940829299994 53.19024383501 -27.80071758985997
             jw12340001001_xx107_00003_nirspec               -1  False        spectrum ...            overdensity_members                52.98086594387915              -27.792269083676928                                                                   Polygon 53.008495388439975 -27.827651680190023 52.94111846859002 -27.816712507090003 52.953009947299996 -27.757277977119983 53.02052311353999 -27.767369056419994


1.3. Query by target name
~~~~~~~~~~~~~~~~~~~~~~~~~

To provide the target coordinates based on its name and execute the query region method.
It uses three different catalogs to resolve the coordinates: SIMBAD, NED and VIZIER. An additional target
resolver is provider, ALL (which is also the default value), using all the aforementioned
catalogues in the defined order to obtain the required coordinates (using the following
element in the list if the target name cannot be resolved).

.. doctest-remote-data::

  >>> from astroquery.esa.jwst import Jwst
  >>> import astropy.units as u
  >>>
  >>> target_name = 'M1'
  >>> target_resolver = 'ALL'
  >>> radius = u.Quantity(1, u.deg)
  >>> result = Jwst.query_target(target_name=target_name, target_resolver=target_resolver, radius=radius)
  >>> result  # doctest: +IGNORE_OUTPUT
  <Table length=1395>
            observationid           calibrationlevel public dataproducttype instrument_name energy_bandpassname      target_name       targetposition_coordinates_cval1 targetposition_coordinates_cval2                                                                    position_bounds_spoly
                                                                                                                                                     deg                              deg
                str256                   int32        bool       str64           str64             str64                str64                      float64                          float64                                                                                         object
  --------------------------------- ---------------- ------ --------------- --------------- ------------------- ---------------------- -------------------------------- -------------------------------- -----------------------------------------------------------------------------------------------------------------------------------------------------------
    jw01714-o005_t003_miri_ch4-long                3   True            cube        MIRI/IFU            CH4-LONG       CRAB-NEBULA-FIL2                83.64303271855034                21.99404662161963 Polygon 83.64156476099977 21.992782729999995 83.64156476099977 21.995310508000028 83.64450067599985 21.995310508000028 83.64450067599985 21.992782729999995
   jw01714-o003_t004_miri_ch3-short                3   True            cube        MIRI/IFU           CH3-SHORT        CRAB-NEBULA-BKG                83.65960468044797               21.931696022675624   Polygon 83.65840687400018 21.93041824399999 83.65840687400018 21.932973799999985 83.66080248699998 21.932973799999985 83.66080248699998 21.93041824399999
  jw01714-c1004_t003_miri_ch1-short                3   True            cube        MIRI/IFU           CH1-SHORT       CRAB-NEBULA-FIL2                83.64319158176133                21.99416787269692 Polygon 83.64241266900012 21.993553982000016 83.64241266900012 21.994781759999984 83.64397049499992 21.994781759999984 83.64397049499992 21.993553982000016
   jw01714-o004_t002_miri_ch4-short                3   True            cube        MIRI/IFU           CH4-SHORT       CRAB-NEBULA-FIL1                83.62295758403198                22.00812603007894   Polygon 83.62148947999995 22.006764917000023 83.62148947999995 22.00948713900001 83.62442568799975 22.00948713900001 83.62442568799975 22.006764917000023
      jw01714-o002_t004_miri_f1800w                3   True           image      MIRI/IMAGE              F1800W        CRAB-NEBULA-BKG                 83.6588126140977               21.926351504834074   Polygon 83.63997091399993 21.945036449000018 83.6788455260002 21.943937831999982 83.67764936799988 21.907664414999974 83.63878465200001 21.90876275200001
   jw01714-o005_t003_miri_ch2-short                3   True            cube        MIRI/IFU           CH2-SHORT       CRAB-NEBULA-FIL2                83.64310713903527               21.994186937886155   Polygon 83.64213948799977 21.993431380999976 83.64213948799977 21.99494249200003 83.64407478999975 21.99494249200003 83.64407478999975 21.993431380999976
  jw01714-o003_t004_miri_ch4-medium                3   True            cube        MIRI/IFU          CH4-MEDIUM        CRAB-NEBULA-BKG                83.65944519557817                21.93143373136718 Polygon 83.65797788100006 21.929780953999995 83.65797788100006 21.933086509000006 83.66091250999979 21.933086509000006 83.66091250999979 21.929780953999995
                                ...              ...    ...             ...             ...                 ...                    ...                              ...                              ...                                                                                                                                                         ...
     jw11816001001_xx109_00001_miri               -1  False        spectrum        MIRI/IFU                             Crab-Nebula-K1                83.64300529853574               21.994736084514088 Polygon 83.64261143469008 21.995312661570015 83.64356249058979 21.995182077500022 83.64339915486977 21.994159494679984 83.64244810567027 21.994290105590014
  jw11816010001_xx106_00002_nirspec               -1  False        spectrum     NIRSPEC/IFU        F170LP;G235H         Crab-Nebula-D4                 83.6219308810129               22.009298019320624   Polygon 83.62189920105011 22.008676439150005 83.62126986743026 22.00934709850002 83.62196253927003 22.009919531240005 83.62259190943027 22.00924908343002
     jw11816001001_xx103_00003_miri               -1  False        spectrum        MIRI/IFU                             Crab-Nebula-K1                 83.6429201362943               21.994747927344747  Polygon 83.64252627217027 21.995324503870016 83.6434773282298 21.995193920290014 83.64331399311028 21.994171337389993 83.64236294376008 21.994301947810026
     jw11816006001_xx108_00004_miri               -1  False        spectrum        MIRI/IFU                     Crab-Nebula-Background                83.65924187725976               21.931406383779958    Polygon 83.65884818702011 21.931982960399996 83.65979881947018 21.931852378789998 83.65963555962011 21.93082979554998 83.6586849338599 21.93096040400001
  jw11816011001_xx103_00003_nirspec               -1  False        spectrum     NIRSPEC/IFU        F170LP;G235H         Crab-Nebula-A1                83.64065363300976               21.990259497183786  Polygon 83.64062195736022 21.989637915509988 83.63999270868021 21.99030857523002 83.64068528793976 21.990881007559995 83.64131457314983 21.990210559379996
  jw11816008001_xx101_00001_nirspec               -1  False        spectrum     NIRSPEC/IFU        F170LP;G235H         Crab-Nebula-B1                83.64314773390427               21.995031159483062          Polygon 83.64311605687985 21.99440957827 83.64248678721012 21.99508023813 83.64317938990992 21.99565267030998 83.64380869612005 21.994982221990007
  jw11816009001_xx103_00003_nirspec               -1  False        spectrum     NIRSPEC/IFU        F170LP;G235H         Crab-Nebula-B2                83.63352863412126               21.994953941120784            Polygon 83.63349695726022 21.994332359949993 83.63286768776007 21.995003019670023 83.6335602899402 21.995575452 83.63418959596986 21.99490500382


This method uses the same parameters as query region, but also includes the target name and the catalogue
(target resolver) to retrieve the coordinates.

.. doctest-remote-data::

  >>> from astroquery.esa.jwst import Jwst
  >>> import astropy.units as u
  >>>
  >>> target_name = 'LMC'
  >>> target_resolver = 'NED'
  >>> width = u.Quantity(1, u.deg)
  >>> height = u.Quantity(1, u.deg)
  >>> result = Jwst.query_target(target_name=target_name, target_resolver=target_resolver,
  ...                            width=width, height=height, async_job=True)
  >>> result  # doctest: +IGNORE_OUTPUT
  <Table length=41063>
           dist                      observationid             calibrationlevel public dataproducttype instrument_name energy_bandpassname target_name targetposition_coordinates_cval1 targetposition_coordinates_cval2                                                                    position_bounds_spoly
                                                                                                                                                                     deg                              deg
         float64                         str256                     int32        bool       str64           str64             str64           str64                float64                          float64                                                                                         object
  ---------------------- ------------------------------------- ---------------- ------ --------------- --------------- ------------------- ----------- -------------------------------- -------------------------------- -----------------------------------------------------------------------------------------------------------------------------------------------------------
  1.2807763824776493e-06 jw01518023001_03108_00001_mirifushort                2   True           image        MIRI/IFU           CH12-LONG    NAME-LMC                  80.894167644957               -69.75610901189543   Polygon 80.89503120600004 -69.75672262899971 80.8925404189998 -69.75649476599992 80.89330414900002 -69.7554953780002 80.89579481800017 -69.75572325800023
  1.2807763824776493e-06 jw01518023001_03108_00001_mirifushort                1   True           image        MIRI/IFU           CH12-LONG    NAME-LMC                  80.894167644957               -69.75610901189543   Polygon 80.89503120600004 -69.75672262899971 80.8925404189998 -69.75649476599992 80.89330414900002 -69.7554953780002 80.89579481800017 -69.75572325800023
  1.2810293979654214e-06    jw01518023001_03108_00001_mirimage                2   True           image      MIRI/IMAGE              F1500W    NAME-LMC                  80.894167644241                -69.7561090117718       Polygon 80.89503120600004 -69.75672262899971 80.892540418 -69.75649476599992 80.89330414800021 -69.7554953780002 80.89579481699978 -69.75572325800023
  1.2810293979654214e-06    jw01518023001_03108_00001_mirimage                1   True           image      MIRI/IMAGE              F1500W    NAME-LMC                  80.894167644241                -69.7561090117718       Polygon 80.89503120600004 -69.75672262899971 80.892540418 -69.75649476599992 80.89330414800021 -69.7554953780002 80.89579481699978 -69.75572325800023
  1.2826137646056745e-06  jw01518023001_03108_00001_mirifulong                1   True           image        MIRI/IFU           CH34-LONG    NAME-LMC                80.89416764521805               -69.75610900944068         Polygon 80.89503120600004 -69.7567226279999 80.892540418 -69.7564947650001 80.89330414800021 -69.7554953780002 80.89579481699978 -69.75572325699984
  1.2826137646056745e-06  jw01518023001_03108_00001_mirifulong                2   True           image        MIRI/IFU           CH34-LONG    NAME-LMC                80.89416764521805               -69.75610900944068         Polygon 80.89503120600004 -69.7567226279999 80.892540418 -69.7564947650001 80.89330414800021 -69.7554953780002 80.89579481699978 -69.75572325699984
  1.2934410724581988e-06 jw01518023001_03107_00001_mirifushort                2   True           image        MIRI/IFU         CH12-MEDIUM    NAME-LMC                80.89416771102887               -69.75610897741043  Polygon 80.89503127300001 -69.7567225930002 80.89254048599977 -69.75649472999983 80.89330421500017 -69.75549534299994 80.89579488399976 -69.75572322200014
                     ...                                   ...              ...    ...             ...             ...                 ...         ...                              ...                              ...                                                                                                                                                         ...
      0.4265750051094012    jw01090001001_06201_00001_mirimage                1   True           image      MIRI/IMAGE              F2550W  SMP-LMC-58                 81.2551520390941               -70.16435805966589  Polygon 81.29686033499998 -70.14711260200019 81.30591980500023 -70.17829367299973 81.21377956800012 -70.18160151199997 81.2040258179999 -70.15049733599994
      0.4265896619279505    jw01090001001_38201_00001_mirimage                1   True           image      MIRI/IMAGE               F560W  SMP-LMC-58                81.25516290359896               -70.16437225938321 Polygon 81.29687138799986 -70.14712664300018 81.30593053399993 -70.17830808600002 81.21379077699977 -70.18161594000028 81.20403638600017 -70.15051135800007
      0.4265896619279505    jw01090001001_38201_00001_mirimage                2   True           image      MIRI/IMAGE               F560W  SMP-LMC-58                81.25516290359896               -70.16437225938321 Polygon 81.29687138799986 -70.14712664300018 81.30593053399993 -70.17830808600002 81.21379077699977 -70.18161594000028 81.20403638600017 -70.15051135800007
      0.4265898346276089    jw01090001001_39201_00001_mirimage                1   True           image      MIRI/IMAGE               F560W  SMP-LMC-58                81.25516209090127               -70.16437252444791 Polygon 81.29687060799975 -70.14712691700005 81.30592969700025 -70.17830836100026 81.21378993299972 -70.18161619699991 81.20403559799986 -70.15051161199972
      0.4265898346276089    jw01090001001_39201_00001_mirimage                2   True           image      MIRI/IMAGE               F560W  SMP-LMC-58                81.25516209090127               -70.16437252444791 Polygon 81.29687060799975 -70.14712691700005 81.30592969700025 -70.17830836100026 81.21378993299972 -70.18161619699991 81.20403559799986 -70.15051161199972
      0.4732768254894247         jw04472009001_01201_00001_nis                2   True           image    NIRISS/IMAGE               F380M     UNKNOWN                81.33835678371165               -70.20429529782012       Polygon 81.39036938199988 -70.18477676099992 81.396616906 -70.22186495400021 81.28627985299987 -70.22379789700001 81.2801540589998 -70.18671650800016
      0.4732768254894247         jw04472009001_01201_00001_nis                1   True           image    NIRISS/IMAGE               F380M     UNKNOWN                81.33835678371165               -70.20429529782012       Polygon 81.39036938199988 -70.18477676099992 81.396616906 -70.22186495400021 81.28627985299987 -70.22379789700001 81.2801540589998 -70.18671650800016


1.4 Getting data products
~~~~~~~~~~~~~~~~~~~~~~~~~

To query the data products associated with a certain Observation ID

.. doctest-remote-data::

  >>> from astroquery.esa.jwst import Jwst
  >>> product_list = Jwst.get_product_list(observation_id='jw01063107001_02101_00013_nrca3')
  >>> print(product_list['filename'])  # doctest: +IGNORE_OUTPUT
                         filename
  -----------------------------------------------------
     jw01063-o107_20230701t234631_image2_00083_asn.json
               jw01063107001_02101_00013_nrca3_cal.fits
                jw01063107001_02101_00013_nrca3_cal.jpg
          jw01063107001_02101_00013_nrca3_cal_thumb.jpg
               jw01063107001_02101_00013_nrca3_i2d.fits
          jw01063107001_02101_00013_nrca3_o107_crf.fits
           jw01063107001_02101_00013_nrca3_o107_crf.jpg
     jw01063107001_02101_00013_nrca3_o107_crf_thumb.jpg
                                                    ...
     jw01063107001_02101_00013_nrca3_rateints_thumb.jpg
       jw01063107001_02101_00013_nrca3_trapsfilled.fits
        jw01063107001_02101_00013_nrca3_trapsfilled.jpg
  jw01063107001_02101_00013_nrca3_trapsfilled_thumb.jpg
             jw01063107001_02101_00013_nrca3_uncal.fits
              jw01063107001_02101_00013_nrca3_uncal.jpg
        jw01063107001_02101_00013_nrca3_uncal_thumb.jpg
                       jw01063_20230701t234631_pool.csv
  Length = 21 rows


You can filter by product type and calibration level (using a numerical
value or the option 'ALL' -set by default- that will download
all the products associated to this observation_id with the same and lower levels).

.. doctest-remote-data::

  >>> from astroquery.esa.jwst import Jwst
  >>> product_list = Jwst.get_product_list(observation_id='jw01023029001_02101_00004_mirimage', product_type='science')
  >>> print(product_list['filename'])
                      filename
  ------------------------------------------------
       jw01023029001_02101_00004_mirimage_cal.fits
       jw01023029001_02101_00004_mirimage_i2d.fits
  jw01023029001_02101_00004_mirimage_o029_crf.fits
      jw01023029001_02101_00004_mirimage_rate.fits
  jw01023029001_02101_00004_mirimage_rateints.fits
     jw01023029001_02101_00004_mirimage_uncal.fits


To download a data product, once you have the file name:

  >>> output_file = Jwst.get_product(file_name='jw01023029001_02101_00004_mirimage_uncal.fits')  # doctest: +SKIP


To download products by observation identifier, it is possible to use the get_obs_products function, with the same parameters
than get_product_list, it also supports product_type parameter as string or list. product_type as string:

.. doctest-remote-data::

  >>> from astroquery.esa.jwst import Jwst
  >>> observation_id = 'jw02739013001_02103_00001_nrcb1'
  >>> Jwst.get_obs_products(observation_id=observation_id, cal_level=2, product_type='science') # doctest: +IGNORE_OUTPUT


A list of products can be retrieved by defining product_type as list:

.. doctest-remote-data::

  >>> from astroquery.esa.jwst import Jwst
  >>> observation_id = 'jw02739013001_02103_00001_nrcb1'
  >>> results = Jwst.get_obs_products(observation_id=observation_id, cal_level=2, product_type=['science', 'preview'])

A temporary directory is created with the files and a list of the them is provided.

When more than one product is found, a tar file is retrieved. This method extracts the products.

This method is only intended to download the products with the same calibration level or below. If an upper level is requested:

.. code-block:: python

  ValueError: Requesting upper levels is not allowed

If proprietary data is requested and the user has not logged in:

.. code-block:: python

  403 Error 403:
  Private file(s) requested: MAST token required for authentication.

It is also possible to extract the products associated to an observation with upper calibration levels with get_related_observations.
Using the observation ID as input parameter, this function will retrieve the observations (IDs) that use it to create a composite observation.

.. doctest-remote-data::

  >>> from astroquery.esa.jwst import Jwst
  >>> observation_id = 'jw02739-o001_t001_nircam_clear-f444w'
  >>> results = Jwst.get_related_observations(observation_id=observation_id)
  >>> results[0:5]
  ['jw02739001001_02105_00001_nrcalong', 'jw02739001001_02105_00001_nrcblong', 'jw02739001001_02105_00002_nrcalong', 'jw02739001001_02105_00002_nrcblong', 'jw02739001001_02105_00003_nrcalong']

To query the data products associated with a certain Proposal ID and filtered by product_type.

.. doctest-remote-data::

  >>> from astroquery.esa.jwst import Jwst
  >>> observation_list = Jwst.download_files_from_program(proposal_id='1172', product_type='preview')  # doctest: +IGNORE_OUTPUT


1.5 Getting public tables
~~~~~~~~~~~~~~~~~~~~~~~~~

To load only table names (TAP+ capability)

.. doctest-remote-data::

  >>> from astroquery.esa.jwst import Jwst
  >>> tables = Jwst.get_tables(only_names=True)
  >>> tables
    ['ivoa.ObsCore', 'jwst.archive', 'jwst.artifact', 'jwst.chunk', 'jwst.harvestskipuri',
    ...
    'tap_schema.tables']


To load table names (TAP compatible)

.. doctest-remote-data::

  >>> from astroquery.esa.jwst import Jwst
  >>> tables = Jwst.get_tables()
  >>> print(*(table.name for table in tables), sep="\n")
    ivoa.ObsCore
    jwst.archive
    jwst.artifact
    jwst.chunk
    jwst.harvestskipuri
    ...
    tap_schema.schemas
    tap_schema.tables

To load only a table (TAP+ capability), the following method can be used.

.. doctest-remote-data::

  >>> from astroquery.esa.jwst import Jwst
  >>> table = Jwst.get_table('jwst.archive')

Once a table is loaded, columns can be inspected

.. doctest-remote-data::

  >>> from astroquery.esa.jwst import Jwst
  >>> table = Jwst.get_table('jwst.archive')
  >>> print(*(column.name for column in table.columns), sep="\n") # doctest: +IGNORE_OUTPUT
  calibrationlevel
  collection
  dataproducttype
  detector
  energy_bandpassname
  ...


1.6 Synchronous query
~~~~~~~~~~~~~~~~~~~~~

A synchronous query will not store the results at server side. These queries
must be used when the amount of data to be retrieve is 'small'.

There is a limit of 2000 rows. If you need more than that, you must use
asynchronous queries.

The results can be saved in memory (default) or in a file.

Query without saving results in a file:

.. doctest-remote-data::

  >>> from astroquery.esa.jwst import Jwst
  >>>
  >>> result = Jwst.launch_job("SELECT TOP 100 "
  ...       "instrument_name, proposal_id, calibrationlevel, "
  ...       "dataproducttype "
  ...       "FROM jwst.archive ORDER BY instrument_name")
  >>> result  # doctest: +IGNORE_OUTPUT
  <Table length=100>
  instrument_name proposal_id calibrationlevel dataproducttype
       str64         str64         int32            str64
  --------------- ----------- ---------------- ---------------
              FGS        1150                2           image
              FGS        1141                1           image
              FGS        1148                2           image
              FGS        1148                2           image
              FGS        1148                2           image
              FGS        1159                1           image
              FGS        1151                1           image
              ...         ...              ...             ...
              FGS        1148                1           image
              FGS        1159                1           image
              FGS        1148                1           image
              FGS        1155                2           image
              FGS        1147                3           image
              FGS        1148                2           image
              FGS        1158                1           image
              FGS        1151                2           image


Query saving results in a file:

.. doctest-remote-data::

  >>> from astroquery.esa.jwst import Jwst
  >>> job = Jwst.launch_job("SELECT TOP 100 "
  ...                       "instrument_name, proposal_id, calibrationlevel, "
  ...                       "dataproducttype "
  ...                       "FROM jwst.archive ORDER BY instrument_name",
  ...                       output_file="file.vot")


1.7 Synchronous query on an 'on-the-fly' uploaded table
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A table can be uploaded to the server in order to be used in a query.

.. doctest-skip::

  >>> from astroquery.esa.jwst import Jwst
  >>> upload_resource = 'mytable.xml.gz'
  >>> result = Jwst.launch_job(query="SELECT * from tap_upload.table_test",
  ...                     upload_resource=upload_resource,
  ...                     upload_table_name="table_test", verbose=True)
  source_id alpha delta
  --------- ----- -----
          a   1.0   2.0
          b   3.0   4.0
          c   5.0   6.0


1.8 Asynchronous query
~~~~~~~~~~~~~~~~~~~~~~

Asynchronous queries save results at server side. These queries can be accessed at any time. For anonymous users, results are kept for three days.

The results can be saved in memory (default) or in a file.

Query without saving results in a file:

.. doctest-remote-data::

  >>> from astroquery.esa.jwst import Jwst
  >>> result = Jwst.launch_job("select top 100 * from jwst.archive", async_job=True)
  >>> result
  <Table length=100>
  calibrationlevel collection dataproducttype   detector  energy_bandpassname energy_bounds_lower energy_bounds_upper energy_bounds_width instrument_name    intent   ...         target_name         targetposition_coordinates_cval1 targetposition_coordinates_cval2                 template                time_bounds_lower  time_bounds_upper time_exposure vis_cube vis_image    wave_central
                                                                                       m                   m                   m                                      ...                                           deg                              deg                                                                d                  d               s                                  µm
       int32         str64         str64         object          str64              float64             float64             float64            str64         str32    ...            str64                        float64                          float64                               object                      float64            float64         float64      bool      bool        float64
  ---------------- ---------- --------------- ----------- ------------------- ------------------- ------------------- ------------------- --------------- ----------- ... --------------------------- -------------------------------- -------------------------------- --------------------------------------- ------------------ ----------------- ------------- -------- --------- ------------------
                 2       JWST           image       NRCB2               F090W               0.795               1.005  0.2099999999999999    NIRCAM/IMAGE calibration ...                      P330-E               247.89368329393696                30.14664764798702              NIRCam Engineering Imaging  60471.51501850694  60471.5150444213         1.672    False      True 0.8999999999999999
                -1       JWST           image                           F770W  6.6000000000000005                 8.8                 2.2      MIRI/IMAGE     science ...                      GC_132                266.9847738407929                -28.2785134188332                          NIRCam Imaging                 --                --         16.65       --     False  7.700000000000001
                 2       JWST           image       NRCB1               F115W  1.0130000000000001               1.282  0.2689999999999999    NIRCAM/IMAGE     science ...             OPH-CORE-Tile-2                246.5742328427403              -24.400402708813985                          NIRCam Imaging   60040.4505228125 60040.45213829861       139.578    False      True             1.1475
                -1       JWST           image                           F200W  1.5999999999999999                 2.3  0.7000000000000001    NIRISS/IMAGE     science ...               ECLIPTIC-RA80                 124.019860712904               19.138870607305506                          NIRCam Imaging                 --                --       687.153       --     False               1.95
                 2       JWST           image       NRCA4               F090W               0.795               1.005  0.2099999999999999    NIRCAM/IMAGE     science ...                    NGC-3643                170.3375891871629                2.985130126450244                          NIRCam Imaging  61160.99709872685 61161.02642601852      2512.404    False      True 0.8999999999999999
                 1       JWST           image       NRCB2               F200W               1.755               2.226 0.47100000000000003    NIRCAM/IMAGE     science ...                    NGC-2835               139.46068692920358               -22.34831151818625 NIRCam Wide Field Slitless Spectroscopy  60801.00090825232  60801.0021509375       107.368    False     False             1.9905
                 1       JWST           image        NRS1        F290LP;G395M                2.87  5.1000000000000005  2.2300000000000004     NIRSPEC/MSA     science ...  CEERS-NIRSPEC-P10-MR-MSATA               214.91812297644287                52.84822109140906        NIRSpec MultiObject Spectroscopy  59935.26957332176   59935.281561875      1021.222    False     False              3.985
               ...        ...             ...         ...                 ...                 ...                 ...                 ...             ...         ... ...                         ...                              ...                              ...                                     ...                ...               ...           ...      ...       ...                ...
                 2       JWST           image    NRCALONG               F277W               2.416               3.127  0.7110000000000001    NIRCAM/IMAGE     science ...                     UNKNOWN                53.15896343558407              -27.887946072187304                          NIRCam Imaging  60188.20147115741 60188.26546927083      5497.226    False      True 2.7714999999999996
                 2       JWST           image    NRCALONG               F250M               2.412               2.595  0.1830000000000002    NIRCAM/IMAGE     science ...               ECLIPTIC-RA60               106.97715213200891                27.54971496885016                          NIRCam Imaging  59671.56161841319 59671.56534645833       311.366    False      True             2.5035
                 3       JWST        spectrum    MULTIPLE        F100LP;G140M                 0.7                 5.0   4.300000000000001     NIRSPEC/MSA     science ... SUSPENSE_v10_correct_coords               150.53652421222472               2.4620705377064667        NIRSpec MultiObject Spectroscopy 60311.575211550924 60311.60931983796      2917.778    False      True               2.85
                 2       JWST            cube MIRIFUSHORT         CH12-MEDIUM                5.66  10.129999999999999                4.47        MIRI/IFU     science ...                  J0937+5628                 144.408518766394                56.47750019928672     MIRI Medium Resolution Spectroscopy 60729.469680381946  60729.4761362037       557.783     True      True              7.895
                 2       JWST           image       NRCA1               F200W               1.755               2.226 0.47100000000000003    NIRCAM/IMAGE     science ...                    NGC-2835               139.45947726034913              -22.362472861173785 NIRCam Wide Field Slitless Spectroscopy  60800.84965297454 60800.85934589121       837.468    False      True             1.9905
                 1       JWST           image       NRCB1               F140M               1.331  1.4789999999999999  0.1479999999999999    NIRCAM/IMAGE     science ...                     UNKNOWN               3.6620150625204437                -30.5310785031449                          NIRCam Imaging  60629.97793209491 60629.98899196759       934.099    False     False              1.405
                 1       JWST           image    MIRIMAGE              F1000W                 9.0                11.0  1.9999999999999996      MIRI/IMAGE     science ...                    NGC-3351               160.99495827680343               11.686557085203447                            MIRI Imaging  60082.70275739583 60082.70311069444        30.525    False     False               10.0

Query saving results in a file:

.. doctest-remote-data::

  >>> from astroquery.esa.jwst import Jwst
  >>> result = Jwst.launch_job("select top 100 * from jwst.archive", output_file="archive.vot")


1.9 Asynchronous job removal
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To remove asynchronous

.. Pseudo code with ``job_id`` list ellipsis, skipping test
.. doctest-skip::

  >>> from astroquery.esa.jwst import Jwst
  >>> job = Jwst.get_job_list()[0]
  >>> job.delete()


-----------------------
2. Authenticated access
-----------------------

Authenticated users are able to access to TAP+ capabilities (shared tables, persistent jobs, etc.)
In order to authenticate a user, ``login`` method must be called. After a successful
authentication, the user will be authenticated until ``logout`` method is called.

All previous methods (``query_object``, ``cone_search``, ``get_table``, ``get_tables``, ``launch_job``) explained for
non authenticated users are applicable for authenticated ones.

The main differences are:

* Asynchronous results are kept at server side for ever (until the user decides to remove one of them).
* Users can access to shared tables.
* It is also possible to set a token after logging using ``set_token`` function.


2.1. Login/Logout
~~~~~~~~~~~~~~~~~

Using the command line:

.. doctest-remote-data::

  >>> from astroquery.esa.jwst import Jwst
  >>> Jwst.login(user='userName', password='userPassword') # doctest: +SKIP


It is possible to use a file where the credentials are stored:

*The file must containing user and password in two different lines.*

.. doctest-remote-data::

  >>> from astroquery.esa.jwst import Jwst
  >>> Jwst.login(credentials_file='my_credentials_file') # doctest: +SKIP

MAST tokens can also be used in command line functions:

.. doctest-remote-data::

  >>> from astroquery.esa.jwst import Jwst
  >>> Jwst.login(user='userName', password='userPassword', token='mastToken') # doctest: +SKIP

If the user is logged in and a MAST token has not been included or must be changed, it can be
specified using the ``set_token`` function.

.. doctest-remote-data::

  >>> from astroquery.esa.jwst import Jwst
  >>> Jwst.login(user='userName', password='userPassword') # doctest: +SKIP
  >>> Jwst.set_token(token='mastToken') # doctest: +SKIP

To perform a logout:

.. doctest-remote-data::

  >>> from astroquery.esa.jwst import Jwst
  >>> Jwst.logout() # doctest: +SKIP



2.2. Listing shared tables
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. doctest-remote-data::

  >>> from astroquery.esa.jwst import Jwst
  >>> tables = Jwst.get_tables(only_names=True)
  >>> tables
  ['ivoa.ObsCore', 'jwst.archive', 'jwst.artifact', 'jwst.chunk', 'jwst.harvestskipuri', 'jwst.main', 'jwst.moc', 'jwst.mv_archive_angular', 'jwst.observation', 'jwst.observationmember', 'jwst.part', 'jwst.plane', 'jwst.plane_vis', 'public.dual', 'tap_config.coord_sys', 'tap_config.properties', 'tap_schema.columns', 'tap_schema.key_columns', 'tap_schema.keys', 'tap_schema.schemas', 'tap_schema.tables']


Reference/API
=============

.. automodapi:: astroquery.esa.jwst
    :no-inheritance-diagram:
