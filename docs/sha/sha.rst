.. doctest-skip-all

.. _astroquery.sha:

*******************************************
Spitzer Heritage Archive (`astroquery.sha`)
*******************************************

Querying catalogs
=================

There are four types of supported queries for the Spitzer Heritage Archive
(SHA) module, searching by: position, NAIFID, PID, and ReqKey. Examples for
each are shown below.

Using the standard imports:

.. code-block:: python

    >>> from astroquery import sha
    >>> from astropy import coordinates as coord
    >>> from astropy import units as u

Query with an astropy coordinate instance (preferred):

.. code-block:: python

    >>> pos_t1 = sha.query(coord=coord.FK5(ra=163.6136, dec=-11.784,
    ... unit=(u.degree, u.degree)), size=0.5)

Query with the alternate ``ra`` and ``dec`` parameters:

.. code-block:: python

    >>> pos_t2 = sha.query(ra=163.6136, dec=-11.784, size=0.5)

Query by NAIFID:

.. code-block:: python

    >>> nid_t = sha.query(naifid=2003226)

Query by PID:

.. code-block:: python

    >>> pid_t = sha.query(pid=30080)

Query by ReqKey:

.. code-block:: python

    >>> # by ReqKey
    >>> rqk_t = sha.query(reqkey=21641216)

Additional Documentation
========================

For column descriptions, metadata, and other information visit the SHA query
API_ help page.

Saving files to disk
====================

Using the access URLs found in the SHA queries, the functions `astroquery.sha.save_file`
writes the file to disk. To save a file:

.. code-block:: python

    >>> pid_t = sha.query(pid=30080)
    >>> url = pid_t['accessUrl'][0].strip()
    >>> sha.save_file(url)

or alternatively with a name and path specified:

.. code-block:: python

   >>> sha.save_file(url, out_dir='proj_files/', out_name='sha_file1')

The extension will automatically be added depending on the filetype.

Reading files into python
=========================

Given an access URL, `astroquery.sha.get_file` returns an appropriate astropy object,
either a `~astropy.table.Table` instance for tabular data, or
`~astropy.io.fits.PrimaryHDU` instance for FITS files.

.. code-block:: python

    >>> pid_t = sha.query(pid=30080)
    >>> url = pid_t['accessUrl'][0].strip()
    >>> img = sha.get_file(url)

Reference/API
=============

.. automodapi:: astroquery.sha
    :no-inheritance-diagram:

.. _API: http://sha.ipac.caltech.edu/applications/Spitzer/SHA/help/doc/api.html
