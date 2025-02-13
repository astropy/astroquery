.. _astroquery.ipac.ned:


***********************************
NED Queries (`astroquery.ipac.ned`)
***********************************

Getting Started
===============

This module provides an interface to the NED web service. All queries other than
image and spectra queries return results in a `~astropy.table.Table`. Image
and spectra queries on the other hand return the results as a list of
`~astropy.io.fits.HDUList` objects. Below are several examples that
illustrate common use cases.


Query an object
---------------

This may be used to query the object *by name* from the NED service. For
instance if you want to query NGC 224.

.. doctest-remote-data::

    >>> from astroquery.ipac.ned import Ned
    >>> result_table = Ned.query_object("NGC 224")
    >>> print(result_table) # an astropy.table.Table
    No. Object Name     RA-s       ...  Phys Type ... Diameter Distances Classification Images Spectra
                                   ...
    --- ----------- -------------- ...  --------  ... -------- --------- -------------- ------ -------
      1 Messier 031 00h42m44.3503s ...         G            13       407            199    302       5


Query a region
--------------

These queries can be used to search a region around either a named object or
coordinates (i.e *near name* and *near position* queries). The search radius of
the region can be specified in degrees or any equivalent angular units. An easy way to do this is to use an
`~astropy.units.Quantity` object to specify the radius and units. The radius may also
be specified as a string in which case it is parsed using
`~astropy.coordinates.Angle`. If no radius is specified, it defaults to 1 arcmin. 

.. doctest-remote-data::

    >>> from astroquery.ipac.ned import Ned
    >>> import astropy.units as u
    >>> result_table = Ned.query_region("3c 273", radius=0.05 * u.deg)
    >>> print(result_table)
    No.        Object Name              RA-s      ... Diameter Distances Classification Images Spectra
                                                  ...
    --- -------------------------- -------------- ... -------- --------- -------------- ------ -------
      1      ICRF J122906.6+020308 12h29m06.6997s ...       11         0              7    149      27
      2      [HB89] 1226+023 ABS17 12h29m06.6502s ...        0         0              0      1       0
      3      [HB89] 1226+023 ABS18 12h29m06.6502s ...        0         0              0      1       0
      4      [HB89] 1226+023 ABS04 12h29m06.6502s ...        0         0              0      1       0
    ...                        ...            ... ...      ...       ...            ...    ...     ...
    864  WISEA J122908.25+020605.8 12h29m08.2832s ...        0         0              0      0       0
    865  WISEA J122908.88+020606.0 12h29m08.8914s ...        3         0              0      0       0
    866 SSTSL2 J122918.52+020338.9 12h29m18.5237s ...        0         0              0      0       0
    867 SSTSL2 J122918.64+020326.7 12h29m18.6419s ...        0         0              0      0       0
    Length = 867 rows

The redshift constraints can be optionally specified to indicate if the redshift is ``Unconstrained``,
``Available``, ``Unavailable``, ``Larger than`` or ``Less than`` a redshift value or ``Between`` a redshift range.

.. doctest-remote-data::

    >>> from astroquery.ipac.ned import Ned
    >>> import astropy.units as u
    >>> result_table = Ned.query_region("3c 273", radius=0.05 * u.deg, z_constraint='Between',
    >>>                                 z_value1=0.025, z_value2=0.090)
    >>> print(result_table)
    No.        Object Name              RA-s      ... Redshift(z) ... Classification Images Spectra
                                                  ...             ...
    --- -------------------------- -------------- ... ----------- ... -------------- ------ -------
      1      [HB89] 1226+023 ABS17 12h29m06.6502s ...    0.087600 ...              7    149      27
      2      [HB89] 1226+023 ABS05 12h29m06.6502s ...    0.049000 ...              0      1       0
      3      [HB89] 1226+023 ABS11 12h29m06.6502s ...    0.061000 ...              0      1       0
      4      [HB89] 1226+023 ABS12 12h29m06.6502s ...    0.048800 ...              0      1       0
    ...                        ...            ... ...      ...    ...            ...    ...     ...
      8      [HB89] 1226+023 ABS10 12h29m06.6502s ...    0.063500 ...              0      1       0
      9      [HB89] 1226+023 ABS13 12h29m06.6502s ...    0.032386 ...              0      1       0
     10      [HB89] 1226+023 ABS15 12h29m06.6502s ...    0.025875 ...              0      1       0
     11      [HB89] 1226+023 ABS14 12h29m06.6502s ...    0.029007 ...              0      1       0
    Length = 11 rows

Instead of using the name, the target may also be specified via
coordinates. Any of the coordinate systems available in `~astropy.coordinates`
may be used (ICRS, Galactic, FK4, FK5). The coordinate system, equinox, and sky position (RA/Dec or longitude/latitude) 
are all derived directly from the input coordinate object.

.. doctest-remote-data::

    >>> from astroquery.ipac.ned import Ned
    >>> import astropy.units as u
    >>> from astropy import coordinates
    >>> co = coordinates.SkyCoord(ra=56.38, dec=38.43, unit=(u.deg, u.deg), frame='fk4')
    >>> result_table = Ned.query_region(co, radius=0.1 * u.deg)
    >>> print(result_table)
    No.        Object Name              RA-s      ... Diameter Distances Classification Images Spectra
                                                  ...
    --- -------------------------- -------------- ... -------- --------- -------------- ------ -------
      1  WISEA J034849.31+383455.7 03h48m49.3166s ...        0         0              0      0       0 
      2  WISEA J034849.50+383505.3 03h48m49.5018s ...        0         0              0      0       0
      3  WISEA J034849.35+383443.8 03h48m49.3680s ...        0         0              0      0       0
      4  WISEA J034850.60+383446.8 03h48m50.6086s ...        0         0              0      0       0
    ...                        ...            ... ...      ...       ...            ...    ...     ...
    635  WISEA J034818.86+383448.7 03h48m18.8617s ...        0         0              0      0       0
    636  WISEA J034819.00+383418.6 03h48m19.0056s ...        0         0              0      0       0
    637  WISEA J034857.93+384042.2 03h48m57.9367s ...        0         0              0      0       0
    638    2MASS J03491851+3833030 03h49m18.5193s ...        0         0              0      0       0
    Length = 638 rows


Query in the IAU format
^^^^^^^^^^^^^^^^^^^^^^^

The `IAU format`_ in equatorial coordinates may also be used for querying purposes.
The equinox defaults to ``B1950`` but may be explicitly set to ``J2000``.
Note that NED reports results by searching within a 15 arcmin 
radius around the specified target.

.. doctest-remote-data::

    >>> from astroquery.ipac.ned import Ned
    >>> result_table = Ned.query_region_iau('1234-423')
    >>> print(result_table)
    No.        Object Name             RA-s         ... Diameter Distances Classification Images Spectra
                                                    ...
    ---- --------------------------  -------------- ... -------- --------- -------------- ------ -------
       1  WISEA J123658.23-424353.6	 12h36m58.2335s ...        0         0              0      0       0
       2  WISEA J123656.38-424350.6	 12h36m56.3841s ...        0         0              0      0       0
       3  WISEA J123700.43-424351.5	 12h37m00.4338s ...        0         0              0      0       0
       4  WISEA J123656.56-424336.2	 12h36m56.5615s ...        0         0              0      0       0
     ...                      ...              ...  ...      ...       ...            ...    ...     ...
    4390  WISEA J123719.28-425829.9	 12h37m19.2884s ...        0         0              0      0       0
    4391  WISEA J123816.82-423955.7	 12h38m16.8271s	...        0         0              0      0       0
    4392  WISEA J123537.95-424646.1	 12h35m37.9588s	...        0         0              0      0       0
    4393  WISEA J123813.48-424952.9	 12h38m13.4833s ...        0         0              0      0       0
    Length = 4393 rows


Query a reference code for objects
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

These queries can be used to retrieve all objects that appear in the specified 
19 digit reference code. They are similar to the
:meth:`~astroquery.simbad.SimbadClass.query_bibobj` queries.

.. doctest-remote-data::

    >>> from astroquery.ipac.ned import Ned
    >>> result_table = Ned.query_refcode('1997A&A...323...31K')
    >>> print(result_table)
    No.      Object Name             RA-s         ... Diameter Distances Classification Images Spectra
                                                  ...
    --- -------------------------- -------------- ... -------- --------- -------------- ------ -------
      1      ICRF J004847.1+315725 00h48m47.1414s ...       12         1             22     31      12
      2                   NGC 0591 01h33m31.2375s ...        7         0              9      8       4
      3                  UGC 01214 01h43m57.7816s ...       12         0              6     13       4
      4                   MRK 0599 02h47m47.4056s ...        6         0              3      2       1
    ...                       ...             ... ...      ...       ...            ...    ...     ...
     33      ICRF J015002.6-072548 01h50m02.6970s ...        2         0              2     11       1
     34  WISEA J202325.39+113134.6 20h23m25.3922s ...        2         0              1      2       0
     35                  Mrk 0463E 13h56m02.8881s ...        2         0              0      1      21
     36                  Mrk 0463W 13h56m02.6145s ...        4         0              1      0       0
     Length = 36 rows

Image and Spectra Queries
^^^^^^^^^^^^^^^^^^^^^^^^^

The image queries return a list of `~astropy.io.fits.HDUList` objects for the
specified name. For instance:

.. doctest-remote-data::

    >>> from astroquery.ipac.ned import Ned
    >>> images = Ned.get_images("m1")  # doctest: +IGNORE_OUTPUT
    Downloading https://ned.ipac.caltech.edu/dss1B2/Bb/MESSIER_001:I:103aE:dss1.fits.gz
    |===========================================|  32k/ 32k (100.00%)        00s
    Downloading https://ned.ipac.caltech.edu/img5/1995RXCD3.T...0000C/p083n22a:I:0.1-2.4keV:cop1995.fits.gz
    |===========================================|  52k/ 52k (100.00%)        01s
    Downloading https://ned.ipac.caltech.edu/img5/1996RXCD6.T...0000C/p083n22a:I:0.1-2.4keV:cps1996.fits.gz
    |===========================================|  96k/ 96k (100.00%)        03s
    Downloading https://ned.ipac.caltech.edu/img5/1995RXCD3.T...0000C/p084n22a:I:0.1-2.4keV:cop1995.fits.gz
    |===========================================|  52k/ 52k (100.00%)        01s
    Downloading https://ned.ipac.caltech.edu/img5/1998RXCD8.T...0000C/h083n22a:I:0.1-2.4keV:cps1998.fits.gz
    |===========================================|  35k/ 35k (100.00%)        00s
    >>> images  # doctest: +IGNORE_OUTPUT
    [[<astropy.io.fits.hdu.image.PrimaryHDU at 0x4311890>],
    [<astropy.io.fits.hdu.image.PrimaryHDU at 0x432b350>],
    [<astropy.io.fits.hdu.image.PrimaryHDU at 0x3e9c5d0>],
    [<astropy.io.fits.hdu.image.PrimaryHDU at 0x4339790>],
    [<astropy.io.fits.hdu.image.PrimaryHDU at 0x433dd90>]]

To get the URLs of the downloadable FITS images:

.. doctest-remote-data::

    >>> from astroquery.ipac.ned import Ned
    >>> image_list = Ned.get_image_list("m1")
    >>> image_list  # doctest: +IGNORE_OUTPUT
    ['https://ned.ipac.caltech.edu/dss1B2/Bb/MESSIER_001:I:103aE:dss1.fits.gz',
     'https://ned.ipac.caltech.edu/img/1995RXCD3.T...0000C/p084n22a:I:0.1-2.4keV:cop1995.fits.gz',
     'https://ned.ipac.caltech.edu/img/1996RXCD6.T...0000C/p083n22a:I:0.1-2.4keV:cps1996.fits.gz',
     'https://ned.ipac.caltech.edu/img/1998RXCD8.T...0000C/h083n22a:I:0.1-2.4keV:cps1998.fits.gz',
     'https://ned.ipac.caltech.edu/img/1995RXCD3.T...0000C/p083n22a:I:0.1-2.4keV:cop1995.fits.gz']


Spectra can also be fetched in the same way:

.. doctest-remote-data::

    >>> from astroquery.ipac.ned import Ned
    >>> spectra = Ned.get_spectra('3c 273')  # doctest: +IGNORE_OUTPUT
    Downloading https://ned.ipac.caltech.edu/spc1/2009A+A...495.1033B/3C_273:S:B:bcc2009.fits.gz
    |===========================================| 7.8k/7.8k (100.00%)        00s
    Downloading https://ned.ipac.caltech.edu/spc1/1992ApJS...80..109B/PG_1226+023:S:B_V:bg1992.fits.gz
    |===========================================| 5.0k/5.0k (100.00%)        00s
    Downloading https://ned.ipac.caltech.edu/spc1/2009A+A...495.1033B/3C_273:S:RI:bcc2009.fits.gz
    |===========================================| 9.4k/9.4k (100.00%)        00s
    >>> spectra  # doctest: +IGNORE_OUTPUT
    [[<astropy.io.fits.hdu.image.PrimaryHDU at 0x41b4190>],
    [<astropy.io.fits.hdu.image.PrimaryHDU at 0x41b0990>],
    [<astropy.io.fits.hdu.image.PrimaryHDU at 0x430a450>]]


Similarly the list of URLs for spectra of a particular object may be fetched:

.. doctest-remote-data::

    >>> from astroquery.ipac.ned import Ned
    >>> spectra_list = Ned.get_image_list("3c 273", item='spectra')
    >>> spectra_list
    ['https://ned.ipac.caltech.edu/spc1/1992/1992ApJS...80..109B/PG_1226+023:S:B_V:bg1992.fits.gz',
     'https://ned.ipac.caltech.edu/spc1/2009/2009A+A...495.1033B/3C_273:S:B:bcc2009.fits.gz',
     ...
     'https://ned.ipac.caltech.edu/spc1/2016/2016ApJS..226...19F/3C_273:S:CII158.3x3.fits.gz']


Fetching other data tables for an object 
----------------------------------------

Several other data tables for an object may be fetched via the :meth:`~astroquery.ipac.ned.NedClass.get_table`
queries. These take a keyword argument ``table``, which may be set to one of ``crossids``, ``positions``,
``redshifts``, ``distances``, ``photometry``, ``extinctions``, ``diameters``, ``references`` or
``notes`` (or ``object_notes``).  For
instance the ``table=photometry`` will fetch all the relevant photometric data
for the specified object, and the optional keyword argument ``is_line=True`` can be
used to get photometric data of line component. We look at a simple example:

.. doctest-remote-data::

    >>> from astroquery.ipac.ned import Ned
    >>> result_table = Ned.get_table("3C 273", table='positions')
    >>> print(result_table)
    No.      RA-s          Dec-s       ... Semi-Min Unc PA of unc      Reference      Fiducial
                                       ...    arcsec       deg
    --- -------------- --------------  ... ------------ --------- ------------------- --------
      1 12h29m06.6900s	+02d03m08.590s ...           --        -- 2025ApJ...978..115W       --
      2 12h29m06.7000s	+02d03m08.700s ...           --	       -- 2025MNRAS.539.2088S	    --
      3 12h29m06.7008s	+02d03m08.604s ...           --	       -- 2025MNRAS.539.1458A	    --
      4 12h29m06.7200s	+02d03m08.640s ...           --	       -- 2025A&A...695A.261H	    --
      5 12h29m06.0000s	+02d03m08.000s ...           --	       -- 2025ApJ...985...31R	    --
    ...            ...             ... ...          ...       ...                 ...      ...
    186	12h29m06.7000s	+02d03m08.700s ...           --        -- 2014ApJ...789..135W	    --
    187	12h29m06.7000s	+02d03m08.600s ...           --        -- 2014MNRAS.439..690H	    --
    188	12h29m06.7018s	+02d03m08.604s ...      0.50000	        0 2014MNRAS.439.2701H       --
    189	12h29m06.7000s	+02d03m09.000s ...           --        -- 2014MNRAS.441.3375X	    --
    190	12h29m06.8017s	+02d03m08.247s ...      1.17525	        0 2012GASC..C...0000S	    --
    Length = 190 rows

All above queries return results in a `~astropy.table.Table` or raise a Exception error (i.e.
`~astroquery.exceptions.RemoteServiceError`) if the service returns a query error.
To handle errors gracefully, wrap the query in a ``try/except`` block to catch the exception
and retrieve the error message. The following example demonstrates this pattern.

.. doctest-remote-data::

    >>> from astroquery.ipac.ned import Ned
    >>> try:
    >>>     result_table = Ned.query_object("mm")
    >>>     print(result_table) 
    >>> except Exception as e:
    >>>     print(e)
    The remote service returned the following message.
    ERROR: GeneralFault:
    Service could not complete request; Failed to resolve input object name (6)

For queries that return results in a `~astropy.table.Table`, you may optionally specify the ``max_rec`` argument to
limit the number of records returned. If ``max_rec`` is 0, only the table fields are returned. For example:

.. doctest-remote-data::

    >>> from astroquery.ipac.ned import Ned
    >>> result_table = Ned.query_region("3c 273", max_rec=4)
    >>> print(result_table)
    No.        Object Name              RA-s      ... Diameter Distances Classification Images Spectra
                                                  ...
    --- -------------------------- -------------- ... -------- --------- -------------- ------ -------
      1      ICRF J122906.6+020308 12h29m06.6997s ...       11         0              7    149      27
      2      [HB89] 1226+023 ABS17 12h29m06.6502s ...        0         0              0      1       0
      3      [HB89] 1226+023 ABS18 12h29m06.6502s ...        0         0              0      1       0
      4      [HB89] 1226+023 ABS08 12h29m06.6502s ...        0         0              0      0       0
    Length = 4 rows


Troubleshooting
===============

If you are repeatedly getting failed queries, or bad/out-of-date results, try clearing your cache:

.. code-block:: python

    >>> from astroquery.ipac.ned import Ned
    >>> Ned.clear_cache()

If this function is unavailable, upgrade your version of astroquery.
The ``clear_cache`` function was introduced in version 0.4.7.dev8479.


Reference/API
=============

.. automodapi:: astroquery.ipac.ned
    :no-inheritance-diagram:

.. _IAU format: https://cds.unistra.fr/Dic/iau-spec.html
