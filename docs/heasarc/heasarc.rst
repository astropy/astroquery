.. _astroquery.heasarc:

**************************************
HEASARC Queries (`astroquery.heasarc`)
**************************************

Getting started
===============

This is a python interface for querying the
`HEASARC <https://heasarc.gsfc.nasa.gov/>`__
archive web service.

There main interface for the Heasarc services``heasarc.Heasac`` now uses
Virtual Observatory protocols with the Xamin interface, which offers
more powerful search options than the old Browse interface.

- :ref:`Heasarc Main (Xamin) Interface`.
- :ref:`Old Browse Interface`.

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
we use `~astropy.units`:

.. doctest-remote-data::

    >>> from astroquery.heasarc import Heasac
    >>> from astropy.coordinates import SkyCoord
    >>> from astropy import units as u
    >>> pos = SkyCoord('120 38', unit=u.deg)
    >>> tab = Heasac.query_region(pos, table='chanmaster', radius=2*u.deg)
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
radius values by calling `~~astroquery.heasarc.HeasarcClass.get_default_radius`,
passing the name of the table.

The list of returned columns can also be given as a comma-separated string to
`~~astroquery.heasarc.HeasarcClass.query_region`:

.. doctest-skip::

    >>> Heasac.query_region(pos, table='chanmaster', radius=2*u.deg,
    ...                    columns='obsid, name, time, pi_lname')

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

    >>> from astroquery.heasarc import Heasac
    >>> tables = Heasac.tables(master=True)
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

    >>> from astroquery.heasarc import Heasac
    >>> tab = Heasac.tables(keywords='chandra')
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

    >>> from astroquery.heasarc import Heasac
    >>> tab = Heasac.tables(keywords='chandra', master=True)
    >>> tab.pprint()
       name        description     
    ---------- --------------------
    chanmaster Chandra Observations

Multiple keywords that are separated by space are joined with **AND**, so the 
following find all tables that have both 'xmm' and 'chandra' keyworkds:

.. doctest-remote-data::

    >>> from astroquery.heasarc import Heasac
    >>> tab = Heasac.tables(keywords='xmm chandra')
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

    >>> from astroquery.heasarc import Heasac
    >>> tab = Heasac.tables(keywords=['nicer', 'swift'], master=True)
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

    >>> from astroquery.heasarc import Heasac
    >>> from astropy.coordinates import SkyCoord
    >>> pos = SkyCoord.from_name('ngc 3516')
    >>> tab = Heasac.query_region(pos, table='nicermastr')
    >>> links = Heasac.get_links(tab[:2])
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

    >>> from astroquery.heasarc import Heasac
    >>> from astropy.coordinates import SkyCoord
    >>> from astropy import units as u
    >>> pos = SkyCoord('120 38', unit=u.deg)
    >>> query = Heasac.query_region(pos, table='xmmmaster', radius=2*u.deg, 
    >>>                            get_query_payload=True)
    >>> query
    "SELECT * FROM xmmmaster WHERE CONTAINS(POINT('ICRS',ra,dec),CIRCLE('ICRS',120.0,38.0,2.0))=1"
    ...
    >>> # The query can be modified and then submitted using:
    >>> query = """SELECT ra,dec,name,obsid FROM xmmmaster 
    ...            WHERE CONTAINS(POINT('ICRS',ra,dec),CIRCLE('ICRS',120.0,38.0,2.0))=1"""
    >>> tab = Heasac.query_tap(query).to_table()
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
In additon to a cone search (some position and search radius), ```Heasac.query_region``` accepts
other options too, including ``'box'``, ``'polygon'`` and ``'all-sky'``. Details can be found
in `~astroquery.heasarc.HeasarcClass.query_region`. Examples include:

.. doctest-skip::

    >>> # query box region
    >>> pos = SkyCoord('226.2 10.6', unit=u.deg)
    >>> Heasac.query_region(pos, table='xmmmaster', spatial='box', width=0.5*u.deg)

for ``'box'`` and:

.. doctest-skip::
    >>> Heasac.query_region(table='xmmmaster', spatial='polygon',
                  polygon=[(226.2,10.6),(225.9,10.5),(225.8,10.2),(226.2,10.3)])

for ``'polygon'``.  

List Table Columns
------------------
To list the columns of some table, use `~astroquery.heasarc.HeasarcClass.columns`. Here we list the columns
in the XMM master table ``xmmmaster``:

.. doctest-remote-data::

    >>> from astroquery.heasarc import Heasac
    >>> columns = Heasac.columns(table_name='xmmmaster')
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


.. _Old Browse Interface:

Old Browse Interface
====================
:::{admonition} Limited Support
:class: warning

The old Browse interface has only limited support from the Heasarc,
please consider using the main `~astroquery.heasarc.HeasarcClas` interface.
:::

Getting lists of available datasets
-----------------------------------

There are two ways to obtain a list of objects. The first is by querying around
an object by name:

.. doctest-remote-data::

    >>> from astroquery.heasarc import Heasarc
    >>> heasarc = Heasarc()
    >>> mission = 'rosmaster'
    >>> object_name = '3c273'
    >>> table = heasarc.query_object(object_name, mission=mission)
    >>> table[:3].pprint(max_width=120)
         SEQ_ID      INSTRUMENT EXPOSURE         NAME         ...  DEC      START_TIME        END_TIME      SEARCH_OFFSET_ 
                                   s                          ...  deg         mjd              mjd                        
    ---------------- ---------- -------- -------------------- ... ------ ---------------- ---------------- ----------------
    RH701576N00          HRI       68154 3C 273               ... 2.0500 49704.3090856482 49724.6236226852  0.190 (3c273)\n
    RP600242A01          PSPCB     24822 GIOVANELLI-HAYNES CL ... 1.6000 48980.6468865741 48982.9284837963 34.236 (3c273)\n
    RH700234N00          HRI       17230 3C 273               ... 2.0500 48629.2693055556 48632.4716782407  0.190 (3c273)\n

Alternatively, a query can also be conducted around a specific set of sky
coordinates:

.. doctest-remote-data::

    >>> from astroquery.heasarc import Heasarc
    >>> from astropy.coordinates import SkyCoord
    >>> heasarc = Heasarc()
    >>> mission = 'rosmaster'
    >>> coords = SkyCoord('12h29m06.70s +02d03m08.7s', frame='icrs')
    >>> table = heasarc.query_region(coords, mission=mission, radius='1 degree')
    >>> table[:3].pprint(max_width=120)
         SEQ_ID      INSTRUMENT EXPOSURE ...    START_TIME        END_TIME                 SEARCH_OFFSET_            
                                   s     ...       mjd              mjd                                              
    ---------------- ---------- -------- ... ---------------- ---------------- --------------------------------------
    RH701576N00          HRI       68154 ... 49704.3090856482 49724.6236226852  0.191 (187.2779228198,2.0524148595)\n
    RP600242A01          PSPCB     24822 ... 48980.6468865741 48982.9284837963 34.237 (187.2779228198,2.0524148595)\n
    RH700234N00          HRI       17230 ... 48629.2693055556 48632.4716782407  0.191 (187.2779228198,2.0524148595)\n

Note that the :meth:`~astroquery.heasarc.HeasarcClass.query_region` converts
the passed coordinates to the FK5 reference frame before submitting the query.


Modifying returned table columns
--------------------------------

Each table has a set of default columns that are returned when querying the
database. You can return all available columns for a given mission by specifying
the ``fields`` parameter in either of the above queries. For exampe:

.. doctest-remote-data::

    >>> table = heasarc.query_object(object_name='3c273', mission='rosmaster', fields='All')

will return all available columns from the ``rosmaster`` mission table.
Alternatively, a comma-separated list of column names can also be provided to
specify which columns will be returned:

.. doctest-remote-data::

    >>> table = heasarc.query_object(object_name='3c273', mission='rosmaster', fields='EXPOSURE,RA,DEC')
    >>> table[:3].pprint()
    EXPOSURE    RA     DEC    SEARCH_OFFSET_ 
       s       deg     deg                   
    -------- -------- ------ ----------------
       68154 187.2800 2.0500  0.190 (3c273)\n
       24822 186.9300 1.6000 34.236 (3c273)\n
       17230 187.2800 2.0500  0.190 (3c273)\n

Note that the ``SEARCH_OFFSET_`` column will always be included in the results.
If a column name is passed to the ``fields`` parameter which does not exist in
the requested mission table, the query will fail. To obtain a list of available
columns for a given mission table, do the following:

.. doctest-remote-data::

    >>> cols = heasarc.query_mission_cols(mission='rosmaster')
    >>> print(cols)
    ['SEQ_ID', 'INSTRUMENT', 'EXPOSURE', 'NAME', 'RA', 'DEC', 'START_TIME', 'END_TIME', 'AO', 'BII', 'CLASS', 'FILTER', 'FITS_TYPE', 'INDEX_ID', 'LII', 'PI_FNAME', 'PI_LNAME', 'PROC_REV', 'PROPOSAL_NUMBER', 'QA_NUMBER', 'RDAY_BEGIN', 'RDAY_END', 'REQUESTED_EXPOSURE', 'ROLL', 'ROR', 'SITE', 'SUBJ_CAT', 'TITLE', 'SEARCH_OFFSET_']


Additional query parameters
---------------------------

By default, the :meth:`~astroquery.heasarc.HeasarcClass.query_object` method
returns all entries within approximately one degree of the specified object.
This can be modified by supplying the ``radius`` parameter. This parameter
takes a distance to look for objects. The following modifies the search radius
to 120 arcmin:

.. doctest-remote-data::

    >>> from astroquery.heasarc import Heasarc
    >>> heasarc = Heasarc()
    >>> table = heasarc.query_object(object_name, mission='rosmaster', radius='120 arcmin')

``radius`` takes an angular distance specified as an astropy Quantity object,
or a string that can be parsed into one (e.g., '1 degree' or 1*u.degree). The
following are equivalent:

.. doctest-remote-data::

    >>> table = heasarc.query_object(object_name, mission='rosmaster', radius='120 arcmin')
    >>> table = heasarc.query_object(object_name, mission='rosmaster', radius='2 degree')
    ...
    >>> from astropy import units as u
    >>> table = heasarc.query_object(object_name, mission='rosmaster', radius=120*u.arcmin)
    >>> table = heasarc.query_object(object_name, mission='rosmaster', radius=2*u.degree)

As per the astroquery specifications, the :meth:`~astroquery.heasarc.HeasarcClass.query_region`
method requires the user to supply the radius parameter.

The results can also be sorted by the value in a given column using the ``sortvar``
parameter. The following sorts the results by the value in the 'EXPOSURE' column.

.. doctest-remote-data::

    >>> table = heasarc.query_object(object_name, mission='rosmaster', sortvar='EXPOSURE')
    >>> table[:3].pprint()
         SEQ_ID      INSTRUMENT EXPOSURE ...     END_TIME      SEARCH_OFFSET_ 
                                   s     ...       mjd                        
    ---------------- ---------- -------- ... ---------------- ----------------
    RH120001N00          HRI           0 ... 48079.8913773148  0.496 (3c273)\n
    RH701979N00          HRI         354 ... 49726.0977083333  0.190 (3c273)\n
    RP141520N00          PSPCB       485 ... 49540.0447569444  0.496 (3c273)\n

Setting the ``resultmax`` parameter controls the maximum number of results to be
returned. The following will store only the first 10 results:

.. doctest-remote-data::

    >>> table = heasarc.query_object(object_name, mission='rosmaster', resultmax=10)

All of the above parameters can be mixed and matched to refine the query results.

It is also possible to select time range:

.. doctest-remote-data::

    >>> from astroquery.heasarc import Heasarc
    >>> heasarc = Heasarc()
    >>> table = heasarc.query_region('3C273', mission="numaster", radius='1 degree', time='2019-01-01 .. 2020-01-01')
    >>> table.pprint(max_width=120)
                           NAME                           RA     DEC   ... ISSUE_FLAG             SEARCH_OFFSET_           
                                                         deg     deg   ...                                                 
    -------------------------------------------------- -------- ------ ... ---------- -------------------------------------
    3C273                                              187.2473 2.0362 ...          0 2.077 (187.2779220936,2.0523864234)\n


Getting list of available missions
----------------------------------

The `~astroquery.heasarc.HeasarcClass.query_mission_list` method will return a list of available missions
that can be queried.

.. doctest-remote-data::

    >>> from astroquery.heasarc import Heasarc
    >>> heasarc = Heasarc()
    >>> table = heasarc.query_mission_list()
    >>> table.pprint()  #doctest: +IGNORE_OUTPUT
       Mission       Table                                   Table Description
    -------------- ---------- --------------------------------------------------------------------------------
    GALAXY CATALOG      a2pic                                                     HEAO 1 A2 Piccinotti Catalog
    GALAXY CATALOG      abell                                                                   Abell Clusters
    GALAXY CATALOG  abellzcat                                        Abell Clusters Measured Redshifts Catalog
    GALAXY CATALOG  acceptcat               Archive of Chandra Cluster Entropy Profile Tables (ACCEPT) Catalog
    GALAXY CATALOG agnsdssxm2 Sloan Digital Sky Survey/XMM-Newton Type1 AGN X-Ray and Radio Properties Catalog
    GALAXY CATALOG agnsdssxmm              Sloan Digital Sky Survey/XMM-Newton AGN Spectral Properties Catalog
    GALAXY CATALOG allwiseagn                                                   AllWISE Catalog of Mid-IR AGNs
    GALAXY CATALOG       arxa                                         Atlas of Radio/X-Ray Associations (ARXA)
    GALAXY CATALOG ascaegclus                             ASCA Elliptical Galaxies and Galaxy Clusters Catalog
    GALAXY CATALOG   asiagosn                                       Asiago Supernova Catalog (Dynamic Version)
    GALAXY CATALOG baxgalclus                                     BAX X-Ray Galaxy Clusters and Groups Catalog
    GALAXY CATALOG cbatpicagn                  CGRO BATSE-Observed Piccinotti Sample of Active Galactic Nuclei
    GALAXY CATALOG ccosrssfag              Chandra COSMOS Radio-Selected Star-Forming Galaxies and AGN Catalog
    GALAXY CATALOG      cfa2s                                     CfA Redshift Survey: South Galactic Cap Data
    GALAXY CATALOG       cgmw                                          Candidate Galaxies Behind the Milky Way
    GALAXY CATALOG cosmosvlba                            COSMOS Field VLBA Observations 1.4-GHz Source Catalog
    GALAXY CATALOG cosxfirmwc         COSMOS Field X-Ray & FIR Detected AGN Multiwavelength Properties Catalog
    GALAXY CATALOG  denisigal                                         First DENIS I-band Extragalactic Catalog
    GALAXY CATALOG  eingalcat               Catalog of Galaxies Observed by the Einstein Observatory IPC & HRI
    GALAXY CATALOG eingalclus                                Einstein Observatory Clusters of Galaxies Catalog
    GALAXY CATALOG esouppsala                                                        ESO-Uppsala ESO(B) Survey
    GALAXY CATALOG  etgalxray                                   Early-Type Galaxies X-Ray Luminosities Catalog
    GALAXY CATALOG exgalemobj          Hewitt & Burbidge (1991) Catalog of Extragalactic Emission-Line Objects
    GALAXY CATALOG     fricat                                             FIRST Catalog of FR I Radio Galaxies
    GALAXY CATALOG    friicat                                            FIRST Catalog of FR II Radio Galaxies
    GALAXY CATALOG fsvsclustr          Faint Sky Variability Survey Catalog of Galaxy Clusters and Rich Groups
            ...        ...                                                                              ...
        xmm-newton xmmlss10ks   XMM-Newton Large-Scale Structure Uniform 10-ksec Exposure X-Ray Source Catalog
        xmm-newton xmmlssclas              XMM-Newton Large-Scale Structure Optical Counterparts and Redshifts
        xmm-newton xmmlssdeep         XMM-Newton Large-Scale Structure Deep Full-Exposure X-Ray Source Catalog
        xmm-newton  xmmlssoid                 XMM-Newton Large-Scale Structure Optical Identifications Catalog
        xmm-newton  xmmmaster                                           XMM-Newton Master Log & Public Archive
        xmm-newton xmmobstars                                                      XMM-Newton OB Stars Catalog
        xmm-newton   xmmomcat                                                     XMM-Newton OM Object Catalog
        xmm-newton  xmmomcdfs                   XMM-Newton Optical Monitor Chandra Deep Field-South UV Catalog
        xmm-newton   xmmomobj                                             XMM-Newton OM Objects (2008 Version)
        xmm-newton  xmmomsuob                   XMM-Newton Optical Monitor SUSS Catalog, v4.1: Observation IDs
        xmm-newton  xmmomsuss          XMM-Newton Optical Monitor Serendipitous UV Source Survey Catalog, v4.1
        xmm-newton xmmsdssgce                                       2XMMi/SDSS Galaxy Cluster Survey Extension
        xmm-newton xmmsdssgcs                                                 2XMMi/SDSS Galaxy Cluster Survey
        xmm-newton xmmslewcln                                XMM-Newton Slew Survey Clean Source Catalog, v2.0
        xmm-newton xmmslewegs                                      XMM-Newton Slew Survey Extragalactic Sample
        xmm-newton xmmslewful                                 XMM-Newton Slew Survey Full Source Catalog, v2.0
        xmm-newton     xmmssc                      XMM-Newton Serendipitous Source Catalog (4XMM-DR10 Version)
        xmm-newton  xmmsscgps                    XMM-Newton Survey Science Center Survey of the Galactic Plane
        xmm-newton xmmssclwbd                          XMM-Newton 2XMMi-DR3 Selected Source Detections Catalog
        xmm-newton xmmssclwbs                     XMM-Newton 2XMMi-DR3 Selected Source Classifications Catalog
        xmm-newton   xmmstack   XMM-Newton Serendipitous Source Catalog from Stacked Observations (4XMM-DR10s)
        xmm-newton xmmstackob     XMM-Newton Serendipitous Source Catalog from Stacked Observations: Obs. Data
        xmm-newton xmmt2flare                                          2XMM Flares Detected from Tycho-2 Stars
        xmm-newton  xmmvaragn                                   Ensemble X-Ray Variability of AGN in 2XMMi-DR3
        xmm-newton xmmxassist                                                   XMM-Newton XAssist Source List
        xmm-newton        xms                        XMM-Newton Medium Sensitivity Survey (XMS) Source Catalog
        xmm-newton       xwas                                                     XMM-Newton Wide Angle Survey
    Length = 1160 rows


The returned table includes both the names and a short description of each
mission table.


Using alternative HEASARC servers
---------------------------------

It is possible to set alternative locations for HEASARC servers. One such location
is hosted by `INTEGRAL Science Data Center <https://www.isdc.unige.ch/>`_, and has further
tables listing the most recent INTEGRAL data.

.. doctest-remote-data::

    >>> from astroquery.heasarc import Heasarc, Conf
    >>> heasarc = Heasarc()
    >>> Conf.server.set('https://www.isdc.unige.ch/browse/w3query.pl')
    >>> table = heasarc.query_mission_list()
    >>> table.pprint(max_width=120)
       Mission            Table                         Table Description
    ------------- ---------------------- -----------------------------------------------
    CTASST1M-REV1     cta_sst1m_rev1_run                                             Run
        FACT-REV1          fact_rev1_run                                             Run
    INTEGRAL-REV3     integral_rev3_prop                                       Proposals
    INTEGRAL-REV3 integral_rev3_prop_obs Proposal Information and Observation Parameters
    INTEGRAL-REV3      integral_rev3_scw                       SCW - Science Window Data
    >>>
    >>> table = heasarc.query_object('Crab', mission='integral_rev3_scw',
    ...                              radius='361 degree', time="2022-12-01 .. 2022-12-31",
    ...                              sortvar='START_DATE', resultmax=100000)
    >>> table.pprint() # doctest: +IGNORE_OUTPUT
       SCW_ID    SCW_VER SCW_TYPE ... GOOD_OMC   DSIZE     SEARCH_OFFSET_ 
    ------------ ------- -------- ... -------- --------- -----------------
    258300400010 001     POINTING ...        0 123494400 5199.027 (CRAB)\n
    258400320021 001     SLEW     ...        0   5799936 5082.095 (CRAB)\n
    258400260021 001     SLEW     ...        0   5791744 5104.388 (CRAB)\n
    258400350010 001     POINTING ...        0 123146240 5167.027 (CRAB)\n
    258700350021 001     SLEW     ...        0   5750784 5120.836 (CRAB)\n
    258400330010 001     POINTING ...        0 123179008 5067.991 (CRAB)\n
    258400260010 001     POINTING ...        0 123371520 5093.007 (CRAB)\n
             ...     ...      ... ...      ...       ...               ...
    258400270021 001     SLEW     ...        0 126386176 5114.308 (CRAB)\n
    258400270010 001     POINTING ...        0   1200128 5113.839 (CRAB)\n
    258700360010 001     POINTING ...        0 122130432 5136.165 (CRAB)\n
    258200770010 001     POINTING ...        0   1490944 4184.684 (CRAB)\n
    258200770021 001     SLEW     ...        0    962560 4184.587 (CRAB)\n
    258200780010 001     POINTING ...        0   1585152 4184.378 (CRAB)\n
    258700340021 001     SLEW     ...        0   5779456 5181.635 (CRAB)\n
    Length = 1601 rows


Troubleshooting
===============

If you are repeatedly getting failed queries, or bad/out-of-date results, try clearing your cache:

.. code-block:: python

    >>> from astroquery.heasarc import Heasarc
    >>> Heasarc.clear_cache()

If this function is unavailable, upgrade your version of astroquery. 
The ``clear_cache`` function was introduced in version 0.4.7.dev8479.


Reference/API
=============

.. automodapi:: astroquery.heasarc
    :no-inheritance-diagram:
