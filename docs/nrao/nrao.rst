.. doctest-skip-all
.. # Skip tests in this file until the new API is implemented:
.. # https://github.com/astropy/astroquery/issues/2316

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

.. doctest-remote-data::

    >>> from astroquery.nrao import Nrao
    >>> import astropy.coordinates as coord
    >>> result_table = Nrao.query_region("04h33m11.1s 05d21m15.5s")
    >>> print(result_table)
      Source      Project        Start Time     ...      DEC      ARCH_FILE_ID
                                    days        ...    degrees
    ---------- ------------- ------------------ ... ------------- ------------
         3C120 AD0094-public 83-Sep-27 09:19:30 ... +05d21'15.47"    181905160
         3C120 AD0094-public 83-Sep-27 09:19:30 ... +05d21'15.47"    181905160
         3C120 AD0094-public 83-Sep-27 09:23:40 ... +05d21'15.47"    181905160
         3C120 AD0094-public 83-Sep-27 09:23:40 ... +05d21'15.47"    181905160
         3C120 AD0094-public 83-Sep-27 09:28:30 ... +05d21'15.47"    181905160
         3C120 AD0094-public 83-Sep-27 09:28:30 ... +05d21'15.47"    181905160
         3C120 AW0092-public 83-Oct-02 06:13:49 ... +05d21'15.47"    181905179
         3C120 AW0092-public 83-Oct-02 06:13:49 ... +05d21'15.47"    181905179
         3C120 AW0092-public 83-Oct-02 06:15:49 ... +05d21'15.47"    181905179
         3C120 AW0092-public 83-Oct-02 06:15:49 ... +05d21'15.47"    181905179
           ...           ...                ... ...           ...          ...
    J0433+0521  16B-353-lock 17-Jan-03 05:58:26 ... +05d21'15.62"    536739153
    J0433+0521  16B-353-lock 17-Jan-03 05:58:26 ... +05d21'15.62"    536739153
    J0433+0521  16B-353-lock 17-Jan-03 05:58:26 ... +05d21'15.62"    536739153
    J0433+0521  16B-353-lock 17-Jan-03 05:58:26 ... +05d21'15.62"    536739153
    J0433+0521  16B-353-lock 17-Jan-03 05:58:26 ... +05d21'15.62"    536739153
    J0433+0521  16B-353-lock 17-Jan-03 05:58:26 ... +05d21'15.62"    536739153
    J0433+0521  16B-353-lock 17-Jan-03 05:58:26 ... +05d21'15.62"    536739153
    J0433+0521  16B-353-lock 17-Jan-03 05:58:26 ... +05d21'15.62"    536739153
    J0433+0521  16B-353-lock 17-Jan-03 05:58:26 ... +05d21'15.62"    536739153
    J0433+0521  16B-353-lock 17-Jan-03 05:58:26 ... +05d21'15.62"    536739153
    Length = 1614 rows


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

.. doctest-remote-data::

    >>> from astroquery.nrao import Nrao
    >>> import astropy.units as u
    >>> import astropy.coordinates as coord
    >>> result_table = Nrao.query_region(coord.SkyCoord(68.29625,
    ... 5.35431,  unit=(u.deg, u.deg), frame='icrs'), radius=2*u.arcmin,
    ... telescope='historical_vla', start_date='1985-06-30 18:16:49',
    ... end_date='1985-06-30 18:20:19', freq_low=1600*u.MHz, freq_up=1700*u.MHz,
    ... telescope_config='BC', sub_array=1)
    >>> print(result_table)
     Source     Project        Start Time     ...      DEC      ARCH_FILE_ID
                                  days        ...    degrees
    -------- ------------- ------------------ ... ------------- ------------
    0430+052 AR0122-public 85-Jun-30 18:16:49 ... +05d21'15.47"    181888822
    0430+052 AR0122-public 85-Jun-30 18:16:49 ... +05d21'15.47"    181888822
    0430+052 AR0122-public 85-Jun-30 18:17:30 ... +05d21'15.47"    181888825
    0430+052 AR0122-public 85-Jun-30 18:17:59 ... +05d21'15.47"    181888828
    0430+052 AR0122-public 85-Jun-30 18:17:59 ... +05d21'15.47"    181888828


Reference/API
=============

.. automodapi:: astroquery.nrao
    :no-inheritance-diagram:

.. _IAU format: http://cdsweb.u-strasbg.fr/Dic/iau-spec.html.
