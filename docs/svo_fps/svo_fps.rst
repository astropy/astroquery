.. _astroquery.svo_fps:

**********************************************************
SVO Filter Profile Service Queries (`astroquery.svo_fps`)
**********************************************************

Getting started
===============

This is a python interface for querying the Spanish Virtual Observatory's
Filter Profile Service (`SVO FPS <https://svo2.cab.inta-csic.es/theory/fps/>`_).
It allows retrieval of filter data (index, transmission data, filter list, etc.)
from the service as astropy tables.

Get index list of all Filters
-----------------------------

The filter index (the properties of all available filters in a wavelength
range) can be listed with
:meth:`~astroquery.svo_fps.SvoFpsClass.get_filter_index`:

.. doctest-remote-data::

    >>> from astropy import units as u
    >>> from astroquery.svo_fps import SvoFps
    >>> index = SvoFps.get_filter_index(12_000*u.angstrom, 12_100*u.angstrom)
    >>> index.info
    <Table length=15>
            name          dtype        unit
    -------------------- ------- ---------------
    FilterProfileService  object
                filterID  object
          WavelengthUnit  object
           WavelengthUCD  object
              PhotSystem  object
            DetectorType  object
                    Band  object
              Instrument  object
                Facility  object
        ProfileReference  object
    CalibrationReference  object
             Description  object
                Comments  object
           WavelengthRef float64        Angstrom
          WavelengthMean float64        Angstrom
           WavelengthEff float64        Angstrom
           WavelengthMin float64        Angstrom
           WavelengthMax float64        Angstrom
                WidthEff float64        Angstrom
           WavelengthCen float64        Angstrom
         WavelengthPivot float64        Angstrom
          WavelengthPeak float64        Angstrom
          WavelengthPhot float64        Angstrom
                    FWHM float64        Angstrom
                    Fsun float64 erg / (A s cm2)
               PhotCalID  object
                  MagSys  object
               ZeroPoint float64              Jy
           ZeroPointUnit  object
                    Mag0 float64
           ZeroPointType  object
               AsinhSoft float64
        TrasmissionCurve  object


If the wavelength range contains too many entries then a ``TimeoutError`` will
occur. A smaller wavelength range might succeed, but if a large range really is
required then you can use the ``timeout`` argument to allow for a longer
response time.

Get list of Filters under a specified Facilty and Instrument
------------------------------------------------------------

Similarly, `~astroquery.svo_fps.SvoFpsClass.get_filter_list` retrieves a list of all
Filters for an arbitrary combination of Facility & Instrument (the Facility
must be specified, but the Instrument is optional).  The data table returned
is of the same form as that from `~astroquery.svo_fps.SvoFpsClass.get_filter_index`:

.. doctest-remote-data::

    >>> filter_list = SvoFps.get_filter_list(facility='Keck', instrument='NIRC2')
    >>> filter_list.info
    <Table length=11>
            name          dtype        unit
    -------------------- ------- ---------------
    FilterProfileService  object
                filterID  object
          WavelengthUnit  object
           WavelengthUCD  object
              PhotSystem  object
            DetectorType  object
                    Band  object
              Instrument  object
                Facility  object
        ProfileReference  object
    CalibrationReference  object
             Description  object
                Comments  object
           WavelengthRef float64        Angstrom
          WavelengthMean float64        Angstrom
           WavelengthEff float64        Angstrom
           WavelengthMin float64        Angstrom
           WavelengthMax float64        Angstrom
                WidthEff float64        Angstrom
           WavelengthCen float64        Angstrom
         WavelengthPivot float64        Angstrom
          WavelengthPeak float64        Angstrom
          WavelengthPhot float64        Angstrom
                    FWHM float64        Angstrom
                    Fsun float64 erg / (A s cm2)
               PhotCalID  object
                  MagSys  object
               ZeroPoint float64              Jy
           ZeroPointUnit  object
                    Mag0 float64
           ZeroPointType  object
               AsinhSoft float64
        TrasmissionCurve  object

Get transmission data for a specific Filter
-------------------------------------------

If you know the ``filterID`` of the filter (which you can determine with
`~astroquery.svo_fps.SvoFpsClass.get_filter_list` or
`~astroquery.svo_fps.SvoFpsClass.get_filter_index`), you can retrieve the
transmission curve data using
`~astroquery.svo_fps.SvoFpsClass.get_transmission_data`:

.. doctest-remote-data::

    >>> data = SvoFps.get_transmission_data('2MASS/2MASS.H')
    >>> print(data)
    Wavelength Transmission
     Angstrom
    ---------- ------------
       12890.0          0.0
       13150.0          0.0
       13410.0          0.0
       13680.0          0.0
       13970.0          0.0
       14180.0          0.0
       14400.0       0.0005
       14620.0 0.0027999999
       14780.0 0.0081000002
       14860.0 0.0286999997
           ...          ...
       18030.0 0.1076999977
       18100.0 0.0706999972
       18130.0 0.0051000002
       18180.0 0.0199999996
       18280.0       0.0004
       18350.0          0.0
       18500.0       0.0001
       18710.0          0.0
       18930.0          0.0
       19140.0          0.0
    Length = 58 rows

These are the data needed to plot the transmission curve for filter:

.. doctest-skip::

    >>> import matplotlib.pyplot as plt
    >>> plt.plot(data['Wavelength'], data['Transmission'])
    >>> plt.xlabel('Wavelength (Angstroms)')
    >>> plt.ylabel('Transmission Fraction')
    >>> plt.title('Filter Curve for 2MASS/2MASS.H')
    >>> plt.show()

.. figure:: images/filter_curve.png
   :scale: 100%
   :alt: Transmission Curve for 2MASS/2MASS.H

   The 2MASS H-band transmission curve


Troubleshooting
===============

If you are repeatedly getting failed queries, or bad/out-of-date results, try clearing your cache:

.. code-block:: python

    >>> from astroquery.svo_fps import SvoFps
    >>> SvoFps.clear_cache()

If this function is unavailable, upgrade your version of astroquery.
The ``clear_cache`` function was introduced in version 0.4.7.dev8479.


Reference/API
=============

.. automodapi:: astroquery.svo_fps
    :no-inheritance-diagram:
