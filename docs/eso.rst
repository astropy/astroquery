.. doctest-skip-all

.. _astroquery.eso:

******************************
ESO Queries (`astroquery.eso`)
******************************

Getting started
===============

This is a python interface for querying the ESO archive web service.
For now, it supports the following:

- listing available instruments
- searching all instrument specific raw data: http://archive.eso.org/cms/eso-data/instrument-specific-query-forms.html
- downloading data by dataset identifiers: http://archive.eso.org/cms/eso-data/eso-data-direct-retrieval.html


Authentication with ESO User Portal
-----------------------------------

Whereas querying the ESO database is fully open, accessing actual datasets requires
authentication with the ESO User Portal (https://www.eso.org/sso/login).
This authentication is performed directly with the provided `login()` command,
as illustrated in the example below. This method uses your keyring to securely
store the password in your operating system. As such you should have to enter your
correct password only once, and later be able to use this package for automated
interaction with the ESO archive.

.. code-block:: python

    >>> from astroquery.eso import Eso
    >>> eso = Eso()
    >>> eso.login("TEST")
    TEST, enter your ESO password:
    
    Authenticating TEST on www.eso.org...
    Authentication failed!
    >>> eso.login("ICONDOR")
    ICONDOR, enter your ESO password:
    
    Authenticating ICONDOR on www.eso.org...
    Authentication successful!
    >>> eso.login("ICONDOR")
    Authenticating ICONDOR on www.eso.org...
    Authentication successful!


Query and direct retrieval of instrument specific raw data
----------------------------------------------------------

The direct retrieval of datasets is better explained with a running example, continuing from the
authentication example above. The first thing to do is to identify the instrument to query.

.. code-block:: python

    >>> eso.list_instruments()
    ['fors1', 'fors2', 'vimos', 'omegacam', 'hawki', 'isaac', 'naco', 'visir', 'vircam',
    'apex', 'uves', 'giraffe', 'xshooter', 'crires', 'kmos', 'sinfoni', 'amber', 'midi']
    >>> instrument = 'amber'

Then, the list of available datasets can be queried for this instrument, using additional constraints.
These constraints are based on the instrument specific options that can be found is the instrument query forms.

Note: these instrument query forms can be opened in your web browser directly using the `show_form` option of
the `instrument_query()` method. For now, this should help with the identification of the acceptable keywords.

In the following, datasets near Sgr A* are searched for in the amber archive, and the first 10 returned datasets
are printed.

.. code-block:: python

    >>> table = eso.query_instrument('amber', target="Sgr A*")
    >>> table[:10].pprint()

In the next step, the first dataset is selected, using its data product ID, and retrieved from the ESO archive.

.. code-block:: python

    >>> data_product_id = table[0]['data_products.dp_id']
    >>> data_files = eso.data_retrieval([data_product_id])
    Downloading AMBER.2006-03-14T07:40:03.741.fits.Z...
    Done!
    
    >>> print(data_files)
    ['AMBER.2006-03-14T07:40:03.741.fits.Z']

