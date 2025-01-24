`Documentation`_ | `View on Github`_ |  `Download Development ZIP`_

.. image:: https://img.shields.io/pypi/v/astroquery.svg
    :target: https://pypi.org/project/astroquery/#history
    :alt: Latest PyPI version

.. image:: https://readthedocs.org/projects/astroquery/badge/?version=latest
    :target: https://astroquery.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status

.. image:: https://github.com/astropy/astroquery/workflows/CI/badge.svg
    :target: https://github.com/astropy/astroquery/actions?query=workflow%37ACI
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

Astroquery is an `astropy <https://www.astropy.org>`_ affiliated package that
contains a collection of tools to access online Astronomical data. Each web
service has its own sub-package. For example, to interface with the `SIMBAD
website <https://simbad.cds.unistra.fr/simbad/>`_, use the ``simbad`` sub-package:

.. code-block:: python

    >>> from astroquery.simbad import Simbad
    >>> theta1c = Simbad.query_object('tet01 Ori C')
    >>> theta1c.pprint()
       main_id          ra           dec      ... coo_wavelength     coo_bibcode       matched_id
                       deg           deg      ...
    ------------- ------------- ------------- ... -------------- ------------------- -------------
    * tet01 Ori C 83.8186095697 -5.3897005033 ...              O 2020yCat.1350....0G * tet01 Ori C

Installation and Requirements
-----------------------------

Astroquery works with Python 3.9 or later.
As an `astropy`_ affiliate, astroquery requires `astropy`_ version 5.0 or later.

The latest version of astroquery can be pip installed (note the ``--pre`` for
picking up released developer versions, and ``-U`` for upgrade):

.. code-block:: bash

    $ python -m pip install -U --pre astroquery

To install all the mandatory and optional dependencies add the ``[all]``
identifier to the pip command above (or use ``[docs]`` or ``[test]`` for the
dependencies required to build the documentation or run the tests):

.. code-block:: bash

    $ python -m pip install -U --pre astroquery[all]


To install the 'bleeding edge' version:

.. code-block:: bash

   $ python -m pip install git+https://github.com/astropy/astroquery.git

or cloned and installed from source:

.. code-block:: bash

    $ # If you have a github account:
    $ git clone git@github.com:astropy/astroquery.git
    $ # If you do not:
    $ git clone https://github.com/astropy/astroquery.git
    $ cd astroquery
    $ python -m pip install .

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
Astronomical Journal <https://adsabs.harvard.edu/abs/2019AJ....157...98G>`__.

The BibTeX entry is available from the package itself::

  import astroquery
  astroquery.__citation__


In addition you may also want to refer to specific versions of the
package. We create a separate Zenodo DOI for each version, they can be
looked up at the following `Zenodo page <https://doi.org/10.5281/zenodo.591669>`__


Additional Links
----------------

Maintained by `Adam Ginsburg`_ and `Brigitta Sipocz <https://github.com/bsipocz>`_


.. _Download Development ZIP: https://github.com/astropy/astroquery/zipball/main
.. _View on Github: https://github.com/astropy/astroquery/
.. _Documentation: https://astroquery.readthedocs.io
.. _Adam Ginsburg: https://www.adamgginsburg.com
.. _API: https://astroquery.readthedocs.io/en/latest/api.html
