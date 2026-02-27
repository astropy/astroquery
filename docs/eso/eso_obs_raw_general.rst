
*******************************************
Observations - Query for Raw Data (Generic)
*******************************************

.. tip:: 
    The `astroquery.eso` module provides several ways to search for data in
    the ESO Science Archive for raw data. This section focuses on the
    **generic query interface** for raw data
    :meth:`~astroquery.eso.EsoClass.query_main`, while in
    :doc:`the instrument-specific raw-data query section <eso_obs_raw_instrument>`
    we describe **instrument-specific queries** using
    :meth:`~astroquery.eso.EsoClass.query_instrument`.

You may want to query the ESO Archive **without targeting a specific instrument**. This is exactly what the :meth:`~astroquery.eso.EsoClass.query_main` method is designed for. It allows access to the **global raw data table**, which combines metadata across all instruments. 
Internally, this method queries the ``dbo.raw`` table via ESO's `TAP service <https://archive.eso.org/programmatic/#TAP>`_ (or using the :meth:`~astroquery.eso.EsoClass.query_tap` function), which you could also access directly using ADQL with a simple statement like: ``SELECT * FROM dbo.raw``.

Available Query Constraints
===========================

We start by inspecting the available columns that can be queried by :meth:`~astroquery.eso.EsoClass.query_main` with the ``help=True`` keyword. 
This will return a list of all columns available, along with their data types, units, and any additional metadata such as ``xtype`` information.

The output includes column names, data types, units, and, where applicable,
``xtype`` information to indicate more specific column content. The ``xtype``
attribute defines how a string-valued column should be interpreted during
querying. For example, a column with datatype ``char`` may represent a standard
string (``xtype = null``), a timestamp (``xtype = timestamp``), or a sky region
footprint usable in ADQL spatial queries (``xtype = adql:REGION``), with this
interpretation reflected in the ``xtype`` field.

.. doctest-remote-data::

    >>> eso.query_main(help=True)
    INFO: 
    Columns present in the table dbo.raw:
        column_name     datatype    xtype     unit 
    ------------------- -------- ----------- ------
        access_estsize     long              kbyte
            access_url     char                   
          datalink_url     char                   
              date_obs     char                   
                   dec   double                deg
               dec_pnt   double                deg
                   ...
             tpl_start     char                   
    Number of records present in the table dbo.raw:
    36404227
    [astroquery.eso.core]

Query with Constraints (All Instruments)
========================================

To perform a genuinely generic raw-data query, you can combine a cone search
with additional constraints in ``column_filters``. The example below retrieves
all data products from any instrument within 30 arcsec of ``SN2013am``, with a
time constraint specified down to the second.

.. doctest-skip::

    >>> from astropy.coordinates import SkyCoord
    >>> import astropy.units as u

    >>> coords = SkyCoord.from_name("SN2013am")  # The Prawn Nebula
    >>> ra = coords.ra.value
    >>> dec = coords.dec.value
    >>> r = (30 * u.arcsec).to(u.deg).value

    >>> table = eso.query_main(
    ...              cone_ra=ra,
    ...              cone_dec=dec,
    ...              cone_radius=r,
    ...              column_filters={
    ...                  "exp_start": "between '2013-04-12' and '2013-04-12T04:52:06'"
    ...              },
    ...              columns=["object", "ra", "dec", "date_obs", "instrument", "prog_id"],
    ...              )
    >>> table
    <Table length=13>
    object      ra      dec            date_obs            prog_id    instrument
                deg      deg                                                     
    object   float64  float64           object              object      object  
    -------- --------- -------- ------------------------ ------------- ----------
    SN2013AM   169.737 13.05858 2013-04-12T04:12:05.4817 188.D-3003(S)       SOFI
    SN2013AM   169.737 13.05858 2013-04-12T04:22:05.6191 188.D-3003(S)       SOFI
    SN2013AM 169.73717 13.06367 2013-04-12T02:40:17.0744 188.D-3003(S)       SOFI
        SKY 169.73717 13.06922 2013-04-12T02:47:39.0284 188.D-3003(S)       SOFI
        SKY 169.73717 13.06367 2013-04-12T02:48:19.3074 188.D-3003(S)       SOFI
        SKY   169.737  13.0672 2013-04-12T02:49:02.2986 188.D-3003(S)       SOFI
    SN2013AM   169.737 13.05887 2013-04-12T02:51:34.0298 188.D-3003(S)       SOFI
    SN2013AM   169.737 13.06029 2013-04-12T03:09:58.1859 188.D-3003(S)       SOFI
    SN2013AM   169.737 13.06029 2013-04-12T03:15:59.6815 188.D-3003(S)       SOFI
    SN2013AM   169.737 13.05682 2013-04-12T03:34:23.8352 188.D-3003(S)       SOFI
    SN2013AM   169.737 13.05887 2013-04-12T03:41:45.3991 188.D-3003(S)       SOFI
    SN2013AM 169.73717 13.06367 2013-04-12T02:31:32.9840 188.D-3003(S)       SOFI
    SN2013AM 169.73717 13.06367 2013-04-12T02:34:32.7246 188.D-3003(S)       SOFI

Query with Constraints (Specific Instrument)
============================================

If needed, you can still narrow a generic query to a single instrument by
passing ``instruments=...`` to :meth:`~astroquery.eso.EsoClass.query_main`.
For example, to retrieve only ``MIDI`` data products within some time range:

.. doctest-remote-data::

    >>> eso.ROW_LIMIT = -1    # 0 or None to return all results without truncation
    >>> table = eso.query_main(
    ...                     instruments="midi",
    ...                     column_filters={
    ...                         "exp_start": "between '2008-01-01' and '2009-05-12'"}
    ...                     )
    >>> print(len(table))
    58810
    >>> table.colnames
    ['object', 'ra', 'dec', 'dp_id', 'date_obs', 'prog_id',
    'access_estsize', 'access_url', 'datalink_url', ... 'tpl_start']
    >>> table[["object", "ra", "dec", "date_obs", "prog_id"]]
    <Table length=58810>
        object           ra           dec              date_obs          prog_id   
                        deg           deg                                          
        object        float64       float64             object            object   
    -------------- ------------- ------------- ----------------------- ------------
            FLAT -596.52323555 -596.52323555 2008-09-28T06:49:15.000 60.A-9224(A)
            FLAT -596.52323555 -596.52323555 2008-09-28T06:54:23.000 60.A-9224(A)
            FLAT -596.52323555 -596.52323555 2008-09-28T06:59:48.000 60.A-9224(A)
            FLAT -596.52323555 -596.52323555 2008-09-28T07:02:29.000 60.A-9224(A)
            ...           ...           ...                     ...          ...
    WAVE,SPECTEMPL -596.52323555 -596.52323555 2009-01-20T10:21:43.000 60.A-9224(A)
    WAVE,SPECTEMPL -596.52323555 -596.52323555 2009-01-20T10:22:36.000 60.A-9224(A)
            OTHER -596.52323555 -596.52323555 2009-01-20T10:25:35.128 60.A-9224(A)
    WAVE,SPECTEMPL -596.52323555 -596.52323555 2009-01-20T10:26:48.000 60.A-9224(A)
    WAVE,SPECTEMPL -596.52323555 -596.52323555 2009-01-20T10:29:37.000 60.A-9224(A)


Suppose that we have a large query; it may be useful to limit the columns
returned in the results table. This can be done using the ``columns`` argument.
For example, to return only the target name, right ascension, declination,
observation date, and program ID:

.. doctest-remote-data::

    >>> table = eso.query_main(
    ...                     instruments="midi",
    ...                     column_filters={
    ...                         "exp_start": "between '2008-01-01' and '2009-05-12'"},
    ...                     columns=["object", "ra", "dec", "date_obs", "prog_id"]
    ...                     )
    >>> table
    <Table length=58810>
            object               ra           dec              date_obs          prog_id   
                                deg           deg                                          
            object            float64       float64             object            object   
    ----------------------- ------------- ------------- ----------------------- ------------
    SEARCH,OBJECT,DISPERSED    0.49041805      -6.01429 2008-10-27T03:27:44.000 60.A-9224(A)
        PHOTOMETRY,OBJECT    0.49041805      -6.01429 2008-10-27T03:36:04.000 60.A-9224(A)
            COARSE,OBJECT    0.49041805      -6.01429 2008-10-27T03:45:32.000 60.A-9224(A)
                    BIAS -596.52323555 -596.52323555 2008-10-27T06:22:12.388 60.A-9224(A)
                        ...           ...           ...                     ...          ...
                    FLAT -596.52323555 -596.52323555 2009-03-27T09:28:52.000 60.A-9224(A)
                    OTHER -596.52323555 -596.52323555 2009-03-27T09:33:31.378 60.A-9224(A)
                    FLAT -596.52323555 -596.52323555 2009-03-27T09:34:46.000 60.A-9224(A)
                    FLAT -596.52323555 -596.52323555 2009-03-27T09:43:46.000 60.A-9224(A)
                    FLAT -596.52323555 -596.52323555 2009-03-27T09:47:37.000 60.A-9224(A)


Query with Constraints (Multiple Instruments)
=============================================

We can also query for raw data from multiple instruments in a single call to
:meth:`~astroquery.eso.EsoClass.query_main`. For example, to retrieve raw data
from the interferometric instruments ``MIDI``, ``GRAVITY``, and ``PIONIER`` within 10 arcsec of
``ETA CAR``:

.. doctest-remote-data::

    >>> coords = SkyCoord.from_name("ETA CAR")  # Eta Carinae
    >>> ra = coords.ra.value
    >>> dec = coords.dec.value
    >>> r = (10 * u.arcsec).to(u.deg).value 

    >>> table = eso.query_main(
    ...              cone_ra=ra,
    ...              cone_dec=dec,
    ...              cone_radius=r,
    ...              instruments=["midi", "gravity", "pionier"],
    ...              column_filters={
    ...              columns=["instrument", "object", "ra", "dec", "date_obs", "prog_id"]
    ...              )
    >>> print(len(table))
    622
    >>> table[["object", "ra", "dec", "date_obs", "prog_id"]]
    <Table length=622>
    object         ra         dec            date_obs            prog_id    instrument
                    deg         deg                                                     
    object      float64     float64           object              object      object  
    ------------ ------------ --------- ------------------------ ------------- ----------
    ETA CARINAE     161.2603 -59.68441      2016-02-25T05:14:21  60.A-9102(A)    GRAVITY
    ETA CARINAE     161.2603 -59.68441      2016-02-25T06:56:58  60.A-9102(A)    GRAVITY
    ETA CARINAE     161.2603 -59.68441      2016-02-25T09:36:24  60.A-9102(A)    GRAVITY
        ETA_CAR 161.26028194 -59.68442      2017-02-20T08:38:01 098.D-0488(A)    GRAVITY
            ...          ...       ...                      ...           ...        ...
    KAPPA,OBJECT 161.26358805 -59.68441 2015-12-07T07:28:26.1927  60.A-9209(A)    PIONIER
    KAPPA,OBJECT 161.26358805 -59.68441 2015-12-07T07:29:14.3074  60.A-9209(A)    PIONIER
    KAPPA,OBJECT 161.26358805 -59.68441 2015-12-07T07:29:38.4820  60.A-9209(A)    PIONIER
        ETA_CAR 161.26358805 -59.68441 2015-12-07T07:48:38.6025  60.A-9209(A)    PIONIER
        ETA_CAR 161.26358805 -59.68441 2015-12-07T07:52:06.9548  60.A-9209(A)    PIONIER

.. tip::

    Use :meth:`~astroquery.eso.EsoClass.query_main` when you want to search
    **across all instruments**. Use
    :meth:`~astroquery.eso.EsoClass.query_instrument` when you want a more
    **refined, instrument-specific search** (e.g. instrument modes,
    configurations, or ambient conditions).

    .. doctest-remote-data::

        >>> column_filters = {
        ...     "dp_cat": "SCIENCE",           # Science data only
        ...     "ins_opt1_name": "HIGH_SENS",  # High sensitivity mode
        ...     "night_flag": "night",         # Nighttime observations only
        ...     "moon_illu": "< 0",            # No moon (below horizon)
        ...     "lst": "between 0 and 6"       # Local sidereal time early in the night
        ... }
        >>> table = eso.query_instrument("midi", column_filters=column_filters)

Download Data
=============

To download the data returned by the query, you can use the :meth:`~astroquery.eso.EsoClass.retrieve_data` method. This method takes a list of data product IDs (``dp_id``) and downloads the corresponding files from the ESO archive.

.. doctest-remote-data::
    >>> eso.retrieve_data(table["dp_id"])

The ``data_files`` list points to the decompressed dataset filenames that have been locally downloaded. The default location of the decompressed datasets can be adjusted by providing a ``destination`` keyword in the call to :meth:`~astroquery.eso.EsoClass.retrieve_data`.

.. doctest-skip::
    >>> data_files = eso.retrieve_data(table["dp_id"], destination="./eso_data/")

For raw data, you can also retrieve associated calibration files by
passing ``with_calib="raw"`` (or ``with_calib="processed"``). See
:doc:`eso_obs_download` for examples and the related CalSelector terminology.
