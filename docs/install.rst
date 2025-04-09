
Installation
============

Uniquely in the Astropy ecosystem, Astroquery is operating with a **continuous deployment model**.
It means that a release is instantaneously available after a pull request has been merged. These
releases are automatically uploaded to `PyPI <https://pypi.org/project/astroquery/#history>`__,
and therefore the latest version of astroquery can be pip installed.
The version number of these automated releases contain the ``'dev'`` tag, thus pip needs to be told
to look for these releases during an upgrade, using the ``--pre`` install option. If astroquery is
already installed, please make sure you use the ``--upgrade`` (or ``-U``) install option as well.

.. code-block:: bash

    $ python -m pip install -U --pre astroquery

To install all the mandatory and optional dependencies add the ``[all]``
identifyer to the pip command above (or use ``[docs]`` or ``[test]`` for the
dependencies required to build the documentation or run the tests):

.. code-block:: bash

    $ python -m pip install -U --pre astroquery[all]

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
--------------------

The development version can be obtained and installed from github:

.. code-block:: bash

    $ # If you have a github account:
    $ git clone git@github.com:astropy/astroquery.git
    $ # If you do not:
    $ git clone https://github.com/astropy/astroquery.git
    $ cd astroquery
    $ python -m pip install .


To install all the optional dependencies (listed below), add the option
``[all]``. To install dependencies required for running the tests locally
use ``[test]``, and for documentation build ``[docs]``.
If you would like to modify the source, you can install
``astroquery`` in editable mode, which means you don't need to rerun the
install command after you made the changes.

To install all dependencies, including those required for local testing and
building the documentation, in editable mode:

.. code-block:: bash

    $ python -m pip install -e .[all,test,docs]


Requirements
------------

Astroquery works with Python 3.9 or later.

The following packages are required for astroquery installation & use:

* `numpy <https://numpy.org>`_ >= 1.20
* `astropy <https://www.astropy.org>`__ (>=5.0)
* `pyVO`_ (>=1.5)
* `requests <https://requests.readthedocs.io/en/latest/>`_
* `keyring <https://pypi.org/project/keyring>`_
* `Beautiful Soup <https://www.crummy.com/software/BeautifulSoup/>`_
* `html5lib <https://pypi.org/project/html5lib>`_

and for running the tests:

* `curl <https://curl.se/>`__
* `pytest-astropy <https://github.com/astropy/pytest-astropy>`__
* `pytest-rerunfailures <https://github.com/pytest-dev/pytest-rerunfailures>`__

The following packages are optional dependencies and are required for the
full functionality of the `~astroquery.mocserver`, `~astroquery.alma`, and `~astroquery.xmatch` modules:

* `astropy-healpix <https://astropy-healpix.readthedocs.io/en/latest/>`_
* `regions <https://astropy-regions.readthedocs.io/en/latest/>`_
* `mocpy <https://cds-astro.github.io/mocpy/>`_ >= 0.9

For the `~astroquery.vamdc` module:

* `vamdclib <https://github.com/VAMDC/vamdclib/>`_  install version from
  personal fork: ``python -m pip install git+https://github.com/keflavich/vamdclib-1.git``

The following packages are optional dependencies and are required for the
full functionality of the `~astroquery.mast` module:

* `boto3 <https://boto3.amazonaws.com/v1/documentation/api/latest/index.html>`_
