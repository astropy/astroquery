.. _astroquery.ipac.irsa:

*************************************
IRSA Queries (`astroquery.ipac.irsa`)
*************************************

Getting started
===============

This module can has methods to perform different types of queries on the
catalogs present in the IRSA general catalog service. All queries can be
performed by calling :meth:`~astroquery.ipac.irsa.IrsaClass.query_region`, with
different keyword arguments. There are 4 different region queries that are
supported: ``Cone``, ``Box``, ``Polygon`` and ``All-Sky``. All successful
queries return the results in a `~astropy.table.Table`.  We now look at some
examples.


Available catalogs
------------------

All region queries require a ``catalog`` keyword argument, which is the name of
the catalog in the IRSA database, on which the query must be performed. To take
a look at all the available catalogs:

.. doctest-remote-data::

    >>> from astroquery.ipac.irsa import Irsa
    >>> Irsa.list_catalogs()   # doctest: +IGNORE_OUTPUT
    {'a1763t2': 'Abell 1763 Source Catalog',
     'a1763t3': 'Abell 1763 MIPS 70 micron Catalog',
     'acs_iphot_sep07': 'COSMOS ACS I-band photometry catalog September 2007',
     'akari_fis': 'Akari/FIS Bright Source Catalogue',
     'akari_irc': 'Akari/IRC Point Source Catalogue',
     'astsight': 'IRAS Minor Planet Survey',
     ...
     ...
     'xmm_cat_s05': "SWIRE XMM_LSS Region Spring '05 Spitzer Catalog"}

To access the full VOTable of the catalog information, use the ``full`` keyword argument.

.. doctest-remote-data::

    >>> from astroquery.ipac.irsa import Irsa
    >>> Irsa.list_catalogs(full=True)  # doctest: +IGNORE_OUTPUT
    <DALResultsTable length=934>
    table_index schema_name             table_name                              description                  ... irsa_access_flag irsa_nrows irsa_odbc_datasource irsa_spatial_idx_name
       int32       object                 object                                   object                    ...      int32         int64           object                object
    ----------- ----------- ---------------------------------- --------------------------------------------- ... ---------------- ---------- -------------------- ---------------------
            303     spitzer              spitzer.m31irac_image                                M31IRAC Images ...               30          4             postgres
            304     spitzer                             mipslg                   MIPS Local Galaxies Catalog ...               30        240              spitzer        SPT_IND_MIPSLG
            305     spitzer             spitzer.mips_lg_images                    MIPS Local Galaxies Images ...               30        606             postgres
    ...


Performing a cone search
------------------------

A cone search query is performed by setting the ``spatial`` keyword to
``Cone``. The target name or the coordinates of the search center must also be
specified. The radius for the cone search may also be specified - if this is
missing, it defaults to a value of 10 arcsec. The radius may be specified in
any appropriate unit using a `~astropy.units.Quantity` object. It may also be
entered as a string that is parsable by `~astropy.coordinates.Angle`.

.. doctest-remote-data::

    >>> from astroquery.ipac.irsa import Irsa
    >>> import astropy.units as u
    >>> table = Irsa.query_region("m31", catalog="fp_psc", spatial="Cone",
    ...                           radius=2 * u.arcmin)
    >>> print(table)
        ra        dec     err_maj err_min ... coadd_key coadd        htm20
       deg        deg      arcsec  arcsec ...
    ---------- ---------- ------- ------- ... --------- ----- -------------------
     10.692216  41.260162    0.10    0.09 ...   1590591    33 4805203678124326400
     10.700059  41.263481    0.31    0.30 ...   1590591    33 4805203678125364736
     10.699131  41.263248    0.28    0.20 ...   1590591    33 4805203678125474304
           ...        ...     ...     ... ...       ...   ...                 ...
     10.661414  41.242363    0.21    0.20 ...   1590591    33 4805203679644192256
     10.665184  41.240238    0.14    0.13 ...   1590591    33 4805203679647824896
     10.663245  41.240646    0.24    0.21 ...   1590591    33 4805203679649555456
    Length = 774 rows

The coordinates of the center may be specified rather than using the target
name. The coordinates can be specified using a `~astropy.coordinates.SkyCoord`
object or a string resolvable by the `~astropy.coordinates.SkyCoord` constructor.

.. doctest-remote-data::

    >>> from astroquery.ipac.irsa import Irsa
    >>> from astropy.coordinates import SkyCoord
    >>> coord = SkyCoord(121.1743, -21.5733, unit='deg', frame='galactic')
    >>> table = Irsa.query_region(coordinates=coord,
    ...                           catalog='fp_psc', radius='0d2m0s')
    >>> print(table)
        ra        dec     err_maj err_min ... coadd_key coadd        htm20
       deg        deg      arcsec  arcsec ...
    ---------- ---------- ------- ------- ... --------- ----- -------------------
     10.692216  41.260162    0.10    0.09 ...   1590591    33 4805203678124326400
     10.700059  41.263481    0.31    0.30 ...   1590591    33 4805203678125364736
     10.699131  41.263248    0.28    0.20 ...   1590591    33 4805203678125474304
           ...        ...     ...     ... ...       ...   ...                 ...
     10.661414  41.242363    0.21    0.20 ...   1590591    33 4805203679644192256
     10.665184  41.240238    0.14    0.13 ...   1590591    33 4805203679647824896
     10.663245  41.240646    0.24    0.21 ...   1590591    33 4805203679649555456
    Length = 774 rows


Performing a box search
-----------------------

The box queries have a syntax similar to the cone queries. In this case the
``spatial`` keyword argument must be set to ``Box``. Also the width of the box
region is required. The width may be specified in the same way as the radius
for cone search queries, above - so it may be set using the appropriate
`~astropy.units.Quantity` object or a string parsable by `~astropy.coordinates.Angle`.

.. doctest-remote-data::

    >>> from astroquery.ipac.irsa import Irsa
    >>> import astropy.units as u
    >>> table = Irsa.query_region("00h42m44.330s +41d16m07.50s",
    ...                           catalog='fp_psc', spatial='Box',
    ...                           width=5 * u.arcsec)
    >>> print(table)
        ra        dec         clon         clat     ... ext_key  j_h   h_k   j_k
       deg        deg                               ...
    ---------- ---------- ------------ ------------ ... ------- ----- ----- -----
     10.684737  41.269035 00h42m44.34s 41d16m08.53s ...      -- 0.785 0.193 0.978

Queries over a polygon
----------------------

Polygon queries can be performed by setting ``spatial='Polygon'``. The search
center is optional in this case. One additional parameter that must be set for
these queries is ``polygon``. This is a list of coordinate pairs that define a
convex polygon. The coordinates may be specified as usual by using the
appropriate `~astropy.coordinates.SkyCoord` object. In addition to using a list of
`~astropy.coordinates.SkyCoord` objects, one additional convenient means of specifying
the coordinates is also available - Coordinates may also be entered as a list of
tuples, each tuple containing the ra and dec values in degrees. Each of these
options is illustrated below:

.. doctest-remote-data::

    >>> from astroquery.ipac.irsa import Irsa
    >>> from astropy import coordinates
    >>> table = Irsa.query_region("m31", catalog="fp_psc", spatial="Polygon",
    ... polygon=[coordinates.SkyCoord(ra=10.1, dec=10.1, unit=(u.deg, u.deg), frame='icrs'),
    ...          coordinates.SkyCoord(ra=10.0, dec=10.1, unit=(u.deg, u.deg), frame='icrs'),
    ...          coordinates.SkyCoord(ra=10.0, dec=10.0, unit=(u.deg, u.deg), frame='icrs')
    ...         ])
    >>> print(table)
        ra        dec     err_maj err_min ... coadd_key coadd        htm20
       deg        deg      arcsec  arcsec ...
    ---------- ---------- ------- ------- ... --------- ----- -------------------
     10.015839  10.038061    0.09    0.06 ...   1443005    91 4805087709670704640
     10.015696  10.099228    0.10    0.07 ...   1443005    91 4805087709940635648
     10.011170  10.093903    0.23    0.21 ...   1443005    91 4805087710032524288
     10.031016  10.063082    0.19    0.18 ...   1443005    91 4805087710169327616
     10.036776  10.060278    0.11    0.06 ...   1443005    91 4805087710175392768
     10.059964  10.085445    0.23    0.20 ...   1443005    91 4805087710674674176
     10.005549  10.018401    0.16    0.14 ...   1443005    91 4805087784811171840

Another way to specify the polygon is directly as a list of tuples - each tuple
is an ra, dec pair expressed in degrees:

.. doctest-remote-data::

    >>> from astroquery.ipac.irsa import Irsa
    >>> table = Irsa.query_region("m31", catalog="fp_psc", spatial="Polygon",
    ... polygon = [(10.1, 10.1), (10.0, 10.1), (10.0, 10.0)])  # doctest: +IGNORE_WARNINGS
    >>> print(table)
        ra        dec     err_maj err_min ... coadd_key coadd        htm20
       deg        deg      arcsec  arcsec ...
    ---------- ---------- ------- ------- ... --------- ----- -------------------
     10.015839  10.038061    0.09    0.06 ...   1443005    91 4805087709670704640
     10.015696  10.099228    0.10    0.07 ...   1443005    91 4805087709940635648
     10.011170  10.093903    0.23    0.21 ...   1443005    91 4805087710032524288
     10.031016  10.063082    0.19    0.18 ...   1443005    91 4805087710169327616
     10.036776  10.060278    0.11    0.06 ...   1443005    91 4805087710175392768
     10.059964  10.085445    0.23    0.20 ...   1443005    91 4805087710674674176
     10.005549  10.018401    0.16    0.14 ...   1443005    91 4805087784811171840

Selecting Columns
--------------------

The IRSA service allows to query either a subset of the default columns for
a given table, or additional columns that are not present by default. This
can be done by listing all the required columns separated by a comma (,) in
a string with the ``columns`` argument.


An example where the AllWISE Source Catalog needs to be queried around the
star HIP 12 with just the ra, dec and w1mpro columns would be:


.. doctest-remote-data::

    >>> from astroquery.ipac.irsa import Irsa
    >>> table = Irsa.query_region("HIP 12", catalog="allwise_p3as_psd", spatial="Cone", columns="ra,dec,w1mpro")
    >>> print(table)
         ra         dec      w1mpro
        deg         deg       mag
    ----------- ----------- -------
      0.0407905 -35.9602605   4.837

A list of available columns for each catalog can be found at
https://irsa.ipac.caltech.edu/holdings/catalogs.html. The "Long Form" button
at the top of the column names table must be clicked to access a full list
of all available columns.


Changing the precision of ascii output
--------------------------------------

The precision of the table display of each column is set upstream by the archive,
and appears as the ``.format`` attribute of individual columns. This attribute affects
not only the display of columns, but also the precision that is output when the table
is written in ``ascii.ipac`` or ``ascii.csv`` formats. The ``.format`` attribute of
individual columns may be set to increase the precision.

.. doctest-remote-data::

    >>> from astroquery.ipac.irsa import Irsa
    >>> table = Irsa.query_region("HIP 12", catalog="allwise_p3as_psd", spatial="Cone", columns="ra,dec,w1mpro")
    >>> table['ra'].format = '{:10.6f}'
    >>> table['dec'].format = '{:10.6f}'
    >>> print(table)
        ra        dec       w1mpro
       deg        deg        mag
    ---------- ----------  -------
      0.040791 -35.960260    4.837


Other Configurations
--------------------

By default the maximum number of rows that is fetched is set to 500. However,
this option may be changed by changing the astroquery configuration file. To
change the setting only for the ongoing python session, you could also do:


    >>> from astroquery.ipac.irsa import Irsa
    >>> Irsa.ROW_LIMIT = 1000   # 1000 is the new value for row limit here.


Reference/API
=============

.. automodapi:: astroquery.ipac.irsa
    :no-inheritance-diagram:
