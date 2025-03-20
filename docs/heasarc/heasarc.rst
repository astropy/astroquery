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
and then pass them to `~astroquery.heasarc.HeasarcClass.query_region`. In following, we
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

List Available Catalogs
-----------------------
The collection of available catalogs can be obtained by calling the `~astroquery.heasarc.HeasarcClass.list_catalogs`
method. In this example, we query the master catalogs only by passing ``master=True``.
which is ``False`` by default (i.e. return all catalogs). `~astroquery.heasarc.HeasarcClass.list_catalogs` returns an
`~astropy.table.Table` with two columns containing the names and description of the available
catalogs.

.. doctest-remote-data::

    >>> from astroquery.heasarc import Heasarc
    >>> catalogs = Heasarc.list_catalogs(master=True)
    >>> catalogs.pprint(align='<')
       name                             description
    ---------- -------------------------------------------------------------
    ascamaster ASCA Master Catalog
    chanmaster Chandra Observations
    cmbmaster  LAMBDA Cosmic Microwave Background Experiments Master Catalog
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

If you are interested only finding the master catalogs, you can also set ``master`` to ``True``.

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
    https://heasarc.gsfc.nasa.gov/FTP/nicer/data/obs/2018_08//1100120101/
    https://heasarc.gsfc.nasa.gov/FTP/nicer/data/obs/2018_08//1100120102/

The ``links`` table has three relevant columns: ``access_url``, ``sciserver`` and ``aws``.
The first gives the url to the data from the main heasarc server. The second gives
the local path to the data on Sciserver. The last gives the S3 URI to the data in the cloud.
You can specify where the data are to be downloaded using the ``location`` parameter.

To download the data, you can pass ``links`` table (or row) to `~astroquery.heasarc.HeasarcClass.download_data`,
specifying from where you want the data to be fetched by specifying the ``host`` parameter. By default,
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

for ``'polygon'``.

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
