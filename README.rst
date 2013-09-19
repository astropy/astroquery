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


As an `astropy`_ affiliate, astroquery requires `astropy`_.  However, because
astroquery relies heavily upon the ``astropy.coordinates`` module, the
development version of `astropy`_ is required. `astropy`_ can be installed from
pip:

.. code-block:: bash

    $ pip install git+http://github.com/astropy/astropy.git#egg=astropy

astroquery uses the `requests <http://docs.python-requests.org/en/latest/>`_
module to communicate with the internet.  `requests`_ can also be installed with
pip.

The `first beta release`_ of astroquery can be downloaded or pip installed:

.. code-block:: bash

   $ pip install https://github.com/astropy/astroquery/archive/v0.1.tar.gz


If you'd like the latest development version, you can install it with the
following commands:

.. code-block:: bash

    $ git clone git@github.com:astropy/astroquery.git
    $ cd astroquery
    $ python setup.py install

pip install also works:

.. code-block:: bash

    $ pip install git+http://github.com/astropy/astroquery.git#egg=astroquery
    
Using astroquery
----------------
Importing astroquery on its own doesn't get you much: you need to import each
sub-module specifically.  Check out the `docs`_
to find a list of the tools available.  The `API
<http://astroquery.readthedocs.org/en/latest/astroquery/api.html>`_ 
shows the standard suite of tools common to most modules, e.g. `query_object`
and `query_region`.  

To report bugs and request features, please use the issue tracker.  Code
contributions are very welcome, though we encourage you to follow the `API`_
and `contributing guidelines
<https://github.com/astropy/astroquery/blob/master/CONTRIBUTING.rst>`_ as much
as possible.

List of Modules
---------------

  * `Simbad <http://astroquery.readthedocs.org/en/latest/simbad.html>`_:           Basic data, cross-identifications, bibliography and measurements for astronomical objects outside the solar system.
  * `Vizier <http://astroquery.readthedocs.org/en/latest/vizier.html>`_:           Set of 11,000+ published, multiwavelength catalogues hosted by the CDS.
  * `IRSA dust <http://astroquery.readthedocs.org/en/latest/irsa_dust.html>`_:     Galactic dust reddening and extinction maps from IRAS 100 um data.
  * `NED <http://astroquery.readthedocs.org/en/latest/ned.html>`_:                 NASA/IPAC Extragalactic Database. Multiwavelength data from both surveys and publications.
  * `IRSA <http://astroquery.readthedocs.org/en/latest/irsa.html>`_:               NASA/IPAC Infrared Science Archive. Science products for all of NASA's infrared and sub-mm missions.
  * `UKIDSS <http://astroquery.readthedocs.org/en/latest/ukidss.html>`_:           UKIRT Infrared Deep Sky Survey. JHK images of 7500 sq deg. in the northern sky.
  * `MAGPIS <http://astroquery.readthedocs.org/en/latest/magpis.html>`_:           Multi-Array Galactic Plane Imaging Survey. 6 and 20-cm radio images of the Galactic plane from the VLA.
  * `NRAO <http://astroquery.readthedocs.org/en/latest/nrao.html>`_:               Science data archive of the National Radio Astronomy Observatory. VLA, JVLA, VLBA and GBT data products.
  * `Besancon <http://astroquery.readthedocs.org/en/latest/besancon.html>`_:       Model of stellar population synthesis in the Galaxy.
  * `NIST <http://astroquery.readthedocs.org/en/latest/nist.html>`_:               National Institute of Standards and Technology (NIST) atomic lines database.
  * `Fermi <http://astroquery.readthedocs.org/en/latest/fermi.html>`_:             Fermi gamma-ray telescope archive.
  * `SDSS <http://astroquery.readthedocs.org/en/latest/sdss.html>`_:               Sloan Digital Sky Survey data, including optical images, spectra, and spectral templates.
  * `Alfalfa <http://astroquery.readthedocs.org/en/latest/alfalfa.html>`_:         Arecibo Legacy Fast ALFA survey; extragalactic HI radio data.
  * `SHA <http://astroquery.readthedocs.org/en/latest/sha.html>`_:                 Spitzer Heritage Archive; infrared data products from the Spitzer Space Telescope
  * `Lamda <http://astroquery.readthedocs.org/en/latest/lamda.html>`_:             Leiden Atomic and Molecular Database; energy levels, radiative transitions, and collisional rates for astrophysically relevant atoms and molecules.
  * `Ogle <http://astroquery.readthedocs.org/en/latest/ogle.html>`_:               Optical Gravitational Lensing Experiment III; information on interstellar extinction towards the Galactic bulge.
  * `Splatalogue <http://astroquery.readthedocs.org/en/latest/splatalogue.html>`_: National Radio Astronomy Observatory (NRAO)-maintained (mostly) molecular radio and millimeter line list service.

Additional Links
----------------

`Download Development ZIP`_  |  `Download Development TAR`_  

Maintained by `Adam Ginsburg`_ (`astropy.astroquery@gmail.com`_)

.. _Download Development ZIP: https://github.com/astropy/astroquery/zipball/master
.. _Download Development TAR: https://github.com/astropy/astroquery/tarball/master
.. _Download Stable ZIP: https://github.com/astropy/astroquery/zipball/stable
.. _Download Stable TAR: https://github.com/astropy/astroquery/tarball/stable
.. _View on Github: https://github.com/astropy/astroquery/
.. _docs: http://astroquery.readthedocs.org
.. _Documentation: http://astroquery.readthedocs.org
.. _first beta release: https://github.com/astropy/astroquery/tarball/v0.1
.. _astropy.astroquery@gmail.com: mailto:astropy.astroquery@gmail.com
.. _Adam Ginsburg: http://www.adamgginsburg.com
.. _Blog: http://astropy.org/astroquery-blog
