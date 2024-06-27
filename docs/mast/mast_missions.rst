
****************
Mission Searches
****************

Mission-Specific Search Queries
===============================

These queries allow for searches based on mission-specific metadata for a given
data collection.  Currently, it provides access to a broad set of Hubble Space
Telescope (HST) and James Webb Space Telescope (JWST) metadata, including header keywords,
proposal information, and observational parameters.  

**Note:** This API interface does not yet support data product downloads, only
metadata search access.

An object of the ``MastMissions`` class is instantiated with a default mission of ``'hst'`` and
default service set to ``'search'``. The searchable metadata for Hubble encompasses all information that
was previously accessible through the original HST web search form and is now available in
the current `MAST HST Search Form <https://mast.stsci.edu/search/ui/#/hst>`__.

.. doctest-remote-data::

   >>> from astroquery.mast import MastMissions
   >>> missions = MastMissions()
   >>> missions.mission
   'hst'
   >>> missions.service
   'search'

To search for JWST metadata, a ``MastMissions`` object is instantiated with a value of ``'jwst'`` for ``mission``.
The searchable metadata for Webb encompasses all information that is available in
the current `MAST JWST Search Form <https://mast.stsci.edu/search/ui/#/jwst>`__.

.. doctest-remote-data::

   >>> from astroquery.mast import MastMissions
   >>> missions = MastMissions(mission='jwst')
   >>> missions.mission
   'jwst'

The ``missions`` object can be used to search metadata by object name, sky position, or other criteria.
When writing queries, keyword arguments can be used to specify output characteristics and filter on 
values like instrument, exposure type, and principal investigator. The available column names for a 
mission are returned by the `~astroquery.mast.MastMissionsClass.get_column_list` function.

.. doctest-remote-data::

   >>> from astroquery.mast import MastMissions
   >>> missions = MastMissions(mission='hst')
   >>> columns = missions.get_column_list()

Metadata queries can be performed on a particular region in the sky. Passing in a set of coordinates to the 
`~astroquery.mast.MastMissionsClass.query_region` function returns datasets that fall within a
certain radius value of that point. This type of search is also known as a cone search. 

The ``select_cols`` keyword argument specifies a list of columns to be included in the response. 
The ``sort_by`` keyword argument specifies a column (or columns) to sort the results by.

.. doctest-remote-data::

   >>> from astroquery.mast import MastMissions
   >>> from astropy.coordinates import SkyCoord
   >>> missions = MastMissions(mission='hst')
   >>> regionCoords = SkyCoord(210.80227, 54.34895, unit=('deg', 'deg'))
   >>> results = missions.query_region(regionCoords, 
   ...                                 radius=3,
   ...                                 sci_pep_id=12556,
   ...                                 select_cols=["sci_stop_time", "sci_targname", "sci_start_time", "sci_status"],
   ...                                 sort_by=['sci_targname'])
   >>> results[:5]   # doctest: +IGNORE_OUTPUT
   <Table masked=True length=5>
    search_pos     sci_data_set_name   sci_targname         sci_start_time             sci_stop_time              ang_sep        sci_status
   ------------------ ----------------- ---------------- -------------------------- -------------------------- -------------------- ----------
   210.80227 54.34895         OBQU01050 NUCLEUS+HODGE602 2012-05-24T07:51:40.553000 2012-05-24T07:54:46.553000 0.017460048037303017     PUBLIC
   210.80227 54.34895         OBQU010H0 NUCLEUS+HODGE602 2012-05-24T09:17:38.570000 2012-05-24T09:20:44.570000 0.017460048037303017     PUBLIC
   210.80227 54.34895         OBQU01030 NUCLEUS+HODGE602 2012-05-24T07:43:20.553000 2012-05-24T07:46:26.553000 0.022143836477276503     PUBLIC
   210.80227 54.34895         OBQU010F0 NUCLEUS+HODGE602 2012-05-24T09:09:18.570000 2012-05-24T09:12:24.570000 0.022143836477276503     PUBLIC
   210.80227 54.34895         OBQU01070 NUCLEUS+HODGE602 2012-05-24T08:00:00.553000 2012-05-24T08:03:06.553000  0.04381046755938432     PUBLIC

You may notice that the above query returned more columns than were specified in the ``select_cols``
argument. For each mission, certain columns are automatically returned.

* *HST*: For positional searches, the columns ``ang_sep``, ``sci_data_set_name``, and ``search_pos``
  are always included in the query results. For non-positional searches, ``sci_data_set_name`` is always 
  present.

* *JWST*: For every query, the ``ArchiveFileID`` column is always returned.

Searches can also be run on target names with the `~astroquery.mast.MastMissionsClass.query_object` 
function.

.. doctest-remote-data::

   >>> results = missions.query_object('M101', 
   ...                                 radius=3, 
   ...                                 select_cols=["sci_stop_time", "sci_targname", "sci_start_time", "sci_status"],
   ...                                 sort_by=['sci_targname'])
   >>> results[:5]  # doctest: +IGNORE_OUTPUT
   <Table masked=True length=5>
    search_pos     sci_data_set_name sci_targname       sci_start_time             sci_stop_time             ang_sep       sci_status
   ------------------ ----------------- ------------ -------------------------- -------------------------- ------------------ ----------
   210.80243 54.34875         LDJI01010   +164.6+9.9 2019-02-19T00:49:58.010000 2019-02-19T05:52:40.020000 2.7469653000840397     PUBLIC
   210.80243 54.34875         J8OB02011          ANY 2003-08-27T07:44:47.417000 2003-08-27T08:27:34.513000 0.8111299061221189     PUBLIC
   210.80243 54.34875         J8D711J1Q          ANY 2003-01-17T00:42:06.993000 2003-01-17T00:50:22.250000 1.1297984178946574     PUBLIC
   210.80243 54.34875         JD6V01012          ANY 2017-06-15T18:10:12.037000 2017-06-15T18:33:25.983000 1.1541053362381077     PUBLIC
   210.80243 54.34875         JD6V01013          ANY 2017-06-15T19:45:30.023000 2017-06-15T20:08:44.063000   1.15442580192948     PUBLIC

For non-positional metadata queries, use the `~astroquery.mast.MastMissionsClass.query_criteria` 
function. For paging through results, the ``offset`` and ``limit`` keyword arguments can be used
to specify the starting record and the number of returned records. The default values for ``offset``
and ``limit`` are 0 and 5000, respectively.

.. doctest-remote-data::

   >>> results = missions.query_criteria(sci_start_time=">=2021-01-01 00:00:00",
   ...                                   select_cols=["sci_stop_time", "sci_targname", "sci_start_time", "sci_status", "sci_pep_id"],
   ...                                   sort_by=['sci_pep_id'],
   ...                                   limit=1000,
   ...                                   offset=1000)  # doctest: +IGNORE_WARNINGS
   ... # MaxResultsWarning('Maximum results returned, may not include all sources within radius.')
   >>> len(results)
   1000
