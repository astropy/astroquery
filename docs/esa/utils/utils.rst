.. _astroquery.esa.utils:

*****************************************
ESA Utils Module (`astroquery.esa.utils`)
*****************************************

The ``astroquery.esa.utils`` module provides the shared infrastructure used by ESA-related services.
It centralizes common logic that is reused across multiple ESA query interfaces migrated to PyVO, reducing code
duplication and ensuring consistent behavior across modules.

At the core of this module is the abstract base class :class:`~astroquery.esa.utils.EsaTap`, which defines common
functionality for interacting with ESA TAP-based services. This class is not intended to be instantiated directly.

The :class:`~astroquery.esa.utils.EsaTap` class provides reusable mechanisms for:

- Authentication and session management with ESA services
  (e.g. :meth:`~astroquery.esa.utils.EsaTap.login` and
  :meth:`~astroquery.esa.utils.EsaTap.logout`)
- Configuration and handling of TAP service endpoints.
- Management of authenticated HTTP requests.
- Common interaction patterns shared by ESA archive and discovery services.

In addition to :class:`~astroquery.esa.utils.EsaTap`, this module includes utility
functions that support ESA modules more generally, such as helpers for file
downloads, request handling, and other low-level operations required by multiple
ESA services.


Reference/API
=============

.. automodapi:: astroquery.esa.utils
    :members:
