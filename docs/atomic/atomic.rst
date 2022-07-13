.. _astroquery_atomic:

**************************************
Atomic Line List (`astroquery.atomic`)
**************************************

Getting started
===============

"Atomic Line List" is a collection of more than 900,000 atomic transitions
in the range from 0.5 Å to 1000 µm (source_).  ``AtomicLineList`` has 13
parameters of which all are optional. In the example below, only a
restricted set of the available parameters is used to keep it simple:
``wavelength_range``, ``wavelength_type``, ``wavelength_accuracy`` and
``element_spectrum``.  The respective web form for Atomic Line List can be
found at http://www.pa.uky.edu/~peter/atomic/. As can be seen there, the
first form fields are "Wavelength range" and "Unit". Because astroquery
encourages the usage of AstroPy units, the expected type for the parameter
``wavelength_range`` is a tuple with two AstroPy quantities in it. This has
the positive side-effect that even more units will be supported than by just
using the web form directly.

In the following Python session you can see the ``atomic`` package in
action. Note that Hz is actually not a supported unit by Atomic Line List,
the atomic package takes care to support all spectral units.

.. doctest-remote-data::

    >>> from astropy import units as u
    >>> from astroquery.atomic import AtomicLineList
    >>> wavelength_range = (15 * u.nm, 1.5e+16 * u.Hz)
    >>> AtomicLineList.query_object(wavelength_range=wavelength_range, wavelength_type='Air',
    ...                             wavelength_accuracy=20, element_spectrum='C II-IV')
    <Table length=3>
    LAMBDA VAC ANG SPECTRUM  TT  ...  J J      A_ki    LEVEL ENERGY  CM 1
       float64       str4   str2 ...  str5   float64         str18
    -------------- -------- ---- ... ----- ----------- ------------------
          196.8874     C IV   E1 ... 1/2-*  91300000.0 0.00 -   507904.40
          197.7992     C IV   E1 ... 1/2-* 118000000.0 0.00 -   505563.30
          199.0122     C IV   E1 ... 1/2-* 157000000.0 0.00 -   502481.80


Reference/API
=============

.. automodapi:: astroquery.atomic
    :no-inheritance-diagram:

.. _source: http://www.pa.uky.edu/~peter/atomic/documentation.html
