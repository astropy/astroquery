
***************
Troubleshooting
***************

Clearing Cache
==============

If you encounter repeated query failures or see outdated or inconsistent results, you may be dealing with a stale or corrupted local cache. You can clear the entire Astropy cache for ESO with the following command:

.. doctest-skip::

    >>> from astroquery.eso import Eso
    >>> Eso.clear_cache()

This will remove all cached ESO queries and downloaded metadata files. Data products already downloaded will remain unless manually deleted.

.. _column-filters-fix:

Using Correct ``column_filters``
================================

.. note::
    This section applies to ``eso.query_main`` (and, in practice, to
    ``eso.query_instrument`` when using similar ``column_filters`` patterns).
    It is not intended for catalogue queries (``eso.query_catalogue``) or
    direct ObsCore/TAP queries (e.g. ``eso.query_tap`` against ``ivoa.ObsCore``).

If your query fails or silently returns no results, it might be because you're using column names that are **accepted in the ESO web interface (WDB)** but **not supported by the TAP/ADQL interface** that is now used within ``astroquery.eso``. A common case involves using ``stime`` and ``etime``, which are not valid TAP fields. Instead, use ``exp_start``, the TAP-compliant column representing the observation start time. This field supports SQL-style date filtering.

Below are examples of invalid filter usage and their corrected TAP-compatible versions.

Filtering between two dates
---------------------------

❌ Invalid (WDB-specific fields, not recognized by TAP)

.. doctest-skip::

    >>> column_filters = {
    ...    "stime": "2024-01-01 12:00:00",
    ...    "etime": "2024-01-03 12:00:00"
    ...}

✅ Correct (TAP-compliant syntax using 'exp_start')

.. doctest-skip::

    >>> column_filters = {
    ...        "exp_start": "between '2024-01-01 12:00:00' and '2024-01-03 12:00:00'"
    ...    }

OR 

.. doctest-skip::

    >>> column_filters = {
    ...        "exp_start": "between '2024-01-01T12:00:00' and '2024-01-03T12:00:00'"
    ...    }

Filtering with only a start date
--------------------------------

# ❌ Invalid

.. doctest-skip::
    
    >>> column_filters = {
    ...        "stime": "2024-01-01 12:00:00"
    ...    }

# ✅ Correct

.. doctest-skip::

    >>> column_filters = {
    ...        "exp_start": "> '2024-01-01 12:00:00'"
    ...    }

Filtering with only an end date
-------------------------------

# ❌ Invalid

.. doctest-skip::
    
    >>> column_filters = {
    ...        "etime": "2024-12-31 12:00:00"
    ...    }

# ✅ Correct

.. doctest-skip::

    >>> column_filters = {
    ...        "exp_start": "< '2024-12-31 12:00:00'"
    ...    }
