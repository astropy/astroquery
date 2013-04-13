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

There are a few current implementations that differ from the above proposal.

1. The UKIDSS model

.. code-block:: python
    from astroquery import ukidss

    q = ukidss.Query()
    q.login(...) # optional
    result = q.query_catalog(...)
    images = q.query_images_radec(...)
    images = q.query_images_gal(...)

i.e., you create a `Query` object and use its various methods.  

2. The `nedpy` model

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
  
