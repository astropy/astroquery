.. _astroquery.heasarc:

**************************************
HEASARC Queries (`astroquery.heasarc`)
**************************************

Getting started
===============

This is a python interface for querying the
`HEASARC <https://heasarc.gsfc.nasa.gov/>`__
archive web service.

The main interface for the Heasarc services``heasarc.Heasarc`` now uses
Virtual Observatory protocols with the Xamin interface, which offers
more powerful search options than the old Browse interface.

- :ref:`Heasarc Main Interface`.

.. _Heasarc Main Interface:

Heasarc Main Interface
=======================

Query a Table
-------------
The basic use case is one where we wants to query a table from some position in the sky.
In this example, we query the NuSTAR master table ``numaster`` for all observations
of the AGN ``NGC 3783``. We use `~astropy.coordinates.SkyCoord` to obtain the coordinates
and then pass them to `~astroquery.heasarc.HeasarcClass.query_region`:

.. doctest-remote-data::

    >>> from astroquery.heasarc import Heasarc
    >>> from astropy.coordinates import SkyCoord
    >>> pos = SkyCoord.from_name('ngc 3783')
    >>> tab = Heasarc.query_region(pos, table='numaster')
    >>> tab['name', 'obsid', 'ra', 'dec'][:3].pprint()
      name    obsid      ra      dec   
                        deg      deg   
    -------- -------- -------- --------
    NGC_3783 80701617 174.7573 -37.7386
    NGC_3783 60901023 174.7571 -37.7385
    NGC_3783 60902005 174.7571 -37.7385

To query a region around some position, specifying the search radius,
we use `~astropy.units.deg`:

.. doctest-remote-data::

    >>> from astroquery.heasarc import Heasarc
    >>> from astropy.coordinates import SkyCoord
    >>> from astropy import units as u
    >>> pos = SkyCoord('120 38', unit=u.deg)
    >>> tab = Heasarc.query_region(pos, table='chanmaster', radius=2*u.deg)
    >>> tab['name', 'obsid', 'ra', 'dec'][:5].pprint()
               name           obsid     ra      dec   
                                       deg      deg   
    ------------------------- ----- --------- --------
                    ABELL 611  3194 120.23708 36.05722
                   B2 0755+37   858 119.61750 37.78667
    WISEA J080357.73+390823.1 28213 120.99060 39.13980
        1RXS J075526.1+391111 13008 118.85875 39.18639
     SDSS J080040.77+391700.5 18110 120.17000 39.28344

If no radius value is given, a default that is appropriate
for each table is used. You can see the value of the default
radius values by calling `~~astroquery.heasarc.HeasarcClass._get_default_radius`,
passing the name of the table.

The list of returned columns can also be given as a comma-separated string to
`~~astroquery.heasarc.HeasarcClass.query_region`:

.. doctest-remote-data::
    >>> from astroquery.heasarc import Heasarc
    >>> from astropy.coordinates import SkyCoord
    >>> from astropy import units as u
    >>> pos = SkyCoord('120 38', unit=u.deg)
    >>> tab = Heasarc.query_region(pos, table='chanmaster', radius=2*u.deg,
    ...                            columns='obsid, name, time, pi')
    >>> tab[:5].pprint()
    obsid            name                 time          pi     search_offset_
                                           d                       arcmin
    ----- ------------------------- ---------------- ------- ------------------
     3194                 ABELL 611 52216.7805324074   Allen  1.951975323208395
      858                B2 0755+37 51637.0090740741 Worrall 0.3696266904766543
    28213 WISEA J080357.73+390823.1 60315.9524768519  Pooley 1.3780163330932278
    29168 WISEA J080357.73+390823.1 60316.2761805556  Pooley 1.3780163330932278
    13008     1RXS J075526.1+391111 55536.6453587963     Liu 1.4842785992883953

If no columns are given, the call will return a set of default columns.
If you want all the columns returned, use ``columns='*'```

List Available Tables
---------------------
The collection of available tables can be obtained by calling the `~astroquery.heasarc.HeasarcClass.tables` 
method. In this example, we query the master tables only by passing ``master=True``.
which is ``False`` by default (i.e. return all table). `~astroquery.heasarc.HeasarcClass.tables` returns an 
`~astropy.table.Table` with two columns containing the names and description of the available
tables.

.. doctest-remote-data::

    >>> from astroquery.heasarc import Heasarc
    >>> tables = Heasarc.tables(master=True)
    >>> tables.pprint(align='<')
       name                             description                         
    ---------- -------------------------------------------------------------
    ascamaster ASCA Master Catalog                                          
    chanmaster Chandra Observations                                         
    cmbmaster  LAMBDA Cosmic Microwave Background Experiments Master Catalog
    erosmaster eROSITA Observations Master Catalog

If you do not know the name of the table you are looking for, you can use the ``keywords`` 
parameter in `~astroquery.heasarc.HeasarcClass.tables`. For example, if you want to find all tables that 
are related to Chandra, you can do:

.. doctest-remote-data::

    >>> from astroquery.heasarc import Heasarc
    >>> tab = Heasarc.tables(keywords='chandra')
    >>> # list the first 10
    >>> tab[:10].pprint()
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

If you are interested only finding the master tables, you can also set ``master`` to ``True``.

.. doctest-remote-data::

    >>> from astroquery.heasarc import Heasarc
    >>> tab = Heasarc.tables(keywords='chandra', master=True)
    >>> tab.pprint()
       name        description     
    ---------- --------------------
    chanmaster Chandra Observations

Multiple keywords that are separated by space are joined with **AND**, so the 
following finds all the tables that have both 'xmm' and 'chandra' keyworkds:

.. doctest-remote-data::

    >>> from astroquery.heasarc import Heasarc
    >>> tab = Heasarc.tables(keywords='xmm chandra')
    >>> tab.pprint()
       name                              description                           
    ---------- ----------------------------------------------------------------
    gmrt1hxcsf Giant Metrewave Radio Telescope 1h XMM/Chandra Survey Fld 610-MH
    ic10xmmcxo          IC 10 XMM-Newton and Chandra X-Ray Point Source Catalog
    ros13hrcxo      ROSAT/XMM-Newton 13-hour Field Chandra X-Ray Source Catalog
    xmmomcdfs   XMM-Newton Optical Monitor Chandra Deep Field-South UV Catalog

If you want an **OR** relation between keywords, you can pass them in a list. The
following for instance will find master tables that have keywords 'nicer' or 'swift'

.. doctest-remote-data::

    >>> from astroquery.heasarc import Heasarc
    >>> tab = Heasarc.tables(keywords=['nicer', 'swift'], master=True)
    >>> tab.pprint()
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
    >>> tab = Heasarc.query_region(pos, table='nicermastr')
    >>> links = Heasarc.get_datalinks(tab[:2])
    >>> links.pprint(max_width=120)
      ID                                access_url                              ... content_length
                                                                                ...      byte     
    ----- --------------------------------------------------------------------- ... --------------
    52637 https://heasarc.gsfc.nasa.gov/FTP/nicer/data/obs/2018_08//1100120101/ ...      868252835
    52641 https://heasarc.gsfc.nasa.gov/FTP/nicer/data/obs/2018_08//1100120102/ ...       79508896

The ``links`` table has three relevant columns: ``access_url``, ``sciserver`` and ``aws``.
The first gives the url to the data from the main heasarc server. The second gives
the local path to the data on Sciserver. The last gives the S3 URI to the data in the cloud.
You can specify where the data are to be downloaded using the ``location`` parameter.

To download the data, you can pass ``links`` table to `~astroquery.heasarc.HeasarcClass.download_data`,
specifying from where you want the data to fetched by specifying the ``host`` parameter. By default,
the data is fetched from the main HEASARC servers.
The recommendation is to use different hosts depending on where you can is running:
* ``host='sciserver'``: Use this option if you running you analysis on Sciserver. Because
all the archive can be mounted locally there, `~astroquery.heasarc.HeasarcClass.download_data`
will only copy the relevent data.
* ``host='aws'``: Use this option if you are running the analysis in Amazon Web Services (AWS).
Data will be downloaded from AWS S3 storage.
* ``host='heasarc'``: Use this option for other cases. Thi is the classical and most general option.
In this case, the requested data will be tarred and downloaded as a single file called xamin.tar
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
    >>> query = Heasarc.query_region(pos, table='xmmmaster', radius=2*u.deg,
    >>>                             get_query_payload=True)
    >>> query
    "SELECT * FROM xmmmaster WHERE CONTAINS(POINT('ICRS',ra,dec),CIRCLE('ICRS',120.0,38.0,2.0))=1"
    ...
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
    121.92084 39.00417              UGC4229 0138951401
    121.92084 39.00417              UGC4229 0138950101
    121.92099 39.00422              MRK 622 0852180501

Complex Regions
---------------
In additon to a cone search (some position and search radius), ```Heasarc.query_region``` accepts
other options too, including ``'box'``, ``'polygon'`` and ``'all-sky'``. Details can be found
in `~astroquery.heasarc.HeasarcClass.query_region`. Examples include:

.. doctest-skip::

    >>> # query box region
    >>> pos = SkyCoord('226.2 10.6', unit=u.deg)
    >>> Heasarc.query_region(pos, table='xmmmaster', spatial='box', width=0.5*u.deg)

for ``'box'`` and:

.. doctest-skip::
    >>> Heasarc.query_region(table='xmmmaster', spatial='polygon',
                  polygon=[(226.2,10.6),(225.9,10.5),(225.8,10.2),(226.2,10.3)])

for ``'polygon'``.  

List Table Columns
------------------
To list the columns of some table, use `~astroquery.heasarc.HeasarcClass.columns`. Here we list the columns
in the XMM master table ``xmmmaster``:

.. doctest-remote-data::

    >>> from astroquery.heasarc import Heasarc
    >>> columns = Heasarc.columns(table_name='xmmmaster')
    >>> columns[:10].pprint(align='<')
         name                                description                          
    -------------- ---------------------------------------------------------------
    rgs2_time      Total RGS-2 Exposure Time (s)                                  
    ra             Right Ascension of Target                                      
    pn_mode        Flags Indicate PN Instrument Modes                             
    obsid          Unique Observation Identifier                                  
    pps_flag       Flag Indicates PPS Products Available                          
    om_time        Total OM Exposure Time (s)                                     
    rgs2_num       Number of RGS-2 Exposures                                      
    name           Target Designation                                             
    xmm_revolution XMM-Newton Revolution (Orbit) Number                           
    status         Status of Observation: scheduled, observed, processed, archived

Reference/API
=============

.. automodapi:: astroquery.heasarc
    :no-inheritance-diagram:
