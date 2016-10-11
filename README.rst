`Documentation`_ | Blog_ |  `View on Github`_ |  `Download Stable ZIP`_  |  `Download Stable TAR`_


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

Astroquery works with Python 2.7 and 3.3 or later.
As an `astropy`_ affiliate, astroquery requires `astropy`_ version 0.4 or later.

astroquery uses the `requests <http://docs.python-requests.org/en/latest/>`_
module to communicate with the internet.  `BeautifulSoup
<http://www.crummy.com/software/BeautifulSoup/>`_  and `html5lib'
<https://html5lib.readthedocs.io/en/latest/>`_ are needed for HTML parsing
for some services.  The `keyring <https://pypi.python.org/pypi/keyring>`_
module is also required for accessing services that require a login.
These can all be installed using `pip <https://pypi.python.org/pypi/pip>`_.

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

  * `Simbad <http://astroquery.readthedocs.io/en/latest/simbad/simbad.html>`_:           Basic data, cross-identifications, bibliography and measurements for astronomical objects outside the solar system.
  * `Vizier <http://astroquery.readthedocs.io/en/latest/vizier/vizier.html>`_:           Set of 11,000+ published, multiwavelength catalogues hosted by the CDS.
  * `ESASky <http://astroquery.readthedocs.io/en/latest/esasky/esasky.html>`_:           ESASky is a science driven discovery portal providing easy visualizations and full access to the entire sky as observed with ESA Space astronomy missions.
  * `IRSA Image Server program interface (IBE) Query Tool<http://astroquery.readthedocs.io/en/latest/ibe/ibe.html>`_: provides access to the 2MASS, WISE, and PTF image archives.
  * `IRSA dust <http://astroquery.readthedocs.io/en/latest/irsa/irsa_dust.html>`_:     Galactic dust reddening and extinction maps from IRAS 100 um data.
  * `NED <http://astroquery.readthedocs.io/en/latest/ned/ned.html>`_:                 NASA/IPAC Extragalactic Database. Multiwavelength data from both surveys and publications.
  * `IRSA <http://astroquery.readthedocs.io/en/latest/irsa/irsa.html>`_:               NASA/IPAC Infrared Science Archive. Science products for all of NASA's infrared and sub-mm missions.
  * `UKIDSS <http://astroquery.readthedocs.io/en/latest/ukidss/ukidss.html>`_:           UKIRT Infrared Deep Sky Survey. JHK images of 7500 sq deg. in the northern sky.
  * `MAGPIS <http://astroquery.readthedocs.io/en/latest/magpis/magpis.html>`_:           Multi-Array Galactic Plane Imaging Survey. 6 and 20-cm radio images of the Galactic plane from the VLA.
  * `NRAO <http://astroquery.readthedocs.io/en/latest/nrao/nrao.html>`_:               Science data archive of the National Radio Astronomy Observatory. VLA, JVLA, VLBA and GBT data products.
  * `Besancon <http://astroquery.readthedocs.io/en/latest/besancon/besancon.html>`_:       Model of stellar population synthesis in the Galaxy.
  * `NIST <http://astroquery.readthedocs.io/en/latest/nist/nist.html>`_:               National Institute of Standards and Technology (NIST) atomic lines database.
  * `Fermi <http://astroquery.readthedocs.io/en/latest/fermi/fermi.html>`_:             Fermi gamma-ray telescope archive.
  * `SDSS <http://astroquery.readthedocs.io/en/latest/sdss/sdss.html>`_:               Sloan Digital Sky Survey data, including optical images, spectra, and spectral templates.
  * `Alfalfa <http://astroquery.readthedocs.io/en/latest/alfalfa/alfalfa.html>`_:         Arecibo Legacy Fast ALFA survey; extragalactic HI radio data.
  * `SHA <http://astroquery.readthedocs.io/en/latest/sha/sha.html>`_:                 Spitzer Heritage Archive; infrared data products from the Spitzer Space Telescope
  * `Lamda <http://astroquery.readthedocs.io/en/latest/lamda/lamda.html>`_:             Leiden Atomic and Molecular Database; energy levels, radiative transitions, and collisional rates for astrophysically relevant atoms and molecules.
  * `Ogle <http://astroquery.readthedocs.io/en/latest/ogle/ogle.html>`_:               Optical Gravitational Lensing Experiment III; information on interstellar extinction towards the Galactic bulge.
  * `Splatalogue <http://astroquery.readthedocs.io/en/latest/splatalogue/splatalogue.html>`_: National Radio Astronomy Observatory (NRAO)-maintained (mostly) molecular radio and millimeter line list service.
  * `CosmoSim <http://astroquery.readthedocs.io/en/latest/cosmosim/cosmosim.html>`_: The CosmoSim database provides results from cosmological simulations performed within different projects: the MultiDark project, the BolshoiP project, and the CLUES project.
  * `ESO Archive <http://astroquery.readthedocs.io/en/latest/eso/eso.html>`_
  * `ALMA Archive <http://astroquery.readthedocs.io/en/latest/alma/alma.html>`_
  * `GAMA database <http://astroquery.readthedocs.io/en/latest/gama/gama.html>`_
  * `NVAS archive <http://astroquery.readthedocs.io/en/latest/nvas/nvas.html>`_
  * `Open Expolanet Catalog (OEC) <http://astroquery.readthedocs.io/en/latest/open_exoplanet_catalogue/open_exoplanet_catalogue.html>`_

Additional Links
----------------

`Download Development ZIP`_  |  `Download Development TAR`_

Maintained by `Adam Ginsburg`_ (`astropy.astroquery@gmail.com`_)

To cite, use our `figshare`_ DOI (http://dx.doi.org/10.6084/m9.figshare.805208) or our Zenodo DOI.


Badges
------
.. image:: https://pypip.in/v/astroquery/badge.png
    :target: https://crate.io/packages/astroquery/
    :alt: Latest PyPI version

.. image:: https://pypip.in/d/astroquery/badge.png
    :target: https://crate.io/packages/astroquery/
    :alt: Number of PyPI downloads

.. image:: https://travis-ci.org/astropy/astroquery.svg?branch=master
   :target: https://travis-ci.org/astropy/astroquery

.. image:: https://coveralls.io/repos/astropy/astroquery/badge.png
   :target: https://coveralls.io/r/astropy/astroquery

.. image:: https://badges.gitter.im/astropy/astroquery.png
   :target: https://gitter.im/astropy/astroquery

.. image:: https://zenodo.org/badge/doi/10.5281/zenodo.44961.svg
   :target: http://dx.doi.org/10.5281/zenodo.44961


.. .. image:: https://d2weczhvl823v0.cloudfront.net/astropy/astroquery/trend.png
..    :alt: Bitdeli badge
..    :target: https://bitdeli.com/free


.. _Download Development ZIP: https://github.com/astropy/astroquery/zipball/master
.. _Download Development TAR: https://github.com/astropy/astroquery/tarball/master
.. _Download Stable ZIP: https://github.com/astropy/astroquery/zipball/stable
.. _Download Stable TAR: https://github.com/astropy/astroquery/tarball/stable
.. _View on Github: https://github.com/astropy/astroquery/
.. _docs: http://astroquery.readthedocs.io
.. _Documentation: http://astroquery.readthedocs.io
.. _latest release: https://github.com/astropy/astroquery/tarball/v0.2
.. _astropy.astroquery@gmail.com: mailto:astropy.astroquery@gmail.com
.. _Adam Ginsburg: http://www.adamgginsburg.com
.. _Blog: http://astropy.org/astroquery-blog
.. _API: http://astroquery.readthedocs.io/en/latest/api.html
.. _figshare: http://figshare.com/articles/Astroquery_v0_1/805208
