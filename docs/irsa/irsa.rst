.. doctest-skip-all

.. _astroquery.irsa:

********************************
IRSA Queries (`astroquery.irsa`)
********************************

Getting started
===============


This module can has methods to perform different types of queries on the
catalogs present in the IRSA general catalog service. All queries can be
performed by calling :meth:`~astroquery.irsa.IrsaClass.query_region`, with
different keyword arguments. There are 4 different region queries that are
supported: ``Cone``, ``Box``, ``Polygon`` and ``All-Sky``. All successful
queries return the results in a `~astropy.table.Table`.  We now look at some
examples.

Available catalogs
------------------

All region queries require a ``catalog`` keyword argument, which is the name of
the catalog in the IRSA database, on which the query must be performed. To take
a look at all the available catalogs:

.. code-block:: python

    >>> from astroquery.irsa import Irsa
    >>> Irsa.list_catalogs()

    {'a1763t2': 'Abell 1763 Source Catalog',
     'a1763t3': 'Abell 1763 MIPS 70 micron Catalog',
     'acs_iphot_sep07': 'COSMOS ACS I-band photometry catalog September 2007',
     'akari_fis': 'Akari/FIS Bright Source Catalogue',
     'akari_irc': 'Akari/IRC Point Source Catalogue',
     'astsight': 'IRAS Minor Planet Survey',
     ...
     ...
     'xmm_cat_s05': "SWIRE XMM_LSS Region Spring '05 Spitzer Catalog"}

This returns a dictionary of catalog names with their description. If you would
rather just print out this information:

.. code-block:: python

    >>> from astroquery.irsa import Irsa
    >>> Irsa.print_catalogs()

    wise_allsky_2band_p1bm_frm      WISE Post-Cryo Single Exposure (L1b) Image Inventory Table
    wise_allsky_4band_p3as_psr      WISE All-Sky Reject Table
    cosmos_morph_col_1              COSMOS Zamojski Morphology Catalog v1.0
    wise_prelim_p3al_lod            WISE Preliminary Release Atlas Inventory Table (Superseded)
    com_pccs1_100                   Planck PCCS 100GHz Catalog
    swire_lhisod                    SWIRE Lockman Hole ISOCAM Deep Field Catalog
    ...
    ...
    sdwfs_ch1_epoch3                SDWFS Aug '09 DR1.1 IRAC 3.6um-Selected 3x30sec Coadd, epoch 3 (Feb '08)

Performing a cone search
------------------------

A cone search query is performed by setting the ``spatial`` keyword to
``Cone``. The target name or the coordinates of the search center must also be
specified. The radius for the cone search may also be specified - if this is
missing, it defaults to a value of 10 arcsec. The radius may be specified in
any appropriate unit using a `~astropy.units.Quantity` object. It may also be
entered as a string that is parsable by `~astropy.coordinates.Angle`.

.. code-block:: python

    >>> from astroquery.irsa import Irsa
    >>> import astropy.units as u
    >>> table = Irsa.query_region("m31", catalog="fp_psc", spatial="Cone",
    ...                           radius=2 * u.arcmin)
    >>> print(table)

          ra     dec       clon         clat     err_maj ...  j_h   h_k    j_k    id
    ------- ------- ------------ ------------ ------- ... ----- ------ ------ ---
     10.685  41.248 00h42m44.45s 41d14m52.56s    0.14 ... 1.792 -0.821  0.971   0
     10.697  41.275 00h42m47.39s 41d16m30.25s    0.13 ...    --     --     --   1
     10.673  41.254 00h42m41.63s 41d15m15.66s    0.26 ...    --  1.433     --   2
     10.671  41.267 00h42m41.10s 41d15m59.97s    0.17 ...    --     --     --   3
     10.684  41.290 00h42m44.11s 41d17m24.99s    0.19 ... 0.261 -1.484 -1.223   4
     10.692  41.290 00h42m46.08s 41d17m24.99s    0.18 ...    --     --  0.433   5
     10.716  41.260 00h42m51.77s 41d15m36.31s    0.13 ...  0.65     --     --   6
     10.650  41.286 00h42m35.96s 41d17m08.48s    0.41 ... 1.205     --     --   7
        ...     ...          ...          ...     ... ...   ...    ...    ... ...
     10.686  41.271 00h42m44.60s 41d16m14.16s    0.13 ...    --     --     -- 768
     10.694  41.277 00h42m46.55s 41d16m36.13s    0.27 ...    --     --     -- 769
     10.690  41.277 00h42m45.71s 41d16m36.54s    0.15 ...    --     --     -- 770
     10.679  41.281 00h42m42.88s 41d16m51.62s    0.43 ...    --     --     -- 771
     10.689  41.237 00h42m45.26s 41d14m13.32s    0.22 ...    --     --     -- 772
     10.661  41.274 00h42m38.53s 41d16m24.76s    0.18 ...    --     --     -- 773
     10.653  41.281 00h42m36.78s 41d16m52.98s    0.17 ...    --  0.795     -- 774



The coordinates of the center may be specified rather than using the target
name. The coordinates can be specified using the appropriate
`astropy.coordinates` object. ICRS coordinates may also be entered directly as
a string, as specified by `astropy.coordinates`:

.. code-block:: python

    >>> from astroquery.irsa import Irsa
    >>> import astropy.coordinates as coord
    >>> table = Irsa.query_region(coord.SkyCoord(121.1743,
    ...                           -21.5733, unit=(u.deg,u.deg),
    ...                           frame='galactic'),
    ...                           catalog='fp_psc', radius='0d2m0s')
    >>> print(table)

Performing a box search
-----------------------

The box queries have a syntax similar to the cone queries. In this case the
``spatial`` keyword argument must be set to ``Box``. Also the width of the box
region is required. The width may be specified in the same way as the radius
for cone search queries, above - so it may be set using the appropriate
`~astropy.units.Quantity` object or a string parsable by `~astropy.coordinates.Angle`.

.. code-block:: python

    >>> from astroquery.irsa import Irsa
    >>> import astropy.units as u
    >>> table = Irsa.query_region("00h42m44.330s +41d16m07.50s",
    ...                           catalog='fp_psc', spatial='Box',
    ...                           width=5 * u.arcsec)

    WARNING: Coordinate string is being interpreted as an ICRS
    coordinate. [astroquery.irsa.core]

    >>> print(table)

          ra     dec       clon         clat     err_maj ...  j_h   h_k   j_k   id
    ------- ------- ------------ ------------ ------- ... ----- ----- ----- ---
     10.685  41.269 00h42m44.34s 41d16m08.53s    0.08 ... 0.785 0.193 0.978   0

Note that in this case we directly passed ICRS coordinates as a string to the
:meth:`~astroquery.irsa.IrsaClass.query_region`.

Queries over a polygon
----------------------


Polygon queries can be performed by setting ``spatial='Polygon'``. The search
center is optional in this case. One additional parameter that must be set for
these queries is ``polygon``. This is a list of coordinate pairs that define a
convex polygon. The coordinates may be specified as usual by using the
appropriate `astropy.coordinates` object (Again ICRS coordinates may be
directly passed as properly formatted strings). In addition to using a list of
`astropy.coordinates` objects, one additional convenient means of specifying
the coordinates is also available - Coordinates may also be entered as a list of
tuples, each tuple containing the ra and dec values in degrees. Each of these
options is illustrated below:

.. code-block:: python

    >>> from astroquery.irsa import Irsa
    >>> from astropy import coordinates
    >>> table = Irsa.query_region("m31", catalog="fp_psc", spatial="Polygon",
    ... polygon=[coordinates.SkyCoord(ra=10.1, dec=10.1, unit=(u.deg, u.deg), frame='icrs'),
    ...          coordinates.SkyCoord(ra=10.0, dec=10.1, unit=(u.deg, u.deg), frame='icrs'),
    ...          coordinates.SkyCoord(ra=10.0, dec=10.0, unit=(u.deg, u.deg), frame='icrs')
    ...         ])
    >>> print(table)

          ra     dec       clon         clat     err_maj ...  j_h   h_k   j_k   id
    ------- ------- ------------ ------------ ------- ... ----- ----- ----- ---
     10.016  10.099 00h40m03.77s 10d05m57.22s     0.1 ... 0.602 0.154 0.756   0
     10.031  10.063 00h40m07.44s 10d03m47.10s    0.19 ... 0.809 0.291   1.1   1
     10.037  10.060 00h40m08.83s 10d03m37.00s    0.11 ... 0.468 0.372  0.84   2
     10.060  10.085 00h40m14.39s 10d05m07.60s    0.23 ... 0.697 0.273  0.97   3
     10.016  10.038 00h40m03.80s 10d02m17.02s    0.09 ... 0.552 0.313 0.865   4
     10.011  10.094 00h40m02.68s 10d05m38.05s    0.23 ... 0.378 0.602  0.98   5
     10.006  10.018 00h40m01.33s 10d01m06.24s    0.16 ... 0.662 0.566 1.228   6

Another way to specify the polygon is directly as a list of tuples - each tuple
is an ra, dec pair expressed in degrees:

.. code-block:: python

    >>> from astroquery.irsa import Irsa
    >>> table = Irsa.query_region("m31", catalog="fp_psc", spatial="Polygon",
    ... polygon = [(10.1, 10.1), (10.0, 10.1), (10.0, 10.0)])
    >>> print(table)

          ra     dec       clon         clat     err_maj ...  j_h   h_k   j_k   id
    ------- ------- ------------ ------------ ------- ... ----- ----- ----- ---
     10.016  10.099 00h40m03.77s 10d05m57.22s     0.1 ... 0.602 0.154 0.756   0
     10.031  10.063 00h40m07.44s 10d03m47.10s    0.19 ... 0.809 0.291   1.1   1
     10.037  10.060 00h40m08.83s 10d03m37.00s    0.11 ... 0.468 0.372  0.84   2
     10.060  10.085 00h40m14.39s 10d05m07.60s    0.23 ... 0.697 0.273  0.97   3
     10.016  10.038 00h40m03.80s 10d02m17.02s    0.09 ... 0.552 0.313 0.865   4
     10.011  10.094 00h40m02.68s 10d05m38.05s    0.23 ... 0.378 0.602  0.98   5
     10.006  10.018 00h40m01.33s 10d01m06.24s    0.16 ... 0.662 0.566 1.228   6

Other Configurations
--------------------

By default the maximum number of rows that is fetched is set to 500. However,
this option may be changed by changing the astroquery configuration file. To
change the setting only for the ongoing python session, you could also do:

.. code-block:: python

    >>> from astroquery.irsa import Irsa
    >>> Irsa.ROW_LIMIT = 1000 # value of new row limit here.


Reference/API
=============

.. automodapi:: astroquery.irsa
    :no-inheritance-diagram:
