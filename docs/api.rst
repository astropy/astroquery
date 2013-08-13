Astroquery API Specification
============================


Service Class
-------------
The query tools will be implemented as class methods, so that the standard approach
for a given web service (e.g., IRSA, UKIDSS, SIMBAD) will be

.. code-block:: python

    from astroquery import Service

    result = Service.query_object('M 31')

for services that do not require login, and  

.. code-block:: python

    from astroquery import Service

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
ADS queries that may return a `bibtex` text block).

query_object
````````````
Will use `astropy.coordinates.name_resolve` to convert the object name to coordinates,
but otherwise is the same as `query_region`.


query_region
````````````
Query a region around a coordinate.

One of these keywords *must* be specified (no default is assumed)::

    radius - an astropy Quantity object, or a string that can be parsed into one.  e.g., '1 degree' or 1*u.degree.
        If radius is specified, the shape is assumed to be a circle
    width - a Quantity.  Specifies the edge length of a square box
    height - a Quantity.  Specifies the height of a rectangular box.  Must be passed with width.

Returns an `astropy.Table`

get_images
``````````
Perform a coordinate-based query to acquire images.

Returns a list of `astropy.io.fits.HDUList`s.  

Shape keywords are optional - some query services allow searches for images
that overlap with a specified coordinate.

(query)_async
`````````````
Includes `get_images_async`, `query_region_async`, `query_object_async`

Same as the above query tools, but returns a list of readable file objects instead of a parsed
object so that the data is not downloaded until `result.get_data()` is run.


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

Additionally, any service can be queried asynchronously - `get_images_async`
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

    from astropy.config import ConfigurationItem

    SERVER = ConfigurationItem('Service_server', ['url1','url2'])

    from .core import *


``core.py`` contains:

.. code-block:: python


    class QueryClass(astroquery.BaseQuery):

        server = SERVER()

        def __init__(self, *args):
            """ set some parameters """
            # do login here
            pass

        @static_or_instance
        def query_region(self, *args):
            result = self.query_region_async(*args)

            try:
                self.parse_result(result)
            except:
                return result

        @static_or_instance
        def query_region_async(self, *args):

            request_payload = self.args_to_payload(*args)

            result = requests.post(url, data=request_payload)

            return result

        @static_or_instance
        def get_images(self, *args):
            readable_objs = self.get_images_async(*args)
            return [fits.open(obj) for obj in readable_objs]

        @static_or_instance
        def get_images_async(self, *args):
            image_urls = self.get_image_list(*args)
            return [get_readable_fileobj(U) for U in image_urls]
            # get_readable_fileobj returns need a "get_data()" method?

        @static_or_instance
        def get_image_list(self, *args):

            request_payload = self.args_to_payload(*args)

            result = requests.post(url, data=request_payload)

            return self.extract_image_urls(result)

        def parse_result(self, result):
            # do something, probably with regexp's
            return astropy.table.Table(tabular_data)

        def args_to_payload(self, *args):
            # convert arguments to a valid requests payload

            return dict


Support Code for classmethod overloading
----------------------------------------

.. code-block:: python


    class static_or_instance(object):
        def __init__(self, func):
            self.func = func

        def __get__(self, instance, owner):
            return functools.partial(self.func, instance)


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
    
    Include a `parallel_map` function in `astroquery.utils`


Present Implementations (April 2013)
------------------------------------

There are a few current implementations that differ from the above proposal.
They will need to be refactored.  However, they provide useful comparison.

1. The UKIDSS model

.. code-block:: python

    from astroquery import ukidss

    q = ukidss.Query()
    q.login(...) # optional
    result = q.query_catalog(...)
    images = q.query_images_radec(...)
    images = q.query_images_gal(...)

i.e., you create a `Query` object and use its various methods.  

2. The `nedpy` model (individual functions for each query type)

.. code-block:: python

    from astroquery import ned

    result = ned.query_object_name('M 31')
    result = ned.query_object_coordinate(ra,dec)


Exceptions
----------

* What errors should be thrown if queries fail?
  Failed queries should raise a custom Exception that will include the full
  html (or xml) of the failure, but where possible should parse the web page's
  error message into something useful.

* How should timeouts be handled?
  Timeouts should raise a `TimeoutError`.  
  



Examples
--------
Standard usage should be along these lines:

.. code-block:: python

    from astroquery import simbad

    result = simbad.query_object("M 31")
    # returns astropy.Table object

    from astroquery import irsa

    images = irsa.get_images("M 31","5 arcmin")
    # searches for images in a 5-arcminute circle around M 31
    # returns list of HDU objects

    images = irsa.get_images("M 31")
    # searches for images overlapping with the SIMBAD position of M 31, if supported by the service?
    # returns list of HDU objects

    from astroquery import ukidss

    ukidss.login(username, password)

    result = ukidss.query_region("5.0 0.0 gal", catalog='GPS')
    # FAILS: no radius specified!
    result = ukidss.query_region("5.0 0.0 gal", catalog='GPS', radius=1)
    # FAILS: no assumed units!
    result = ukidss.query_region("5.0 0.0 gal", catalog='GPS', radius='1 arcmin')
    # SUCCEEDS!  returns an astropy.Table

    import astropy.coordinates as coords
    import astropy.units as u
    result = ukidss.query_region(coords.GalacticCoordinates(5,0,unit=('deg','deg')),
        catalog='GPS', region='circle', radius=5*u.arcmin)
    # returns an astropy.Table

    hydrogen = NIST.query(linename='H I', minwav=4000, maxwav=7000,
                wavelength_unit='A', energy_level_unit='eV')
    # returns an astropy.Table


For tools in which multiple catalogs can be queried, e.g. as in the UKIDSS
examples, they must be specified.  There should also be a `list_catalogs`
function that returns a `list` of catalog name strings:

.. code-block:: python

    print(ukidss.list_catalogs())


Remaining Questions
-------------------

Storing Data Locally
~~~~~~~~~~~~~~~~~~~~
(this was left as an open question on the June 7, 2013 telecon)

How will data be stored locally?  What is the interface to determine whether
and where it will be stored permanently?

Proposals
#########

result object
`````````````

.. code-block:: python

    class Result(object):
        def __init__(self, URL):
            self.URL = URL
            self.data = None

        def get_data(self, timeout=10):

            if self._data is None:
                success = False
                t0 = time.time()
                while not success:
                    try:
                        with astropy.utils.data.get_readable_fileobj(URL) as f:
                            self._data = f.read()
                    except URLError:
                        continue
                    except IOError:
                        raise IOError("Not a valid URL: "+str(self.URL))
                    if time.time() - t0 > timeout:
                        raise TimeoutError("Elapse time exceeded %i seconds" % timeout)
            return self._data

        def write(self, savepath, **kwargs):
            if self._data is None:
                self.get_data()
            self._data.write(savepath)

savepath keyword
````````````````

.. code-block:: python

    from astroquery import Service

    result = Service.query_object('M31', radius='1 degree', savepath='Service_M31_1degree.ipac')
    # expect to use astropy.Table.write to make an .ipac file

    result = Service.query_object('M31', radius='1 degree', savepath='Service_M31_1degree.xml')
    # expect to write the data exactly as downloaded
             

Unparseable Data
~~~~~~~~~~~~~~~~
(this was not discussed on the June 7, 2013 telecon)

A. If data cannot be parsed into its expected form (`astropy.Table`,
    `fits.HDU`), the raw unparsed data will be returned and a `Warning` issued.
B. If data cannot be parsed, an Exception will be raised that identifies where the
    raw/unparsed data is stored / cached on disk
       

