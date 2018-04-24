*****
astroquery.cds
*****

The cds query package allows you to query the cds to retrieve datasets satisfying specific constraints. Constraints can be spatial (i.e. you can ask for all the catalogs, images, cubes having entries in a user defined cone, moc or polygon) or acting on specific dataset properties (you can ask for only the catalogs coming from the CDS).

The cds query package follows the astroquery template for adding new query services.

=======
License
=======

The cds query package is distributed under the BSD 3-Clause License.

============
Requirements
============

``astroquery``, ``astropy``, ``pytest``, ``mocpy``, ``regions``, ``pyvo`` are required.

See the environment.yml file.

===========
Examples
===========

You can run example1.ipynb and example2.ipynb giving examples on how to use astroquery.cds to
query the cds with different type of constraints.

.. image:: https://mybinder.org/badge.svg 
    :target: https://mybinder.org/v2/gh/cds-astro/astroquery.cds/master

Launch the Binder to execute live and interact with the notebooks examples.  

=====
Tests
=====

You can run the tests with ``pytest`` by executing the following command in the root's repository:

    python -m pytest cds
