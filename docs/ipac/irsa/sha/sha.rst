:orphan:

.. _astroquery.ipac.irsa.sha:


*****************************************************
Spitzer Heritage Archive (`astroquery.ipac.irsa.sha`)
*****************************************************

Querying catalogs
=================

There are four types of supported queries for the Spitzer Heritage Archive
(SHA) module, searching by: position, NAIFID, PID, and ReqKey. Examples for
each are shown below.

Using the standard imports:

.. code-block:: python

    >>> from astroquery.ipac.irsa import sha
    >>> from astropy import coordinates as coord
    >>> from astropy import units as u

Query with an astropy coordinate instance (preferred):

.. doctest-remote-data::

    >>> pos_t1 = sha.query(coord=coord.SkyCoord(ra=163.6136, dec=-11.784,
    ... unit=(u.degree, u.degree)), size=0.5)

Query with the alternate ``ra`` and ``dec`` parameters:

.. doctest-remote-data::

    >>> pos_t2 = sha.query(ra=163.6136, dec=-11.784, size=0.5)

Query by NAIFID:

.. doctest-remote-data::

    >>> nid_t = sha.query(naifid=2003226)

Query by PID:

.. doctest-remote-data::

    >>> pid_t = sha.query(pid=30080)

Query by ReqKey:

.. doctest-remote-data::

    >>> # by ReqKey
    >>> rqk_t = sha.query(reqkey=21641216)


Additional Documentation
========================

For column descriptions, metadata, and other information visit the SHA query
API_ help page.

Saving files to disk
====================

Using the access URLs found in the SHA queries, the functions `astroquery.ipac.irsa.sha.save_file`
writes the file to disk. To save a file:

.. doctest-remote-data::

    >>> pid_t = sha.query(pid=30080)
    >>> url = pid_t['accessUrl'][0].strip()
    >>> sha.save_file(url)

or alternatively with a name and path specified:

.. doctest-skip::

   >>> sha.save_file(url, out_dir='proj_files/', out_name='sha_file1')

The extension will automatically be added depending on the filetype.


Reading files into python
=========================

Given an access URL, `astroquery.ipac.irsa.sha.get_file` returns an appropriate astropy object,
either a `~astropy.table.Table` instance for tabular data, or
`~astropy.io.fits.PrimaryHDU` instance for FITS files.

.. doctest-remote-data::

    >>> pid_t = sha.query(pid=30080)
    >>> url = pid_t['accessUrl'][0].strip()
    >>> img = sha.get_file(url)

Reference/API
=============

.. automodapi:: astroquery.ipac.irsa.sha
    :no-inheritance-diagram:

.. _API: http://sha.ipac.caltech.edu/applications/Spitzer/SHA/help/doc/api.html

.. testcleanup::

    >>> from astroquery.utils import cleanup_saved_downloads
    >>> cleanup_saved_downloads(['sha_tmp'])
