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

Outline of an Example Module
-----------------------------
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

    class QueryClass(astroquery.Query):

        url = 'http://static_url'

        def __init__(self, *args):
            """ set some parameters """
            # do login here
            self.request_data = {}
            pass

        def __call__(self, **kwargs):
            return self.execute(**kwargs)

        def execute(self, timeout=1):

            self.result = requests.post(url, data=self.request_data)

            return self.parse_result(self.result)


        def parse_result(self, result):
            # do something, probably with regexp's
            pass

For multiple parallel queries logged in to the same object, you could do:

.. code-block:: python

    from astroquery import module

    module_query = QueryClass(login_information)

    results = parallel_map(module_query,['m31','m51','m17'])


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
  Catalog queries should return `astropy.Table` instances


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
  
