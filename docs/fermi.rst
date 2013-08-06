.. _astroquery.simbad:

**********************************
Fermi Queries (`astroquery.fermi`)
**********************************

Getting started
===============

The following example illustrates a Fermi LAT query,
centered on M 31 for the energy range 1 to 100 GeV for the first day in 2013.

.. code-block:: python

    >>> from astroquery import fermi
    >>> query = fermi.FermiLAT_Query()
    >>> URL = query('M31', energyrange_MeV='1000, 100000', obsdates='2013-01-01 00:00:00, 2013-01-02 00:00:00')
    >>> print URL
    'http://fermi.gsfc.nasa.gov/cgi-bin/ssc/LAT/QueryResults.cgi?id=L1304140823265C26556A17'

Reference/API
=============

.. automodapi:: astroquery.fermi
    :no-inheritance-diagram:
