Astroquery
==========


Introduction
------------

Astroquery is a set of tools for querying astronomical web forms and databases.

There are two other packages with complimentary functionality as Astroquery:
`pyvo <https://pyvo.readthedocs.io/en/latest/>`_ is an Astropy affiliated package, and
`Simple-Cone-Search-Creator <https://github.com/tboch/Simple-Cone-Search-Creator/>`_ to
generate a cone search service complying with the
`IVOA standard <http://www.ivoa.net/documents/latest/ConeSearch.html>`_.
They are more oriented to general `virtual observatory <http://www.virtualobservatory.org>`_
discovery and queries, whereas Astroquery has web service specific interfaces.

Using astroquery
----------------

All astroquery modules are supposed to follow the same API.  In its simplest form, the API involves
queries based on coordinates or object names.  Some simple examples, using SIMBAD:

.. doctest-remote-data::

    >>> from astroquery.simbad import Simbad
    >>> result_table = Simbad.query_object("m1")
    >>> result_table.pprint()

    main_id    ra     dec   coo_err_maj coo_err_min coo_err_angle coo_wavelength     coo_bibcode     matched_id
              deg     deg       mas         mas          deg
    ------- ------- ------- ----------- ----------- ------------- -------------- ------------------- ----------
      M   1 83.6324 22.0174      5000.0      5000.0            90              X 2022A&A...661A..38P      M   1

All query tools allow coordinate-based queries:

.. doctest-remote-data::

    >>> from astropy import coordinates
    >>> import astropy.units as u
    >>> c = coordinates.SkyCoord("05h35m17.3s -05d23m28s", frame='icrs')
    >>> r = 5 * u.arcminute
    >>> result_table = Simbad.query_region(c, radius=r)
    >>> result_table.pprint(show_unit=True, max_width=80, max_lines=5)
              main_id                  ra       ...     coo_bibcode
                                      deg       ...
    ---------------------------- -------------- ... -------------------
    ALMA J053514.4142-052220.792  83.8100591667 ... 2023MNRAS.522...56V
                             ...            ... ...                 ...
         2MASS J05351163-0522515 83.79846499816 ... 2020yCat.1350....0G
                     [H97b] 9009 83.79990004111 ... 2020yCat.1350....0G
    Length = 3324 rows

For additional guidance and examples, read the documentation for the individual services, indexed :doc:`alphabetically<services_alph>`, or by :doc:`type<services_type>`.

.. _default_config:

Default configuration file
--------------------------

To customize this, copy the default configuration to ``$HOME/.astropy/config/astroquery.cfg``,
uncomment the relevant configuration item(s), and insert your desired value(s).

.. toctree::
  :maxdepth: 1

  configuration


.. _astroquery_cache:
 
Caching
-------

By default Astroquery employs query caching with a timeout of 1 week.
The user can clear their cache at any time, as well as suspend cache usage,
and change the cache location. Caching persists between Astroquery sessions.
If you know the service you are using has released new data recently, or if you believe you are
not receiving the newest data, try clearing the cache.

Service specific settings
^^^^^^^^^^^^^^^^^^^^^^^^^

The Astroquery cache location is specific to individual services,
so each service's cache should be managed individually.
The cache location can be viewed with the following command
(using :ref:`VizieR <astroquery.vizier>` as an example):

.. code-block:: python

    >>> from astroquery.vizier import Vizier
    >>> print(Vizier.cache_location)   # doctest: +IGNORE_OUTPUT
    /Users/username/.astropy/cache/astroquery/Vizier

Each service's cache is cleared with the ``clear_cache`` function within that service.

.. code-block:: python

    >>> import os
    >>> from astroquery.vizier import Vizier
    ...
    >>> os.listdir(Vizier.cache_location)   # doctest: +IGNORE_OUTPUT
    ['8abafe54f49661237bdbc2707179df53b6ee0d74ca6b7679c0e4fac0.pickle',
    '0e4766a7673ddfa4adaee2cfa27a924ed906badbfae8cc4a4a04256c.pickle']
    >>> Vizier.clear_cache()
    >>> os.listdir(Vizier.cache_location)   # doctest: +IGNORE_OUTPUT
    []

Astroquery-wide settings
^^^^^^^^^^^^^^^^^^^^^^^^

Whether caching is active and when cached files expire are controlled centrally through the
astroquery ``cache_conf`` module, and shared among all services.
Astroquery uses the Astropy configuration infrastructure, information about
temporarily or permanently changing configuration values can be found
`here <https://docs.astropy.org/en/latest/config/index.html>`_.

.. code-block:: python

  >>> from astroquery import cache_conf
  ...
  >>> # Is the cache active?
  >>> print(cache_conf.cache_active)
  True
  >>> # Cache timout in seconds
  >>> print(cache_conf.cache_timeout)
  604800
