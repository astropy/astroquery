.. doctest-skip-all

.. _astroquery.nasa_ads:

****************************************
NASA ADS Queries (`astroquery.nasa_ads`)
****************************************

Getting Started
===============

This module provides an interface to the online `SAO/NASA Astrophysics Data System`_.
Only the one-box modern search form is accessible.

Note that you need to acquire and provide an API access token. Create and/or sign into
your account in the new ADS, then create and copy your API token from your `account settings.`_.
Provide your token in the module configuration (example shown below), in the ADS_DEV_KEY
environment variable, or store it in a text file at ~/.ads/dev_key

Examples
========

Search works by specific identifier
-----------------------------------
.. code-block:: python

    from astroquery import nasa_ads as na

    # if you don't store your token as an environment variable
    # or in a file, give it here
    na.ADS.TOKEN = 'your-token-goes-here'

    # by default, the top 10 records are returned, sorted in
    # reverse chronological order. This can be changed

    # change the number of rows returned
    na.ADS.NROWS = 20
    # change the sort order
    na.ADS.SORT = 'bibcode desc'
    # change the fields that are returned (enter as strings in a list)
    na.ADS.ADS_FIELDS = ['author','title','abstract','pubdate']

    # the "^" makes ADS to return only papers where Persson
    # is first author
    results = na.ADS.query_simple('^Persson Origin of water\
	 around deeply embedded low-mass protostars') results[0].title

    # to sort after publication date
    results.sort(['pubdate'])

    #  get the title of the last hit
    title = results[-1]['title'][0]

    # printout the authors of the last hit
    print(results[-1]['author'])


Reference/API
=============

.. automodapi:: astroquery.nasa_ads
    :no-inheritance-diagram:

.. _nasa_ads: http://adsabs.harvard.edu/
.. _SAO/NASA Astrophysics Data System: https://ui.adsabs.harvard.edu/
.. _account settings.: https://ui.adsabs.harvard.edu/#user/settings/token



