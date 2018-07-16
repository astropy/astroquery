.. doctest-skip-all

.. _astroquery.cds:

**********************************
CDS MOC Service (`astroquery.cds`)
**********************************

Getting started
===============

This module provides a python interface for querying the `CDS MOCServer`_.

MOC is an `IVOA standard`_ enabling description of arbitrary sky regions. Based on the HEALPix sky tessellation, it maps
regions on the sky into hierarchically grouped predefined cells. It corresponds to a set of HEALPix cells at different
orders.

For those wanting to know more about MOCs, please refer to this `IVOA paper
<http://ivoa.net/documents/MOC/20140602/REC-MOC-1.0-20140602.pdf>`_ and the `MOCPy's documentation
<https://github.com/cds-astro/mocpy>`_ developed by the CDS.

CDS has set up a server known as the `MOCServer <http://alasky.unistra.fr/MocServer/query?>`_ storing data-set names
each associated with a MOC spatial coverage and some meta-datas giving a more detailed explanation of the data-set.

The MOCServer aims at returning the data-sets having at least one source lying in a specific sky region defined by the
user. Internally the MOCServer performs the intersection between the given sky region and the MOCs associated with each
data-sets. Because the MOC associated to a data-set describes its sky coverage, if the above intersection is not null
then the MOCServer knows that some sources of this data-set are in the user defined sky region.

To be aware of what the MOCServer returns, please refers to this `link
<http://alasky.unistra.fr/MocServer/query?RA=10.8&DEC=32.2&SR=1.5&intersect=overlaps&get=record&fmt=html>`_.
We have queried the MOCServer with a cone region of center ra, dec = (10.8, 32.2) deg and radius = 1.5 deg. In return,
the MOCServer gives a list of data-sets each tagged with an unique ID along with some other meta-datas too e.g.
``obs_title``, ``obs_description``, ``moc_access_url`` (url for accessing the MOC associated with the data-set. Usually
a FITS file storing a list of HEALPix cells).

It is also possible to ask the MOCServer for retrieving data-sets based on their meta-data values. `Here
<http://alasky.unistra.fr/MocServer/query?RA=10.8&DEC=32.2&SR=1.5&intersect=overlaps&get=record&fmt=html&expr=(dataproduct_type=image)>`_
we have queried the MOCServer for only the image data-sets being in the cone defined above (``dataproduct_type``
meta-data equals to ``"image"``).

Requirements
----------------------------------------------------
The following packages are required for the use of this module:

* `astropy-healpix`_
* `mocpy`_
* `regions`_

Examples
========

Performing a CDS MOC query on a cone region
-------------------------------------------

The first thing to do is to import the `regions`_ and the ``cds`` module.

.. code-block:: python

    >>> from astropy import coordinates
    >>> from regions import CircleSkyRegion
    >>> from astroquery.cds import cds

``cds`` implements only the method :meth:`~astroquery.cds.CdsClass.query_region`.
We need to define a cone region. For that purpose we will instantiate a `regions.CircleSkyRegion` object:

.. code-block:: python

    >>> center = coordinates.SkyCoord(10.8, 32.2, unit='deg')
    >>> radius = coordinates.Angle(1.5, unit='deg')

    >>> cone = CircleSkyRegion(center, radius)

And basically call the :meth:`~astroquery.cds.CdsClass.query_region` method with the cone and that's all.

.. code-block:: python

    >>> cds.query_region(region=cone)
             tap_tablename       hips_status_7              hips_creator                hipsgen_date_1  ...   hipsgen_date_6                 hips_service_url_4                hips_pixel_bitpix hips_order_4
    ------------------------ ------------- -------------------------------------- ----------------- ... ----------------- ------------------------------------------------ ----------------- ------------
    ivoa.B/assocdata/obscore             -                                      -                 - ...                 -                                                -                 -            -
          viz7.B/cb/lmxbdata             -                                      -                 - ...                 -                                                -                 -            -
           vcds1.B/cfht/cfht             -                                      -                 - ...                 -                                                -                 -            -
        vcds1.B/cfht/obscore             -                                      -                 - ...                 -                                                -                 -            -
      viz1.B/chandra/chandra             -                                      -                 - ...                 -                                                -                 -            -
         vcds1.B/eso/eso_arc             -                                      -                 - ...                 -                                                -                 -            -
        viz1.B/gcvs/gcvs_cat             -                                      -                 - ...                 -                                                -                 -            -
         viz1.B/gcvs/nsv_cat             -                                      -                 - ...                 -                                                -                 -            -
      vcds1.B/gemini/obscore             -                                      -                 - ...                 -                                                -                 -            -
           viz1.B/hst/hstlog             -                                      -                 - ...                 -                                                -                 -            -
         vcds1.B/hst/obscore             -                                      -                 - ...                 -                                                -                 -            -
            viz1.B/hst/wfpc2             -                                      -                 - ...                 -                                                -                 -            -
        vcds1.B/jcmt/obscore             -                                      -                 - ...                 -                                                -                 -            -
        viz4.B/merlin/merlin             -                                      -                 - ...                 -                                                -                 -            -
           viz7.B/mk/mktypes             -                                      -                 - ...                 -                                                -                 -            -
        viz7.B/pastel/pastel             -                                      -                 - ...                 -                                                -                 -            -
             viz7.B/sb9/main             -                                      -                 - ...                 -                                                -                 -            -
             viz7.B/sn/sncat             -                                      -                 - ...                 -                                                -                 -            -
       vbig.B/subaru/suprimc             -                                      -                 - ...                 -                                                -                 -            -
       vizB.B/swift/swiftlog             -                                      -                 - ...                 -                                                -                 -            -
              vizC.B/vsx/vsx             -                                      -                 - ...                 -                                                -                 -            -
           viz7.B/wd/catalog             -                                      -                 - ...                 -                                                -                 -            -
              vizC.B/wds/wds             -                                      -                 - ...                 -                                                -                 -            -
           viz4.B/xmm/xmmlog             -                                      -                 - ...                 -                                                -                 -            -
                           -             -                            CDS (C.Bot)                 - ...                 -                                                -              16.0            -
                           -             -                           M.Buga [CDS] 2017-06-23T19:52Z ...                 - https://alaskybis.u-strasbg.fr/HI4PI/C_HI4PI_NHI             -32.0            -
             viz1.I/100A/w10             -                                      -                 - ...                 -                                                -                 -            -
             viz1.I/100A/w25             -                                      -                 - ...                 -                                                -                 -            -
             viz1.I/100A/w50             -                                      -                 - ...                 -                                                -                 -            -
                         ...           ...                                    ...               ... ...               ...                                              ...               ...          ...
                           -             -                                      -                 - ...                 -                                                -             -32.0            -
                           -             -                                      -                 - ...                 -                                                -             -32.0            -
                           -             -                                      -                 - ...                 -                                                -             -32.0            -
                           -             -                                      -                 - ...                 -                                                -             -32.0            -
                           -             -                 D. Paradis (IRAP/CADE) 2017-12-13T13:32Z ...                 -                                                -             -32.0            -
                           -             -                 D. Paradis (IRAP/CADE) 2017-12-13T13:33Z ...                 -                                                -             -32.0            -
                           -             -                 D. Paradis (IRAP/CADE) 2016-09-15T13:35Z ...                 -                                                -             -32.0            -
                           -             -                 D. Paradis (IRAP/CADE) 2017-02-09T13:41Z ... 2017-02-09T13:48Z                                                -             -32.0            -
                           -             -                 D. Paradis (IRAP/CADE) 2018-03-05T09:11Z ...                 -                                                -             -32.0            -
                           -             -                 D. Paradis (IRAP/CADE) 2018-03-05T09:27Z ...                 -                                                -             -32.0            -
                           -             -                 D. Paradis (IRAP/CADE) 2016-09-15T14:23Z ...                 -                                                -             -32.0            -
                           -             -                                      -                 - ...                 -                                                -             -32.0            -
                           -             -                                      -                 - ...                 -                                                -             -32.0            -
                           -             -                                      -                 - ...                 -                                                -             -32.0            -
                           -             -                                      -                 - ...                 -                                                -             -32.0            -
                           -             -                                      -                 - ...                 -                                                -             -32.0            -
                           -             -                 D. Paradis (IRAP/CADE) 2017-12-07T09:56Z ...                 -                                                -             -32.0            -
                           -             -                 D. Paradis (IRAP/CADE) 2017-12-06T12:48Z ...                 -                                                -             -32.0            -
                           -             -                                      -                 - ...                 -                                                -             -32.0            -
                           -             -                                      -                 - ...                 -                                                -             -32.0            -
                           -             -                                      -                 - ...                 -                                                -             -32.0            -
                           -             -                                      -                 - ...                 -                                                -             -32.0            -
                           -             -                 D. Paradis (IRAP/CADE) 2016-09-15T14:43Z ...                 -                                                -             -32.0            -
                           -             -                 D. Paradis (IRAP/CADE) 2018-03-12T15:45Z ...                 -                                                -             -32.0            -
                           -             -                 D. Paradis (IRAP/CADE) 2018-03-12T14:47Z ...                 -                                                -             -32.0            -
                           -             -                 D. Paradis (IRAP/CADE) 2017-05-15T12:23Z ...                 -                                                -             -32.0            -
                           -             - L. Michel [Observatoire de Strasbourg] 2018-07-10T06:48Z ...                 -                                                -                 -            -
                           -             - L. Michel [Observatoire de Strasbourg] 2018-07-09T16:14Z ...                 -                                                -             -32.0            -
                           -             - L. Michel [Observatoire de Strasbourg] 2018-07-09T17:43Z ...                 -                                                -             -32.0            -
                           -             - L. Michel [Observatoire de Strasbourg] 2018-07-09T19:15Z ...                 -                                                -             -32.0            -
    Length = 1289 rows

You can query the MOCServer on a `regions.PolygonSkyRegion` or even an `mocpy.MOC` following the same pattern i.e. just
by replacing ``cone`` with a polygon or a MOC object.


By default, :meth:`~astroquery.cds.CdsClass.query_region` returns an `astropy.table.Table` object storing the data-sets
as rows and their meta-datas as columns. Data-sets might have no information for a specific meta-data. If so, the value
associated with this meta-data for this data-set is set to "-". The above astropy table looks like :


Retrieve only a subset of meta-datas
------------------------------------

This table refers to a lot of meta-datas whereas we could use only a few of them. In fact, it is possible to ask the
MOCServer to give us only a reduced set of meta-datas for the resulting data-sets. The table returned by the MOCServer
will be lighter and thus faster to retrieve.

The parameter ``fields`` of :meth:`~astroquery.cds.CdsClass.query_region` allows us to provide the list of meta-datas we
want to get. Let's say we would like only the ``ID``, the ``moc_sky_fraction`` and the ``moc_access_url`` of the
resulting data-sets. We just have to do:

.. code-block:: python

    >>> cds.query_region(region=cone, fields=['ID', 'moc_sky_fraction', 'moc_access_url'])
    moc_sky_fraction                  ID                                                     moc_access_url
    ---------------- ------------------------------------ ------------------------------------------------------------------------------------
              0.0588              CDS/B/assocdata/obscore http://alasky.unistra.fr/footprints/tables/vizier/B_assocdata_obscore/MOC?nside=2048
           2.066e-06                    CDS/B/cb/lmxbdata       http://alasky.unistra.fr/footprints/tables/vizier/B_cb_lmxbdata/MOC?nside=2048
            0.002134                      CDS/B/cfht/cfht         http://alasky.unistra.fr/footprints/tables/vizier/B_cfht_cfht/MOC?nside=2048
            0.003107                   CDS/B/cfht/obscore      http://alasky.unistra.fr/footprints/tables/vizier/B_cfht_obscore/MOC?nside=2048
           0.0001764                CDS/B/chandra/chandra   http://alasky.unistra.fr/footprints/tables/vizier/B_chandra_chandra/MOC?nside=2048
            0.008365                    CDS/B/eso/eso_arc       http://alasky.unistra.fr/footprints/tables/vizier/B_eso_eso_arc/MOC?nside=2048
           0.0009891                  CDS/B/gcvs/gcvs_cat     http://alasky.unistra.fr/footprints/tables/vizier/B_gcvs_gcvs_cat/MOC?nside=2048
           0.0004252                   CDS/B/gcvs/nsv_cat      http://alasky.unistra.fr/footprints/tables/vizier/B_gcvs_nsv_cat/MOC?nside=2048
           0.0006163                 CDS/B/gemini/obscore    http://alasky.unistra.fr/footprints/tables/vizier/B_gemini_obscore/MOC?nside=2048
           0.0008544                     CDS/B/hst/hstlog        http://alasky.unistra.fr/footprints/tables/vizier/B_hst_hstlog/MOC?nside=2048
           0.0009243                    CDS/B/hst/obscore       http://alasky.unistra.fr/footprints/tables/vizier/B_hst_obscore/MOC?nside=2048
             0.00016                      CDS/B/hst/wfpc2         http://alasky.unistra.fr/footprints/tables/vizier/B_hst_wfpc2/MOC?nside=2048
            0.000729                   CDS/B/jcmt/obscore      http://alasky.unistra.fr/footprints/tables/vizier/B_jcmt_obscore/MOC?nside=2048
           2.998e-05                  CDS/B/merlin/merlin     http://alasky.unistra.fr/footprints/tables/vizier/B_merlin_merlin/MOC?nside=2048
             0.01136                     CDS/B/mk/mktypes        http://alasky.unistra.fr/footprints/tables/vizier/B_mk_mktypes/MOC?nside=2048
           0.0006112                  CDS/B/pastel/pastel     http://alasky.unistra.fr/footprints/tables/vizier/B_pastel_pastel/MOC?nside=2048
           6.632e-05                       CDS/B/sb9/main          http://alasky.unistra.fr/footprints/tables/vizier/B_sb9_main/MOC?nside=2048
           0.0001141                       CDS/B/sn/sncat          http://alasky.unistra.fr/footprints/tables/vizier/B_sn_sncat/MOC?nside=2048
           0.0008666                 CDS/B/subaru/suprimc    http://alasky.unistra.fr/footprints/tables/vizier/B_subaru_suprimc/MOC?nside=2048
            0.001025                 CDS/B/swift/swiftlog    http://alasky.unistra.fr/footprints/tables/vizier/B_swift_swiftlog/MOC?nside=2048
            0.008088                        CDS/B/vsx/vsx           http://alasky.unistra.fr/footprints/tables/vizier/B_vsx_vsx/MOC?nside=2048
            0.000282                     CDS/B/wd/catalog        http://alasky.unistra.fr/footprints/tables/vizier/B_wd_catalog/MOC?nside=2048
            0.002413                        CDS/B/wds/wds           http://alasky.unistra.fr/footprints/tables/vizier/B_wds_wds/MOC?nside=2048
           0.0001468                     CDS/B/xmm/xmmlog        http://alasky.unistra.fr/footprints/tables/vizier/B_xmm_xmmlog/MOC?nside=2048
              0.3164                 CDS/C/GALFAHI/Narrow                                                                                    -
                 1.0                       CDS/C/HI4PI/HI                                                                                    -
           4.444e-05                       CDS/I/100A/w10          http://alasky.unistra.fr/footprints/tables/vizier/I_100A_w10/MOC?nside=2048
           4.641e-05                       CDS/I/100A/w25          http://alasky.unistra.fr/footprints/tables/vizier/I_100A_w25/MOC?nside=2048
             0.00044                       CDS/I/100A/w50          http://alasky.unistra.fr/footprints/tables/vizier/I_100A_w50/MOC?nside=2048
                 ...                                  ...                                                                                  ...
                 1.0                 ov-gso/P/DIRBE/ZSMA6                                                                                    -
                 1.0                 ov-gso/P/DIRBE/ZSMA7                                                                                    -
                 1.0                 ov-gso/P/DIRBE/ZSMA8                                                                                    -
                 1.0                 ov-gso/P/DIRBE/ZSMA9                                                                                    -
                 1.0   ov-gso/P/DRAO-VillaElisa/21cm/POLQ                                                                                    -
                 1.0   ov-gso/P/DRAO-VillaElisa/21cm/POLU                                                                                    -
              0.7283                  ov-gso/P/DRAO/22MHz                                                                                    -
              0.5723            ov-gso/P/DWINGELOO/820MHz                                                                                    -
              0.5468                       ov-gso/P/EBHIS                                                                                    -
                 1.0                  ov-gso/P/GASS+EBHIS                                                                                    -
              0.8623                ov-gso/P/GAURIBIDANUR                                                                                    -
                 1.0                      ov-gso/P/IRIS/1                                                                                    -
                 1.0                      ov-gso/P/IRIS/2                                                                                    -
                 1.0                      ov-gso/P/IRIS/3                                                                                    -
                 1.0                      ov-gso/P/IRIS/4                                                                                    -
                 1.0                         ov-gso/P/LAB                                                                                    -
              0.9635                    ov-gso/P/MAIPU-MU                                                                                    -
              0.4284                      ov-gso/P/MITEoR                                                                                    -
                 1.0                        ov-gso/P/RASS                                                                                    -
                 1.0                    ov-gso/P/RASS/EXP                                                                                    -
                 1.0               ov-gso/P/RASS/HardBand                                                                                    -
                 1.0               ov-gso/P/RASS/SoftBand                                                                                    -
                 1.0 ov-gso/P/STOCKERT+VILLAELISA/1420MHz                                                                                    -
               0.181                   ov-gso/P/VTSS/CONT                                                                                    -
              0.1918                     ov-gso/P/VTSS/Ha                                                                                    -
                 1.0                        ov-gso/P/WHAM                                                                                    -
             0.08287                xcatdb/P/XMM/PN/color                                                                                    -
             0.02227                  xcatdb/P/XMM/PN/eb2                                                                                    -
             0.02227                  xcatdb/P/XMM/PN/eb3                                                                                    -
             0.02227                  xcatdb/P/XMM/PN/eb4                                                                                    -
    Length = 1289 rows

This astropy table now have only 3 columns and can be manipulated much faster.

Retrieving data-sets based on their meta-data values
----------------------------------------------------

As expressed in the last paragraph of the Getting Started section, we can ask the MOCServer to do some filtering tasks for us
at the server side. The ``meta_data`` parameter of :meth:`~astroquery.cds.CdsClass.query_region` allows the user to
write an algebraic expression on the meta-datas. Let's query the MOCServer for retrieving what we have done using the
web interface in the Getting Started section i.e. retrieving only the image data-sets that lie in the previously defined cone.

.. code-block:: python

    >>> cds.query_region(region=cone,
    ...                  fields=['ID', 'dataproduct_type', 'moc_sky_fraction', 'moc_access_url'],
    ...                  meta_data="dataproduct_type=image")
    moc_sky_fraction                              moc_access_url                                                 ID                   dataproduct_type
    ---------------- ------------------------------------------------------------------------ --------------------------------------- ----------------
                 1.0                              http://alasky.u-strasbg.fr/2MASS/H/Moc.fits                           CDS/P/2MASS/H            image
                 1.0                              http://alasky.u-strasbg.fr/2MASS/J/Moc.fits                           CDS/P/2MASS/J            image
                 1.0                              http://alasky.u-strasbg.fr/2MASS/K/Moc.fits                           CDS/P/2MASS/K            image
                 1.0                          http://alasky.u-strasbg.fr/2MASS/Color/Moc.fits                       CDS/P/2MASS/color            image
                 1.0                 http://alasky.u-strasbg.fr/AKARI-FIS/ColorLSN60/Moc.fits                   CDS/P/AKARI/FIS/Color            image
              0.9988                       http://alasky.u-strasbg.fr/AKARI-FIS/N160/Moc.fits                    CDS/P/AKARI/FIS/N160            image
              0.9976                        http://alasky.u-strasbg.fr/AKARI-FIS/N60/Moc.fits                     CDS/P/AKARI/FIS/N60            image
              0.9989                      http://alasky.u-strasbg.fr/AKARI-FIS/WideL/Moc.fits                   CDS/P/AKARI/FIS/WideL            image
              0.9976                      http://alasky.u-strasbg.fr/AKARI-FIS/WideS/Moc.fits                   CDS/P/AKARI/FIS/WideS            image
                 1.0                                                                        -                     CDS/P/Ariel/Voyager            image
                 1.0                                   http://alasky.u-strasbg.fr/CO/Moc.fits                                CDS/P/CO            image
                 1.0                                                                        - CDS/P/Callisto/Voyager-Galileo-simp-1km            image
                 1.0                                                                        -        CDS/P/Charon/NewHorizon-PIA19866            image
                 1.0                                                                        -            CDS/P/DM/flux-Bp/I/345/gaia2            image
                 1.0                                                                        -             CDS/P/DM/flux-G/I/345/gaia2            image
                 1.0                                                                        -            CDS/P/DM/flux-Rp/I/345/gaia2            image
                 1.0                                                                        - CDS/P/DM/flux-color-Rp-G-Bp/I/345/gaia2            image
              0.9943                                                                        -                          CDS/P/DSS2/NIR            image
              0.9956                   http://alasky.u-strasbg.fr/DSS/DSS2-blue-XJ-S/Moc.fits                         CDS/P/DSS2/blue            image
                 1.0                         http://alasky.u-strasbg.fr/DSS/DSSColor/Moc.fits                        CDS/P/DSS2/color            image
                 1.0                       http://alasky.u-strasbg.fr/DSS/DSS2Merged/Moc.fits                          CDS/P/DSS2/red            image
                 1.0                                                                        -            CDS/P/Dione/Cassini-PIA12577            image
                 1.0    http://alasky.u-strasbg.fr/EGRET/EGRET-dif/EGRET_dif_100-150/Moc.fits                 CDS/P/EGRET/Dif/100-150            image
                 1.0  http://alasky.u-strasbg.fr/EGRET/EGRET-dif/EGRET_dif_1000-2000/Moc.fits               CDS/P/EGRET/Dif/1000-2000            image
                 1.0    http://alasky.u-strasbg.fr/EGRET/EGRET-dif/EGRET_dif_150-300/Moc.fits                 CDS/P/EGRET/Dif/150-300            image
                 1.0  http://alasky.u-strasbg.fr/EGRET/EGRET-dif/EGRET_dif_2000-4000/Moc.fits               CDS/P/EGRET/Dif/2000-4000            image
                 1.0      http://alasky.u-strasbg.fr/EGRET/EGRET-dif/EGRET_dif_30-50/Moc.fits                   CDS/P/EGRET/Dif/30-50            image
                 1.0    http://alasky.u-strasbg.fr/EGRET/EGRET-dif/EGRET_dif_300-500/Moc.fits                 CDS/P/EGRET/Dif/300-500            image
                 1.0 http://alasky.u-strasbg.fr/EGRET/EGRET-dif/EGRET_dif_4000-10000/Moc.fits              CDS/P/EGRET/Dif/4000-10000            image
                 ...                                                                      ...                                     ...              ...
                 1.0                                                                        -                    ov-gso/P/DIRBE/ZSMA6            image
                 1.0                                                                        -                    ov-gso/P/DIRBE/ZSMA7            image
                 1.0                                                                        -                    ov-gso/P/DIRBE/ZSMA8            image
                 1.0                                                                        -                    ov-gso/P/DIRBE/ZSMA9            image
                 1.0                                                                        -      ov-gso/P/DRAO-VillaElisa/21cm/POLQ            image
                 1.0                                                                        -      ov-gso/P/DRAO-VillaElisa/21cm/POLU            image
              0.7283                                                                        -                     ov-gso/P/DRAO/22MHz            image
              0.5723                                                                        -               ov-gso/P/DWINGELOO/820MHz            image
              0.5468                                                                        -                          ov-gso/P/EBHIS            image
                 1.0                                                                        -                     ov-gso/P/GASS+EBHIS            image
              0.8623                                                                        -                   ov-gso/P/GAURIBIDANUR            image
                 1.0                                                                        -                         ov-gso/P/IRIS/1            image
                 1.0                                                                        -                         ov-gso/P/IRIS/2            image
                 1.0                                                                        -                         ov-gso/P/IRIS/3            image
                 1.0                                                                        -                         ov-gso/P/IRIS/4            image
                 1.0                                                                        -                            ov-gso/P/LAB            image
              0.9635                                                                        -                       ov-gso/P/MAIPU-MU            image
              0.4284                                                                        -                         ov-gso/P/MITEoR            image
                 1.0                                                                        -                           ov-gso/P/RASS            image
                 1.0                                                                        -                       ov-gso/P/RASS/EXP            image
                 1.0                                                                        -                  ov-gso/P/RASS/HardBand            image
                 1.0                                                                        -                  ov-gso/P/RASS/SoftBand            image
                 1.0                                                                        -    ov-gso/P/STOCKERT+VILLAELISA/1420MHz            image
               0.181                                                                        -                      ov-gso/P/VTSS/CONT            image
              0.1918                                                                        -                        ov-gso/P/VTSS/Ha            image
                 1.0                                                                        -                           ov-gso/P/WHAM            image
             0.08287                                                                        -                   xcatdb/P/XMM/PN/color            image
             0.02227                                                                        -                     xcatdb/P/XMM/PN/eb2            image
             0.02227                                                                        -                     xcatdb/P/XMM/PN/eb3            image
             0.02227                                                                        -                     xcatdb/P/XMM/PN/eb4            image
    Length = 279 rows

Looking at the ``dataproduct_type`` column, all the data-sets seem to be images. We could have been done that using
numpy operations on `astropy.table.Table` objects but here the MOCServer made it for us.

`This page <http://alasky.unistra.fr/MocServer/example>`_ on the web interface of the MOCServer gives some examples of filtering expressions.

Misc
----

Limiting the number of returned data-sets
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Another parameter called ``max_rec`` specifies an upper limit for the number of data-sets to be returned:

.. code-block:: python

    >>> cds.query_region(region=cone, max_rec=3)
         tap_tablename       publisher_id ... vizier_popularity
    ------------------------ ------------ ... -----------------
    ivoa.B/assocdata/obscore    ivo://CDS ...               7.0
          viz7.B/cb/lmxbdata    ivo://CDS ...               2.0
           vcds1.B/cfht/cfht    ivo://CDS ...               5.0

This astropy table has only 3 rows although we know more data-sets match the query. It's useful if you do not need
to retrieve all the data-sets matching a query but only a few. Again, the result will come faster from the MOCServer because
this operation is done at the server side.

Returning a `~mocpy.MOC` object as a result
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Some users might want the union of all the MOCs from the data-sets matching the query. You can get a `mocpy.MOC` object
instead of an `astropy.table.Table` by setting the parameter ``return_moc`` to True. An additional parameter ``max_norder``
allows the user to set the resolution/precision of the returned MOC that he wants.

As an example, we would like to obtain the union of the spatial coverage of all the Hubble surveys:

.. code-block:: python

    >>> from mocpy import MOC
    >>> # We want to retrieve all the HST surveys i.e. the HST surveys covering any region of the sky.
    >>> allsky = CircleSkyRegion(coordinates.SkyCoord(0, 0, unit="deg"), coordinates.Angle(180, unit="deg"))
    >>> moc = cds.query_region(region=allsky,
    ... # We want a mocpy object instead of an astropy table
    ...                        return_moc=True,
    ... # The order of the MOC
    ...                         max_norder=7,
    ... # Expression on the ID meta-data
    ...                        meta_data="ID=*HST*")
    >>> moc.plot(title='Union of the spatial coverage of all the Hubble surveys.')

.. image:: ./HST_union.png


Reference/API
=============

.. automodapi:: astroquery.cds
    :no-inheritance-diagram:


.. _CDS MOCServer: http://alasky.unistra.fr/MocServer/query
.. _IVOA standard: http://ivoa.net/documents/MOC/20140602/REC-MOC-1.0-20140602.pdf
.. _astropy-healpix: http://astropy-healpix.readthedocs.io/en/latest/
.. _regions: https://github.com/astropy/regions
.. _mocpy: https://github.com/cds-astro/mocpy
