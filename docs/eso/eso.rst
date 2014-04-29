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
- listing available surveys (phase 3)
- searching all instrument specific raw data: http://archive.eso.org/cms/eso-data/instrument-specific-query-forms.html
- searching data products (phase 3): http://archive.eso.org/wdb/wdb/adp/phase3_main/form
- downloading data by dataset identifiers: http://archive.eso.org/cms/eso-data/eso-data-direct-retrieval.html


Requirements
------------

The following packages are required for the use of this module:

* keyring
* lxml


Authentication with ESO User Portal
-----------------------------------

Whereas querying the ESO database is fully open, accessing actual datasets requires
authentication with the ESO User Portal (https://www.eso.org/sso/login).
This authentication is performed directly with the provided :meth:`~astroquery.query.QueryWithLogin.login` command,
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

Note: these instrument query forms can be opened in your web browser directly using the ``show_form`` option of
the :meth:`~astroquery.eso.EsoClass.query_instrument` method. For now, this should help with the identification of the acceptable keywords.

In the following, datasets near Sgr A* are searched for in the amber archive, after limiting the number of
returned rows to 10.

.. code-block:: python

    >>> eso.ROW_LIMIT = 10
    >>> table = eso.query_instrument('amber', target="Sgr A*")
    >>> table.pprint(max_width=300)
     Object      Target Ra Dec           Target l b          ProgId                DP.ID               OB.ID   DPR.CATG    DPR.TYPE      DPR.TECH    ISS.CONF.STATION1 ISS.CONF.STATION2 ISS.CONF.STATION3 INS.GRAT1.WLEN  DIMM S-avg
    ------- ----------------------- -------------------- ------------- ----------------------------- --------- -------- ------------- -------------- ----------------- ----------------- ----------------- -------------- -----------
    GC_IRS7 17:45:40.09 -29:00:22.1 359.945774 -0.045458 076.B-0863(A) AMBER.2006-03-14T07:40:03.741 200156177  SCIENCE FRNSRC,BASE12 INTERFEROMETRY                U1                U3                U4           -1.0 0.64 [0.01]
    GC_IRS7 17:45:40.09 -29:00:22.1 359.945774 -0.045458 076.B-0863(A) AMBER.2006-03-14T07:40:19.830 200156177  SCIENCE FRNSRC,BASE12 INTERFEROMETRY                U1                U3                U4           -1.0 0.64 [0.01]
    GC_IRS7 17:45:40.09 -29:00:22.1 359.945774 -0.045458 076.B-0863(A) AMBER.2006-03-14T07:40:35.374 200156177  SCIENCE FRNSRC,BASE12 INTERFEROMETRY                U1                U3                U4           -1.0 0.64 [0.01]
    GC_IRS7 17:45:40.09 -29:00:22.1 359.945774 -0.045458 076.B-0863(A) AMBER.2006-03-14T07:40:50.932 200156177  SCIENCE FRNSRC,BASE12 INTERFEROMETRY                U1                U3                U4           -1.0 0.68 [0.01]
    GC_IRS7 17:45:40.09 -29:00:22.1 359.945774 -0.045458 076.B-0863(A) AMBER.2006-03-14T07:41:07.444 200156177  SCIENCE FRNSRC,BASE12 INTERFEROMETRY                U1                U3                U4           -1.0 0.68 [0.01]
    GC_IRS7 17:45:40.09 -29:00:22.1 359.945774 -0.045458 076.B-0863(A) AMBER.2006-03-14T07:41:24.179 200156177  SCIENCE FRNSRC,BASE12 INTERFEROMETRY                U1                U3                U4           -1.0 0.68 [0.01]
    GC_IRS7 17:45:40.09 -29:00:22.1 359.945774 -0.045458 076.B-0863(A) AMBER.2006-03-14T07:41:39.523 200156177  SCIENCE FRNSRC,BASE12 INTERFEROMETRY                U1                U3                U4           -1.0 0.68 [0.01]
    GC_IRS7 17:45:40.09 -29:00:22.1 359.945774 -0.045458 076.B-0863(A) AMBER.2006-03-14T07:41:55.312 200156177  SCIENCE FRNSRC,BASE12 INTERFEROMETRY                U1                U3                U4           -1.0 0.69 [0.01]
    GC_IRS7 17:45:40.09 -29:00:22.1 359.945774 -0.045458 076.B-0863(A) AMBER.2006-03-14T07:42:12.060 200156177  SCIENCE FRNSRC,BASE12 INTERFEROMETRY                U1                U3                U4           -1.0 0.69 [0.01]
    GC_IRS7 17:45:40.09 -29:00:22.1 359.945774 -0.045458 076.B-0863(A) AMBER.2006-03-14T07:42:29.119 200156177  SCIENCE FRNSRC,BASE12 INTERFEROMETRY                U1                U3                U4           -1.0 0.69 [0.01]

In the next step, the first dataset is selected, using its data product ID, and retrieved from the ESO archive.

.. code-block:: python

    >>> data_product_id = table[0]['DP.ID']
    >>> data_files = eso.data_retrieval([data_product_id])
    Downloading AMBER.2006-03-14T07:40:03.741.fits.Z...
    Done!

    >>> print(data_files)
    ['AMBER.2006-03-14T07:40:03.741.fits.Z']

The returned file names correspond to datasets downloaded locally. They are ready to be used.


Obtaining extended information on data products
-----------------------------------------------

Only a small subset of the keywords presents in the data products can be obtained
with :meth:`~astroquery.eso.EsoClass.query_instrument`.
There is however a way to get the full primary header of the FITS data products,
using :meth:`~astroquery.eso.EsoClass.get_headers`.
This method is detailed in the example below, continuing with the previously obtained table.

.. code-block:: python

    >>> table_headers = eso.get_headers(table['DP.ID'])
    >>> table_headers.pprint()
                 ARCFILE               BITPIX ...    TELESCOP      UTC
    ---------------------------------- ------ ... ------------- ---------
    AMBER.2006-03-14T07:40:03.741.fits     16 ... ESO-VLTI-U134   27600.0
    AMBER.2006-03-14T07:40:19.830.fits     16 ... ESO-VLTI-U134   27616.0
    AMBER.2006-03-14T07:40:35.374.fits     16 ... ESO-VLTI-U134   27632.0
    AMBER.2006-03-14T07:40:50.932.fits     16 ... ESO-VLTI-U134 27646.667
    AMBER.2006-03-14T07:41:07.444.fits     16 ... ESO-VLTI-U134   27664.0
    AMBER.2006-03-14T07:41:24.179.fits     16 ... ESO-VLTI-U134 27680.667
    AMBER.2006-03-14T07:41:39.523.fits     16 ... ESO-VLTI-U134   27696.0
    AMBER.2006-03-14T07:41:55.312.fits     16 ... ESO-VLTI-U134   27712.0
    AMBER.2006-03-14T07:42:12.060.fits     16 ... ESO-VLTI-U134   27728.0
    AMBER.2006-03-14T07:42:29.119.fits     16 ... ESO-VLTI-U134   27746.0
    >>> len(table_headers.columns)
    570

As shown above, for each data product ID (``DP.ID``), the full header (570 columns in our case) of the archive
FITS file is collected. In the above table ``table_headers``, there are as many rows as in the column ``table['DP.ID']``.

Reference/API
=============

.. automodapi:: astroquery.eso
    :no-inheritance-diagram:
