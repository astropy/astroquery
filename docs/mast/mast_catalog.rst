

***************
Catalog Queries
***************

The Catalogs class provides access to a subset of the astronomical catalogs stored at MAST.
The catalogs currently available through this interface are:

- The Hubble Source Catalog (HSC)
- The GALEX Catalog (V2 and V3)
- The Gaia (DR1 and DR2) and TGAS Catalogs
- The TESS Input Catalog (TIC)
- The TESS Candidate Target List (CTL)
- The Disk Detective Catalog
- The PanSTARRS Catalog (DR1 and DR2)
- The All-Sky PLATO Input Catalog (DR1)

Catalog Positional Queries
==========================

Positional queries can be based on a sky position or a target name.
The returned fields vary by catalog, find the field documentation for specific catalogs
`here <https://mast.stsci.edu/api/v0/pages.html>`__.
If no catalog is specified, the Hubble Source Catalog will be queried.

 
.. doctest-remote-data::

   >>> from astroquery.mast import Catalogs
   ...
   >>> catalog_data = Catalogs.query_region("158.47924 -7.30962", catalog="Galex")
   >>> print(catalog_data[:10])  # doctest: +IGNORE_OUTPUT
    distance_arcmin          objID        survey ... fuv_flux_aper_7 fuv_artifact
   ------------------ ------------------- ------ ... --------------- ------------
   0.3493802506329695 6382034098673685038    AIS ...     0.047751952            0
   0.7615422488595471 6382034098672634783    AIS ...              --            0
   0.9243329366166956 6382034098672634656    AIS ...              --            0
    1.162615739258038 6382034098672634662    AIS ...              --            0
   1.2670891287503308 6382034098672634735    AIS ...              --            0
    1.492173395497916 6382034098674731780    AIS ...    0.0611195639            0
   1.6051235757244107 6382034098672634645    AIS ...              --            0
    1.705418541388336 6382034098672634716    AIS ...              --            0
   1.7463721100195875 6382034098672634619    AIS ...              --            0
   1.7524423152919317 6382034098672634846    AIS ...              --            0


Some catalogs have a maximum number of results they will return.
If a query results in this maximum number of results a warning will be displayed to alert
the user that they might be getting a subset of the true result set.

.. doctest-remote-data::

   >>> from astroquery.mast import Catalogs
   ...
   >>> catalog_data = Catalogs.query_region("322.49324 12.16683", 
   ...                                      catalog="HSC", 
   ...                                      magtype=2)  # doctest: +SHOW_WARNINGS
   InputWarning: Coordinate string is being interpreted as an ICRS coordinate provided in degrees.
   MaxResultsWarning: Maximum catalog results returned, may not include all sources within radius.
   >>> print(catalog_data[:10])
    MatchID        Distance            MatchRA       ... W3_F160W_MAD W3_F160W_N
   --------- -------------------- ------------------ ... ------------ ----------
    50180585 0.003984902849540913  322.4931746094701 ...          nan          0
     8150896 0.006357935819940561 322.49334740450234 ...          nan          0
   100906349  0.00808206428937523  322.4932839715549 ...          nan          0
   105434103 0.011947078376104195 322.49324000530777 ...          nan          0
   103116183  0.01274757103013683  322.4934207202404 ...          nan          0
    45593349 0.013026569623011767  322.4933878707698 ...          nan          0
   103700905  0.01306760650244682  322.4932769229944 ...          nan          0
   102470085 0.014611879195009472 322.49311034430366 ...          nan          0
    93722307  0.01476438046135455 322.49348351134466 ...          nan          0
    24781941 0.015234351867433582 322.49300148743345 ...          nan          0

Radius is an optional parameter and the default is 0.2 degrees.

.. doctest-remote-data::

   >>> from astroquery.mast import Catalogs
   ...
   >>> catalog_data = Catalogs.query_object("M10", radius=.02, catalog="TIC")
   >>> print(catalog_data[:10])   # doctest: +IGNORE_OUTPUT
       ID            ra               dec        ... wdflag     dstArcSec
   ---------- ---------------- ----------------- ... ------ ------------------
    510188144 254.287449269816 -4.09954224264168 ...     -1 0.7650443624931581
    510188143  254.28717785824 -4.09908635292493 ...     -1 1.3400566638148848
    189844423 254.287799703996  -4.0994998249247 ...      0 1.3644407138867785
   1305764031 254.287147439535 -4.09866105132406 ...     -1  2.656905409847388
   1305763882 254.286696117371 -4.09925522448626 ...     -1 2.7561196688252894
    510188145 254.287431890823 -4.10017293344746 ...     -1  3.036238557555728
   1305763844 254.286675148545 -4.09971617257086 ...      0 3.1424781549696217
   1305764030 254.287249718516 -4.09841883152995 ...     -1  3.365991083435227
   1305764097 254.287599269103 -4.09837925361712 ...     -1    3.4590276863989
   1305764215  254.28820865799 -4.09859677020253 ...     -1 3.7675526728257034


The Hubble Source Catalog, the Gaia Catalog, and the PanSTARRS Catalog have multiple versions.
An optional version parameter allows you to select which version you want, the default is the highest version.

.. doctest-remote-data::

   >>> catalog_data = Catalogs.query_region("158.47924 -7.30962", radius=0.1,
   ...                                       catalog="Gaia", version=2)
   >>> print("Number of results:",len(catalog_data))
   Number of results: 111
   >>> print(catalog_data[:4])
       solution_id             designation          ...      distance
   ------------------- ---------------------------- ... ------------------
   1635721458409799680 Gaia DR2 3774902350511581696 ... 0.6326770410972467
   1635721458409799680 Gaia DR2 3774901427093274112 ... 0.8440033390947586
   1635721458409799680 Gaia DR2 3774902148648277248 ... 0.9199206487344911
   1635721458409799680 Gaia DR2 3774902453590798208 ... 1.3578181104319944

The PanSTARRS Catalog has multiple data releases as well as multiple queryable tables.
An optional data release parameter allows you to select which data release is desired, with the default being the latest version (dr2).
The table to query is a required parameter.

.. doctest-remote-data::

   >>> catalog_data = Catalogs.query_region("158.47924 -7.30962", 
   ...                                      radius=0.1,
   ...                                      catalog="Panstarrs", 
   ...                                      data_release="dr1", 
   ...                                      table="mean")
   >>> print("Number of results:",len(catalog_data))
   Number of results: 7007
   >>> print(catalog_data[:10])     # doctest: +IGNORE_OUTPUT
            ObjName           objAltName1 ... yFlags       distance
   -------------------------- ----------- ... ------ --------------------
   PSO J103359.653-071622.382        -999 ...  16416  0.04140441098310487
   PSO J103359.605-071622.873        -999 ...      0  0.04121935961328582
   PSO J103359.691-071640.232        -999 ...      0  0.03718729257758985
   PSO J103400.268-071639.192        -999 ...      0  0.03870112803784765
   PSO J103400.073-071637.358        -999 ...      0  0.03867536827891155
   PSO J103359.789-071632.606        -999 ...      0  0.03921557769883566
   PSO J103359.192-071654.790        -999 ...      0  0.03266232705300051
   PSO J103359.959-071655.155        -999 ...      0 0.034361022297827955
   PSO J103359.847-071655.610        -999 ...      0 0.033986082329893995
   PSO J103400.586-071656.646        -999 ...      0 0.035645179491121386

Catalog Criteria Queries
========================

The TESS Input Catalog (TIC), Disk Detective Catalog, and PanSTARRS Catalog can also be queried based on non-positional criteria.

.. doctest-remote-data::

   >>> from astroquery.mast import Catalogs
   ...
   >>> catalog_data = Catalogs.query_criteria(catalog="Tic",Bmag=[30,50],objType="STAR")
   >>> print(catalog_data)  # doctest: +IGNORE_OUTPUT
       ID    version  HIP TYC ...     e_Dec_orig     raddflag wdflag   objID
   --------- -------- --- --- ... ------------------ -------- ------ ----------
   125413929 20190415  --  -- ...  0.293682765259495        1      0  579825059
   261459129 20190415  --  -- ...  0.200397148604244        1      0 1701625107
    64575709 20190415  --  -- ...   0.21969663115091        1      0  595775997
    94322581 20190415  --  -- ...  0.205286802302475        1      0  606092549
   125414201 20190415  --  -- ...   0.22398993783274        1      0  579825329
   463721073 20190415  --  -- ...  0.489828592248652       -1      1  710312391
    81609218 20190415  --  -- ...  0.146788572369267        1      0  630541794
   282024596 20190415  --  -- ...  0.548806522539047        1      0  573765450
    23868624 20190415  --  -- ...            355.949       --      0  916384285
   282391528 20190415  --  -- ...   0.47766300834538        0      0  574723760
   123585000 20190415  --  -- ...  0.618316068787371        0      0  574511442
   260216294 20190415  --  -- ...  0.187170498094167        1      0  683390717
   406300991 20190415  --  -- ... 0.0518318978617112        0      0 1411465651


.. doctest-remote-data::

   >>> from astroquery.mast import Catalogs
   ...
   >>> catalog_data = Catalogs.query_criteria(catalog="Ctl",
   ...                                        objectname='M101', 
   ...                                        radius=1, 
   ...                                        Tmag=[10.75,11])
   >>> print(catalog_data)
       ID    version  HIP     TYC      ... raddflag wdflag   objID
   --------- -------- --- ------------ ... -------- ------ ---------
   233458861 20190415  -- 3852-01407-1 ...        1      0 150390757
   441662028 20190415  -- 3855-00941-1 ...        1      0 150395533
   441658008 20190415  -- 3852-00116-1 ...        1      0 150246361
   441639577 20190415  -- 3852-00429-1 ...        1      0 150070672
   441658179 20190415  -- 3855-00816-1 ...        1      0 150246482
   154258521 20190415  -- 3852-01403-1 ...        1      0 150281963
   441659970 20190415  -- 3852-00505-1 ...        1      0 150296707
   441660006 20190415  -- 3852-00341-1 ...        1      0 150296738


.. doctest-remote-data::

   >>> from astroquery.mast import Catalogs
   ...
   >>> catalog_data = Catalogs.query_criteria(catalog="DiskDetective",
   ...                                        objectname="M10",
   ...                                        radius=2,
   ...                                        state="complete")
   >>> print(catalog_data)      # doctest: +IGNORE_OUTPUT
       designation     ...                    ZooniverseURL
   ------------------- ... ----------------------------------------------------
   J165628.40-054630.8 ... https://talk.diskdetective.org/#/subjects/AWI0005cka
   J165748.96-054915.4 ... https://talk.diskdetective.org/#/subjects/AWI0005ckd
   J165427.11-022700.4 ... https://talk.diskdetective.org/#/subjects/AWI0005ck5
   J165749.79-040315.1 ... https://talk.diskdetective.org/#/subjects/AWI0005cke
   J165327.01-042546.2 ... https://talk.diskdetective.org/#/subjects/AWI0005ck3
   J165949.90-054300.7 ... https://talk.diskdetective.org/#/subjects/AWI0005ckk
   J170314.11-035210.4 ... https://talk.diskdetective.org/#/subjects/AWI0005ckv


The `~astroquery.mast.CatalogsClass.query_criteria` function requires at least one non-positional parameter.
These parameters are the column names listed in the `field descriptions <https://mast.stsci.edu/api/v0/pages.html>`__
of the catalog being queried. They do not include objectname, coordinates, or radius. Running a query with only positional
parameters will result in an error.

.. doctest-remote-data::

   >>> from astroquery.mast import Catalogs
   ...
   >>> catalog_data = Catalogs.query_criteria(catalog="Tic",
   ...                                        objectname='M101', radius=1)
   Traceback (most recent call last):
   ...
   astroquery.exceptions.InvalidQueryError: At least one non-positional criterion must be supplied.


The PanSTARRS catalog also accepts additional parameters to allow for query refinement. These options include column selection,
sorting, column criteria, page size and page number. Additional information on PanSTARRS queries may be found
`here <https://catalogs.mast.stsci.edu/docs/panstarrs.html>`__.

Columns returned from the query may be submitted with the columns parameter as a list of column names.

The query may be sorted  with the sort_by parameter composed of either a single column name (to sort ascending),
or a list of multiple column names and/or tuples of direction and column name (ASC/DESC, column name).

To filter the query, criteria per column name are accepted. The 'AND' operation is performed between all
column name criteria, and the 'OR' operation is performed within column name criteria. Per each column name
parameter, criteria may consist of either a value or a list. The list may consist of a mix of values and
tuples of criteria decorator (min, gte, gt, max, lte, lt, like, contains) and value.

.. doctest-remote-data::

   >>> catalog_data = Catalogs.query_criteria(coordinates="5.97754 32.53617", 
   ...                                        radius=0.01,
   ...                                        catalog="PANSTARRS", 
   ...                                        table="mean", 
   ...                                        data_release="dr2",
   ...                                        nStackDetections=[("gte", 2)],
   ...                                        columns=["objName", "objID", "nStackDetections", "distance"],
   ...                                        sort_by=[("desc", "distance")], 
   ...                                        pagesize=15)
   >>> print(catalog_data[:10])   # doctest: +IGNORE_OUTPUT
          objName              objID        nStackDetections        distance
   --------------------- ------------------ ---------------- ---------------------
   PSO J005.9812+32.5270 147030059812483022                5  0.009651200148871086
   PSO J005.9726+32.5278 147030059727583992                2    0.0093857181370567
   PSO J005.9787+32.5453 147050059787164914                4  0.009179045509852305
   PSO J005.9722+32.5418 147050059721440704                4  0.007171813230776031
   PSO J005.9857+32.5377 147040059855825725                4  0.007058815429178634
   PSO J005.9810+32.5424 147050059809651427                2  0.006835678269917365
   PSO J005.9697+32.5368 147040059697224794                2  0.006654002479439699
   PSO J005.9712+32.5330 147040059711340087                4  0.006212461367287632
   PSO J005.9747+32.5413 147050059747400181                5 0.0056515210592035965
   PSO J005.9775+32.5314 147030059774678271                3  0.004739286624336443


Hubble Source Catalog (HSC) specific queries
============================================

Given an HSC Match ID, return all catalog results.

.. doctest-remote-data::

   >>> from astroquery.mast import Catalogs
   ...
   >>> catalog_data = Catalogs.query_object("M10", 
   ...                                      radius=.001,
   ...                                      catalog="HSC", 
   ...                                      magtype=1)
   >>> matchid = catalog_data[0]["MatchID"]
   >>> print(matchid)
   7542452
   >>> matches = Catalogs.query_hsc_matchid(matchid)
   >>> print(matches)
     CatID   MatchID ...                       cd_matrix                       
   --------- ------- ... ------------------------------------------------------
   419094794 7542452 ...   -1.10056e-005 5.65193e-010 5.65193e-010 1.10056e-005
   419094795 7542452 ...   -1.10056e-005 5.65193e-010 5.65193e-010 1.10056e-005
   401289578 7542452 ...   -1.10056e-005 1.56577e-009 1.56577e-009 1.10056e-005
   401289577 7542452 ...   -1.10056e-005 1.56577e-009 1.56577e-009 1.10056e-005
   257194049 7542452 ... -1.38889e-005 -5.26157e-010 -5.26157e-010 1.38889e-005
   257438887 7542452 ... -1.38889e-005 -5.26157e-010 -5.26157e-010 1.38889e-005


HSC spectra accessed through this class as well. `~astroquery.mast.CatalogsClass.get_hsc_spectra`
does not take any arguments, and simply loads all HSC spectra.

.. doctest-remote-data::

   >>> from astroquery.mast import Catalogs
   ...
   >>> all_spectra = Catalogs.get_hsc_spectra()
   >>> print(all_spectra[:10])
   ObjID                 DatasetName                  MatchID  ... PropID HSCMatch
   ----- -------------------------------------------- -------- ... ------ --------
   20010 HAG_J072655.67+691648.9_J8HPAXAEQ_V01.SPEC1D 19657846 ...   9482        Y
   20011 HAG_J072655.69+691648.9_J8HPAOZMQ_V01.SPEC1D 19657846 ...   9482        Y
   20012 HAG_J072655.76+691729.7_J8HPAOZMQ_V01.SPEC1D 19659745 ...   9482        Y
   20013 HAG_J072655.82+691620.0_J8HPAOZMQ_V01.SPEC1D 19659417 ...   9482        Y
   20014 HAG_J072656.34+691704.7_J8HPAXAEQ_V01.SPEC1D 19660230 ...   9482        Y
   20015 HAG_J072656.36+691704.7_J8HPAOZMQ_V01.SPEC1D 19660230 ...   9482        Y
   20016 HAG_J072656.36+691744.9_J8HPAOZMQ_V01.SPEC1D 19658847 ...   9482        Y
   20017 HAG_J072656.37+691630.2_J8HPAXAEQ_V01.SPEC1D 19660827 ...   9482        Y
   20018 HAG_J072656.39+691630.2_J8HPAOZMQ_V01.SPEC1D 19660827 ...   9482        Y
   20019 HAG_J072656.41+691734.9_J8HPAOZMQ_V01.SPEC1D 19656620 ...   9482        Y


Individual or ranges of spectra can be downloaded using the
`~astroquery.mast.CatalogsClass.download_hsc_spectra` function.

.. doctest-remote-data::

   >>> from astroquery.mast import Catalogs
   ...
   >>> all_spectra = Catalogs.get_hsc_spectra()
   >>> manifest = Catalogs.download_hsc_spectra(all_spectra[100:104])   # doctest: +IGNORE_OUTPUT
   Downloading URL https://hla.stsci.edu/cgi-bin/ecfproxy?file_id=HAG_J072704.61+691530.3_J8HPAOZMQ_V01.SPEC1D.fits to ./mastDownload/HSC/HAG_J072704.61+691530.3_J8HPAOZMQ_V01.SPEC1D.fits ... [Done]
   Downloading URL https://hla.stsci.edu/cgi-bin/ecfproxy?file_id=HAG_J072704.68+691535.9_J8HPAOZMQ_V01.SPEC1D.fits to ./mastDownload/HSC/HAG_J072704.68+691535.9_J8HPAOZMQ_V01.SPEC1D.fits ... [Done]
   Downloading URL https://hla.stsci.edu/cgi-bin/ecfproxy?file_id=HAG_J072704.70+691530.2_J8HPAOZMQ_V01.SPEC1D.fits to ./mastDownload/HSC/HAG_J072704.70+691530.2_J8HPAOZMQ_V01.SPEC1D.fits ... [Done]
   Downloading URL https://hla.stsci.edu/cgi-bin/ecfproxy?file_id=HAG_J072704.73+691808.0_J8HPAOZMQ_V01.SPEC1D.fits to ./mastDownload/HSC/HAG_J072704.73+691808.0_J8HPAOZMQ_V01.SPEC1D.fits ... [Done]
   ...
   >>> print(manifest)     # doctest: +IGNORE_OUTPUT
                                Local Path                              ... URL
   -------------------------------------------------------------------- ... ----
   ./mastDownload/HSC/HAG_J072704.61+691530.3_J8HPAOZMQ_V01.SPEC1D.fits ... None
   ./mastDownload/HSC/HAG_J072704.68+691535.9_J8HPAOZMQ_V01.SPEC1D.fits ... None
   ./mastDownload/HSC/HAG_J072704.70+691530.2_J8HPAOZMQ_V01.SPEC1D.fits ... None
   ./mastDownload/HSC/HAG_J072704.73+691808.0_J8HPAOZMQ_V01.SPEC1D.fits ... None