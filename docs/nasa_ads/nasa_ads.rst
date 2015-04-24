.. doctest-skip-all

.. _astroquery.nasa_ads:

****************************************
NASA ADS Queries (`astroquery.nasa_ads`)
****************************************

Getting Started
===============

This module provides an interface to the online `SAO/NASA Astrophysics Data System`_.
At the moment only the "simple search", i.e. omni-box search is available, and only 
a subset of the results are accessible.

Examples
========

Search works by specific identifier
-----------------------------------
.. code-block:: python

    from astroquery import nasa_ads as na
    # the "^" makes ADS to return only papers where Persson 
    # is first author
    results = na.ADS.query_simple('^Persson Origin of water\
	 around deeply embedded low-mass protostars') results[0].title 
    
    # to sort after publication date
    results.sort(['pubdate']) 
    
    #  get the title of the last hit
    title = results[-1]['title'][0] 
    
    # printout the authors of the last hit
    print results[-1]['authors']


Get links 
---------
Not yet implemented.

Download publisher/ArXiv PDF
----------------------------
Not yet implemented.

Get Bibtex
----------
Not yet implemented.






Reference/API
=============

#.. automodapi:: astroquery.nasa_ads:no-inheritance-diagram:

.. _nasa_ads: http://adsabs.harvard.edu/
.. _SAO/NASA Astrophysics Data System: http://adsabs.harvard.edu/



