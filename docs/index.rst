.. doctest-skip-all

Astroquery
==========

This is the documentation for the Astroquery coordinated package of `astropy
<http://www.astropy.org>`__.

Code and issue tracker are on `GitHub <https://github.com/astropy/astroquery>`_.

If you use astroquery, please `cite <https://github.com/astropy/astroquery/blob/main/astroquery/CITATION>`__ the
paper `Ginsburg, Sipőcz, Brasseur et al 2019 <https://ui.adsabs.harvard.edu/abs/2019AJ....157...98G/abstract>`_.

Introduction
------------

Astroquery is a set of tools for querying astronomical web forms and databases.

There are two other packages with complimentary functionality as Astroquery:
`pyvo <https://pyvo.readthedocs.io/en/latest/>`_ is an Astropy affiliated package, and
`Simple-Cone-Search-Creator <https://github.com/tboch/Simple-Cone-Search-Creator/>`_ to
generate a cone search service complying with the
`IVOA standard <http://www.ivoa.net/documents/latest/ConeSearch.html>`_.
They are more oriented to general `virtual observatory <http://www.virtualobservatory.org>`_
discovery and queries, whereas Astroquery has web service specific interfaces.

Check out the :doc:`gallery` for some nice examples.

Installation
------------

Uniquely in the Astropy ecosystem, Astroquery is operating with a **continuous deployment model**.
It means that a release is instantaneously available after a pull request has been merged. These
releases are automatically uploaded to `PyPI <https://pypi.org/project/astroquery/#history>`__,
and therefore the latest version of astroquery can be pip installed.
The version number of these automated releases contain the ``'dev'`` tag, thus pip needs to be told
to look for these releases during an upgrade, using the ``--pre`` install option. If astroquery is
already installed, please make sure you use the ``--upgrade`` install option as well.

.. code-block:: bash

    $ pip install --pre astroquery

To install all the mandatory and optional dependencies add the ``[all]``
identifyer to the pip command above (or use ``[docs]`` or ``[test]`` for the
dependencies required to build the documentation or run the tests):

.. code-block:: bash

    $ pip install --pre astroquery[all]

In addition to the automated releases, we also keep doing regular, tagged version for maintenance
and packaging purposes. These can be ``pip`` installed without the ``--pre`` option and
are also available from the ``conda-forge`` conda channel.

.. code-block:: bash

    $ conda install -c conda-forge astroquery

To review recent changes and fixes, please have a look at the changelog:

.. toctree::
   :maxdepth: 1

   changelog


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

Astroquery works with Python 3.7 or later.

The following packages are required for astroquery installation & use:

* `numpy <http://www.numpy.org>`_ >= 1.16
* `astropy <http://www.astropy.org>`__ (>=4)
* `pyVO`_ (>=1.1)
* `requests <http://docs.python-requests.org/en/latest/>`_
* `keyring <https://pypi.python.org/pypi/keyring>`_
* `Beautiful Soup <https://www.crummy.com/software/BeautifulSoup/>`_
* `html5lib <https://pypi.python.org/pypi/html5lib>`_

and for running the tests:

* `curl <https://curl.haxx.se/>`__
* `pytest-astropy <https://github.com/astropy/pytest-astropy>`__

The following packages are optional dependencies and are required for the
full functionality of the `~astroquery.alma` module:

* `APLpy <http://aplpy.readthedocs.io/>`_
* `pyregion <http://pyregion.readthedocs.io/>`_

The following packages are optional dependencies and are required for the
full functionality of the `~astroquery.cds` module:

* `astropy-healpix <http://astropy-healpix.readthedocs.io/en/latest/>`_
* `regions <https://astropy-regions.readthedocs.io/en/latest/>`_
* `mocpy <https://cds-astro.github.io/mocpy/>`_ >= 0.5.2
* `vamdclib <https://github.com/VAMDC/vamdclib/>`_  install version from
  personal fork: ``pip install git+https://github.com/keflavich/vamdclib-1.git``

The following packages are optional dependencies and are required for the
full functionality of the `~astroquery.mast` module:

* `boto3 <https://boto3.readthedocs.io/>`_

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

.. _default_config:

Default configuration file
--------------------------

To customize this, copy the default configuration to ``$HOME/.astropy/config/astroquery.cfg``,
uncomment the relevant configuration item(s), and insert your desired value(s).

.. toctree::
  :maxdepth: 1

  configuration

Available Services
==================

If you're new to Astroquery, a good place to start is the :doc:`gallery`:

.. toctree::
  :maxdepth: 1

  gallery

The following modules have been completed using a common API:

.. toctree::
  :maxdepth: 1

  alma/alma.rst
  atomic/atomic.rst
  besancon/besancon.rst
  cadc/cadc.rst
  casda/casda.rst
  cds/cds.rst
  linelists/cdms/cdms.rst
  dace/dace.rst
  esa/hsa/hsa.rst
  esa/hubble/hubble.rst
  esa/iso/iso.rst
  esa/jwst/jwst.rst
  esa/xmm_newton/xmm_newton.rst
  esasky/esasky.rst
  eso/eso.rst
  image_cutouts/first/first.rst
  gaia/gaia.rst
  gama/gama.rst
  gemini/gemini.rst
  heasarc/heasarc.rst
  hips2fits/hips2fits.rst
  hitran/hitran.rst
  ipac/irsa/irsa_dust/irsa_dust.rst
  ipac/irsa/ibe/ibe.rst
  ipac/irsa/irsa.rst
  jplspec/jplspec.rst
  magpis/magpis.rst
  mast/mast.rst
  mpc/mpc.rst
  nasa_ads/nasa_ads.rst
  ipac/ned/ned.rst
  nist/nist.rst
  noirlab/noirlab.rst
  nrao/nrao.rst
  nvas/nvas.rst
  simbad/simbad.rst
  skyview/skyview.rst
  splatalogue/splatalogue.rst
  svo_fps/svo_fps.rst
  ukidss/ukidss.rst
  vamdc/vamdc.rst
  vizier/vizier.rst
  vo_conesearch/vo_conesearch.rst
  vsa/vsa.rst
  xmatch/xmatch.rst


These others are functional, but do not follow a common & consistent API:

.. toctree::
  :maxdepth: 1

  alfalfa/alfalfa.rst
  cosmosim/cosmosim.rst
  exoplanet_orbit_database/exoplanet_orbit_database.rst
  fermi/fermi.rst
  jplhorizons/jplhorizons.rst
  jplsbdb/jplsbdb.rst
  lamda/lamda.rst
  ipac/nexsci/nasa_exoplanet_archive.rst
  oac/oac.rst
  ogle/ogle.rst
  open_exoplanet_catalogue/open_exoplanet_catalogue.rst
  sdss/sdss.rst
  ipac/irsa/sha/sha.rst

There are also subpackages that serve as the basis of others.

.. toctree::
  :maxdepth: 1

  wfau/wfau.rst

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
  exoplanet_orbit_database/exoplanet_orbit_database.rst
  gama/gama.rst
  ipac/irsa/irsa_dust/irsa_dust.rst
  ipac/irsa/ibe/ibe.rst
  ipac/irsa/irsa.rst
  mast/mast.rst
  ipac/nexsci/nasa_exoplanet_archive.rst
  ipac/ned/ned.rst
  ogle/ogle.rst
  open_exoplanet_catalogue/open_exoplanet_catalogue.rst
  sdss/sdss.rst
  simbad/simbad.rst
  ipac/irsa/sha/sha.rst
  ukidss/ukidss.rst
  vizier/vizier.rst
  vo_conesearch/vo_conesearch.rst
  vsa/vsa.rst
  xmatch/xmatch.rst

Archives
--------

Archive services provide data, usually in FITS images or spectra.  They will
generally return a table listing the available data first.

.. toctree::
  :maxdepth: 1

  alfalfa/alfalfa.rst
  alma/alma.rst
  cadc/cadc.rst
  casda/casda.rst
  esa/hubble/hubble.rst
  esa/jwst/jwst.rst
  esa/xmm_newton/xmm_newton.rst
  eso/eso.rst
  fermi/fermi.rst
  gaia/gaia.rst
  gemini/gemini.rst
  heasarc/heasarc.rst
  ipac/irsa/ibe/ibe.rst
  ipac/irsa/irsa.rst
  magpis/magpis.rst
  mast/mast.rst
  ipac/ned/ned.rst
  noirlab/noirlab.rst
  nrao/nrao.rst
  nvas/nvas.rst
  sdss/sdss.rst
  skyview/skyview.rst
  ipac/irsa/sha/sha.rst
  ukidss/ukidss.rst
  vsa/vsa.rst

Simulations
-----------

These services query databases of simulated or synthetic data:

.. toctree::
  :maxdepth: 1

  besancon/besancon.rst
  cosmosim/cosmosim.rst

Line List Services
------------------

There are several web services that provide atomic or molecular line lists, as
well as  cross section and collision rates.  Those services are:

.. toctree::
  :maxdepth: 1

  atomic/atomic.rst
  linelists/cdms/cdms.rst
  hitran/hitran.rst
  jplspec/jplspec.rst
  lamda/lamda.rst
  nist/nist.rst
  splatalogue/splatalogue.rst
  vamdc/vamdc.rst

Other
-----

There are other astronomically significant services, that don't fit the
above categories. Those services are here:

.. toctree::
  :maxdepth: 1

  astrometry_net/astrometry_net.rst
  imcce/imcce.rst
  jplhorizons/jplhorizons.rst
  jplsbdb/jplsbdb.rst
  nasa_ads/nasa_ads.rst
  utils/tap.rst


Topical Collections
===================

Some services focusing on similar topics are also collected in
topical submodules:

.. toctree::
  :maxdepth: 1

  image_cutouts/image_cutouts.rst
  solarsystem/solarsystem.rst


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
  utils/tap.rst

To debug astroquery, logging level can be configured with the following:

.. code-block:: python

    >>> from astroquery import log
    >>> log.setLevel(level)

If ``level`` is set to ``"DEBUG"``, then HTTP requests are logged.
If ``level`` is set to ``"TRACE"``, then HTTP requests and responses are logged.

License
-------

Astroquery is licensed under a 3-clause BSD style license - see :doc:`license`.
