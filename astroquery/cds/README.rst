*****
astroquery.cds
*****

The ``cds`` query package allows you to query the CDS to retrieve data sets (i.e. catalogs, images, cubes) satisfying specific constraints. Constraints can be spatial (i.e. you can ask for all data sets having entries in a user defined cone, moc or polygon) or acting on specific data sets properties/meta-data (e.g. you can ask only for catalog data sets which are coming from the CDS).

The ``cds`` query package follows the astroquery template for adding new query services.

=======
License
=======

The ``cds`` query package is distributed under the BSD 3-Clause License.

============
Requirements
============
``cds`` needs the following packages to work :

* ``astroquery``
* ``astropy``
* ``pytest`` : https://docs.pytest.org/en/latest/
* ``mocpy`` : https://github.com/cds-astro/mocpy
* ``regions`` : http://astropy-regions.readthedocs.io/en/latest/
* ``pyvo`` : https://pyvo.readthedocs.io/en/latest/

===========
Examples
===========

Jupyter notebooks have been set up to give some examples on how to use the ``cds`` package to
query the CDS MOC server with different type of constraints. Running the notebooks examples is done in a binder executable environnement.

Binder is a very useful tool allowing people to open jupyter notebooks, run them line by line, modify them... It creates a executable environment for those notebooks so that you can manually interact with them.

For interacting with the notebooks, please follow the link below. You will be redirected to the ``cds-astro/astroquery.cds`` repo where you can launch the notebooks by clicking on them (*.ipynb files) :

.. image:: https://mybinder.org/badge.svg 
    :target: https://mybinder.org/v2/gh/cds-astro/astroquery.cds/master

=====
Tests
=====

You can run the tests following the astropy's recommended way by typing :

    python setup.py test -p cds

Or directly run ``pytest`` by executing the following command in the root's repository:

    python -m pytest astroquery/cds
