.. doctest-skip-all

Astroquery
==========

This is the documentation for the Astroquery affiliated package of `astropy
<http://www.astropy.org>`__.

Code and issue tracker are on `GitHub <https://github.com/astropy/astroquery>`_.

Introduction
------------

Astroquery is a set of tools for querying astronomical web forms and databases.

There are two other packages with complimentary functionality as Astroquery:
`astropy.vo <http://docs.astropy.org/en/latest/vo/index.html>`_ is in the Astropy core and
`pyvo <https://pyvo.readthedocs.io/en/latest/>`_ is an Astropy affiliated package.
They are more oriented to general `virtual observatory <http://www.virtualobservatory.org>`_
discovery and queries, whereas Astroquery has web service specific interfaces.

Check out the :doc:`gallery` for some nice examples.

Installation
------------
The latest version of astroquery can be conda installed while the latest and
development versions can be pip installed or be downloaded directly from GitHub.

Using pip
^^^^^^^^^
.. code-block:: bash

    $ pip install astroquery

and the 'bleeding edge' master version:

.. code-block:: bash

   $ pip install https://github.com/astropy/astroquery/archive/master.zip

Using conda
^^^^^^^^^^^

It is also possible to install the latest astroquery with `anaconda
<http://continuum.io/>`_ from the astropy channel:

.. code-block:: bash

    $ conda install -c astropy astroquery


Building from source
^^^^^^^^^^^^^^^^^^^^

The development version can be obtained and installed from github:

.. code-block:: bash

    $ # If you have a github account:
    $ git clone git@github.com:astropy/astroquery.git
    $ # If you do not:
    $ git clone https://github.com/astropy/astroquery.git
    $ cd astroquery
    $ python setup.py install


Requirements
------------

Astroquery works with Python 2.7 and 3.3 or later.

The following packages are required for astroquery installation & use:

* `numpy <http://www.numpy.org>`_ >= 1.6
* `astropy <http://www.astropy.org>`__ (>=0.4)
* `requests <http://docs.python-requests.org/en/latest/>`_
* `keyring <https://pypi.python.org/pypi/keyring>`_ (required for the
  `~astroquery.eso`, `~astroquery.alma` and `~astroquery.cosmosim` modules)
* `Beautiful Soup <http://www.crummy.com/software/BeautifulSoup/>`_
* `html5lib <https://pypi.python.org/pypi/html5lib>`_

Using astroquery
----------------

All astroquery modules are supposed to follow the same API.  In its simplest form, the API involves
queries based on coordinates or object names.  Some simple examples, using SIMBAD:

.. code-block:: python

    >>> from astroquery.simbad import Simbad
    >>> result_table = Simbad.query_object("m1")
    >>> result_table.pprint(show_unit=True)
    MAIN_ID      RA         DEC     RA_PREC ... COO_QUAL COO_WAVELENGTH     COO_BIBCODE
              "h:m:s"     "d:m:s"           ...
    ------- ----------- ----------- ------- ... -------- -------------- -------------------
      M   1 05 34 31.94 +22 00 52.2       6 ...        C              R 2011A&A...533A..10L



All query tools allow coordinate-based queries:

.. code-block:: python

    >>> from astropy import coordinates
    >>> import astropy.units as u
    >>> # works only for ICRS coordinates:
    >>> c = coordinates.SkyCoord("05h35m17.3s -05d23m28s", frame='icrs')
    >>> r = 5 * u.arcminute
    >>> result_table = Simbad.query_region(c, radius=r)
    >>> result_table.pprint(show_unit=True, max_width=80, max_lines=5)
      MAIN_ID         RA          DEC      ... COO_WAVELENGTH     COO_BIBCODE
                   "h:m:s"      "d:m:s"    ...
    ------------ ------------ ------------ ... -------------- -------------------
           M  42   05 35 17.3    -05 23 28 ...                1981MNRAS.194..693L
             ...          ...          ... ...            ...                 ...
    V* V2114 Ori 05 35 01.671 -05 26 36.30 ...              I 2003yCat.2246....0C


For additional guidance and examples, read the documentation for the individual services below.

Available Services
==================

If you're new to Astroquery, a good place to start is the :doc:`gallery`:

.. toctree::
  :maxdepth: 1

  gallery

The following modules have been completed using a common API:

.. toctree::
  :maxdepth: 1

  simbad/simbad.rst
  vizier/vizier.rst
  esasky/esasky.rst
  irsa/irsa_dust.rst
  ned/ned.rst
  splatalogue/splatalogue.rst
  ibe/ibe.rst
  irsa/irsa.rst
  ukidss/ukidss.rst
  magpis/magpis.rst
  nrao/nrao.rst
  besancon/besancon.rst
  nist/nist.rst
  nvas/nvas.rst
  gama/gama.rst
  eso/eso.rst
  xmatch/xmatch.rst
  atomic/atomic.rst
  alma/alma.rst
  skyview/skyview.rst
  nasa_ads/nasa_ads.rst
  heasarc/heasarc.rst

These others are functional, but do not follow a common & consistent API:

.. toctree::
  :maxdepth: 1

  fermi/fermi.rst
  sdss/sdss.rst
  alfalfa/alfalfa.rst
  sha/sha.rst
  lamda/lamda.rst
  ogle/ogle.rst
  open_exoplanet_catalogue/open_exoplanet_catalogue.rst
  cosmosim/cosmosim.rst

Catalog, Archive, and Other
===========================

A second index of the services by the type of data they serve.  Some services
perform many tasks and are listed more than once.

Catalogs
--------

The first serve catalogs, which generally return one row of information for
each source (though they may return many catalogs that *each* have one row
for each source)

.. toctree::
  :maxdepth: 1

  alfalfa/alfalfa.rst
  gama/gama.rst
  ibe/ibe.rst
  irsa/irsa.rst
  irsa/irsa_dust.rst
  ned/ned.rst
  ogle/ogle.rst
  open_exoplanet_catalogue/open_exoplanet_catalogue.rst
  sdss/sdss.rst
  sha/sha.rst
  simbad/simbad.rst
  ukidss/ukidss.rst
  vizier/vizier.rst
  xmatch/xmatch.rst

Archives
--------

Archive services provide data, usually in FITS images or spectra.  They will
generally return a table listing the available data first.

.. toctree::
  :maxdepth: 1

  alfalfa/alfalfa.rst
  alma/alma.rst
  eso/eso.rst
  fermi/fermi.rst
  heasarc/heasarc.rst
  ibe/ibe.rst
  irsa/irsa.rst
  magpis/magpis.rst
  ned/ned.rst
  nrao/nrao.rst
  nvas/nvas.rst
  sdss/sdss.rst
  sha/sha.rst
  ukidss/ukidss.rst
  skyview/skyview.rst

Simulations
-----------

Simulation services query databases of simulated or synthetic data

.. toctree::
  :maxdepth: 1

  besancon/besancon.rst
  cosmosim/cosmosim.rst

Other
-----

There are other astronomically significant services, e.g. line list and
atomic/molecular cross section and collision rate services, that don't fit the
above categories.

.. toctree::
  :maxdepth: 1

  atomic/atomic.rst
  lamda/lamda.rst
  nist/nist.rst
  splatalogue/splatalogue.rst
  nasa_ads/nasa_ads.rst


Developer documentation
-----------------------

The modules and their maintainers are listed on the
`Maintainers <https://github.com/astropy/astroquery/wiki/Maintainers>`_
wiki page.


The :doc:`api` is intended to be kept as consistent as possible, such
that any web service can be used with a minimal learning curve imposed on the
user.

.. toctree::
   :maxdepth: 1

   api.rst
   template.rst
   testing.rst

The following Astroquery modules are mostly meant for internal use of
services in Astroquery, you can use them for your scripts, but we don't guarantee API stability.

.. toctree::
  :maxdepth: 1

  utils.rst
  query.rst
