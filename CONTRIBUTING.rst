Contributing to Astroquery
==========================
The first official release of astroquery occurred in September 2013.

Please refer to `astropy's contributing guidelines` 
`http://www.astropy.org/contribute.html` for a general guide to the
workflow involving git, etc.  Everything below is astroquery-specific.

We strongly encourage draft pull requests to be opened early in development. 
If you are considering contributing a new module, please open a pull request
as soon as you start developing code and mark it as a Draft PR on GitHub.


New Features
------------
We welcome any and all new features!  If you have your own little query tool
that you've written to access some obscure service, feel free to refine it and
submit it as a pull request (PR)!  However, we'll ask you to at least write
some simple tests and do your best to align the API to match the `astroquery API`_.

Tests are welcome and encouraged, but can be developed over time. At least one
example use is necessary for a new module to be accepted.

The template_ module should be the starting point for any new contribution.
It includes detailed explanations of each function and class and can
be filled out straightforwardly.

As shown in the template_ module, the minimum requirements for a new feature are:

* Add the feature as a subdirectory of astroquery with at least an ``__init__.py`` and a ``core.py``::
 
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

Important Guidelines
--------------------

Astroquery is based on the requests module.  All contributions must be based on
the `requests`_ module and should not use `urllib` or any of the base python url
modules unless there is a demonstrated necessity.

he `requests` module should also not be used directly since the `Astroquery.query.BaseQuery` class,
from which all Astroquery classes should inherit, provides access to its own `_request` method.
This custom `_request` method is a wrapper around the `requests.request`
function, providing important Astroquery-specific utilities, including caching,
HTTP header generation, progress bars, and local writing to disk.

Dependencies
------------
New contributions are generally not allowed to introduce additional dependencies.

The astropy ecosystem tools should be used whenever possible.
For example, `astropy.table` should be used for table handling,
and `astropy.units` for unit and quantity
handling.



.. _astroquery API: docs/api.rst
.. _template: docs/template.rst
.. _requests: http://docs.python-requests.org/en/master/
