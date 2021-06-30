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
.. doctest-remote-data::

    >>> from astroquery.irsa import Irsa
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

This returns a dictionary of catalog names with their description. If you would
rather just print out this information:

.. code-block:: python
.. doctest-remote-data::

    >>> from astroquery.irsa import Irsa
    >>> Irsa.print_catalogs()
    allwise_p3as_psd                AllWISE Source Catalog
    allwise_p3as_mep                AllWISE Multiepoch Photometry Table
    allwise_p3as_psr                AllWISE Reject Table
    ...
    wisegalhii                      WISE Catalog of Galactic HII Regions v2.2
    denis3                          DENIS 3rd Release (Sep. 2005)


Performing a cone search
------------------------

A cone search query is performed by setting the ``spatial`` keyword to
``Cone``. The target name or the coordinates of the search center must also be
specified. The radius for the cone search may also be specified - if this is
missing, it defaults to a value of 10 arcsec. The radius may be specified in
any appropriate unit using a `~astropy.units.Quantity` object. It may also be
entered as a string that is parsable by `~astropy.coordinates.Angle`.

.. code-block:: python
.. doctest-remote-data::

    >>> from astroquery.irsa import Irsa
    >>> import astropy.units as u
    >>> table = Irsa.query_region("m31", catalog="fp_psc", spatial="Cone",
    ...                           radius=2 * u.arcmin)
    >>> print(table)
        ra        dec         clon         clat     ...  j_h   h_k    j_k
       deg        deg                               ...
    ---------- ---------- ------------ ------------ ... ----- ------ -----
     10.684737  41.269035 00h42m44.34s 41d16m08.53s ... 0.785  0.193 0.978
     10.685657  41.269550 00h42m44.56s 41d16m10.38s ...    --     --    --
           ...        ...          ...          ... ...   ...    ...   ...
     10.702501  41.299492 00h42m48.60s 41d17m58.17s ...    --     --    --
     10.728661  41.273312 00h42m54.88s 41d16m23.92s ...    --     --    --
     10.728869  41.265533 00h42m54.93s 41d15m55.92s ... 0.803  0.613 1.416
    Length = 500 rows


The coordinates of the center may be specified rather than using the target
name. The coordinates can be specified using the appropriate
`astropy.coordinates` object. ICRS coordinates may also be entered directly as
a string, as specified by `astropy.coordinates`:

.. code-block:: python
.. doctest-remote-data::

    >>> from astroquery.irsa import Irsa
    >>> import astropy.coordinates as coord
    >>> table = Irsa.query_region(coord.SkyCoord(121.1743,
    ...                           -21.5733, unit=(u.deg,u.deg),
    ...                           frame='galactic'),
    ...                           catalog='fp_psc', radius='0d2m0s')
    >>> print(table)
        ra        dec         clon         clat     ...   angle     j_h   h_k   j_k
       deg        deg                               ...    deg
    ---------- ---------- ------------ ------------ ... ---------- ----- ----- -----
     10.684737  41.269035 00h42m44.34s 41d16m08.53s ...   10.37715 0.785 0.193 0.978
     10.683469  41.268585 00h42m44.03s 41d16m06.91s ... 259.028985    --    --    --
     10.685657  41.269550 00h42m44.56s 41d16m10.38s ...  43.199247    --    --    --
           ...        ...          ...          ... ...        ...   ...   ...   ...
     10.656898  41.294655 00h42m37.66s 41d17m40.76s ...  321.14224 1.237    --    --
     10.647116  41.286366 00h42m35.31s 41d17m10.92s ... 301.969315    --    --    --
    Length = 500 rows


Performing a box search
-----------------------

The box queries have a syntax similar to the cone queries. In this case the
``spatial`` keyword argument must be set to ``Box``. Also the width of the box
region is required. The width may be specified in the same way as the radius
for cone search queries, above - so it may be set using the appropriate
`~astropy.units.Quantity` object or a string parsable by `~astropy.coordinates.Angle`.

.. code-block:: python
.. doctest-remote-data::

    >>> from astroquery.irsa import Irsa
    >>> import astropy.units as u
    >>> table = Irsa.query_region("00h42m44.330s +41d16m07.50s",
    ...                           catalog='fp_psc', spatial='Box',
    ...                           width=5 * u.arcsec)
    >>> print(table)
        ra        dec         clon         clat     ... ext_key  j_h   h_k   j_k
       deg        deg                               ...
    ---------- ---------- ------------ ------------ ... ------- ----- ----- -----
     10.684737  41.269035 00h42m44.34s 41d16m08.53s ...      -- 0.785 0.193 0.978

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
.. doctest-remote-data::

    >>> from astroquery.irsa import Irsa
    >>> from astropy import coordinates
    >>> table = Irsa.query_region("m31", catalog="fp_psc", spatial="Polygon",
    ... polygon=[coordinates.SkyCoord(ra=10.1, dec=10.1, unit=(u.deg, u.deg), frame='icrs'),
    ...          coordinates.SkyCoord(ra=10.0, dec=10.1, unit=(u.deg, u.deg), frame='icrs'),
    ...          coordinates.SkyCoord(ra=10.0, dec=10.0, unit=(u.deg, u.deg), frame='icrs')
    ...         ])
    >>> print(table)
        ra        dec         clon         clat     ... ext_key  j_h   h_k   j_k
       deg        deg                               ...
    ---------- ---------- ------------ ------------ ... ------- ----- ----- -----
     10.015839  10.038061 00h40m03.80s 10d02m17.02s ...      -- 0.552 0.313 0.865
     10.015696  10.099228 00h40m03.77s 10d05m57.22s ...      -- 0.602 0.154 0.756
     10.011170  10.093903 00h40m02.68s 10d05m38.05s ...      -- 0.378 0.602  0.98
     10.031016  10.063082 00h40m07.44s 10d03m47.10s ...      -- 0.809 0.291   1.1
     10.036776  10.060278 00h40m08.83s 10d03m37.00s ...      -- 0.468 0.372  0.84
     10.059964  10.085445 00h40m14.39s 10d05m07.60s ...      -- 0.697 0.273  0.97
     10.005549  10.018401 00h40m01.33s 10d01m06.24s ...      -- 0.662 0.566 1.228

Another way to specify the polygon is directly as a list of tuples - each tuple
is an ra, dec pair expressed in degrees:

.. code-block:: python
.. doctest-remote-data::

    >>> from astroquery.irsa import Irsa
    >>> table = Irsa.query_region("m31", catalog="fp_psc", spatial="Polygon",
    ... polygon = [(10.1, 10.1), (10.0, 10.1), (10.0, 10.0)])
    >>> print(table)
        ra        dec         clon         clat     ... ext_key  j_h   h_k   j_k
       deg        deg                               ...
    ---------- ---------- ------------ ------------ ... ------- ----- ----- -----
     10.015839  10.038061 00h40m03.80s 10d02m17.02s ...      -- 0.552 0.313 0.865
     10.015696  10.099228 00h40m03.77s 10d05m57.22s ...      -- 0.602 0.154 0.756
     10.011170  10.093903 00h40m02.68s 10d05m38.05s ...      -- 0.378 0.602  0.98
     10.031016  10.063082 00h40m07.44s 10d03m47.10s ...      -- 0.809 0.291   1.1
     10.036776  10.060278 00h40m08.83s 10d03m37.00s ...      -- 0.468 0.372  0.84
     10.059964  10.085445 00h40m14.39s 10d05m07.60s ...      -- 0.697 0.273  0.97
     10.005549  10.018401 00h40m01.33s 10d01m06.24s ...      -- 0.662 0.566 1.228


Selecting Columns
--------------------

The IRSA service allows to query either a subset of the default columns for
a given table, or additional columns that are not present by default. This
can be done by listing all the required columns separated by a comma (,) in
a string with the ``selcols`` argument.


An example where the AllWISE Source Catalog needs to be queried around the
star HIP 12 with just the ra, dec and w1mpro columns would be:


.. code-block:: python
.. doctest-remote-data::

    >>> from astroquery.irsa import Irsa
    >>> table = Irsa.query_region("HIP 12", catalog="allwise_p3as_psd", spatial="Cone", selcols="ra,dec,w1mpro")
    >>> print(table)
         ra         dec         clon          clat      w1mpro   dist     angle
        deg         deg                                  mag    arcsec     deg
    ----------- ----------- ------------ ------------- ------- -------- ----------
      0.0407905 -35.9602605 00h00m09.79s -35d57m36.94s   4.837 0.350806 245.442148

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

.. code-block:: python
.. doctest-remote-data::

    >>> from astroquery.irsa import Irsa
    >>> table = Irsa.query_region("HIP 12", catalog="allwise_p3as_psd", spatial="Cone", selcols="ra,dec,w1mpro")
    >>> table['ra'].format = '{:10.6f}'
    >>> table['dec'].format = '{:10.6f}'
    >>> print(table)
        ra        dec         clon          clat      w1mpro   dist     angle
       deg        deg                                  mag    arcsec     deg
    ---------- ---------- ------------ ------------- ------- -------- ----------
      0.040791 -35.960260 00h00m09.79s -35d57m36.94s   4.837 0.350806 245.442148


Other Configurations
--------------------

By default the maximum number of rows that is fetched is set to 500. However,
this option may be changed by changing the astroquery configuration file. To
change the setting only for the ongoing python session, you could also do:

.. code-block:: python

    >>> from astroquery.irsa import Irsa
    >>> Irsa.ROW_LIMIT = 1000   # 1000 is the new value for row limit here.


Reference/API
=============

.. automodapi:: astroquery.irsa
    :no-inheritance-diagram:
