.. _astroquery.irsa_dust:

*************************************************************
IRSA Dust Extinction Service Queries (`astroquery.irsa_dust`)
*************************************************************

Getting started
===============

This module can be used to query the `IRSA Dust Extinction Service`_.


Fetch images
------------

Retrieve the image cut-outs for the specified object name or coordinates. The
images fetched in the FITS format and the result is returned as a list of
`~astropy.io.fits.HDUList` objects. For all image queries, the radius may be optionally
specified. If missing the radius defaults to 5 degrees. Note that radius may be
specified in any appropriate unit, however it must fall in the range of 2 to
37.5 degrees.

.. code-block:: python
.. doctest-remote-data::

    >>> from astroquery.irsa_dust import IrsaDust
    >>> image_list = IrsaDust.get_images("m81")   # doctest: +IGNORE_OUTPUT
    Downloading http://irsa.ipac.caltech.edu//workspace/TMP_pdTImE_1525/DUST/m81.v0001/p414Dust.fits
    |===========================================| 331k/331k (100.00%)        15s
    Downloading http://irsa.ipac.caltech.edu//workspace/TMP_pdTImE_1525/DUST/m81.v0001/p414i100.fits
    |===========================================| 331k/331k (100.00%)        13s
    Downloading http://irsa.ipac.caltech.edu//workspace/TMP_pdTImE_1525/DUST/m81.v0001/p414temp.fits
    |===========================================| 331k/331k (100.00%)        05s
    >>> image_list   # doctest: +IGNORE_OUTPUT
    [[<astropy.io.fits.hdu.image.PrimaryHDU at 0x39b8610>],
    [<astropy.io.fits.hdu.image.PrimaryHDU at 0x39b8bd0>],
    [<astropy.io.fits.hdu.image.PrimaryHDU at 0x39bd8d0>]]

Image queries return cutouts for 3 images - E(B-V) reddening, 100 micron
intensity, and dust temperature maps. If only the image of a particular type is
required, then this may be specified by using the ``image_type`` keyword argument
to the :meth:`~astroquery.irsa_dust.IrsaDustClass.get_images` method. It can take on one of the three values
``ebv``, ``100um`` and ``temperature``, corresponding to each of the 3 kinds of
images:

.. code-block:: python
.. doctest-remote-data::

    >>> from astroquery.irsa_dust import IrsaDust
    >>> import astropy.units as u
    >>> image = IrsaDust.get_images("m81", image_type="100um", radius=2*u.deg)  # doctest: +IGNORE_OUTPUT
    Downloading http://irsa.ipac.caltech.edu//workspace/TMP_007Vob_24557/DUST/m81.v0001/p414i100.fits
    |===========================================| 149k/149k (100.00%)        02s
    >>> image  # doctest: +IGNORE_OUTPUT
    [[<astropy.io.fits.hdu.image.PrimaryHDU at 0x3a5a650>]]

The image types that are available can also be listed out any time:

.. code-block:: python
.. doctest-remote-data::

    >>> from astroquery.irsa_dust import IrsaDust
    >>> IrsaDust.list_image_types()
    ['temperature', 'ebv', '100um']

The target may also be specified via coordinates passed as strings. Examples of acceptable coordinate
strings can be found on this `IRSA DUST coordinates description page`_.

.. code-block:: python
.. doctest-remote-data::

    >>> from astroquery.irsa_dust import IrsaDust
    >>> import astropy.coordinates as coord
    >>> import astropy.units as u
    >>> image_list = IrsaDust.get_images("17h44m34s -27d59m13s", radius=2.0 * u.deg)  # doctest: +IGNORE_OUTPUT
    Downloading http://irsa.ipac.caltech.edu//workspace/TMP_46IWzq_9460/DUST/17h44m34s_-27d59m13s.v0001/p118Dust.fits
    |==============================|  57k/ 57k (100.00%)        00s
    Downloading http://irsa.ipac.caltech.edu//workspace/TMP_46IWzq_9460/DUST/17h44m34s_-27d59m13s.v0001/p118i100.fits
    |==============================|  57k/ 57k (100.00%)        00s
    Downloading http://irsa.ipac.caltech.edu//workspace/TMP_46IWzq_9460/DUST/17h44m34s_-27d59m13s.v0001/p118temp.fits
    |==============================|  57k/ 57k (100.00%)        00s


A list having the download links for the FITS image may also be fetched, rather
than the actual images, via the :meth:`~astroquery.irsa_dust.IrsaDustClass.get_image_list` method. This also
supports the ``image_type`` argument, in the same way as described for
:meth:`~astroquery.irsa_dust.IrsaDustClass.get_images`.

.. code-block:: python
.. doctest-remote-data::

    >>> from astroquery.irsa_dust import IrsaDust
    >>> import astropy.coordinates as coord
    >>> import astropy.units as u
    >>> coo = coord.SkyCoord(34.5565*u.deg, 54.2321*u.deg, frame='galactic')
    >>> image_urls = IrsaDust.get_image_list(coo)
    >>> image_urls  # doctest: +IGNORE_OUTPUT
    ['http://irsa.ipac.caltech.edu//workspace/TMP_gB3awn_6492/DUST/34.5565_54.2321_gal.v0001/p292Dust.fits',
    'http://irsa.ipac.caltech.edu//workspace/TMP_gB3awn_6492/DUST/34.5565_54.2321_gal.v0001/p292i100.fits',
    'http://irsa.ipac.caltech.edu//workspace/TMP_gB3awn_6492/DUST/34.5565_54.2321_gal.v0001/p292temp.fits']


Fetching the extinction table
-----------------------------

This fetches the extinction table as a `~astropy.table.Table`. The input parameters are the same as in
the queries discussed above, namely the target string and optionally a radius
value:

.. code-block:: python
.. doctest-remote-data::

    >>> from astroquery.irsa_dust import IrsaDust
    >>> import astropy.coordinates as coord
    >>> import astropy.units as u
    >>> # "22h57m57.5s +26d09m00.09s Equatorial B1950"
    >>> coo = coord.SkyCoord("22h57m57.5s +26d09m00.09s", frame='fk4')
    >>> table = IrsaDust.get_extinction_table(coo)  # doctest: +IGNORE_OUTPUT
    Downloading http://irsa.ipac.caltech.edu//workspace/TMP_wuevFn_3781/DUST/345.094229457703_26.418650782801027.v0001/extinction.tbl
    |=======================================================================================| 4.4k/4.4k (100.00%)         0s
    >>> print(table)
    Filter_name LamEff A_over_E_B_V_SandF A_SandF A_over_E_B_V_SFD A_SFD
                micron                      mag                     mag
    ----------- ------ ------------------ ------- ---------------- -----
         CTIO U 0.3734              4.107   0.174            4.968  0.21
         CTIO B 0.4309              3.641   0.154            4.325 0.183
         CTIO V 0.5517              2.682   0.113             3.24 0.137
         CTIO R  0.652              2.119    0.09            2.634 0.111
         CTIO I 0.8007              1.516   0.064            1.962 0.083
       DSS-II g 0.4621              3.381   0.143            3.907 0.165
       DSS-II r 0.6546              2.088   0.088            2.649 0.112
       DSS-II i 0.8111              1.487   0.063            1.893  0.08
         SDSS u 0.3587              4.239   0.179            5.155 0.218
         SDSS g 0.4717              3.303    0.14            3.793  0.16
            ...    ...                ...     ...              ...   ...
        UKIRT K   2.19              0.302   0.013            0.367 0.016
        2MASS J   1.23              0.723   0.031            0.937  0.04
        2MASS H   1.64               0.46   0.019            0.591 0.025
       2MASS Ks   2.16               0.31   0.013            0.382 0.016
         IRAC-1   3.52              0.178   0.008             0.22 0.009
         IRAC-2   4.46              0.148   0.006            0.183 0.008
         IRAC-3   5.66               0.13   0.005            0.162 0.007
         IRAC-4   7.68              0.122   0.005            0.151 0.006
         WISE-1   3.32              0.189   0.008            0.234  0.01
         WISE-2   4.57              0.146   0.006             0.18 0.008
    Length = 25 rows

Get other query details
-----------------------

This fetches in a `~astropy.table.Table` other additional details that may be
returned in the query results. For instance additional details in the three
sections - ``ebv``, ``100um`` and ``temperature`` as mentioned earlier and an
additional section ``location`` may be fetched using the ``section`` keyword
argument. If on the other hand, ``section`` is missing then the complete table
with all the four sections will be returned.

.. code-block:: python
.. doctest-remote-data::

    >>> from astroquery.irsa_dust import IrsaDust
    >>> table = IrsaDust.get_query_table('2MASXJ23045666+1219223') # get the whole table
    >>> print(table)
        RA      Dec    coord sys regSize ... temp mean temp std temp max temp min
       deg      deg                deg   ...
    --------- -------- --------- ------- ... --------- -------- -------- --------
    346.23608 12.32286 equ J2000     5.0 ...   17.0721   0.0345  17.1189  17.0152
    >>> table_ebv = IrsaDust.get_query_table('2MASXJ23045666+1219223', section='ebv') # get only one section
    >>> print(table_ebv)
        ext desc     ... ext SFD min
                     ...
    ---------------- ... -----------
    E(B-V) Reddening ...      0.1099


Reference/API
=============

.. automodapi:: astroquery.irsa_dust
    :no-inheritance-diagram:

.. _IRSA Dust Extinction Service: http://irsa.ipac.caltech.edu/applications/DUST/index.html
.. _IRSA DUST coordinates description page: http://irsa.ipac.caltech.edu/applications/DUST/docs/coordinate.html
