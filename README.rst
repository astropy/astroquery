`Documentation`_ | Blog_ |  `View on Github`_ |  `Download Stable ZIP`_  |  `Download Stable TAR`_

.. image:: https://pypip.in/v/astroquery/badge.png
   :target: https://img.shields.io/pypi/v/astroquery.svg
   :alt: Latest PyPI version

.. image:: https://readthedocs.org/projects/astroquery/badge/?version=latest
    :target: https://astroquery.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status

.. image:: https://github.com/astropy/astroquery/workflows/CI/badge.svg
    :target: https://github.com/astropy/astroquery/actions?query=workflow%3ACI
    :alt: Github Actions CI Status

.. image:: https://codecov.io/gh/astropy/astroquery/branch/main/graph/badge.svg
    :target: https://codecov.io/gh/astropy/astroquery
    :alt: Coverage results

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

Astroquery works with Python 3.7 or later.
As an `astropy`_ affiliate, astroquery requires `astropy`_ version 4.0 or later.

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

    $ conda install -c conda-forge astroquery

or pip installed:

.. code-block:: bash

    $ pip install --pre astroquery

and the 'bleeding edge' main version:

.. code-block:: bash

   $ pip install https://github.com/astropy/astroquery/archive/main.zip

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
sub-module specifically.  See the documentation for a list of `Available
Services <https://astroquery.readthedocs.io/en/latest/#available-services>`_.
The `API`_ shows the standard suite of tools common to most modules, e.g.
`query_object` and `query_region`.

To report bugs and request features, please use the issue tracker.  Code
contributions are very welcome, though we encourage you to follow the `API`_
and `contributing guidelines
<https://github.com/astropy/astroquery/blob/main/CONTRIBUTING.rst>`_ as much
as possible.

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


.. _Download Development ZIP: https://github.com/astropy/astroquery/zipball/main
.. _Download Development TAR: https://github.com/astropy/astroquery/tarball/main
.. _Download Stable ZIP: https://github.com/astropy/astroquery/zipball/stable
.. _Download Stable TAR: https://github.com/astropy/astroquery/tarball/stable
.. _View on Github: https://github.com/astropy/astroquery/
.. _Documentation: http://astroquery.readthedocs.io
.. _astropy.astroquery@gmail.com: mailto:astropy.astroquery@gmail.com
.. _Adam Ginsburg: http://www.adamgginsburg.com
.. _Blog: http://astropy.org/astroquery-blog
.. _API: http://astroquery.readthedocs.io/en/latest/api.html
