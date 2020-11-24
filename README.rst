`Documentation`_ | Blog_ |  `View on Github`_ |  `Download Stable ZIP`_  |  `Download Stable TAR`_

.. image:: https://pypip.in/v/astroquery/badge.png
   :target: https://img.shields.io/pypi/v/astroquery.svg
   :alt: Latest PyPI version

.. image:: https://travis-ci.com/astropy/astroquery.svg?branch=master
   :target: https://travis-ci.com/astropy/astroquery
   :alt: Travis CI Status

.. image:: https://coveralls.io/repos/astropy/astroquery/badge.png
   :target: https://coveralls.io/r/astropy/astroquery
   :alt: Coverage Status

.. image:: https://zenodo.org/badge/DOI/10.5281/zenodo.1160627.svg
   :target: https://doi.org/10.5281/zenodo.1160627
   :alt: Zenodo


==================================
Accessing Online Astronomical Data
==================================

Astroquery is an `astropy <http://www.astropy.org>`_ affiliated package that
contains a collection of tools to access online Astronomical data. Each web
service has its own sub-package. For example, to interface with the `SIMBAD
website <http://simbad.u-strasbg.fr/simbad/>`_, use the ``simbad`` sub-package:

.. code-block:: python

    >>> from astroquery.simbad import Simbad
    >>> theta1c = Simbad.query_object('tet01 Ori C')
    >>> theta1c.pprint()
       MAIN_ID          RA           DEC      ... COO_QUAL COO_WAVELENGTH     COO_BIBCODE
    ------------- ------------- ------------- ... -------- -------------- -------------------
    * tet01 Ori C 05 35 16.4637 -05 23 22.848 ...        A              O 2007A&A...474..653V

Installation and Requirements
-----------------------------

Astroquery works with Python 3.6 or later.
As an `astropy`_ affiliate, astroquery requires `astropy`_ version 3.1 or later.

astroquery uses the `requests <http://docs.python-requests.org/en/latest/>`_
module to communicate with the internet.  `BeautifulSoup
<http://www.crummy.com/software/BeautifulSoup/>`_ and `html5lib'
<https://html5lib.readthedocs.io/en/latest/>`_ are needed for HTML parsing for
some services.  The `keyring <https://pypi.python.org/pypi/keyring>`_ module is
also required for accessing services that require a login.  These can all be
installed using `pip <https://pypi.python.org/pypi/pip>`_ or `anaconda
<http://continuum.io/>`_.  Running the tests requires `curl
<https://curl.haxx.se/>`_ to be installed.

The latest version of astroquery can be conda installed:

.. code-block:: bash

    $ conda install -c astropy astroquery

or pip installed:

.. code-block:: bash

    $ pip install astroquery

and the 'bleeding edge' master version:

.. code-block:: bash

   $ pip install https://github.com/astropy/astroquery/archive/master.zip

or cloned and installed from source:

.. code-block:: bash

    $ # If you have a github account:
    $ git clone git@github.com:astropy/astroquery.git
    $ # If you do not:
    $ git clone https://github.com/astropy/astroquery.git
    $ cd astroquery
    $ python setup.py install

Using astroquery
----------------

Importing astroquery on its own doesn't get you much: you need to import each
sub-module specifically.  Check out the `docs`_
to find a list of the tools available.  The `API`_
shows the standard suite of tools common to most modules, e.g. `query_object`
and `query_region`.

To report bugs and request features, please use the issue tracker.  Code
contributions are very welcome, though we encourage you to follow the `API`_
and `contributing guidelines
<https://github.com/astropy/astroquery/blob/master/CONTRIBUTING.rst>`_ as much
as possible.

List of Modules
---------------

The following modules have been completed using a common API:

  * `ALMA Archive <http://astroquery.readthedocs.io/en/latest/alma/alma.html>`_
  * `Atomic Line List <http://astroquery.readthedocs.io/en/latest/atomic/atomic.html>`_: A collection of more than 900,000 atomic transitions.
  * `Besancon <http://astroquery.readthedocs.io/en/latest/besancon/besancon.html>`_: Model of stellar population synthesis in the Galaxy.
  * `CDS MOC Service <https://astroquery.readthedocs.io/en/latest/cds/cds.html>`_: A collection of all-sky survey coverage maps.
  * `CADC <https://astroquery.readthedocs.io/en/latest/cadc/cadc.html>`_: Canadian Astronomy Data Centre.
  * `ESASky <http://astroquery.readthedocs.io/en/latest/esasky/esasky.html>`_: ESASky is a science driven discovery portal providing easy visualizations and full access to the entire sky as observed with ESA Space astronomy missions.
  * `ESO Archive <http://astroquery.readthedocs.io/en/latest/eso/eso.html>`_
  * `FIRST <http://astroquery.readthedocs.io/en/latest/image_cutouts/first/first.html>`_: Faint Images of the Radio Sky at Twenty-cm. 20-cm radio images of the extragalactic sky from the VLA.
  * `Gaia <http://astroquery.readthedocs.io/en/latest/gaia/gaia.html>`_: European Space Agency Gaia Archive.
  * `ESA XMM <https://astroquery.readthedocs.io/en/latest/esa/xmm_newton.html>`_: European Space Agency XMM-Newton Science Archive.
  * `ESA Hubble <https://astroquery.readthedocs.io/en/latest/esa/hubble.html>`_: European Space Agency Hubble Science Archive.
  * `GAMA database <http://astroquery.readthedocs.io/en/latest/gama/gama.html>`_
  * `Gemini <http://astroquery.readthedocs.io/en/latest/gemini/gemini.html>`_: Gemini Archive.
  * `HEASARC <http://astroquery.readthedocs.io/en/latest/heasarc/heasarc.html>`_: NASA's High Energy Astrophysics Science Archive Research Center.
  * `IBE <http://astroquery.readthedocs.io/en/latest/ibe/ibe.html>`_: IRSA Image Server program interface (IBE) Query Tool provides access to the 2MASS, WISE, and PTF image archives.
  * `IRSA <http://astroquery.readthedocs.io/en/latest/irsa/irsa.html>`_: NASA/IPAC Infrared Science Archive. Science products for all of NASA's infrared and sub-mm missions.
  * `IRSA dust <http://astroquery.readthedocs.io/en/latest/irsa/irsa_dust.html>`_: Galactic dust reddening and extinction maps from IRAS 100 um data.
  * `MAGPIS <http://astroquery.readthedocs.io/en/latest/magpis/magpis.html>`_: Multi-Array Galactic Plane Imaging Survey. 6 and 20-cm radio images of the Galactic plane from the VLA.
  * `MAST <http://astroquery.readthedocs.io/en/latest/mast/mast.html>`_: Barbara A. Mikulski Archive for Space Telescopes.
  * `Minor Planet Center <http://astroquery.readthedocs.io/en/latest/mpc/mpc.html>`_
  * `NASA ADS <http://astroquery.readthedocs.io/en/latest/nasa_ads/nasa_ads.html>`_: SAO/NASA Astrophysics Data System.
  * `NED <http://astroquery.readthedocs.io/en/latest/ned/ned.html>`_: NASA/IPAC Extragalactic Database. Multiwavelength data from both surveys and publications.
  * `NIST <http://astroquery.readthedocs.io/en/latest/nist/nist.html>`_: National Institute of Standards and Technology (NIST) atomic lines database.
  * `NRAO <http://astroquery.readthedocs.io/en/latest/nrao/nrao.html>`_: Science data archive of the National Radio Astronomy Observatory. VLA, JVLA, VLBA and GBT data products.
  * `NVAS archive <http://astroquery.readthedocs.io/en/latest/nvas/nvas.html>`_
  * `Simbad <http://astroquery.readthedocs.io/en/latest/simbad/simbad.html>`_: Basic data, cross-identifications, bibliography and measurements for astronomical objects outside the solar system.
  * `Skyview <http://astroquery.readthedocs.io/en/latest/skyview/skyview.html>`_: NASA SkyView service for imaging surveys.
  * `Splatalogue <http://astroquery.readthedocs.io/en/latest/splatalogue/splatalogue.html>`_: National Radio Astronomy Observatory (NRAO)-maintained (mostly) molecular radio and millimeter line list service.
  * `UKIDSS <http://astroquery.readthedocs.io/en/latest/ukidss/ukidss.html>`_: UKIRT Infrared Deep Sky Survey. JHK images of 7500 sq deg. in the northern sky.
  * `Vamdc <http://astroquery.readthedocs.io/en/latest/vamdc/vamdc.html>`_: VAMDC molecular line database.
  * `Vizier <http://astroquery.readthedocs.io/en/latest/vizier/vizier.html>`_: Set of 11,000+ published, multiwavelength catalogues hosted by the CDS.
  * `VO Simple Cone Search <http://astroquery.readthedocs.io/en/latest/vo_conesearch/vo_conesearch.html>`_
  * `xMatch <http://astroquery.readthedocs.io/en/latest/xmatch/xmatch.html>`_:  Cross-identify sources between very large data sets or between a user-uploaded list and a large catalogue.

These others are functional, but do not follow a common or consistent API:

  * `Alfalfa <http://astroquery.readthedocs.io/en/latest/alfalfa/alfalfa.html>`_: Arecibo Legacy Fast ALFA survey; extragalactic HI radio data.
  * `CosmoSim <http://astroquery.readthedocs.io/en/latest/cosmosim/cosmosim.html>`_: The CosmoSim database provides results from cosmological simulations performed within different projects: the MultiDark project, the BolshoiP project, and the CLUES project.
  * `Exoplanet Orbit Database  <http://astroquery.readthedocs.io/en/latest/exoplanet_orbit_database/exoplanet_orbit_database.html>`_
  * `Fermi <http://astroquery.readthedocs.io/en/latest/fermi/fermi.html>`_: Fermi gamma-ray telescope archive.
  * `HITRAN <http://astroquery.readthedocs.io/en/latest/hitran/hitran.html>`_: Access to the high-resolution transmission molecular absorption database.
  * `JPL Horizons <http://astroquery.readthedocs.io/en/latest/jplhorizons/jplhorizons.html>`_: JPL Solar System Dynamics Horizons Service.
  * `JPL SBDB <http://astroquery.readthedocs.io/en/latest/jplsbdb/jplsbdb.html>`_: JPL Solar System Dynamics Small-Body Database Browser Service.
  * `Lamda <http://astroquery.readthedocs.io/en/latest/lamda/lamda.html>`_: Leiden Atomic and Molecular Database; energy levels, radiative transitions, and collisional rates for astrophysically relevant atoms and molecules.
  * `NASA Exoplanet Archive  <http://astroquery.readthedocs.io/en/latest/nasa_exoplanet_archive/nasa_exoplanet_archive.html>`_
  * `OAC API <http://astroquery.readthedocs.io/en/latest/oac/oac.html>`_: Open Astronomy Catalog REST API Service.
  * `Ogle <http://astroquery.readthedocs.io/en/latest/ogle/ogle.html>`_: Optical Gravitational Lensing Experiment III; information on interstellar extinction towards the Galactic bulge.
  * `Open Expolanet Catalog (OEC) <http://astroquery.readthedocs.io/en/latest/open_exoplanet_catalogue/open_exoplanet_catalogue.html>`_
  * `SDSS <http://astroquery.readthedocs.io/en/latest/sdss/sdss.html>`_: Sloan Digital Sky Survey data, including optical images, spectra, and spectral templates.
  * `SHA <http://astroquery.readthedocs.io/en/latest/sha/sha.html>`_: Spitzer Heritage Archive; infrared data products from the Spitzer Space Telescope.


Citing Astroquery
-----------------

If you use ``astroquery``, please cite the paper we published in `The
Astronomical Journal <http://adsabs.harvard.edu/abs/2019AJ....157...98G>`__.

The BibTeX entry is available from the package itself::

  import astroquery
  astroquery.__citation__


In addition you may also want to refer to specific versions of the
package. We create a separate Zenodo DOI for each version, they can be
looked up at the following `Zenodo page <https://doi.org/10.5281/zenodo.591669>`__


Additional Links
----------------

`Download Development ZIP`_  |  `Download Development TAR`_

Maintained by `Adam Ginsburg`_ and `Brigitta Sipocz <https://github.com/bsipocz>`_ (`astropy.astroquery@gmail.com`_)


.. _Download Development ZIP: https://github.com/astropy/astroquery/zipball/master
.. _Download Development TAR: https://github.com/astropy/astroquery/tarball/master
.. _Download Stable ZIP: https://github.com/astropy/astroquery/zipball/stable
.. _Download Stable TAR: https://github.com/astropy/astroquery/tarball/stable
.. _View on Github: https://github.com/astropy/astroquery/
.. _docs: http://astroquery.readthedocs.io
.. _Documentation: http://astroquery.readthedocs.io
.. _astropy.astroquery@gmail.com: mailto:astropy.astroquery@gmail.com
.. _Adam Ginsburg: http://www.adamgginsburg.com
.. _Blog: http://astropy.org/astroquery-blog
.. _API: http://astroquery.readthedocs.io/en/latest/api.html
