.. _astroquery.heasarc:

**************************************
HEASARC Queries (`astroquery.heasarc`)
**************************************

Getting started
===============

This is a python interface for querying the
`HEASARC <https://heasarc.gsfc.nasa.gov/>`__
archive web service.

The capabilities are currently very limited ... feature requests and contributions welcome!

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
       SEQ_ID   INSTRUMENT EXPOSURE         NAME            RA     DEC      START_TIME        END_TIME      SEARCH_OFFSET_
                              S                           DEGREE  DEGREE       MJD              MJD
    ----------- ---------- -------- -------------------- -------- ------ ---------------- ---------------- ---------------
    RH701576N00 HRI           68154 3C 273               187.2800 2.0500 49704.3090856482 49724.6236226852  0.190 (3C273)
    <BLANKLINE>
    RP600242A01 PSPCB         24822 GIOVANELLI-HAYNES CL 186.9300 1.6000 48980.6468865741 48982.9284837963 34.236 (3C273)
    <BLANKLINE>
    RH700234N00 HRI           17230 3C 273               187.2800 2.0500 48629.2693055556 48632.4716782407  0.190 (3C273)
    <BLANKLINE>

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
       SEQ_ID   INSTRUMENT EXPOSURE ...    START_TIME        END_TIME                     SEARCH_OFFSET_
                              S     ...       MJD              MJD
    ----------- ---------- -------- ... ---------------- ---------------- ----------------------------------------------
    RH701576N00 HRI           68154 ... 49704.3090856482 49724.6236226852  0.191 (187.2779228198005,2.0524148595265435)
    <BLANKLINE>
    RP600242A01 PSPCB         24822 ... 48980.6468865741 48982.9284837963 34.237 (187.2779228198005,2.0524148595265435)
    <BLANKLINE>
    RH700234N00 HRI           17230 ... 48629.2693055556 48632.4716782407  0.191 (187.2779228198005,2.0524148595265435)
    <BLANKLINE>

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
       S      DEGREE  DEGREE
    -------- -------- ------ ---------------
       68154 187.2800 2.0500  0.190 (3C273)
    <BLANKLINE>
       24822 186.9300 1.6000 34.236 (3C273)
    <BLANKLINE>
       17230 187.2800 2.0500  0.190 (3C273)

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
       SEQ_ID   INSTRUMENT EXPOSURE ...     END_TIME      SEARCH_OFFSET_
                              S     ...       MJD
    ----------- ---------- -------- ... ---------------- ---------------
    RH120001N00 HRI               0 ... 48079.8913773148  0.496 (3C273)
    <BLANKLINE>
    RH701979N00 HRI             354 ... 49726.0977083333  0.190 (3C273)
    <BLANKLINE>
    RP141520N00 PSPCB           485 ... 49540.0447569444  0.496 (3C273)
    <BLANKLINE>

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
    >>> table.pprint()
     NAME    RA    ... ISSUE_FLAG                 SEARCH_OFFSET_
           DEGREE  ...
    ----- -------- ... ---------- ----------------------------------------------
    3C273 187.2473 ...          0 2.077 (187.27792209362673,2.0523864234098044)
    <BLANKLINE>


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

It is possible to set alternative locations for HEASARC server. One such location
is hosted by `INTEGRAL Science Data Center <https://www.isdc.unige.ch/>`_, and has further
tables listing most recent INTEGRAL data.

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
    ...                              radius='361 degree', time="2021-02-01 .. 2030-12-01",
    ...                              sortvar='START_DATE', resultmax=100000)
    >>> table.pprint()
       SCW_ID    SCW_VER SCW_TYPE    RA_X    ... GOOD_OMC   DSIZE   _SEARCH_OFFSET
                                             ...
    ------------ ------- -------- ---------- ... -------- --------- --------------
    232600870020 001     POINTING  48.302208 ...      370  20242432       2004.207
    232600870031 001     SLEW      47.182667 ...        0   1380352       2328.123
    232600880010 001     POINTING  46.372791 ...        0   1572864       2730.070
    232600880021 001     SLEW      46.357828 ...        0    917504       2729.667
    232600890010 001     POINTING  46.323544 ...        0   2244608       2728.770
    ...

Reference/API
=============

.. automodapi:: astroquery.heasarc
    :no-inheritance-diagram:
