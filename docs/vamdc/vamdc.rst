.. doctest-skip-all

.. _astroquery.vamdc:

**********************************
Vamdc Queries (`astroquery.vamdc`)
**********************************

Getting Started
===============

The astroquery vamdc interface requires vamdclib_.  The documentation is sparse
to nonexistent, but installation is straightforward::

    pip install https://github.com/keflavich/vamdclib/archive/master.zip

This is the personal fork of the astroquery maintainer that includes astropy's
setup helpers on top of the vamdclib infrastructure.  If the infrastructure is
`merged <https://github.com/VAMDC/vamdclib/pull/1>`_ into the main vamdclib
library, we'll change these instructions.

Examples
========

If you want to compute the partition function, you can do so using a combination
of astroquery and the vamdclib tools::

.. code-block:: python

    >>> from astroquery.vamdc import Vamdc
    >>> ch3oh = Vamdc.query_molecule('CH3OH')
    >>> from vamdclib import specmodel
    >>> partition_func = specmodel.calculate_partitionfunction(ch3oh.data['States'],
                                                               temperature=100)
    >>> print(partition_func)
    {'XCDMS-149': 1185.5304044622881}

Reference/API
=============

.. automodapi:: astroquery.vamdc
    :no-inheritance-diagram:

.. _vamdclib: http://vamdclib.readthedocs.io/en/latest/ 
