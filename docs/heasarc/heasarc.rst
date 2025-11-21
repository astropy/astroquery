.. _astroquery.heasarc:

**************************************
HEASARC Queries (`astroquery.heasarc`)
**************************************

Getting started
===============

This is a python interface for querying the
`HEASARC <https://heasarc.gsfc.nasa.gov/>`__
archive web service.

The main interface for the Heasarc services ``heasarc.Heasarc`` uses
Virtual Observatory protocols, which offer powerful archive search options.

- :ref:`Heasarc Main Interface`.

.. _Heasarc Main Interface:

Heasarc Main Interface
=======================

Query a Catalog
---------------
The basic use case is one where we want to query a catalog from some position in the sky.
In this example, we query the NuSTAR master catalog ``numaster`` for all observations
of the AGN ``NGC 3783``. We use `~astropy.coordinates.SkyCoord` to obtain the coordinates
and then pass them to `~astroquery.heasarc.HeasarcClass.query_region`. In the following, we
also select only columns with ``time > 0``. Zero values are typically used for observations
that have been approved but not observed.

.. doctest-remote-data::

    >>> from astroquery.heasarc import Heasarc
    >>> from astropy.coordinates import SkyCoord
    >>> pos = SkyCoord.from_name('ngc 3783')
    >>> tab = Heasarc.query_region(pos, catalog='numaster')
    >>> tab = tab[tab['time'] > 0]
    >>> tab.sort('time')
    >>> tab['name', 'obsid', 'ra', 'dec'][:3].pprint()
    name      obsid       ra      dec
                        deg      deg
    -------- ----------- -------- --------
    NGC_3783 60101110002 174.7236 -37.7230
    NGC_3783 60101110004 174.7253 -37.7277
    NGC_3783 80202006002 174.7838 -37.7277

To query a region around some position, specifying the search radius,
we use `~astropy.units.Quantity`:

.. doctest-remote-data::

    >>> from astroquery.heasarc import Heasarc
    >>> from astropy.coordinates import SkyCoord
    >>> from astropy import units as u
    >>> pos = SkyCoord('120 38', unit=u.deg)
    >>> tab = Heasarc.query_region(pos, catalog='chanmaster', radius=2*u.deg)
    >>> tab.sort('time')
    >>> tab['name', 'obsid', 'ra', 'dec'][:5].pprint(align='<')
               name           obsid     ra      dec
                                       deg      deg
    ------------------------- ----- --------- --------
    B2 0755+37                858   119.61750 37.78667
    ABELL 611                 3194  120.23708 36.05722
    1RXS J075526.1+391111     13008 118.85875 39.18639
    SDSS J080040.77+391700.5  18110 120.17000 39.28344
    WISEA J080357.73+390823.1 28213 120.99060 39.13980

If no radius value is given, a default that is appropriate
for each catalog is used. You can see the value of the default
radius values by calling `~astroquery.heasarc.HeasarcClass.get_default_radius`,
passing the name of the catalog.

The list of returned columns can also be given as a comma-separated string to
`~astroquery.heasarc.HeasarcClass.query_region`:

.. doctest-remote-data::
    >>> from astroquery.heasarc import Heasarc
    >>> from astropy.coordinates import SkyCoord
    >>> from astropy import units as u
    >>> pos = SkyCoord('120 38', unit=u.deg)
    >>> tab = Heasarc.query_region(pos, catalog='chanmaster', radius=2*u.deg,
    ...                            columns='obsid, name, time, pi')
    >>> tab[:5].pprint()
    obsid            name                 time          pi
                                        d
    ----- ------------------------- ---------------- -------
    3194                 ABELL 611 52216.7805324074   Allen
    858                B2 0755+37 51637.0090740741 Worrall
    28213 WISEA J080357.73+390823.1 60315.9524768519  Pooley
    29168 WISEA J080357.73+390823.1 60316.2761805556  Pooley
    13008     1RXS J075526.1+391111 55536.6453587963     Liu

If no columns are given, the call will return a set of default columns.
If you want all the columns returned, use ``columns='*'``

To add a search offset column that gives the angular distance in arcminutes
between the query position and the positions in the catalog,
use the ``add_offset=True``:

To do a full sky search, use ``spatial='all-sky'``:

.. doctest-remote-data::

    >>> from astroquery.heasarc import Heasarc
    >>> tab = Heasarc.query_region(catalog='chanmaster', spatial='all-sky',
    ...                            columns='name, obsid, ra, dec')
    >>> tab[:5].pprint()
            name         obsid     ra       dec   
                                  deg       deg   
    -------------------- ----- --------- ---------
             ESO005-G004 21421  91.42333 -86.63194
    1RXSJ200924.1-853911 10143 302.30417 -85.64633
            RE J0317-853 22326  49.31604 -85.54043
                ACO 4023 15124 354.93333 -85.17583
               GRB020321  3477 242.76000 -83.70000

List Available Catalogs
-----------------------
The collection of available catalogs can be obtained by calling the `~astroquery.heasarc.HeasarcClass.list_catalogs`
method. In this example, we request the master catalogs only by passing ``master=True``.
Master catalogs are catalogs that contain one entry per observation, as opposed to
other catalogs that may record other information. There is typically one master catalog
per mission. The ``master`` parameter is a boolean flag, which is ``False`` by default 
(i.e. return all catalogs). `~astroquery.heasarc.HeasarcClass.list_catalogs` returns an
`~astropy.table.Table` with two columns containing the names and description of the available
catalogs.

.. doctest-remote-data::

    >>> from astroquery.heasarc import Heasarc
    >>> catalogs = Heasarc.list_catalogs(master=True)
    >>> catalogs.pprint(align='<')
       name                             description
    ---------- -------------------------------------------------------------
    ascamaster ASCA Master Catalog
    burcbmastr BurstCube Master Observation Catalog
    chanmaster Chandra Observations
    ...

If you do not know the name of the catalog you are looking for, you can use the ``keywords``
parameter in `~astroquery.heasarc.HeasarcClass.list_catalogs`. For example, if you want to find all catalogs that
are related to Chandra, you can do:

.. doctest-remote-data::

    >>> from astroquery.heasarc import Heasarc
    >>> catalogs = Heasarc.list_catalogs(keywords='chandra')
    >>> # list the first 10
    >>> catalogs[:10].pprint()
       name                              description
    ---------- ----------------------------------------------------------------
    acceptcat Archive of Chandra Cluster Entropy Profile Tables (ACCEPT) Catal
        aegisx  AEGIS-X Chandra Extended Groth Strip X-Ray Point Source Catalog
    aegisxdcxo           AEGIS-X Deep Survey Chandra X-Ray Point Source Catalog
    aknepdfcxo  Akari North Ecliptic Pole Deep Field Chandra X-Ray Point Source
    arcquincxo Arches and Quintuplet Clusters Chandra X-Ray Point Source Catalo
    atcdfsss82  Australia Telescope Chandra Deep Field-South and SDSS Stripe 82
    bmwchancat                 Brera Multi-scale Wavelet Chandra Source Catalog
    candelscxo                   CANDELS H-Band Selected Chandra Source Catalog
    cargm31cxo          Carina Nebula Gum 31 Chandra X-Ray Point Source Catalog
    carinaclas                 Carina Nebula Chandra X-Ray Point Source Classes

If you are interested only finding the master catalogs only, you can set ``master`` to ``True``.

.. doctest-remote-data::

    >>> from astroquery.heasarc import Heasarc
    >>> catalog = Heasarc.list_catalogs(keywords='chandra', master=True)
    >>> catalog.pprint()
       name        description
    ---------- --------------------
    chanmaster Chandra Observations

Multiple keywords that are separated by space are joined with **AND**, so the
following finds all the catalogs that have both 'xmm' and 'chandra' keywords:

.. doctest-remote-data::

    >>> from astroquery.heasarc import Heasarc
    >>> catalog = Heasarc.list_catalogs(keywords='xmm chandra')
    >>> catalog.pprint()
       name                              description
    ---------- ----------------------------------------------------------------
    gmrt1hxcsf Giant Metrewave Radio Telescope 1h XMM/Chandra Survey Fld 610-MH
    ic10xmmcxo          IC 10 XMM-Newton and Chandra X-Ray Point Source Catalog
    ros13hrcxo      ROSAT/XMM-Newton 13-hour Field Chandra X-Ray Source Catalog
    xmmomcdfs   XMM-Newton Optical Monitor Chandra Deep Field-South UV Catalog

If you want an **OR** relation between keywords, you can pass them in a list. The
following for instance will find master catalogs that have keywords 'nicer' or 'swift'

.. doctest-remote-data::

    >>> from astroquery.heasarc import Heasarc
    >>> catalog = Heasarc.list_catalogs(keywords=['nicer', 'swift'], master=True)
    >>> catalog.pprint()
       name        description
    ---------- --------------------
    nicermastr NICER Master Catalog
    swiftmastr Swift Master Catalog


Adding Column Constraints
----------------------------------------
In addition to region search in `~astroquery.heasarc.HeasarcClass.query_region`,
you can also pass other column constraints. This is done by passing a dictionary
to the ``column_filters`` parameter. The keys of the dictionary are the column names
and the values are the constraints. Exampels include:
- ``{'flux': (1e-12, 1e-10)}`` translates to a flux range.
- ``{'exposure': ('>', 10000)}`` translates to exposure greater than 10000.
- ``{'instrument': ['ACIS', 'HRC']}`` translates to a value in a list.
- ``{'obsid': '12345'}`` translates to obsid equal to 12345.

This allows you to query a catalog by specifying
various column constraints. For example, the following query searches the ``chanmaster``
catalog for all observations with exposure time greater than 190 ks.

Note that when column filters are given and no position is specified,
the search defaults to an all-sky search.

.. doctest-remote-data::

    >>> from astroquery.heasarc import Heasarc
    >>> tab = Heasarc.query_region(
    ...     catalog='chanmaster', column_filters={'exposure': ('>', '190000')}
    ... )
    >>> tab['name', 'obsid', 'ra', 'dec', 'exposure'][:3].pprint()
        name      obsid     ra       dec    exposure
                            deg       deg       s    
    --------------- ----- --------- --------- --------
       GW Transient 29852        --        --   300000
             Sgr A* 13842 266.41667 -29.00781   191760
    IGR J17480-2446 30481 267.02013 -24.78024   200000

Another example may be to search the ``xmmmaster`` for a observation in some time range:

.. doctest-remote-data::

    >>> from astroquery.heasarc import Heasarc
    >>> tab = Heasarc.query_region(
    ...     catalog='xmmmaster', column_filters={'time': (52300, 52310)}
    ... )
    >>> tab['name', 'obsid', 'ra', 'dec', 'time', 'duration'][:3].pprint()
         name       obsid       ra       dec          time       duration
                                deg       deg           d            s    
    ------------- ---------- -------- --------- ---------------- --------
        NGC 1316 0091770101 50.95833 -37.28333 52308.6872337963    60362
        NGC 1316 0091770201 50.67296 -37.20928  52308.642974537     3462
    Fei 16 offset 0154150101 28.64374  -6.86667 52305.2210416667    24619

To see the available columns that can be queried for a given catalog and their units,
use `~astroquery.heasarc.HeasarcClass.list_columns` (see below).

Links to Data Products
----------------------
Once the query result is obtained, you can query any data products associated
with those results.

.. doctest-remote-data::

    >>> from astroquery.heasarc import Heasarc
    >>> from astropy.coordinates import SkyCoord
    >>> pos = SkyCoord.from_name('ngc 3516')
    >>> tab = Heasarc.query_region(pos, catalog='nicermastr')
    >>> tab = tab[tab['exposure'] > 0]
    >>> links = Heasarc.locate_data(tab[:2])
    >>> links['access_url'].pprint()
                                  access_url
    ---------------------------------------------------------------------
    https://heasarc.gsfc.nasa.gov/FTP/nicer/data/obs/2025_01//7100120102/
    https://heasarc.gsfc.nasa.gov/FTP/nicer/data/obs/2025_01//7100120101/

The ``links`` table has three relevant columns: ``access_url``, ``sciserver`` and ``aws``.
The first gives the url to the data from the main heasarc server. The second gives
the local path to the data on Sciserver. The last gives the S3 URI to the data in the cloud.
You can specify where the data are to be downloaded using the ``location`` parameter.

To download the data, you can pass ``links`` table (or row) to `~astroquery.heasarc.HeasarcClass.download_data`,
specifying from where you want the data to be fetched by specifying the ``host`` parameter. By default,
the function will try to guess the best host based on your environment. If it cannot guess, then
the data is fetched from the main HEASARC servers.
The recommendation is to use different hosts depending on where your code is running:
* ``host='sciserver'``: Use this option if you running you analysis on Sciserver. Because
all the archive can be mounted locally there, `~astroquery.heasarc.HeasarcClass.download_data`
will only copy the relevant data.
* ``host='aws'``: Use this option if you are running the analysis in Amazon Web Services (AWS).
Data will be downloaded from AWS S3 storage.
* ``host='heasarc'``: Use this option for other cases. This is the classical and most general option.
In this case, the requested data will be tarred and downloaded as a single file called ``heasarc-data.tar``
before being untarred.

Advanced Queries
----------------
Behind the scenes, `~astroquery.heasarc.HeasarcClass.query_region` constructs an query in the
Astronomical Data Query Language ADQL, which is powerful in constructing
complex queries. Passing ``get_query_payload=True`` to `~astroquery.heasarc.HeasarcClass.query_region`
returns the constructed ADQL query.

.. doctest-remote-data::

    >>> from astroquery.heasarc import Heasarc
    >>> from astropy.coordinates import SkyCoord
    >>> from astropy import units as u
    >>> pos = SkyCoord('120 38', unit=u.deg)
    >>> query = Heasarc.query_region(pos, catalog='xmmmaster', radius=2*u.deg,
    ...                              columns='*', get_query_payload=True)
    >>> query
    "SELECT * FROM xmmmaster WHERE CONTAINS(POINT('ICRS',ra,dec),CIRCLE('ICRS',120.0,38.0,2.0))=1"
    >>> # The query can be modified and then submitted using:
    >>> query = """SELECT ra,dec,name,obsid FROM xmmmaster
    ...            WHERE CONTAINS(POINT('ICRS',ra,dec),CIRCLE('ICRS',120.0,38.0,2.0))=1"""
    >>> tab = Heasarc.query_tap(query).to_table()
    >>> tab[:10].pprint()
        ra      dec            name           obsid
    deg      deg
    --------- -------- -------------------- ----------
    120.22707 36.04139            Abell 611 0781590301
    120.25583 36.04944            Abell 611 0781590501
    120.23300 36.06100                 A611 0605000601
    120.21750 36.06500            Abell 611 0781590401
    120.24624 36.07305            Abell 611 0781590201
    120.39708 36.46875 RMJ080135.3+362807.5 0881901001
    119.61710 37.78661           B2 0755+37 0602390101
    121.92084 39.00417              UGC4229 0138950101
    121.92084 39.00417              UGC4229 0138951401
    121.92099 39.00422              MRK 622 0852180501

Table Uploads
-----------------
You can also upload a table of positions to be queried. The table can be an
`~astropy.table.Table` or a path to a file in VOtable format. The following example 
shows how to use the upload feature to do a cross-match between the
``chanmaster`` catalog and a list of known source positions:

.. doctest-remote-data::
    
    >>> from astroquery.heasarc import Heasarc
    >>> from astropy.table import Table
    >>> sample = Table({
    ...     'ra': [1.58, 188.90],
    ...     'dec': [20.20, -39.90]
    ... })
    >>> query = """
    ... SELECT cat.name, cat.ra, cat.dec, cat.obsid
    ... FROM chanmaster cat, tap_upload.mytable mt
    ... WHERE 1=CONTAINS(POINT('ICRS', mt.ra, mt.dec), CIRCLE('ICRS',cat.ra, cat.dec, 0.1))
    ... """
    >>> result = Heasarc.query_tap(query, uploads={'mytable': sample}).to_table()
    >>> result.pprint()
        name        ra       dec    obsid
                   deg       deg         
    ----------- --------- --------- -----
       NGC 4507 188.90250 -39.90928 12292
       NGC 4507 188.90208 -39.90925  2150
         HR4796 189.00417 -39.86950  7414
    KUG0003+199   1.58134  20.20291 23709
        Mrk 335   1.58142  20.20295 23292
        Mrk 335   1.58142  20.20295 23297
        Mrk 335   1.58142  20.20295 23298
        Mrk 335   1.58142  20.20295 23299
        Mrk 335   1.58142  20.20295 23300
        Mrk 335   1.58142  20.20295 23301
        Mrk 335   1.58142  20.20295 23302


Complex Regions
---------------
In addition to a cone search (some position and search radius), ```Heasarc.query_region``` accepts
other options too, including ``'box'``, ``'polygon'`` and ``'all-sky'``. Details can be found
in `~astroquery.heasarc.HeasarcClass.query_region`. Examples include:

.. doctest-skip::

    >>> # query box region
    >>> pos = SkyCoord('226.2 10.6', unit=u.deg)
    >>> Heasarc.query_region(pos, catalog='xmmmaster', spatial='box', width=0.5*u.deg)

for ``'box'`` and:

.. doctest-skip::
    >>> Heasarc.query_region(catalog='xmmmaster', spatial='polygon',
                  polygon=[(226.2,10.6),(225.9,10.5),(225.8,10.2),(226.2,10.3)])

for ``'polygon'``. For ``'all-sky'``:

.. doctest-skip::

    >>> Heasarc.query_region(pos, spatial='all-sky', catalog='csc', maxrec=None)

though you may find that maxrec has a hard limit of 1e5 regardless of how you set it. 

In this case one can do instead:

.. doctest-skip::

    >>> # get a comma-separated list of the default columns in csc.
    >>> columns = ', '.join(Heasarc._get_default_columns('csc'))
    >>> # construct a query for all entries; use TOP with a large number greater than the server's 1e5 LIMIT
    >>> query = f'SELECT TOP 9999999 {columns} FROM csc'
    >>> Heasarc.query_tap(query).to_table()

List Catalog Columns
--------------------
To list the columns of some catalog, use `~astroquery.heasarc.HeasarcClass.list_columns`. Here we list the columns
in the XMM master catalog ``xmmmaster``:

.. doctest-remote-data::

    >>> from astroquery.heasarc import Heasarc
    >>> columns = Heasarc.list_columns(catalog_name='suzamaster')
    >>> columns.sort('name')
    >>> columns[:10].pprint(align='<')
          name                    description                 unit
    --------------- ---------------------------------------- ------
    dec             Declination (Pointing Position)          degree
    exposure        Effective Total Observation Exposure (s) s
    name            Designation of the Pointed Source
    obsid           Unique Observation/Sequence Number
    processing_date Date of Processing                       mjd
    public_date     Public Date                              mjd
    ra              Right Ascension (Pointing Position)      degree

Reference/API
=============

.. automodapi:: astroquery.heasarc
    :no-inheritance-diagram:
