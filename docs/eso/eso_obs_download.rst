
****************************
Observations - Download Data
****************************

Assuming you have already performed a query (e.g., using :meth:`~astroquery.eso.EsoClass.query_surveys`, :meth:`~astroquery.eso.EsoClass.query_instrument`, or :meth:`~astroquery.eso.EsoClass.query_main`) and have a resulting table of data products, you can download the actual datasets using the :meth:`~astroquery.eso.EsoClass.retrieve_data` method. This method takes as input a list of data product IDs (``dp_id``) obtained from the query results.

.. doctest-skip::

    >>> data_files = eso.retrieve_data(table['dp_id'][:2])
    INFO: Downloading datasets ... [astroquery.eso.core]
    INFO: Downloading 2 files ... [astroquery.eso.core]
    INFO: Downloading file 1/2 https://dataportal.eso.org/dataPortal/file/MIDI.2007-02-07T07:01:51.000 to /Users/foobar/.astropy/cache/astroquery/Eso [astroquery.eso.core]
    INFO: Successfully downloaded dataset MIDI.2007-02-07T07:01:51.000 to /Users/foobar/.astropy/cache/astroquery/Eso/MIDI.2007-02-07T07:01:51.000.fits.Z [astroquery.eso.core]
    INFO: Downloading file 2/2 https://dataportal.eso.org/dataPortal/file/MIDI.2007-02-07T07:02:49.000 to /Users/foobar/.astropy/cache/astroquery/Eso [astroquery.eso.core]
    INFO: Successfully downloaded dataset MIDI.2007-02-07T07:02:49.000 to /Users/foobar/.astropy/cache/astroquery/Eso/MIDI.2007-02-07T07:02:49.000.fits.Z [astroquery.eso.core]
    INFO: Uncompressing file /Users/foobar/.astropy/cache/astroquery/Eso/MIDI.2007-02-07T07:01:51.000.fits.Z [astroquery.eso.core]
    INFO: Uncompressing file /Users/foobar/.astropy/cache/astroquery/Eso/MIDI.2007-02-07T07:02:49.000.fits.Z [astroquery.eso.core]
    INFO: Done! [astroquery.eso.core]

    >>> data_files
    ['/Users/foobar/.astropy/cache/astroquery/Eso/MIDI.2007-02-07T07:01:51.000.fits',
     '/Users/foobar/.astropy/cache/astroquery/Eso/MIDI.2007-02-07T07:02:49.000.fits']

The file names returned in ``data_files`` point to the decompressed datasets
(without the .Z extension) that have been locally downloaded. The default location of the decompressed datasets can be adjusted by providing a ``destination`` keyword in the call to :meth:`~astroquery.eso.EsoClass.retrieve_data`.

.. doctest-skip::
    >>> data_files = eso.retrieve_data(table['dp_id'][:2], destination="./eso_data/")

By default, if a requested dataset is already found, it is not downloaded again from the archive.
To force the retrieval of data that are present in the destination directory, use ``continuation=True`` in the call to :meth:`~astroquery.eso.EsoClass.retrieve_data`.

When downloading datasets, you can optionally retrieve associated calibration files by using the ``with_calib`` argument. 
This makes use of the ESO CalSelector service (see the `CalSelector information page <https://archive.eso.org/cms/application_support/calselectorInfo.html>`_).

Available options:

- ``None`` (default): Download only the requested science data.
- ``"raw"``: Include raw calibration files associated with each dataset.
- ``"processed"``: Include processed calibration files (i.e., reduced/calibrated).

.. doctest-skip::

    >>> # Download science data with raw calibrations
    >>> data_files = eso.retrieve_data(table['dp_id'][:2], with_calib="raw")

.. doctest-skip::

    >>> # Download science data with processed calibrations
    >>> data_files = eso.retrieve_data(table['dp_id'][:2], with_calib="processed")
