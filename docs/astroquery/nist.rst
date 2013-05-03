.. _astroquery.nist:

********************************
NIST Queries (`astroquery.nist`)
********************************

Tool to query the NIST Atomic Lines database (http://physics.nist.gov/cgi-bin/ASD/lines1.pl).

Example
=======

.. code-block:: python

    >>> from astroquery import NISTAtomicLinesQuery
    >>> Q = NISTAtomicLinesQuery()
    >>> Q.query_line('H I',4000,7000,wavelength_unit='A',energy_level_unit='eV')

Reference/API
=============

.. automodapi:: astroquery.nist
    :no-inheritance-diagram:
