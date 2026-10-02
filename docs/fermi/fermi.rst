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
    ...                                obsdates='2013-01-01 00:00:00, 2013-01-02 00:00:00')
    >>> print(result)  # doctest: +IGNORE_OUTPUT
    ['https://fermi.gsfc.nasa.gov/FTP/fermi/data/lat/queries/L210111120827756AAA3A88_PH00.fits',
    'https://fermi.gsfc.nasa.gov/FTP/fermi/data/lat/queries/L210111120827756AAA3A88_SC00.fits']

`~astroquery.fermi.FermiLATClass.query_object` blocks until the server has
finished staging the data; the maximum wait can be bounded with ``max_wait``
(in minutes).  If you already have the ``query_id`` of a previously submitted
query - for example one submitted through the `LAT Data Query web form
<https://fermi.gsfc.nasa.gov/cgi-bin/ssc/LAT/LATDataQuery.cgi>`_ - its status
and file URLs can be retrieved directly:

.. doctest-skip::

    >>> from astroquery.fermi import FermiLAT
    >>> FermiLAT.get_status('L210111120827756AAA3A88')['state']
    'Query completed'
    >>> FermiLAT.get_file_urls('L210111120827756AAA3A88')
    ['https://fermi.gsfc.nasa.gov/FTP/fermi/data/lat/queries/L210111120827756AAA3A88_PH00.fits',
    'https://fermi.gsfc.nasa.gov/FTP/fermi/data/lat/queries/L210111120827756AAA3A88_SC00.fits']

.. note::
   The module talks to the Fermi LAT Data Query REST API, which is replacing
   the ``LATDataQuery.cgi`` form endpoint that earlier versions of this
   module scraped.  The ``query_object_async`` method, which previously
   returned the URL of an HTML results page, is deprecated; use
   `~astroquery.fermi.FermiLATClass.query_object` instead.

A maximum zenith angle can be supplied with ``zenithangle`` (the server
default is 180 degrees), and coordinates may be given in ``J2000`` (default),
``B1950`` or ``Galactic`` frames via ``coordsystem``.

All-sky queries
===============

All-sky queries are handled specially by the server: the search radius must be
greater than 60 degrees (in practice, 180), the observation window must be no
longer than 24 hours, and the coordinates are ignored.

.. doctest-remote-data::

    >>> from astroquery.fermi import FermiLAT
    >>> result = FermiLAT.query_object('0.0,0.0', searchradius=180,
    ...                                energyrange_MeV='100, 300000',
    ...                                obsdates='2008-08-04 15:43:36, 2008-08-05 09:14:33')

Queries that exceed the 24-hour window are rejected by the server.

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
