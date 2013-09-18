.. _astroquery.gama:

********************************
GAMA Queries (`astroquery.gama`)
********************************

Getting started
===============

This module can be used to query the GAMA (Galaxy And Mass Assembly) survey,
second data release (DR2). Currently queries must be formulated in SQL. If
successful, the results are returned as an `astropy.fits.HDUList`_.

**SQL Queries**

This sends an SQL query, passed as a string, to the GAMA server and returns
an `astropy.fits.HDUList`_. For example, to return basic information on the
first 100 spectroscopic objects in the database:

.. code-block:: python

    >>> from astroquery.gama import GAMA
    >>> result = GAMA.query_sql('SELECT * FROM SpecAll LIMIT 100')
    Downloading http://www.gama-survey.org/dr2/query/../tmp/GAMA_ZDJn2g.fits
    |===========================================|  37k/ 37k (100.00%)        00s
    >>> result.info()
    Filename: (No file associated with this HDUList)
    No.    Name         Type      Cards   Dimensions   Format
    0    PRIMARY     PrimaryHDU       5   ()           uint8   
    1                BinTableHDU     49   100R x 19C   [K, 4A, I, D, E, E, E, E, I, E, 53A, 74A, 78A, J, 23A, I, E, I, I]   
    >>> print result[1].data[:2]
    [ (131671727225700352, 'SDSS', 1, 132.16668000000001, -0.58222002, 3797.52, 9221.4697, 0.18984, 5, 0.99800003, '/GAMA/dr2/data/spectra/sdss/spSpec-51901-0467-001.fit', 'http://www.gama-survey.org/dr2/data/spectra/sdss/spSpec-51901-0467-001.fit', 'http://www.gama-survey.org/dr2/data/spectra/sdss/png/spSpec-51901-0467-001.png', 549638, 'GAMAJ084840.00-003456.0', 3, 0.1, 1, 1)
     (131671727229894656, 'SDSS', 1, 132.17204000000001, -0.20192, 3797.52, 9221.4697, 0.19219001, 5, 0.99900001, '/GAMA/dr2/data/spectra/sdss/spSpec-51901-0467-002.fit', 'http://www.gama-survey.org/dr2/data/spectra/sdss/spSpec-51901-0467-002.fit', 'http://www.gama-survey.org/dr2/data/spectra/sdss/png/spSpec-51901-0467-002.png', 536565, 'GAMAJ084841.29-001207.0', 3, 0.13, 1, 1)]

Reference/API
=============

.. automodapi:: astroquery.gama
    :no-inheritance-diagram
