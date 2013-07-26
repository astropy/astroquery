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

As an `astropy`_ affiliate, astroquery requires `astropy`_.  `astropy`_ can be
installed from pip:

.. code-block:: bash

    $ pip install astropy

astroquery uses the `requests <http://docs.python-requests.org/en/latest/>`_
module to communicate with the internet.  `requests`_ can also be installed with
pip.

As of July 2013, astroquery is in pre-release state, so to install, you need to
clone it:

.. code-block:: bash

    $ git clone git@github.com:astropy/astroquery.git
    $ cd astroquery
    $ python setup.py install
    
Using astroquery
----------------
Importing astroquery on its own doesn't get you much: you need to import each
sub-module specifically.  Check out the `docs <astroquery.readthedocs.org>`_
to find a list of the tools available.  The `API
<http://astroquery.readthedocs.org/en/latest/astroquery/api.html>`_ 
shows the standard suite of tools common to most modules, e.g. `query_object`
and `query_region`.  

To report bugs and request features, please use the issue tracker.  Code
contributions are very welcome, though we encourage you to follow the `API`_
and `contributing guidelines
<https://github.com/astropy/astroquery/blob/master/CONTRIBUTING.rst>`_ as much
as possible.
