.. doctest-skip-all

Astroquery API Specification
============================


Service Class
-------------
The query tools will be implemented as class methods, so that the standard approach
for a given web service (e.g., IRSA, UKIDSS, SIMBAD) will be

.. code-block:: python

    from astroquery.service import Service

    result = Service.query_object('M 31')

for services that do not require login, and

.. code-block:: python

    from astroquery.service import Service

    S = Service(user='username',password='password')
    result = S.query_object('M 31')

for services that do.

Query Methods
~~~~~~~~~~~~~
The classes will have the following methods where appropriate:

.. code-block:: python

    query_object(objectname, ...)
    query_region(coordinate, radius=, width=)
    get_images(coordinate)

They may also have other methods for querying non-standard data types (e.g.,
ADS queries that may return a ``bibtex`` text block).

query_object
````````````

``query_object`` is only needed for services that are capable of parsing an
object name (e.g., SIMBAD, Vizier, NED), otherwise ``query_region`` is an
adequate approach, as any name can be converted to a coordinate via the SIMBAD
name parser.


query_region
````````````
Query a region around a coordinate.

One of these keywords *must* be specified (no default is assumed)::

    radius - an astropy Quantity object, or a string that can be parsed into one.  e.g., '1 degree' or 1*u.degree.
        If radius is specified, the shape is assumed to be a circle
    width - a Quantity.  Specifies the edge length of a square box
    height - a Quantity.  Specifies the height of a rectangular box.  Must be passed with width.

Returns a `~astropy.table.Table`.

get_images
``````````
Perform a coordinate-based query to acquire images.

Returns a list of `~astropy.io.fits.HDUList` objects.

Shape keywords are optional - some query services allow searches for images
that overlap with a specified coordinate.

(query)_async
`````````````

Includes ``get_images_async``, ``query_region_async``, ``query_object_async``

Same as the above query tools, but returns a list of readable file objects instead of a parsed
object so that the data is not downloaded until ``result.get_data()`` is run.


Common Keywords
```````````````

These keywords are common to all query methods::

    return_query_payload - Return the POST data that will be submitted as a dictionary
    savename - [optional - see discussion below] File path to save the downloaded query to
    timeout - timeout in seconds


Asynchronous Queries
--------------------
Some services require asynchronous query submission & download, e.g. Besancon,
the NRAO Archive, the Fermi archive, etc.  The data needs to be "staged" on the
remote server before it can be downloaded.  For these queries, the approach is

.. code-block:: python

    result = Service.query_region_async(coordinate)

    data = result.get_data()
    # this will periodically check whether the data is available at the specified URL

Additionally, any service can be queried asynchronously - ``get_images_async``
will return readable objects that can be downloaded at a later time.

Outline of an Example Module
----------------------------
Directory Structure::

    module/
    module/__init__.py
    module/core.py
    module/tests/test_module.py

``__init__.py`` contains:

.. code-block:: python

    from astropy import config as _config

    class Conf(_config.ConfigNamespace):
        """
        Configuration parameters for `astroquery.template_module`.
        """
        server = _config.ConfigItem(
            ['http://dummy_server_mirror_1',
             'http://dummy_server_mirror_2',
             'http://dummy_server_mirror_n'],
            'Name of the template_module server to use.'
            )
        timeout = _config.ConfigItem(
            30,
            'Time limit for connecting to template_module server.'
            )

    from .core import QueryClass

    __all__ = ['QueryClass']


``core.py`` contains:

.. code-block:: python

    from ..utils.class_or_instance import class_or_instance
    from ..utils import commons, async_to_sync

    __all__ = ['QueryClass']  # specifies what to import

    @async_to_sync
    class QueryClass(astroquery.BaseQuery):

        server = SERVER()

        def __init__(self, *args):
            """ set some parameters """
            # do login here
            pass

        @class_or_instance
        def query_region_async(self, *args, get_query_payload=False):

            request_payload = self._args_to_payload(*args)

            response = commons.send_request(self.server, request_payload, TIMEOUT)

            # primarily for debug purposes, but also useful if you want to send
            # someone a URL linking directly to the data
            if get_query_payload:
                return request_payload

            return response

        @class_or_instance
        def get_images_async(self, *args):
            image_urls = self.get_image_list(*args)
            return [get_readable_fileobj(U) for U in image_urls]
            # get_readable_fileobj returns need a "get_data()" method?

        @class_or_instance
        def get_image_list(self, *args):

            request_payload = self.args_to_payload(*args)

            result = requests.post(url, data=request_payload)

            return self.extract_image_urls(result)

        def _parse_result(self, result):
            # do something, probably with regexp's
            return astropy.table.Table(tabular_data)

        def _args_to_payload(self, *args):
            # convert arguments to a valid requests payload

            return dict




Parallel Queries
----------------
For multiple parallel queries logged in to the same object, you could do:

.. code-block:: python

    from astroquery import module

    QC = QueryClass(login_information)

    results = parallel_map(QC.query_object,['m31','m51','m17'],radius=['1"','1"','1"'])

    results = [QC.query_object_async(obj, radius=r)
        for obj,r in zip(['m31','m51','m17'],['1"','1"','1"'])]

.. TODO::

    Include a ``parallel_map`` function in ``astroquery.utils``


Exceptions
----------

* What errors should be thrown if queries fail?
  Failed queries should raise a custom Exception that will include the full
  html (or xml) of the failure, but where possible should parse the web page's
  error message into something useful.

* How should timeouts be handled?
  Timeouts should raise a ``TimeoutError``.


Examples
--------

Standard usage should be along these lines:

.. code-block:: python

    from astroquery.simbad import Simbad

    result = Simbad.query_object("M 31")
    # returns astropy.Table object

    from astroquery.irsa import Irsa

    images = Irsa.get_images("M 31","5 arcmin")
    # searches for images in a 5-arcminute circle around M 31
    # returns list of HDU objects

    images = Irsa.get_images("M 31")
    # searches for images overlapping with the SIMBAD position of M 31, if supported by the service?
    # returns list of HDU objects

    from astroquery.ukidss import Ukidss

    Ukidss.login(username, password)

    result = Ukidss.query_region("5.0 0.0 gal", catalog='GPS')
    # FAILS: no radius specified!
    result = Ukidss.query_region("5.0 0.0 gal", catalog='GPS', radius=1)
    # FAILS: no assumed units!
    result = Ukidss.query_region("5.0 0.0 gal", catalog='GPS', radius='1 arcmin')
    # SUCCEEDS!  returns an astropy.Table

    from astropy.coordinates import SkyCoord
    import astropy.units as u
    result = Ukidss.query_region(
        SkyCoord(5,0,unit=('deg','deg'), frame='galactic'),
        catalog='GPS', region='circle', radius=5*u.arcmin)
    # returns an astropy.Table

    from astroquery.nist import Nist

    hydrogen = Nist.query(4000*u.AA, 7000*u.AA, linename='H I', energy_level_unit='eV')
    # returns an astropy.Table


For tools in which multiple catalogs can be queried, e.g. as in the UKIDSS
examples, they must be specified.  There should also be a ``list_catalogs``
function that returns a ``list`` of catalog name strings:

.. code-block:: python

    print(Ukidss.list_catalogs())

Unparseable Data
~~~~~~~~~~~~~~~~

If data cannot be parsed into its expected form (`~astropy.table.Table`, `astropy.io.fits.PrimaryHDU`),
the raw unparsed data will be returned and a ``Warning`` issued.
