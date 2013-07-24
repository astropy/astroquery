AstroQuery
==========

This is the documentation for the AstroQuery affiliated package of astropy.

Introduction
------------

AstroQuery is a set of tools for querying astronomical web forms and databases.

The :doc:`api` is intended to be kept as consistent as possible, such
that any web service can be used with a minimal learning curve imposed on the
user.

Installation
------------
Astroquery must be installed from source:

.. code-block:: bash

    $ git clone git@github.com:astropy/astroquery.git
    $ cd astroquery
    $ python setup.py install

Requirements
````````````

The following packages are required for astroquery installation & use:

 * `numpy <www.numpy.org>`_
 * `astropy <www.astropy.org>`_
 * `requests <http://docs.python-requests.org/en/latest/>`_

Using astroquery
----------------

All astroquery modules are supposed to follow the same API.  In its simplest form, the API involves
queries based on coordinates or object names.  Some simple examples, using SIMBAD:

.. code-block:: python

    >>> from astroquery.simbad import Simbad
    >>> result_table = Simbad.query_object("m1")
    >>> print result_table
    MAIN_ID      RA         DEC     RA_PREC DEC_PREC COO_ERR_MAJA COO_ERR_MINA COO_ERR_ANGLE COO_QUAL COO_WAVELENGTH     COO_BIBCODE
    ------- ----------- ----------- ------- -------- ------------ ------------ ------------- -------- -------------- -------------------
      M   1 05 34 31.94 +22 00 52.2       6        6          nan          nan             0        C              R 2011A&A...533A..10L
    

All query tools allow coordinate-based queries:      

.. code-block:: python

    >>> import astropy.coordinates as coord
    >>> import astropy.units as u
    >>> # works only for ICRS coordinates:
    >>> c = coord.ICRSCoordinates("05h35m17.3s -05h23m28s")
    >>> r = 5 * u.arcminute
    >>> result_table = Simbad.query_region(c, radius=r)
    MAIN_ID           RA           DEC      RA_PREC DEC_PREC COO_ERR_MAJA COO_ERR_MINA COO_ERR_ANGLE COO_QUAL COO_WAVELENGTH     COO_BIBCODE
    -------------- ------------- ------------- ------- -------- ------------ ------------ ------------- -------- -------------- -------------------
         HD  38875 05 34 59.7297 -80 51 09.082       9        9        5.360        5.270             0        A              O 2007A&A...474..653V
    TYC 9390-799-1 05 33 58.2222 -80 50 18.575       8        8       73.940       58.480            90        B                1998A&A...335L..65H


Table of Contents
-----------------

The following modules have been completed using a common API:

.. toctree::
  :maxdepth: 1

  simbad.rst
  vizier.rst
  irsa_dust.rst

These others are functional, but do not follow a common & consistent API:


.. toctree::
  :maxdepth: 1

  irsa.rst
  ukidss.rst
  magpis.rst
  nrao.rst
  besancon.rst
  ned.rst
  nist.rst
  fermi.rst
  sdss.rst
  alfalfa.rst
  sha.rst
  lamda.rst
  ogle.rst
