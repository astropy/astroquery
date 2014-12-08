.. doctest-skip-all

.. _astroquery.ukidss:

************************************
UKIDSS Queries (`astroquery.ukidss`)
************************************

Getting started
===============

This module allows searching catalogs and retrieving images from the UKIDSS web
service. Some data can on UKIDSS can be accessed only after a valid login. For
accessing such data a UKIDSS object must first be instantiated with valid
credentials. On the other hand, to access the public data, the various query
functions may just be called as class methods - i.e. no instantiation is
required. Below are examples that illustrate both the means for accessing the
data.

**Case 1 : Access only public data - No login**

.. code-block:: python

    >>> from astroquery.ukidss import Ukidss

    # perform any query as a class method - no instantiation required

    >>> images = Ukidss.get_images("m1")

    Found 1 targets
    Downloading http://surveys.roe.ac.uk/wsa/cgi-bin/getFImage.cgi?file=/disk05/wsa/ingest/fits/20071011_v1/w20071011_01818_sf_st.fit&mfid=1737581&extNo=4&lx=1339&hx=1638&ly=1953&hy=2252&rf=0&flip=1&uniq=5348_573_21_31156_1&xpos=150.7&ypos=150.3&band=K&ra=83.633083&dec=22.0145
    |===========================================| 174k/174k (100.00%)        02s


**Case 2 : Login to access non-public data**

.. code-block:: python

    >>> from astroquery.ukidss import Ukidss

    # Now first instantiate a Ukidss object with login credentials

    >>> u_obj = Ukidss(username='xyz', password='secret', # doctest: +SKIP
    ...                community='your_community')        # doctest: +SKIP

    >>> # The prompt appears indicating successful login


Note that at login time you may also optionally set the database and the survey
that you would like to query. By default the database is set to 'UKIDSSDR7PLUS'
and the ``programme_id`` is set to 'all' - which includes all the surveys. A word
of warning - for region queries you should explicitly set the
``programme_id`` to the survey you wish to query. Querying all surveys is
permitted only for image queries.

.. code-block:: python

    >>> from astroquery.ukidss import Ukidss
    >>> u_obj = Ukidss(username='xyz', password='secret',                    # doctest: +SKIP
    ...                community='your_community', database='UKIDSSDR8PLUS', # doctest: +SKIP
    ...                programme_id='GPS')                                   # doctest: +SKIP
    >>>

At any given time you may if you wish check your login status (continuing from
the above example):

.. code-block:: python

    >>> u_obj.logged_in() # doctest: +SKIP

    True

If you want to change your programme_id and database after you have already instantiated the
object - say ``u_obj`` then you should do:

.. code-block:: python

    >>> u_obj.programme_id = 'new_id_here'   # doctest: +SKIP
    >>> u_obj.database = 'new_database_here' # doctest: +SKIP

The above examples mention ``programme_id`` that specifies the catalog
or survey you wish to query. If you would like to get a list of the commonly
available UKIDSS survey - either the abbreviations or the complete names, you
can do so by using :meth:`~astroquery.ukidss.UkidssClass.list_catalogs`:

.. code-block:: python

    >>> from astroquery.ukidss import Ukidss
    >>> Ukidss.list_catalogs()

    ['UDS', 'GCS', 'GPS', 'DXS', 'LAS']

    >>> Ukidss.list_catalogs(style='long')

    ['Galactic Plane Survey',
     'Deep Extragalactic Survey',
     'Galactic Clusters Survey',
     'Ultra Deep Survey',
     'Large Area Survey']

Now we look at examples of the actual queries that can be performed.

Get images around a target
--------------------------

You can fetch images around the specified target or coordinates. When a target
name is used rather than the coordinates, this will be resolved to coordinates
using astropy name resolving methods that utilize online services like
SESAME. Coordinates may be entered using the suitable object from
`astropy.coordinates`. The images are returned as a list of
`~astropy.io.fits.HDUList` objects.


.. code-block:: python

    >>> from astroquery.ukidss import Ukidss
    >>> images = Ukidss.get_images("m1")

    Found 1 targets
    Downloading http://surveys.roe.ac.uk/wsa/cgi-bin/getFImage.cgi?file=/disk05/wsa/ingest/fits/20071011_v1/w20071011_01818_sf_st.fit&mfid=1737581&extNo=4&lx=1339&hx=1638&ly=1953&hy=2252&rf=0&flip=1&uniq=142_292_19_31199_1&xpos=150.7&ypos=150.3&band=K&ra=83.633083&dec=22.0145
    |===========================================| 174k/174k (100.00%)        07s

    >>> print(images)

    [[<astropy.io.fits.hdu.image.PrimaryHDU object at 0x40f8b10>, <astropy.io.fits.hdu.image.ImageHDU object at 0x41026d0>]]

Note if you have logged in using the procedure described earlier and assuming
that you already have a `~astroquery.ukidss.UkidssClass` object ``u_obj`` instantiated:

.. code-block:: python

    >>> images = u_obj.get_images("m1") # doctest: +SKIP

There are several optional parameters that you can specify in image
queries. For instance to specify the image size you should set the
``image_width`` and the ``image_height`` keyword arguments. If only the
``image_width`` is set then the ``image_height`` is taken to be the same as this
width. By default the ``image_width`` is set to 1 arcmin. To set this to your
desired value, you should enter it using a `~astropy.units.Quantity` object
with appropriate units or as a string that is parsable by
`~astropy.coordinates.Angle`. Another parameter you may set is
``radius``. This may be specified in the same way as the ``image_height`` and
``image_width`` with the ``radius`` keyword. By specifying this multi-frame FITS
images will be retrieved. Note that in this case the image height and width
parameters will no longer be effective.

.. code-block:: python

    >>> from astroquery.ukidss import Ukidss
    >>> import astropy.units as u
    >>> import astropy.coordinates as coord
    >>> images = Ukidss.get_images(coord.SkyCoord(49.489, -0.27,
    ...                                           unit=(u.deg, u.deg),
    ...                                           frame='galactic'),
    ...                            image_width=5 * u.arcmin)

        Found 6 targets
    Downloading http://surveys.roe.ac.uk/wsa/cgi-bin/getFImage.cgi?file=/disk24/wsa/ingest/fits/20060603_v1/w20060603_01510_sf_st_two.fit&mfid=2514752&extNo=1&lx=862&hx=1460&ly=1539&hy=2137&rf=270&flip=1&uniq=575_115_31_31555_1&xpos=300.1&ypos=299.7&band=J&ra=290.8256247&dec=14.56435
    |===========================================| 518k/518k (100.00%)        06s
    Downloading http://surveys.roe.ac.uk/wsa/cgi-bin/getFImage.cgi?file=/disk24/wsa/ingest/fits/20060603_v1/w20060603_01510_sf_st.fit&mfid=966724&extNo=1&lx=862&hx=1460&ly=1539&hy=2137&rf=270&flip=1&uniq=575_115_31_31555_2&xpos=300&ypos=299.8&band=J&ra=290.8256247&dec=14.56435
    |===========================================| 517k/517k (100.00%)        06s
    Downloading http://surveys.roe.ac.uk/wsa/cgi-bin/getFImage.cgi?file=/disk24/wsa/ingest/fits/20060603_v1/w20060603_01544_sf_st_two.fit&mfid=2514753&extNo=1&lx=863&hx=1461&ly=1538&hy=2136&rf=270&flip=1&uniq=575_115_31_31555_3&xpos=300&ypos=300&band=H&ra=290.8256247&dec=14.56435
    |===========================================| 654k/654k (100.00%)        06s
    Downloading http://surveys.roe.ac.uk/wsa/cgi-bin/getFImage.cgi?file=/disk24/wsa/ingest/fits/20060603_v1/w20060603_01544_sf_st.fit&mfid=965662&extNo=1&lx=863&hx=1461&ly=1538&hy=2136&rf=270&flip=1&uniq=575_115_31_31555_4&xpos=300&ypos=300.1&band=H&ra=290.8256247&dec=14.56435
    |===========================================| 647k/647k (100.00%)        06s
    Downloading http://surveys.roe.ac.uk/wsa/cgi-bin/getFImage.cgi?file=/disk24/wsa/ingest/fits/20060603_v1/w20060603_01577_sf_st.fit&mfid=952046&extNo=1&lx=863&hx=1460&ly=1538&hy=2135&rf=270&flip=1&uniq=575_115_31_31555_5&xpos=299.2&ypos=299.7&band=K&ra=290.8256247&dec=14.56435
    |===========================================| 586k/586k (100.00%)        06s
    Downloading http://surveys.roe.ac.uk/wsa/cgi-bin/getFImage.cgi?file=/disk24/wsa/ingest/fits/20060603_v1/w20060603_01577_sf_st_two.fit&mfid=2514749&extNo=1&lx=863&hx=1460&ly=1538&hy=2135&rf=270&flip=1&uniq=575_115_31_31555_6&xpos=299.5&ypos=299.3&band=K&ra=290.8256247&dec=14.56435
    |===========================================| 587k/587k (100.00%)        04s


Again the query may be performed similarly with a log-in.

If you haven't logged-in then you could also specify the ``programme_id`` as a
keyword argument. By default this is set to 'all'. But you can change it to a
specific survey as mentioned earlier. The same goes for the ``database`` which
is set by default to 'UKIDSSDR7PLUS'. Some more parameters you can set are the
``frame_type`` which may be one of ::

    'stack' 'normal' 'interleave' 'deep_stack' 'confidence' 'difference'
    'leavstack' 'all'

and the ``waveband`` that decides the color filter to download. This must be
chosen from ::

    'all' 'J' 'H' 'K' 'H2' 'Z' 'Y' 'Br'

Note that rather than fetching the actual images, you could also get the URLs of the downloadable
images. To do this simply replace the call to
:meth:`~astroquery.ukidss.UkidssClass.get_images` by a call to
:meth:`~astroquery.ukidss.UkidssClass.get_image_list` with exactly the same
parameters. Let us now see a complete example to illustrate these points.


.. code-block:: python

    >>> from astroquery.ukidss import Ukidss
    >>> import astropy.units as u
    >>> import astropy.coordinates as coord
    >>> image_urls = Ukidss.get_image_list(coord.SkyCoord(ra=83.633083,
    ...          dec=22.0145, unit=(u.deg, u.deg), frame='icrs'),
    ...          frame_type='interleave',
    ...          programme_id="GCS", waveband="K", radius=20*u.arcmin)
    >>> image_urls

        ['http://surveys.roe.ac.uk/wsa/cgi-bin/fits_download.cgi?file=/disk05/wsa/ingest/fits/20071011_v1/w20071011_01802_sf.fit&MFID=1737551&rID=2544',
     'http://surveys.roe.ac.uk/wsa/cgi-bin/fits_download.cgi?file=/disk05/wsa/ingest/fits/20071011_v1/w20071011_01802_sf_st.fit&MFID=1737553&rID=2544',
     'http://surveys.roe.ac.uk/wsa/cgi-bin/fits_download.cgi?file=/disk05/wsa/ingest/fits/20071011_v1/w20071011_01806_sf.fit&MFID=1737559&rID=2544',
     'http://surveys.roe.ac.uk/wsa/cgi-bin/fits_download.cgi?file=/disk05/wsa/ingest/fits/20071011_v1/w20071011_01818_sf_st.fit&MFID=1737581&rID=2544',
     'http://surveys.roe.ac.uk/wsa/cgi-bin/fits_download.cgi?file=/disk05/wsa/ingest/fits/20071011_v1/w20071011_01818_sf.fit&MFID=1737579&rID=2544',
     'http://surveys.roe.ac.uk/wsa/cgi-bin/fits_download.cgi?file=/disk05/wsa/ingest/fits/20071011_v1/w20071011_01822_sf.fit&MFID=1737587&rID=2544']


Query a region
--------------

Another type of query is to search a catalog for objects within a specified
radius of a source. Again the source may be either a named identifier or it may
be specified via coordinates. The radius may be specified as in the previous
cases by using a `~astropy.units.Quantity` or a string parsable via
`~astropy.coordinates.Angle`. If this is missing, then it defaults to 1 arcmin.
As before you may also mention the ``programme_id`` and the ``database``. The query
results are returned in a `~astropy.table.Table`.

.. code-block:: python

    >>> from astroquery.ukidss import Ukidss
    >>> import astropy.coordinates as coord
    >>> import astropy.units as u
    >>> table = Ukidss.query_region(coord.SkyCoord(10.625, -0.38,
    ...                                            unit=(u.deg, u.deg),
    ...                                            frame='galactic'),
    ...                             radius=6 * u.arcsec)

    Downloading http://surveys.roe.ac.uk/wsa/tmp/tmp_sql/results1_4_45_58_24651.xml
    |===========================================| 4.6k/4.6k (100.00%)        00s

    >>> print(table)

         sourceID    framesetID        RA      ... H2AperMag3Err     distance
    ------------ ------------ ------------- ... ------------- ---------------
    438758381345 438086690175 272.615581037 ...  -9.99999e+08 0.0864656469768
    438758381157 438086690175   272.6178395 ...  -9.99999e+08 0.0717893063941
    438758381256 438086690175 272.616581639 ...  -9.99999e+08 0.0725261678319
    438758399768 438086690175 272.618154346 ...  -9.99999e+08 0.0800819201056
    438758399809 438086690175 272.617630209 ...  -9.99999e+08 0.0996951205267
    438758399828 438086690175 272.617238438 ...  -9.99999e+08 0.0435480204348
    438758399832 438086690175 272.617034836 ...  -9.99999e+08 0.0665854385804
    438758414982 438086690175 272.616576986 ...  -9.99999e+08 0.0214102038115


Reference/API
=============

.. automodapi:: astroquery.ukidss
    :no-inheritance-diagram:
