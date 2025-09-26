Developer documentation
-----------------------

The modules and their maintainers are listed on the
`Maintainers <https://github.com/astropy/astroquery/wiki/Maintainers>`_
wiki page.


The :doc:`api` is intended to be kept as consistent as possible, such
that any web service can be used with a minimal learning curve imposed on the
user.

.. toctree::
   :maxdepth: 1

   api.rst
   template.rst
   testing.rst

The following Astroquery modules are mostly meant for internal use of
services in Astroquery, you can use them for your scripts, but we don't guarantee API stability.

.. toctree::
  :maxdepth: 1

  utils.rst
  query.rst
  utils/tap.rst

To debug astroquery, logging level can be configured with the following:

.. doctest-skip::

    >>> from astroquery import log
    >>> log.setLevel(level)

If ``level`` is set to ``"DEBUG"``, then HTTP requests are logged.
If ``level`` is set to ``"TRACE"``, then HTTP requests and responses are logged.
