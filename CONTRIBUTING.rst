Contributing to Astroquery
==========================
The first official release of astroquery is scheduled for September 2013.
There are therefore two sets of contribution
guidelines below.

Please see `astropy's contributing guildelines
<http://www.astropy.org/contributing.html>`__ for a general guide to the
workflow involving git, etc.  Everything below is astroquery-specific.

Prior to first release
----------------------
We welcome any and all new features!  If you have your own little query tool
you wrote to access some obscure service, feel free to clean it up a little and
submit it as a pull request (PR)!  At this stage, we are mostly looking to be
as inclusive as possible.

Tests are welcome and encouraged, but can be built up over time.  At least one
example use is necessary, however!

The minimum requirements for a new feature are:

 * Add the feature as a subdirectory of astroquery with at least an
   ``__init__.py`` and a ``core.py``::
 
     astroquery/feature
     astroquery/feature/__init__.py
     astroquery/feature/core.py

 * Add a ``tests/`` directory with at least one test::
 
     astroquery/feature/tests
     astroquery/feature/tests/__init__.py
     astroquery/feature/tests/test_feature.py

 * Add some documentation - at least one example, but it can be sparse at first::
 
     docs/astroquery/feature.rst

PRs will not be accepted if tests fail.


After first release
-------------------
Once the first release has occurred, it will be necessary to follow the strict
API guidelines laid out in :doc:`api`.

Still feel free to submit PRs that do not fully follow the guidelines - at
least it will make us aware of the need for a new feature.  However, please be
willing to work with us to make the new feature conform to astroquery
standards: no PRs will be accepted that do not conform.
