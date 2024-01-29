**********************************
Fermi Queries (`astroquery.fermi`)
**********************************

Getting started
===============

The following example illustrates a Fermi LAT query,
centered on M 31 for the energy range 1 to 100 GeV for the first day in 2013.

.. doctest-remote-data::

    >>> from astroquery.fermi import FermiLAT
    >>> result = FermiLAT.query_object('M31', energyrange_MeV='1000, 100000',
    ...                                      obsdates='2013-01-01 00:00:00, 2013-01-02 00:00:00')
    >>> print(result)  # doctest: +IGNORE_OUTPUT
    ['https://fermi.gsfc.nasa.gov/FTP/fermi/data/lat/queries/L210111120827756AAA3A88_PH00.fits',
    'https://fermi.gsfc.nasa.gov/FTP/fermi/data/lat/queries/L210111120827756AAA3A88_SC00.fits']


Troubleshooting
===============

If you are repeatedly getting failed queries, or bad/out-of-date results, try clearing your cache:

.. code-block:: python

    >>> from astroquery.fermi import FermiLAT
    >>> FermiLAT.clear_cache()

If this function is unavailable, upgrade your version of astroquery. 
The ``clear_cache`` function was introduced in version 0.4.7.dev8479.


Reference/API
=============

.. automodapi:: astroquery.fermi
    :no-inheritance-diagram:
