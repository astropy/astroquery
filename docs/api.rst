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
