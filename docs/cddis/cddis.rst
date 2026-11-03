NASA CDDIS GNSS Archive (`astroquery.cddis`)
============================================

The `Crustal Dynamics Data Information System (CDDIS)
<https://www.earthdata.nasa.gov/centers/cddis-daac>`_ archives GNSS observation
data and derived products. Astroquery's ``cddis`` module provides directory
browsing and file downloads from the CDDIS GNSS archive. It does not interpret
RINEX observations or calculate telescope pointing coordinates.

==============
Authentication
==============

CDDIS access requires an `Earthdata Login
<https://urs.earthdata.nasa.gov/>`_ account and authorization for CDDIS.
Follow the `CDDIS archive access instructions
<https://www.earthdata.nasa.gov/centers/cddis-daac/archive-access>`_ to
authorize the CDDIS application. Put your Earthdata Login credentials in the
``.netrc`` file in your home directory (``~/.netrc``), not in the Astroquery
repository or current working directory:

.. code-block:: text

    machine urs.earthdata.nasa.gov
        login YOUR_EARTHDATA_USERNAME
        password YOUR_EARTHDATA_PASSWORD

Restrict access to the credentials file (on macOS or Linux, run
``chmod 600 ~/.netrc``). Astroquery uses Requests, which reads Earthdata Login
credentials from this file during the authentication redirect. After creating
or correcting the file, retry the query; failed login responses are discarded
instead of being retained in Astroquery's response cache.

=====================
Browsing the archive
=====================

Archive paths are relative to the GNSS archive root. For example, a daily
observation directory can be listed as follows:

.. doctest-remote-data::

    >>> from astroquery.cddis import CDDIS
    >>> files = CDDIS.query_files('data/daily/2025/001/25d')
    >>> files['name', 'path', 'is_directory']

The CDDIS directory layout contains multiple GNSS product types. Consult the
`CDDIS GNSS data documentation
<https://www.earthdata.nasa.gov/data/space-geodesy-techniques/gnss>`_ to select
the product and directory appropriate for your use.

====================
Downloading a file
====================

Pass a listed archive path to ``download_file`` to save that product locally:

.. doctest-remote-data::

    >>> from astroquery.cddis import CDDIS
    >>> files = CDDIS.query_files('data/daily/2025/001/25d')
    >>> file_paths = files[~files['is_directory']]['path']
    >>> if len(file_paths) == 0:
    ...     raise RuntimeError(
    ...         'No files in this directory; choose a populated archive date.')
    >>> path = CDDIS.download_file(file_paths[0])

The method returns the local path. Files are saved to Astroquery's CDDIS cache
directory by default; pass ``savedir`` to select another directory.

For telescope tracking, Astroquery's
`JPL Horizons interface <../jplhorizons/jplhorizons.rst>`_ is more suitable:
it returns observer-dependent satellite ephemerides, whereas CDDIS primarily
provides geodetic observations and orbit products.
