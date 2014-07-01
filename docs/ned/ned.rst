.. doctest-skip-all

.. _astroquery.ned:

******************************
NED Queries (`astroquery.ned`)
******************************

Getting Started
===============

This module can be used to query the Ned web service. All queries other than
image and spectra queries return results in a `~astropy.table.Table`. Image
and spectra queries on the other hand return the results as a list of
`~astropy.io.fits.HDUList` objects. Below are some working examples that
illustrate common use cases.

Query an object
---------------

This may be used to query the object *by name* from the NED service. For
instance if you want to query NGC 224

.. code-block:: python

    >>> from astroquery.ned import Ned
    >>> result_table = Ned.query_object("NGC 224")
    >>> print(result_table) # an astropy.table.Table

     No. Object Name  RA(deg)   ... Redshift Points Diameter Points Associations
    --- ----------- ---------- ... --------------- --------------- ------------
      1 MESSIER 031   10.68479 ...              26               7            2

Query a region
--------------

These queries may be used for querying a region around a named object or
coordinates (i.e *near name* and *near position* queries). The radius of
the region should be specified in degrees or equivalent units. An easy way to do this is to use an
`~astropy.units.Quantity` object to specify the radius and units. The radius may also
be specified as a string in which case it will be parsed using
`~astropy.coordinates.Angle`. If no radius is specified, it defaults to 1
arcmin. Another optional parameter is the equinox if coordinates are
specified. By default this is J2000.0 but can also be set to B1950.0.

.. code-block:: python

    >>> from astroquery.ned import Ned
    >>> import astropy.units as u
    >>> result_table = Ned.query_region("3c 273", radius=0.05 * u.deg)
    >>> print(result_table)

    No.       Object Name        ... Diameter Points Associations
    --- ------------------------ ... --------------- ------------
      1    3C 273:[PWC2011] 3640 ...               0            0
      2    3C 273:[PWC2011] 3592 ...               0            0
      3    3C 273:[PWC2011] 3593 ...               0            0
      4    3C 273:[PWC2011] 3577 ...               0            0
      5 SDSS J122856.35+020325.3 ...               3            0
      6    3C 273:[PWC2011] 3553 ...               0            0
      7    3C 273:[PWC2011] 3544 ...               0            0
      8    3C 273:[PWC2011] 3521 ...               0            0
    ...                      ... ...             ...          ...
    346    3C 273:[PWC2011] 2370 ...               0            0
    347 SDSS J122917.00+020436.3 ...               4            0
    348    3C 273:[PWC2011] 2338 ...               0            0
    349    3C 273:[PWC2011] 2349 ...               0            0
    350 SDSS J122917.52+020301.5 ...               4            0
    351    3C 273:[PWC2011] 2326 ...               0            0
    352 SDSS J122917.72+020356.8 ...               3            0
    353 SDSS J122918.38+020323.4 ...               4            0

Instead of using the name, the target may also be specified via
coordinates. Any of the coordinate systems available in `astropy.coordinates`
may be used (ICRS, Galactic, FK4, FK5). Note also the use of the equinox keyword argument:

.. code-block:: python

    >>> from astroquery.ned import Ned
    >>> import astropy.units as u
    >>> from astropy import coordinates
    >>> co = coordinates.SkyCoord(ra=56.38, dec=38.43,
    ...                           unit=(u.deg, u.deg), frame='fk4')
    >>> result_table = Ned.query_region(co, radius=0.1 * u.deg, equinox='B1950.0')
    >>> print(result_table)

    No.       Object Name       ... Diameter Points Associations
    --- ----------------------- ... --------------- ------------
      1 2MASX J03514350+3841573 ...               2            0
      2 2MASX J03514563+3839573 ...               2            0
      3     NVSS J035158+384747 ...               0            0
      4 2MASX J03521115+3849288 ...               2            0
      5 2MASX J03521844+3840179 ...               2            0

Query in the IAU format
^^^^^^^^^^^^^^^^^^^^^^^

The `IAU format`_ for coordinates may also be used for querying
purposes. Additional parameters that can be specified for these queries is the
reference frame of the coordinates. The reference frame defaults to
``Equatorial``. But it can also take the values ``Ecliptic``, ``Galactic`` and
``SuperGalactic``. The equinox can also be explicitly chosen (same as in region
queries). It defaults to ``B1950`` but again it may be set to ``J2000.0``. Note
that Ned report results by searching in a 15 arcmin radius around the specified
target.

.. code-block:: python

    >>> from astroquery.ned import Ned
    >>> result_table = Ned.query_region_iau('1234-423', frame='SuperGalactic', equinox='J2000.0')
    >>> print(result_table)

        No.       Object Name        RA(deg)   ... Diameter Points Associations
    --- ----------------------- ---------- ... --------------- ------------
      1    SUMSS J123651-423554  189.21425 ...               0            0
      2    SUMSS J123658-423457    189.245 ...               0            0
      3    SUMSS J123711-424119  189.29663 ...               0            0
      4 2MASX J12373141-4239342  189.38083 ...               2            0
      5 2MASX J12373567-4239122  189.39908 ...               2            0

Query a reference code for objects
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

These queries can be used to retrieve all objects that appear in the specified
19 digit reference code. These are similar to the
:meth:`~astroquery.simbad.SimbadClass.query_bibobj` queries.

.. code-block:: python

    >>> from astroquery.ned import Ned
    >>> result_table = Ned.query_refcode('1997A&A...323...31K')
    >>> print(result_table)

        No.       Object Name        RA(deg)   ... Diameter Points Associations
    --- ----------------------- ---------- ... --------------- ------------
      1                NGC 0262   12.19642 ...               8            0
      2                NGC 0449    19.0302 ...               7            0
      3                NGC 0591   23.38028 ...               7            0
      4               UGC 01214   25.99084 ...               7            0
      5 2MASX J01500266-0725482   27.51124 ...               2            0
      6             MESSIER 077   40.66963 ...               8            0
      7                MRK 0599   41.94759 ...               6            0
      8                MRK 1058   42.46596 ...               4            0
    ...                     ...        ... ...             ...          ...
     30                NGC 5643  218.16977 ...              18            0
     31            SBS 1439+537   220.1672 ...               2            3
     32                MRK 1388  222.65772 ...               6            0
     33 2MASX J20232535+1131352  305.85577 ...               2            0
     34               UGC 12149  340.28163 ...               8            0
     35                MRK 0522  345.07954 ...               4            0
     36                NGC 7674  351.98635 ...               8            0

Image and Spectra Queries
^^^^^^^^^^^^^^^^^^^^^^^^^

The image queries return a list of `~astropy.io.fits.HDUList` objects for the
specified name. For instance:

.. code-block:: python

    >>> from astroquery.ned import Ned
    >>> images = Ned.get_images("m1")

    Downloading http://ned.ipac.caltech.edu/dss1B2/Bb/MESSIER_001:I:103aE:dss1.fits.gz
    |===========================================|  32k/ 32k (100.00%)        00s
    Downloading http://ned.ipac.caltech.edu/img5/1995RXCD3.T...0000C/p083n22a:I:0.1-2.4keV:cop1995.fits.gz
    |===========================================|  52k/ 52k (100.00%)        01s
    Downloading http://ned.ipac.caltech.edu/img5/1996RXCD6.T...0000C/p083n22a:I:0.1-2.4keV:cps1996.fits.gz
    |===========================================|  96k/ 96k (100.00%)        03s
    Downloading http://ned.ipac.caltech.edu/img5/1995RXCD3.T...0000C/p084n22a:I:0.1-2.4keV:cop1995.fits.gz
    |===========================================|  52k/ 52k (100.00%)        01s
    Downloading http://ned.ipac.caltech.edu/img5/1998RXCD8.T...0000C/h083n22a:I:0.1-2.4keV:cps1998.fits.gz
    |===========================================|  35k/ 35k (100.00%)        00s

    >>> images # may be used to do further processing on individual cutouts

    [[<astropy.io.fits.hdu.image.PrimaryHDU at 0x4311890>],
    [<astropy.io.fits.hdu.image.PrimaryHDU at 0x432b350>],
    [<astropy.io.fits.hdu.image.PrimaryHDU at 0x3e9c5d0>],
    [<astropy.io.fits.hdu.image.PrimaryHDU at 0x4339790>],
    [<astropy.io.fits.hdu.image.PrimaryHDU at 0x433dd90>]]

To get the URLs of the downloadable FITS images:

.. code-block:: python

    >>> from astroquery.ned import Ned
    >>> image_list = Ned.get_image_list("m1")
    >>> image_list

    ['http://ned.ipac.caltech.edu/dss1B2/Bb/MESSIER_001:I:103aE:dss1.fits.gz',
     'http://ned.ipac.caltech.edu/img5/1995RXCD3.T...0000C/p083n22a:I:0.1-2.4keV:cop1995.fits.gz',
     'http://ned.ipac.caltech.edu/img5/1996RXCD6.T...0000C/p083n22a:I:0.1-2.4keV:cps1996.fits.gz',
     'http://ned.ipac.caltech.edu/img5/1995RXCD3.T...0000C/p084n22a:I:0.1-2.4keV:cop1995.fits.gz',
     'http://ned.ipac.caltech.edu/img5/1998RXCD8.T...0000C/h083n22a:I:0.1-2.4keV:cps1998.fits.gz']

Spectra can also be fetched in the same way:

.. code-block:: python

    >>> from astroquery.ned import Ned
    >>> spectra = Ned.get_spectra('3c 273')

    Downloading http://ned.ipac.caltech.edu/spc1/2009A+A...495.1033B/3C_273:S:B:bcc2009.fits.gz
    |===========================================| 7.8k/7.8k (100.00%)        00s
    Downloading http://ned.ipac.caltech.edu/spc1/1992ApJS...80..109B/PG_1226+023:S:B_V:bg1992.fits.gz
    |===========================================| 5.0k/5.0k (100.00%)        00s
    Downloading http://ned.ipac.caltech.edu/spc1/2009A+A...495.1033B/3C_273:S:RI:bcc2009.fits.gz
    |===========================================| 9.4k/9.4k (100.00%)        00s

    >>> spectra

    [[<astropy.io.fits.hdu.image.PrimaryHDU at 0x41b4190>],
    [<astropy.io.fits.hdu.image.PrimaryHDU at 0x41b0990>],
    [<astropy.io.fits.hdu.image.PrimaryHDU at 0x430a450>]]

Similarly the list of URLs for spectra of a particular object may be fetched:

.. code-block:: python

    >>> from astroquery.ned import Ned
    >>> image_list = Ned.get_image_list("3c 273", item='spectra')
    >>> image_list

    ['http://ned.ipac.caltech.edu/spc1/2009A+A...495.1033B/3C_273:S:B:bcc2009.fits.gz',
    'http://ned.ipac.caltech.edu/spc1/1992ApJS...80..109B/PG_1226+023:S:B_V:bg1992.fits.gz',
    'http://ned.ipac.caltech.edu/spc1/2009A+A...495.1033B/3C_273:S:RI:bcc2009.fits.gz']

Fetching other data tables for an object
----------------------------------------

Several other data tables for an object may be fetched via the :meth:`~astroquery.ned.NedClass.get_table`
queries. These take a keyword argument ``table``, which may be set to one of
``photometry``, ``diameters``, ``redshifts``, ``references`` or ``object-notes``. For
instance the ``table=photometry`` will fetch all the relevant photometric data
for the specified object. We look at a simple example:

.. code-block:: python

    >>> from astroquery.ned import Ned
    >>> result_table = Ned.get_table("3C 273", table='positions')
    >>> print(result_table)

      No.       RA            DEC       ... Published Frame  Published Frequence Mode                           Qualifiers
    --- -------------- -------------- ... --------------- ------------------------- --------------------------------------------------------------
      0 12h29m06.6997s +02d03m08.598s ...
      1 12h29m06.6997s +02d03m08.598s ...             ICR Multiple line measurement                                             From new, raw data
      2  12h29m06.699s  +02d03m08.59s ...             ICR    Broad-band measurement                                             From new, raw data
      3   12h29m06.64s   +02d03m09.0s ...             FK4    Broad-band measurement From reprocessed raw data; Corrected for contaminating sources
      4   12h29m06.79s   +02d03m08.0s ...             FK5    Broad-band measurement  From new, raw data; Systematic errors in RA and Dec corrected
      5   12h29m06.05s   +02d02m57.1s ...             FK4    Broad-band measurement                                             From new, raw data
      6   12h29m05.60s   +02d03m09.0s ...             FK5    Broad-band measurement                                             From new, raw data
      7    12h29m04.5s     +02d03m03s ...                    Broad-band measurement                                             From new, raw data
      8   12h29m07.55s   +02d03m02.3s ...             FK4    Broad-band measurement                                      From reprocessed raw data
      9   12h29m06.05s   +02d03m11.3s ...             FK4    Broad-band measurement                                             From new, raw data
     10    12h29m06.5s     +02d02m53s ...             FK4    Broad-band measurement                                             From new, raw data
     11    12h29m06.5s     +02d02m52s ...             FK4    Broad-band measurement                                      From reprocessed raw data

.. note::

    All query methods that return the results in a `~astropy.table.Table` will
    return meaningful column names only with Astropy version >= 0.3. For
    versions older than this, the table headers will have column names of the form
    ``main_col_number`` because of the way in which the NED returns VOTables.

.. warning::

    table=references does not work correctly `astroquery issue #141`_

Reference/API
=============

.. automodapi:: astroquery.ned
    :no-inheritance-diagram:

.. _IAU format: http://cdsweb.u-strasbg.fr/Dic/iau-spec.html.
.. _astroquery issue #141: https://github.com/astropy/astroquery/issues/141
