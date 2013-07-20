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

.. code-block:: 
    git clone git@github.com:astropy/astroquery.git
    cd astroquery
    python setup.py install

Using astroquery
----------------

All astroquery modules are supposed to follow the same API.  In its simplest form, the API involves
queries based on coordinates or object names.  Some simple examples, using SIMBAD:

.. code-block:: python
    from astroquery.simbad import Simbad
    result_table = Simbad.query_object("m1")
    
    import astropy.coordinates as coord
    import astropy.units as u
    # works only for ICRS coordinates:
    c = coord.ICRSCoordinates("05h35m17.3s -05h23m28s")
    r = 5 * u.arcminute
    result_table = Simbad.query_region(c, radius=r)
 


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
