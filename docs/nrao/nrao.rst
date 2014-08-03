.. doctest-skip-all

.. _astroquery.nrao:

********************************
NRAO Queries (`astroquery.nrao`)
********************************

Getting started
===============

This module supports fetching the table of observation summaries from the NRAO
data archive. The results are returned in a `~astropy.table.Table`. The service
can be queried using the :meth:`~astroquery.nrao.NraoClass.query_region`. The
only required argument to this is the target around which to query. This may be
specified either by using the identifier name directly - this is resolved via
astropy functions using online services. The coordinates may also be specified
directly using the appropriate coordinate system from
`astropy.coordinates`. Here is a basic example:

.. code-block:: python

    >>> from astroquery.nrao import Nrao
    >>> import astropy.coordinates as coord
    >>> result_table = Nrao.query_region("04h33m11.1s 05d21m15.5s")
    >>> print(result_table)
    
      Source     Project    Start Time Stop Time ...  RA DEC ARCH_FILE_ID
    ---------- ------------ ---------- --------- ... --- --- ------------
      0430+052  SRAM-public         --        -- ...  --  --    181927539
      0430+052  SRAM-public         --        -- ...  --  --    181927647
      0430+052  SRAM-public         --        -- ...  --  --    181927705
         3C120  BALI-public         --        -- ...  --  --    181927008
         3C120  BALI-public         --        -- ...  --  --    181927008
         3C120  BALI-public         --        -- ...  --  --    181927010
         3C120  BALI-public         --        -- ...  --  --    181927016
         3C120  BALI-public         --        -- ...  --  --    181927024
           ...          ...        ...       ... ... ... ...          ...
    J0433+0521 13A-281-lock         --        -- ...  --  --    424632771
    J0433+0521 13A-281-lock         --        -- ...  --  --    424632771
    J0433+0521 13A-281-lock         --        -- ...  --  --    424632771
    J0433+0521 13A-281-lock         --        -- ...  --  --    424632771
    J0433+0521 13A-281-lock         --        -- ...  --  --    424632771
    J0433+0521 13A-281-lock         --        -- ...  --  --    424632771
    J0433+0521 13A-281-lock         --        -- ...  --  --    424632771

More detailed parameters
------------------------

There are several other optional parameters that may also be specified. For
instance the ``radius`` may be specified via `~astropy.units.Quantity` object or a
string acceptable be `~astropy.coordinates.Angle`. By default this is set to 1
degree. ``equinox`` may be set to 'J2000' or 'B1950' for equatorial systems, the
default being 'J2000'. You can also specify the ``telescope`` from which to fetch
the observations. This can be one of the following. ::

    'gbt' 'all' 'historical_vla' 'vlba' 'jansky_vla'

Another parameter is the ``telescope_config``. Valid values are ::


     'all' 'A' 'AB' 'BnA' 'B' 'BC' 'CnB' 'C' 'CD' 'DnC' 'D'  'DA'                

You may also specify the range of frequencies for the observation by specifying
the ``freq_low`` and ``freq_up`` in appropriate units of frequency via
`astropy.units`. The other optional parameters are the ``sub_array`` which may be
set to 'all' or any value from 1 to 5. Finally you may also set the frequency
bands for observation ::

     'all' '4' 'P' 'L' 'S'  'C' 'X' 'U' 'K' 'Ka' 'Q' 'W'

Here's an example with all these optional parameters.

.. code-block:: python

   >>> from astroquery.nrao import Nrao
   >>> import astropy.units as u
   >>> import astropy.coordinates as coord
   >>> result_table = Nrao.query_region(coord.SkyCoord(68.29625,
   ... 5.35431,  unit=(u.deg, u.deg), frame='icrs'), radius=2*u.arcmin,
   ... telescope='historical_vla', start_date='1985-06-30 18:16:49',
   ... end_date='1985-06-30 18:20:19', freq_low=1600*u.MHz, freq_up=1700*u.MHz,
   ... telescope_config='BC', sub_array=1)
   >>> print(result_table)
   
   Source     Project    Start Time Stop Time ...  RA DEC ARCH_FILE_ID
    -------- ------------- ---------- --------- ... --- --- ------------
    0430+052 AR0122-public         --        -- ...  --  --    181888822
    0430+052 AR0122-public         --        -- ...  --  --    181888822


Reference/API
=============

.. automodapi:: astroquery.nrao
    :no-inheritance-diagram:

.. _IAU format: http://cdsweb.u-strasbg.fr/Dic/iau-spec.html.
