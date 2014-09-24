.. doctest-skip-all

.. _astroquery.eso:

******************************
ESO Queries (`astroquery.eso`)
******************************

Getting started
===============

This is a python interface for querying the ESO archive web service.
For now, it supports the following:

- listing available instruments
- listing available surveys (phase 3)
- searching all instrument specific raw data: http://archive.eso.org/cms/eso-data/instrument-specific-query-forms.html
- searching data products (phase 3): http://archive.eso.org/wdb/wdb/adp/phase3_main/form
- downloading data by dataset identifiers: http://archive.eso.org/cms/eso-data/eso-data-direct-retrieval.html


Requirements
============

The following packages are required for the use of this module:

* keyring
* lxml
* requests >= 2.4.0


Authentication with ESO User Portal
===================================

Whereas querying the ESO database is fully open, accessing actual datasets requires
authentication with the ESO User Portal (https://www.eso.org/sso/login).
This authentication is performed directly with the provided :meth:`~astroquery.query.QueryWithLogin.login` command,
as illustrated in the example below. This method uses your keyring to securely
store the password in your operating system. As such you should have to enter your
correct password only once, and later be able to use this package for automated
interaction with the ESO archive.

.. code-block:: python

    >>> from astroquery.eso import Eso
    >>> eso = Eso()
    >>> # First example: TEST is not a valid username, it will fail
    >>> eso.login("TEST") # doctest: +SKIP
    TEST, enter your ESO password:

    Authenticating TEST on www.eso.org...
    Authentication failed!
    >>> # Second example: pretend ICONDOR is a valid username
    >>> eso.login("ICONDOR", store_password=True) # doctest: +SKIP
    ICONDOR, enter your ESO password:

    Authenticating ICONDOR on www.eso.org...
    Authentication successful!
    >>> # After the first login, your password has been stored
    >>> eso.login("ICONDOR") # doctest: +SKIP
    Authenticating ICONDOR on www.eso.org...
    Authentication successful!

Automatic password
------------------

As shown above, your password can be stored by the `keyring
<https://pypi.python.org/pypi/keyring>`_ module, if you
pass the argument ``store_password=False`` to `Eso.login`.
For security reason, storing the password is turned off by default.

MAKE SURE YOU TRUST THE MACHINE WHERE YOU USE THIS FUNCTIONALITY!!!

NB: You can delete your password later with the command
``keyring.delete_password('astroquery:www.eso.org', 'username')``.

Automatic login
---------------

You can further automate the authentication process by configuring a default username.
The astroquery configuration file, which can be found following the procedure
detailed in `astropy.config <http://docs.astropy.org/en/stable/config/index.html>`_,
needs to be edited by adding ``username = ICONDOR`` in the ``[eso]`` section.

When configured, the username in the :meth:`~astroquery.eso.EsoClass.login` call
can be omitted as follows:

.. code-block:: python

    >>> from astroquery.eso import Eso
    >>> eso = Eso()
    >>> eso.login() # doctest: +SKIP
    ICONDOR, enter your ESO password:

NB: If an automatic login is configured, other Eso methods can log you in
automatically when needed.


Query and direct retrieval of instrument specific raw data
==========================================================

Identifying available instruments
---------------------------------

The direct retrieval of datasets is better explained with a running example, continuing from the
authentication example above. The first thing to do is to identify the instrument to query. The
list of available instruments can be queried with the :meth:`~astroquery.eso.EsoClass.list_instruments`
method.

.. code-block:: python

    >>> eso.list_instruments()
    ['fors1', 'fors2', 'vimos', 'omegacam', 'hawki', 'isaac', 'naco', 'visir', 'vircam',
    'apex', 'uves', 'giraffe', 'xshooter', 'crires', 'kmos', 'sinfoni', 'amber', 'midi']

In the example above, 18 instruments are available, they correspond to the instrument listed on
the following web page: http://archive.eso.org/cms/eso-data/instrument-specific-query-forms.html.

Inspecting available query options
----------------------------------

Once an instrument is chosen, ``midi`` in our case, the query options for that instrument can be
inspected by setting the ``help=True`` keyword of the :meth:`~astroquery.eso.EsoClass.query_instrument`
method.

.. code-block:: python

    >>> eso.query_instrument('midi', help=True)
    List of the column_filters parameters accepted by the amber instrument query.
    The presence of a column in the result table can be controlled if prefixed with a [ ] checkbox.
    The default columns in the result table are shown as already ticked: [x].

    Target Information
    ------------------
        target:
        resolver: simbad (SIMBAD name), ned (NED name), none (OBJECT as specified by the observer)
        coord_sys: eq (Equatorial (FK5)), gal (Galactic)
        coord1:
        coord2:
        box:
        format: sexagesimal (Sexagesimal), decimal (Decimal)
    [x] wdb_input_file:

    Observation  and proposal parameters
    ------------------------------------
    [ ] night:
        stime:
        starttime: 01 (01 hrs [UT]), 02 (02 hrs [UT]), 03 (03 hrs [UT]), 04 (04 hrs [UT]), 05 (05 hrs [UT]), 06 (06 hrs [UT]), 07 (07 hrs [UT]), 08 (08 hrs [UT]), 09 (09 hrs [UT]), 10 (10 hrs [UT]), 11 (11 hrs [UT]), 12 (12 hrs [UT]), 13 (13 hrs [UT]), 14 (14 hrs [UT]), 15 (15 hrs [UT]), 16 (16 hrs [UT]), 17 (17 hrs [UT]), 18 (18 hrs [UT]), 19 (19 hrs [UT]), 20 (20 hrs [UT]), 21 (21 hrs [UT]), 22 (22 hrs [UT]), 23 (23 hrs [UT]), 24 (24 hrs [UT])
        etime:
        endtime: 01 (01 hrs [UT]), 02 (02 hrs [UT]), 03 (03 hrs [UT]), 04 (04 hrs [UT]), 05 (05 hrs [UT]), 06 (06 hrs [UT]), 07 (07 hrs [UT]), 08 (08 hrs [UT]), 09 (09 hrs [UT]), 10 (10 hrs [UT]), 11 (11 hrs [UT]), 12 (12 hrs [UT]), 13 (13 hrs [UT]), 14 (14 hrs [UT]), 15 (15 hrs [UT]), 16 (16 hrs [UT]), 17 (17 hrs [UT]), 18 (18 hrs [UT]), 19 (19 hrs [UT]), 20 (20 hrs [UT]), 21 (21 hrs [UT]), 22 (22 hrs [UT]), 23 (23 hrs [UT]), 24 (24 hrs [UT])
    [x] prog_id:
    [ ] prog_type: % (Any), 0 (Normal), 1 (GTO), 2 (DDT), 3 (ToO), 4 (Large), 5 (Short), 6 (Calibration)
    [ ] obs_mode: % (All modes), s (Service), v (Visitor)
    [ ] pi_coi:
        pi_coi_name: PI_only (as PI only), none (as PI or CoI)
    [ ] prog_title:

Only the first two sections, of the parameters accepted by the ``midi`` instrument query,
are shown in the example above: ``Target Information`` and ``Observation and proposal parameters``.

As stated at the beginning of the help message, the parameters accepted by the query are given just before
the first ``:`` sign (e.g. ``target``, ``resolver``, ``stime``, ``etime``...). When a parameter is prefixed
by ``[ ]``, the presence of the associated column in the query result can be controlled.

Note: the instrument query forms can be opened in your web browser directly using the ``show_form`` option of
the :meth:`~astroquery.eso.EsoClass.query_instrument` method. This should also help with the identification of
acceptable keywords.

Querying with constraints
-------------------------

It is now time to query the ``midi`` instrument for datasets. In the following example, observations of
target ``NGC 4151`` between ``2007-01-01`` and ``2008-01-01`` are searched, and the query is configured to
return the observation date column.

.. code-block:: python

    >>> table = eso.query_instrument('midi', column_filters={'target':'NGC 4151', 'stime':'2007-01-01', 'etime':'2008-01-01'}, columns=['night'])
    >>> print(len(table))
    38
    >>> print(table.columns)
    <TableColumns names=('Object','Target Ra Dec','Target l b','DATE OBS','ProgId','DP.ID','OB.ID','OBS.TARG.NAME','DPR.CATG','DPR.TYPE','DPR.TECH','INS.MODE','DIMM S-avg')>
    >>> table.pprint(max_width=100)
             Object              Target Ra Dec           Target l b      ... INS.MODE  DIMM S-avg
    ----------------------- ----------------------- -------------------- ... -------- -----------
                    NGC4151 12:10:32.63 +39:24:20.7 155.076719 75.063247 ... STARINTF 0.69 [0.01]
                    NGC4151 12:10:32.63 +39:24:20.7 155.076719 75.063247 ... STARINTF 0.68 [0.01]
                    NGC4151 12:10:32.63 +39:24:20.7 155.076719 75.063247 ... STARINTF 0.68 [0.01]
                    NGC4151 12:10:32.63 +39:24:20.7 155.076719 75.063247 ... STARINTF 0.69 [0.01]
                    NGC4151 12:10:32.63 +39:24:20.7 155.076719 75.063247 ... STARINTF 0.69 [0.01]
                    NGC4151 12:10:32.63 +39:24:20.7 155.076719 75.063247 ... STARINTF 0.74 [0.01]
                    NGC4151 12:10:32.63 +39:24:20.7 155.076719 75.063247 ... STARINTF 0.69 [0.01]
                    NGC4151 12:10:32.63 +39:24:20.7 155.076719 75.063247 ... STARINTF 0.66 [0.01]
                    NGC4151 12:10:32.63 +39:24:20.7 155.076719 75.063247 ... STARINTF 0.64 [0.01]
                    NGC4151 12:10:32.63 +39:24:20.7 155.076719 75.063247 ... STARINTF 0.60 [0.01]
                    NGC4151 12:10:32.63 +39:24:20.7 155.076719 75.063247 ... STARINTF 0.59 [0.01]
                        ...                     ...                  ... ...      ...         ...
     TRACK,OBJECT,DISPERSED 12:10:32.63 +39:24:20.7 155.076719 75.063247 ... STARINTF 0.70 [0.01]
     TRACK,OBJECT,DISPERSED 12:10:32.63 +39:24:20.7 155.076719 75.063247 ... STARINTF 0.72 [0.01]
    SEARCH,OBJECT,DISPERSED 12:10:32.63 +39:24:20.7 155.076719 75.063247 ... STARINTF 0.62 [0.01]
    SEARCH,OBJECT,DISPERSED 12:10:32.63 +39:24:20.7 155.076719 75.063247 ... STARINTF 0.61 [0.01]
    SEARCH,OBJECT,DISPERSED 12:10:32.63 +39:24:20.7 155.076719 75.063247 ... STARINTF 0.54 [0.01]
    SEARCH,OBJECT,DISPERSED 12:10:32.63 +39:24:20.7 155.076719 75.063247 ... STARINTF 0.53 [0.01]
     TRACK,OBJECT,DISPERSED 12:10:32.63 +39:24:20.7 155.076719 75.063247 ... STARINTF 0.51 [0.01]
     TRACK,OBJECT,DISPERSED 12:10:32.63 +39:24:20.7 155.076719 75.063247 ... STARINTF 0.51 [0.01]
     TRACK,OBJECT,DISPERSED 12:10:32.63 +39:24:20.7 155.076719 75.063247 ... STARINTF 0.51 [0.01]
          PHOTOMETRY,OBJECT 12:10:32.63 +39:24:20.7 155.076719 75.063247 ... STARINTF 0.54 [0.01]
          PHOTOMETRY,OBJECT 12:10:32.63 +39:24:20.7 155.076719 75.063247 ... STARINTF 0.54 [0.01]

And indeed, 38 datasets are found, and the ``DATE OBS`` column is in the result table.

Downloading identified datasets
-------------------------------

Continuing from the previous example, the first two datasets are selected, using their data product IDs ``DP.ID``, and retrieved from the ESO archive.

.. code-block:: python

    >>> data_files = eso.retrieve_data(table['DP.ID'][:2])
    Staging request...
    Downloading files...
    Downloading MIDI.2007-02-07T07:01:51.000.fits.Z...
    Downloading MIDI.2007-02-07T07:02:49.000.fits.Z...
    Done!

The file names, returned in data_files, points to the decompressed datasets (without the .Z extension) that have been locally downloaded.
They are ready to be used with `~astropy.io.fits`.


Obtaining extended information on data products
===============================================

Only a small subset of the keywords presents in the data products can be obtained
with :meth:`~astroquery.eso.EsoClass.query_instrument`.
There is however a way to get the full primary header of the FITS data products,
using :meth:`~astroquery.eso.EsoClass.get_headers`.
This method is detailed in the example below, continuing with the previously obtained table.

.. code-block:: python

    >>> table_headers = eso.get_headers(table['DP.ID'])
    >>> table_headers.pprint()
                 ARCFILE              BITPIX ...   TELESCOP     UTC
    --------------------------------- ------ ... ------------ -------
    MIDI.2007-02-07T07:01:51.000.fits     16 ... ESO-VLTI-U23 25300.5
    MIDI.2007-02-07T07:02:49.000.fits     16 ... ESO-VLTI-U23 25358.5
    MIDI.2007-02-07T07:03:30.695.fits     16 ... ESO-VLTI-U23 25358.5
    MIDI.2007-02-07T07:05:47.000.fits     16 ... ESO-VLTI-U23 25538.5
    MIDI.2007-02-07T07:06:28.695.fits     16 ... ESO-VLTI-U23 25538.5
    MIDI.2007-02-07T07:09:03.000.fits     16 ... ESO-VLTI-U23 25732.5
    MIDI.2007-02-07T07:09:44.695.fits     16 ... ESO-VLTI-U23 25732.5
    MIDI.2007-02-07T07:13:09.000.fits     16 ... ESO-VLTI-U23 25978.5
    MIDI.2007-02-07T07:13:50.695.fits     16 ... ESO-VLTI-U23 25978.5
    MIDI.2007-02-07T07:15:55.000.fits     16 ... ESO-VLTI-U23 26144.5
    MIDI.2007-02-07T07:16:36.694.fits     16 ... ESO-VLTI-U23 26144.5
                                  ...    ... ...          ...     ...
    MIDI.2007-02-07T07:51:13.485.fits     16 ... ESO-VLTI-U23 28190.5
    MIDI.2007-02-07T07:52:27.992.fits     16 ... ESO-VLTI-U23 28190.5
    MIDI.2007-02-07T07:56:21.000.fits     16 ... ESO-VLTI-U23 28572.5
    MIDI.2007-02-07T07:57:35.485.fits     16 ... ESO-VLTI-U23 28572.5
    MIDI.2007-02-07T07:59:46.000.fits     16 ... ESO-VLTI-U23 28778.5
    MIDI.2007-02-07T08:01:00.486.fits     16 ... ESO-VLTI-U23 28778.5
    MIDI.2007-02-07T08:03:42.000.fits     16 ... ESO-VLTI-U23 29014.5
    MIDI.2007-02-07T08:04:56.506.fits     16 ... ESO-VLTI-U23 29014.5
    MIDI.2007-02-07T08:06:11.013.fits     16 ... ESO-VLTI-U23 29014.5
    MIDI.2007-02-07T08:08:19.000.fits     16 ... ESO-VLTI-U23 29288.5
    MIDI.2007-02-07T08:09:33.506.fits     16 ... ESO-VLTI-U23 29288.5
    >>> len(table_headers.columns)
    340

As shown above, for each data product ID (``DP.ID``), the full header (570 columns in our case) of the archive
FITS file is collected. In the above table ``table_headers``, there are as many rows as in the column ``table['DP.ID']``.

Reference/API
=============

.. automodapi:: astroquery.eso
    :no-inheritance-diagram:
