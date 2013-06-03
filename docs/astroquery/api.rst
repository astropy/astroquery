Astroquery API Specification
============================

Standard usage should be along these lines:

.. code-block:: python

    from astroquery import simbad

    result = simbad.query("M 31")

    from astroquery import irsa

    images = irsa.box_image_query("M 31","5 arcmin")

    from astroquery import ukidss

    ukidss.login(username, password)

    result = ukidss.query("5.0 0.0 gal", catalog='GPS')


In order for this all to work, we will need to utilize some coordinate parsing,
which has only just been decided on (April 13, 2013).

For tools in which multiple catalogs can be queried, e.g. as in the last UKIDSS
example, they must be specified.  There should also be a `list_catalogs`
function that returns a `list` of catalog name strings:

.. code-block:: python

    print ukidss.list_catalogs()

Two Levels of API
-----------------
There will be two different levels of API, exposed to the user via different imports.

User Friendly / Common API
~~~~~~~~~~~~~~~~~~~~~~~~~~
The "user-friendly" API will be as uniform as possible across all query tools.
Each service will have `query_object` and `query_region` functions if they are
interfaces to astronomical catalogs.  For non-object-catalog services (e.g.
NIST, LAMDA, Splatalogue), there will just be a `query` function.

"Query" methods will return `astropy.table.Table` objects.  

.. note:: 

    Point for discussion: should we allow query methods to return anything
    else, or should other return types be restricted to the tool-specific API
    methods (below)?

To support image servers, there will also be a `get_images` that will return a
list of `astropy.io.fits.HDUList` objects.

.. note::

    Alternative: 

     * `get_images` will return a list of `astropy.nddata` objects
        with correct associated metadata.
     * `get_spectra` will do the same for spectra services
     * `get_data` will be a more generic tool to grab any data type,
       and will return it in the raw format returned by the website
       (this approach allows for unparseable data to be acquired)
       
Examples:

.. code-block:: python

    from astroquery import simbad,NIST,irsa

    M31 = simbad.query_object('M 31')
    OrionObjects = simbad.query_region('M 42', radius='1 degree', region='circle')

    hydrogen = NIST.query(linename='H I', minwav=4000, maxwav=7000,
                wavelength_unit='A', energy_level_unit='eV')

    irsa.get_images(object='M 42', survey='2MASS', bands='all')

As shown in this example, objects can be queried by name.  Queries by coordinate will also
be allowed with the normal coordinates interface:

.. code-block:: python

    irsa.get_images(coordinates.FK5(083.8221,-05.3911,units='deg,deg'))

There are two driving motivations behind this overall approach, which should
serve as guidelines for when the above rules can be broken:

 1. Simplicity for the end-user - astroquery tools should all look as much the
    same as possible
 2. Support for a large variety of different web tools (both astronomical
    catalogs corresponding to sky positions and other catalogs that do not)

These high-level functions are wrappers; they may instantiate classes but will
not return them by default.  For both debugging and reproducibility purposes,
however, these functions should have a `return_query_payload` and
`return_class` method that would return the HTML POST data as a dict and the
created class, respectively.  

Deeper / Tool-Specific API
~~~~~~~~~~~~~~~~~~~~~~~~~~
For many tools, there are special features implemented in the web API that
should be available to the user, but should not be the default interface.

There are different reasons one would want to use the API directly:

 1. The data type returned by the query is non-standard (e.g., a URL)
 2. The returned web page from a query contains important information
    that cannot/should not be parsed by astroquery (e.g., an NRAO query for
    ALMA data that requires security for the next stage of downloads?)
 3. Debugging when trying to implement the user-friendly interface...

.. code-block:: python

    from astroquery import simbad

    # simply get the web page returned from this query, i.e. it would be 
    # what is returned from the requests.post command
    web_result = simbad.api.reference_query('2012ASPC..461..407M')


General rules for API queries:

 1. The naming scheme should reflect the parent website
 2. The raw return and the parser should be in different functions (i.e., if
    query sends you to a web page that contains a table, there should be a
    separate function to parse the table)
 3. All options available on the website should be made available to the user
 4. An effort should be made to catch invalid queries prior to submission to
    the website (invalid input types for fields, invalid combinations of
    fields).  


Outline of an Example Module
----------------------------
Directory Structure::

    module/
    module/__init__.py
    module/core.py
    module/tests/test_module.py


`core.py` would contain:


.. code-block:: python

    def query(*args):
        """ Wrapper for simple queries """
        QueryTool = QueryClass(*args)
        return QueryTool.execute()

    def query(*args):
        """ Wrapper for simple queries (using static_or_instance approach)"""
        return QueryClass.execute(*args)

    class QueryClass(astroquery.Query):

        url = 'http://static_url'

        def __init__(self, *args):
            """ set some parameters """
            # do login here
            # set up the query here as well (e.g., coordinates, object name)
            self.request_data = {}
            pass

        def __call__(self, **kwargs):
            return self.execute(**kwargs)

        @static_or_instance
        def execute(self, timeout=1, *args):

            # Parse arguments here if being run as classmethod

            self.result = requests.post(url, data=self.request_data)

            return self.parse_result(self.result)


        def parse_result(self, result):
            # do something, probably with regexp's
            return astropy.table.Table(tabular_data)




For multiple parallel queries logged in to the same object, you could do:

.. code-block:: python

    from astroquery import module

    module_query = QueryClass(login_information)

    results = parallel_map(module_query,['m31','m51','m17'])

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

Details & Questions
-------------------

* What type of objects are returned by these functions?

  * Catalog queries should return `astropy.Table` instances
  * All returned objects should have a `.save` or `.write` attribute (this needs discussion)
  * Returned objects must be indexable like dictionaries (?)
  * image_query functions should return astropy.io.fits.HDUList objects (?) or astropy.ndarray objects (?)


* What errors should be thrown if queries fail?
  Failed queries should raise a custom Exception that will include the full
  html (or xml) of the failure, but where possible should parse the web page's
  error message into something useful.

* How should timeouts be handled?
  Timeouts should raise a `TimeoutError`.  
  
  Note that for some query tools, e.g.
  the besancon model, and perhaps in the future for archive queries via MAST, 
  NRAO, etc., the user must wait for a notification from the archive that the
  tapes have been read.  For these sorts of queries, it may be possible to
  do a check for completion every 5-30 minutes rather than requiring user input.
  
* Some services return similar / identical data (see issue #82), and care
  should be taken that these return the same objects if the data are identical


ALTERNATIVE API SUGGESTIONS
===========================

Pseudocode example based on @astrofrog's suggestion:

.. code-block:: python


    class static_or_instance(object):
        def __init__(self, func):
            self.func = func

        def __get__(self, instance, owner):
            return functools.partial(self.func, instance)


    class QueryClass(astroquery.Query):

        url = 'http://static_url'

        def __init__(self, *args):
            """ set some parameters """
            # do login here
            # DO NOT set up the query here 
            self.request_data = {}
            pass

        def __call__(self, **kwargs):
            return self.execute(**kwargs)

        @static_or_instance
        def query(self, timeout=1, *args):

            # THIS method defines the query
            self.request_data = parse_args_to_request_data(*args)

            self.result = requests.post(url, data=self.request_data)

            return self.parse_result(self.result)


        def parse_result(self, result):
            # do something, probably with regexp's
            return astropy.table.Table(tabular_data)

This suggestion allows the user to perform queries in two ways:

.. code-block:: python

    from astroquery import QueryClass
    QueryClass.query()

for simple queries, or

.. code-block:: python

    from astroquery import QueryClass
    q = QueryClass()
    q.query(...)

