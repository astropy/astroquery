.. doctest-skip-all

.. _astroquery.hsc:

************************************
HSC-SSP Queries (`astroquery.hsc`)
************************************

Getting started
===============

This module allows searching catalogs and retrieving images from the 
`Hyper Suprime-Cam Subaru Strategic Program`_ (HSC-SSP) archive. In order to
use this service a valid account for the HSC archive is needed. An HSC object
must be instantiated using the account credentials.

.. code-block:: python

    >>> from astroquery.hsc import Hsc

    # Now first instantiate a new Hsc object with login credentials

    >>> h_obj = Hsc(username='xyz', password='secret') # doctest: +SKIP

    >>> # The prompt appears indicating successful login

Alternatively, you can use the `login` method after importing the HSC module.

.. code-block:: python

    >>> from astroquery.hsc import Hsc
    >>> Hsc.login(username='xyz', password='secret') # doctest: +SKIP

If ``username`` and/or ``password`` parameters are missing, a prompt in the 
console will appear for you to introduce them

.. code-block:: python

    >>> from astroquery.hsc import Hsc
    >>> Hsc.login() # doctest: +SKIP

    HSC Archive user: xyz
    xyz, enter your password:

The HSC archive password can be stored in the system keyring service using
the service name `hscssp`. If no ``password`` is passed while login, the module
will search the user's password in the keyring.


Note that at login time you may also optionally set the data release and the 
survey that you would like to query. By default the ``public_release`` is set 
to 'pdr1' and the ``survey`` is set to 'wide'.

.. code-block:: python

    >>> from astroquery.hsc import Hsc
    >>> h_obj = Hsc(username='xyz', password='secret',       # doctest: +SKIP
    ...             release_version='pdr1', survey='deep')   # doctest: +SKIP
    >>>

At any given time you may if you wish check your login status (continuing from
the above example):

.. code-block:: python

    >>> h_obj.authenticated() # doctest: +SKIP

    True

If you want to change your data release and survey after you have already 
instantiated the object - say ``h_obj`` then you should do:

.. code-block:: python

    >>> h_obj.survey = 'new_survey_here'           # doctest: +SKIP
    >>> h_obj.release_version = 'new_release_here' # doctest: +SKIP

If you would like to get a list of the available HSC surveys, you
can do so by using :meth:`~astroquery.hsc.HscClass.list_surveys`:

.. code-block:: python

    >>> from astroquery.hsc import Hsc
    >>> Hsc.list_surveys()

    ['wide', 'deep', 'udeep']

Similarly, you can get the list of data releases using 
:meth:`~astroquery.hsc.HscClass.list_releases`:

.. code-block:: python

    >>> Hsc.list_releases()

    ['pdr1']

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

    >>> from astroquery.hsc import Hsc
    >>> from astropy import units as u
    >>> from astropy.coordinates import SkyCoord

    >>> Hsc.login(username='xyz', password='secret')
    >>> images = Hsc.get_images(SkyCoord(ra=34.0*u.deg, dec=-5.0*u.deg, frame='icrs'))

    Downloading URL https://hsc-release.mtk.nao.ac.jp/das_quarry/cgi-bin/quarryImage?ra=34.0&dec=-5.0&sw=0.00833&sh=0.00833&type=coadd&filter=HSC-G&image=on&rerun=pdr1_wide to /tmp/tmpf4qq6gpg ... [Done]

    >>> images

    [[<astropy.io.fits.hdu.image.PrimaryHDU object at 0x7fe033c5ccc0>, <astropy.io.fits.hdu.image.ImageHDU object at 0x7fe033bf2a58>, <astropy.io.fits.hdu.image.ImageHDU object at 0x7fe033bf2dd8>, <astropy.io.fits.hdu.image.ImageHDU object at 0x7fe033bf2f98>]]

Note if you have logged in using the procedure described earlier and assuming
that you already have a `~astroquery.hsc.HscClass` object ``h_obj`` instantiated:

.. code-block:: python

    >>> images = h_obj.get_images(SkyCoord(ra=34.0*u.deg, dec=-5.0*u.deg, frame='icrs'),
    ...                           image_width=2*u.arcmin)


:meth:`~astroquery.hsc.HscClass.get_images` works with two different modes. 
If the parameter ``radius`` is set, it returns all the coadded survey images 
(coadds) covering the defined area. Otherwise, it returns a cut out image with
size defined by the ``image_width`` and the ``image_height`` keyword arguments.
If only the ``image_width`` is set then the ``image_height`` is taken to be 
the same as this width. By default the ``image_width`` is set to 1 arcmin. To 
set these parameters to your desired value, you should enter it using a 
`~astropy.units.Quantity` object with appropriate units or as a string that is 
parsable by `~astropy.coordinates.Angle`.

For downloading a 10 x 20 arcsec cut out image from the ultradeep survey:

.. code-block:: python

    >>> from astroquery.hsc import Hsc
    >>> from astropy import units as u
    >>> from astropy.coordinates import SkyCoord
    >>> h_obj = Hsc(username='xyz', password='secret', survey='udeep')
    >>> images = h_obj.get_images(SkyCoord(ra=34.0*u.deg, dec=-5.0*u.deg, frame='icrs'),
    ...                           image_width=10*u.arcsec, image_height=20*u.arcsec)


Other parameter you can set are is ``filters`` that decides the color filters 
to download. This must be a list with elements chosen from ::

    'g' 'r' 'i' 'z' 'y' 'NB0921' 'NB0816'

Alternatively, you can pass the value 'all', which includes in the list all 
the above values. Note that in cut out mode only the first value of the list 
is used.

Note that rather than fetching the actual images, you could also get the URLs 
of the downloadable images. This is particularly useful while searching for 
coadds, since they can be quite large. To do this simply replace the call to
:meth:`~astroquery.hsc.HscClass.get_images` by a call to
:meth:`~astroquery.hsc.HscClass.get_image_list` with exactly the same
parameters. Let us now see a complete example to illustrate these points.

.. code-block:: python

    >>> from astroquery.hsc import Hsc
    >>> from astropy import units as u
    >>> from astropy.coordinates import SkyCoord
    >>> h_obj = Hsc(username='xyz', password='secret', survey='wide')
    >>> image_urls = h_obj.get_image_list(SkyCoord(ra=34.0*u.deg, dec=-5.0*u.deg, 
    ...                                   frame='icrs'), radius=3*u.arcmin,
    ...                                   filters=['g', 'i', 'y'])

    ['https://hsc-release.mtk.nao.ac.jp/archive/filetree/pdr1_wide/deepCoadd/HSC-I/8523/6,5/calexp-HSC-I-8523-6,5.fits.gz', 
     'https://hsc-release.mtk.nao.ac.jp/archive/filetree/pdr1_wide/deepCoadd/HSC-G/8523/5,6/calexp-HSC-G-8523-5,6.fits.gz', 
     'https://hsc-release.mtk.nao.ac.jp/archive/filetree/pdr1_wide/deepCoadd/HSC-Y/8523/6,5/calexp-HSC-Y-8523-6,5.fits.gz', 
     'https://hsc-release.mtk.nao.ac.jp/archive/filetree/pdr1_wide/deepCoadd/HSC-I/8523/5,5/calexp-HSC-I-8523-5,5.fits.gz', 
     'https://hsc-release.mtk.nao.ac.jp/archive/filetree/pdr1_wide/deepCoadd/HSC-I/8523/5,6/calexp-HSC-I-8523-5,6.fits.gz', 
     'https://hsc-release.mtk.nao.ac.jp/archive/filetree/pdr1_wide/deepCoadd/HSC-G/8523/6,5/calexp-HSC-G-8523-6,5.fits.gz', 
     'https://hsc-release.mtk.nao.ac.jp/archive/filetree/pdr1_wide/deepCoadd/HSC-Y/8523/5,6/calexp-HSC-Y-8523-5,6.fits.gz', 
     'https://hsc-release.mtk.nao.ac.jp/archive/filetree/pdr1_wide/deepCoadd/HSC-Y/8523/5,5/calexp-HSC-Y-8523-5,5.fits.gz', 
     'https://hsc-release.mtk.nao.ac.jp/archive/filetree/pdr1_wide/deepCoadd/HSC-G/8523/5,5/calexp-HSC-G-8523-5,5.fits.gz']

Query a region
--------------

Another type of query is to search a catalog for objects within a specified
radius of a source. Again the source may be either a named identifier or it may
be specified via coordinates. The radius may be specified as in the previous
cases by using a `~astropy.units.Quantity` or a string parsable via
`~astropy.coordinates.Angle`. If this is missing, then it defaults to 1 arcmin.
The query results are returned in a `~astropy.table.Table`.

.. code-block:: python

    >>> from astroquery.hsc import Hsc
    >>> from astropy import units as u
    >>> from astropy.coordinates import SkyCoord

    >>> Hsc.login(username='xyz', password='secret')
    >>> table = Hsc.query_region(SkyCoord(ra=34.0, dec=-5.0, unit='deg', 
    ...                          frame='icrs'), radius=6*u.arcsec)    

    Waiting for query to finish... [Done]
    Downloading https://hsc-release.mtk.nao.ac.jp/datasearch/catalog_jobs/download/77af1bd99cebdc48dabaa28a4b4c58e7c05920e51cce14ec0e1d69b088b99470
    |========================================| 8.6k/8.6k (100.00%)         0s

    >>> print(table)

        object_id             ra                dec        
    ----------------- ----------------- -------------------
    37485259083748138 33.99899148216766  -5.000156511563555
    37485259083748145 33.99972328462561  -4.998867128067907
    37485259083766167 33.99972328091072 -4.9988670755433295
    37485259083766168 34.00010729810445  -5.000045699595388
    37485259083766169 34.00045276837051  -5.000067874545467


You can also select the columns that are returned in the search using they
optional keyword ``columns``. See the `schema browser of the HSC database`_ 
for all available options.

.. code-block:: python

    >>> from astroquery.hsc import Hsc
    >>> from astropy import units as u
    >>> from astropy.coordinates import SkyCoord

    >>> h_obj = Hsc(username='xyz', password='secret', survey='udeep')
    >>> columns = ['object_id', 'gcmodel_mag', 'gcmodel_mag_err', 
    ...            'rcmodel_mag', 'rcmodel_mag_err']
    >>> table = h_obj.query_region(SkyCoord(ra=34.0, dec=-5.0, unit='deg', 
    ...                            frame='icrs'), radius=6*u.arcsec, 
    ...                            columns=columns) 

    >>> print(table)

        object_id     gcmodel_mag gcmodel_mag_err rcmodel_mag rcmodel_mag_err
    ----------------- ----------- --------------- ----------- ---------------
    37485259083776096   26.743294       0.0994086   26.273159      0.10481422
    37485259083776073    23.45693     0.005696027   22.793543    0.0045330757
    37485259083776100   24.725897     0.018476432   24.643585     0.025570812
    37485259083776183   27.423729      0.16541111   27.359972      0.22967525
    37485259083776025   27.385054      0.23840225   25.665733      0.07151146
    37485259083776024    28.46108       0.5845834   28.553331      0.99405605

Reference/API
=============

.. automodapi:: astroquery.hsc
    :no-inheritance-diagram:
    :inherited-members:


.. _Hyper Suprime-Cam Subaru Strategic Program: https://hsc-release.mtk.nao.ac.jp
.. _schema browser of the HSC database: https://hsc-release.mtk.nao.ac.jp/schema