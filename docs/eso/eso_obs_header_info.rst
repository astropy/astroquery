
*********************************
Observations - Header Information
*********************************

Only a small subset of the keywords present in the data products can be obtained with the :meth:`~astroquery.eso.EsoClass.query_instrument`, :meth:`~astroquery.eso.EsoClass.query_main`, :meth:`~astroquery.eso.EsoClass.query_surveys`, or :meth:`~astroquery.eso.EsoClass.query_tap` methods.

There is, however, a way to get the full primary header of the FITS data products using :meth:`~astroquery.eso.EsoClass.get_headers`.

.. doctest-remote-data::

    >>> table = eso.query_instrument("midi",
    ...                     column_filters={
    ...                         "date_obs": "between '2008-01-01' and '2008-01-02'"
    ...                     },
    ...                     columns=["object", "date_obs", "dp_id"]
    ...                          )

While the archive query interfaces expose the most commonly used metadata fields,
they do not return the complete FITS headers associated with each data product.
For applications that require access to instrument- or pipeline-specific
keywords, the full primary FITS header can be retrieved directly from the
archive using a dedicated helper method.

.. doctest-remote-data::
    >>> table_headers = eso.get_headers(table["dp_id"][:5])
    >>> table_headers
    <Table length=5>
            DP.ID             SIMPLE BITPIX ...   HIERARCH ESO OCS EXPO8 FNAME1     HIERARCH ESO OCS EXPO9 FNAME1  
            str28              bool  int64  ...               str33                             str33              
    ---------------------------- ------ ------ ... --------------------------------- ---------------------------------
    MIDI.2008-01-01T08:29:16.388   True     16 ...                                                                    
    MIDI.2008-01-01T08:39:38.000   True     16 ...                                                                    
    MIDI.2008-01-01T08:47:35.000   True     16 ...                                                                    
    MIDI.2008-01-01T08:52:00.623   True      8 ... MIDI.2008-01-01T08:51:42.000.fits MIDI.2008-01-01T08:52:00.623.fits
    MIDI.2008-01-01T09:00:10.000   True     16 ... MIDI.2008-01-01T09:00:10.000.fits                                  

As shown above, for each data product ID (``DP.ID``; note that this is equivalent to ``dp_id`` in ``table``), the full primary header (336 columns in our case) of the archive FITS file is collected. In the above table ``table_headers``, there are as many rows as there are entries in the ``table['dp_id']`` column.

.. note:: 

    At present, astroquery returns only the primary header; the rest of the FITS header is not accessible through astroquery yet. Support for returning the entire header is planned for a future version.
