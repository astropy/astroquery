
****************
Mission Searches
****************

Mission-Specific Search Queries
===============================

These queries allow for searches based on mission-specific metadata for a given
data collection.  Currently it provides access to a broad set of Hubble Space
Telescope (HST) metadata, including header keywords, proposal information, and
observational parameters.  The available metadata includes all information that
was previously available in the original HST web search form, and are present in
the current `Mission Search interface <https://mast.stsci.edu/search/ui/#/hst>`__.

**Note:** this API interface does not yet support data product download, only
metadata earch access.

An object of MastMissions class is instantiated with a default mission of 'hst' and
default service set to 'search'.

.. doctest-remote-data::

   >>> from astroquery.mast import MastMissions
   >>> missions = MastMissions()
   >>> missions.mission
   'hst'
   >>> missions.service
   'search'

The missions object can be used to search metadata using by sky position, or other criteria.
The keyword arguments can be used to specify output characteristics like selec_cols and
sort_by and conditions that filter on values like proposal id, pi last name etc.
The available column names for a mission are returned by the
`~astroquery.mast.MastMissionsClass.get_column_list` function.

.. doctest-remote-data::

   >>> from astroquery.mast import MastMissions
   >>> missions = MastMissions(mission='hst')
   >>> columns = missions.get_column_list()

For positional searches, the columns "ang_sep", "sci_data_set_name", "search_key" and "search_position"
will always be included, in addition to any columns specified using "select_cols". For non-positional
searches, "search_key" and "sci_data_set_name" will always be included, in addition to any columns
specified using "select_cols".

For a non positional search, ``select_cols`` would always include ``'search_key'`` and ``'sci_data_set_name'``.

.. doctest-remote-data::

   >>> from astroquery.mast import MastMissions
   >>> from astropy.coordinates import SkyCoord
   >>> missions = MastMissions(mission='hst')
   >>> regionCoords = SkyCoord(210.80227, 54.34895, unit=('deg', 'deg'))
   >>> results = missions.query_region(regionCoords, radius=3, sci_pep_id=12556,
   ...                                 select_cols=["sci_stop_time", "sci_targname", "sci_start_time", "sci_status"],
   ...                                 sort_by=['sci_targname'])
   >>> results[:5]   # doctest: +IGNORE_OUTPUT
   <Table masked=True length=5>
    sci_status   sci_targname   sci_data_set_name       ang_sep        sci_pep_id     search_pos     sci_pi_last_name          search_key
       str6         str16              str9              str20           int64          str18              str6                  str27
    ---------- ---------------- ----------------- -------------------- ---------- ------------------ ---------------- ---------------------------
        PUBLIC NUCLEUS+HODGE602         OBQU010H0 0.017460048037303017      12556 210.80227 54.34895           GORDON 210.80227 54.34895OBQU010H0
        PUBLIC NUCLEUS+HODGE602         OBQU01050 0.017460048037303017      12556 210.80227 54.34895           GORDON 210.80227 54.34895OBQU01050
        PUBLIC NUCLEUS+HODGE602         OBQU01030 0.022143836477276503      12556 210.80227 54.34895           GORDON 210.80227 54.34895OBQU01030
        PUBLIC NUCLEUS+HODGE602         OBQU010F0 0.022143836477276503      12556 210.80227 54.34895           GORDON 210.80227 54.34895OBQU010F0
        PUBLIC NUCLEUS+HODGE602         OBQU010J0  0.04381046755938432      12556 210.80227 54.34895           GORDON 210.80227 54.34895OBQU010J0

for paging through the results, offset and limit can be used to specify the starting record and the number
of returned records. the default values for offset and limit is 0 and 5000 respectively.

.. doctest-remote-data::

   >>> from astroquery.mast import MastMissions
   >>> from astropy.coordinates import SkyCoord
   >>> missions = MastMissions()
   >>> results = missions.query_criteria(sci_start_time=">=2021-01-01 00:00:00",
   ...                                   select_cols=["sci_stop_time", "sci_targname", "sci_start_time", "sci_status", "sci_pep_id"],
   ...                                   sort_by=['sci_pep_id'], limit=1000, offset=1000)  # doctest: +IGNORE_WARNINGS
   ... # MaxResultsWarning('Maximum results returned, may not include all sources within radius.')
   >>> len(results)
   1000

Metadata queries can also be performed using object names with the
~astroquery.mast.MastMissionsClass.query_object function.

.. doctest-remote-data::

   >>> results = missions.query_object('M101', radius=3, select_cols=["sci_stop_time", "sci_targname", "sci_start_time", "sci_status"],
   ...                                 sort_by=['sci_targname'])
   >>> results[:5]  # doctest: +IGNORE_OUTPUT
   <Table masked=True length=5>
        ang_sep           search_pos     sci_status          search_key               sci_stop_time        sci_targname       sci_start_time       sci_data_set_name
        str20              str18           str6               str27                      str26               str16               str26                   str9
   ------------------ ------------------ ---------- --------------------------- -------------------------- ------------ -------------------------- -----------------
   2.751140575012458  210.80227 54.34895     PUBLIC 210.80227 54.34895LDJI01010 2019-02-19T05:52:40.020000   +164.6+9.9 2019-02-19T00:49:58.010000         LDJI01010
   0.8000626246647815 210.80227 54.34895     PUBLIC 210.80227 54.34895J8OB02011 2003-08-27T08:27:34.513000   ANY        2003-08-27T07:44:47.417000         J8OB02011
   1.1261718338567348 210.80227 54.34895     PUBLIC 210.80227 54.34895J8D711J1Q 2003-01-17T00:50:22.250000   ANY        2003-01-17T00:42:06.993000         J8D711J1Q
   1.1454431087675097 210.80227 54.34895     PUBLIC 210.80227 54.34895JD6V01012 2017-06-15T18:33:25.983000   ANY        2017-06-15T18:10:12.037000         JD6V01012
   1.1457795862361977 210.80227 54.34895     PUBLIC 210.80227 54.34895JD6V01013 2017-06-15T20:08:44.063000   ANY        2017-06-15T19:45:30.023000         JD6V01013

Metadata queries can also be performed using non-positional parameters with the
`~astroquery.mast.MastMissionsClass.query_criteria` function.

.. doctest-remote-data::

   >>> results = missions.query_criteria(sci_data_set_name="Z06G0101T", sci_pep_id="1455",
   ...                                   select_cols=["sci_stop_time", "sci_targname", "sci_start_time", "sci_status"],
   ...                                   sort_by=['sci_targname'])
   >>> results[:5]  # doctest: +IGNORE_OUTPUT
   <Table masked=True length=5>
   search_key       sci_stop_time        sci_data_set_name       sci_start_time       sci_targname sci_status
   str9              str26      str9    str26               str19        str6
   ---------- -------------------------- ----------------- -------------------------- ------------ ----------
   Z06G0101T  1990-05-13T11:02:34.567000         Z06G0101T 1990-05-13T10:38:09.193000           --     PUBLIC