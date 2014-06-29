.. doctest-skip-all

**********************************
Fermi Queries (`astroquery.fermi`)
**********************************

Getting started
===============

The following example illustrates a Fermi LAT query,
centered on M 31 for the energy range 1 to 100 GeV for the first day in 2013.

.. code-block:: python

    >>> from astroquery import fermi
    >>> result = fermi.FermiLAT.query_object('M31', energyrange_MeV='1000, 100000',
    ...                                      obsdates='2013-01-01 00:00:00, 2013-01-02 00:00:00')
    >>> print result
    ['http://fermi.gsfc.nasa.gov/FTP/fermi/data/lat/queries/L1309041729388EB8D2B447_SC00.fits',
     'http://fermi.gsfc.nasa.gov/FTP/fermi/data/lat/queries/L1309041729388EB8D2B447_PH00.fits']
    >>> from astropy.io import fits
    >>> sc = fits.open('http://fermi.gsfc.nasa.gov/FTP/fermi/data/lat/queries/L1309041729388EB8D2B447_SC00.fits')
    

Reference/API
=============

.. automodapi:: astroquery.fermi
    :no-inheritance-diagram:
