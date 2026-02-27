
**********************************
Observations - Query for APEX Data
**********************************

APEX observations can be discovered via the standard
archive query interfaces for reduced and raw data:

- reduced data: :meth:`~astroquery.eso.EsoClass.query_surveys`
- raw data: :meth:`~astroquery.eso.EsoClass.query_main`
- raw (instrument-specific): :meth:`~astroquery.eso.EsoClass.query_instrument`

In addition, :meth:`~astroquery.eso.EsoClass.query_apex_quicklooks` provides a
dedicated interface to retrieve APEX Quick Look products. These Quick Looks are
distributed as ``.tar`` bundles that typically include diagnostic material
(e.g. plots and logs) and ``class`` (``.apex``) files; for heterodyne
observations, the calibrated ``.class`` product is often the most practical
starting point, and the accompanying uncalibrated ``.fits`` files are usually
not required.

The archive contains APEX observations from July 11, 2005 onward. This notebook
walks through a practical workflow to identify, query, and download APEX Quick
Look products. As an example, we use APEX observations from the ALCOHOLS survey
(12CO(3–2) line emission in the Milky Way) available in the ESO Archive. We
first locate the reduced survey products, then use an instrument-specific query
to identify the corresponding raw datasets, and finally retrieve the associated
Quick Look bundles. This indirection is sometimes necessary because Quick Look
queries may require the APEX project ID (distinct from the ESO proposal - aka
programme - ID). If the APEX project ID is known (e.g. for proprietary data),
Quick Look products can be queried directly.

Query Reduced APEX data
=======================

We first query for the reduced data from the **ALCOHOLS** survey, and retrieve
the ESO proposal ID.

.. doctest-remote-data::

    >>> # query the ESO archive for the ALCOHOLS survey
    >>> table_reduced = eso.query_surveys("ALCOHOLS") 

    >>> # extract unique ESO run IDs from the query result
    >>> # (the survey table actually contains ESO run IDs)
    >>> run_ids = list(set(table_reduced["proposal_id"]))
    
    >>> # check if we have a single run ID or multiple
    >>> if len(run_ids) == 1:
    ...     run_id = run_ids[0]
    ... else:
    ...     print("Warning: Multiple proposal IDs found...")
    ...     run_id = run_ids[0]
    
    >>> # Extract the proposal (aka programme) ID from the run ID
    >>> def proposal_remove_run(run_id):
    ...     proposal_id = ".".join(run_id.split(".", 2)[:2])
    ...     proposal_id = ".".join(proposal_id.split("(")[:1])
    ...     return proposal_id

    >>> proposal_id = proposal_remove_run(run_id)
    >>> print(f"Proposal ID: {proposal_id}")
    Proposal ID: 094.C-0935

Note that multiple values of ``proposal_id`` may be returned,
which would require minor changes to the above example to loop through all
relevant IDs.

Available Query Constraints
===========================

As always, it is good practice to check the available columns to search in the instrument-specific query.

.. doctest-remote-data::

    >>> eso.query_instrument("APEX", help=True) 
    INFO: 
    Columns present in the table ist.APEX:
       column_name    datatype    xtype     unit
    ----------------- -------- ----------- -----
       access_estsize     long             kbyte
           access_url     char                  
                 bwid    float               GHz
             channels      int                  
         datalink_url     char                  
             date_obs     char                  
                  ...      
         tel_airm_end    float                  
       tel_airm_start    float                  
              tel_alt    float               deg
               tel_az    float               deg
            telescope     char                  
             wobcycle    float                 s
             wobthrow    float               deg
              wobused     char                  
    Number of records present in the table ist.APEX:
    913029
     [astroquery.eso.core]

Query Raw APEX data
===================

We now query for raw data from the APEX instrument, using the ESO proposal ID
retrieved from the previous query.

.. doctest-remote-data::
    
    >>> # query the APEX instrument for data related to the ESO proposal ID
    >>> table_raw = eso.query_instrument("APEX", column_filters={"prog_id": f"like '{proposal_id}%'"})  

    >>> # extract unique APEX project IDs from the raw data query
    >>> project_id = list(set(table_raw["project_id"])) 

    >>> # assuming we only have one project ID 
    >>> project_id = project_id[0] 
    >>> print(f"Project ID: {project_id}")
    Project ID: E-094.C-0935A-2014

In this case, we know there is only **one** APEX project ID, but if there were
multiple IDs, we would need to loop through them.

.. tip::
    In the :meth:`~astroquery.eso.EsoClass.query_surveys` query, the
    ``"proposal_id"`` column refers to the ESO program/run ID. Whereas, in
    :meth:`~astroquery.eso.EsoClass.query_instrument`, it is the ``"prog_id"``
    column that refers to the ESO program/run ID (the proposal ID can be
    extracted from the run ID), and ``"project_id"`` refers to the APEX project
    ID. This is the value used to identify APEX Quick Look products (see
    below).

Query APEX Quick Look products
==============================

We can check the available columns to search in the query.

.. doctest-remote-data::

    >>> eso.query_apex_quicklooks(help=True)
    INFO: 
    Columns present in the table ist.apex_quicklooks:
      column_name   datatype   xtype    unit
    --------------- -------- --------- -----
     access_estsize     long           kbyte
         access_url     char                
         instrument     char                
    instrument_type     char                
            partner     char                
             pi_coi     char                
            prog_id     char                
         prog_title     char                
          prog_type     char                
         project_id     char                
       quicklook_id     char                
       release_date     char timestamp      
    Number of records present in the table ist.apex_quicklooks:
    282296
     [astroquery.eso.core]

And now, use :meth:`~astroquery.eso.EsoClass.query_apex_quicklooks` to query
for the APEX Quick Look products using the APEX project ID
(``project_id``) we retrieved from the previous query.

.. doctest-remote-data::

    >>> table_quicklooks = eso.query_apex_quicklooks(project_id) 
    >>> table_quicklooks  
    <Table length=15>
    access_estsize                               access_url                               instrument instrument_type partner ...                                    prog_title                                   prog_type     project_id             quicklook_id              release_date      
        kbyte                                                                                                                ...                                                                                                                                                                  
        int64                                      object                                   object        object      object ...                                      object                                       object        object                  object                    object         
    -------------- ---------------------------------------------------------------------- ---------- --------------- ------- ... ------------------------------------------------------------------------------- --------- ------------------ --------------------------- ------------------------
            846755 https://dataportal.eso.org/dataPortal/file/E-094.C-0935A.2014DEC10.TAR    APEXHET      Heterodyne     ESO ... The APEX Large CO Heterodyne Outflow Legacy Supercam survey of Orion (ALCOHOLS)    Normal E-094.C-0935A-2014 E-094.C-0935A.2014DEC10.TAR 2014-12-10T07:05:44.397Z
               ...                                                                    ...        ...             ...     ... ...                                                                             ...       ...                ...                         ...                      ...
          40963041 https://dataportal.eso.org/dataPortal/file/E-094.C-0935A.2015AUG07.TAR    APEXHET      Heterodyne     ESO ... The APEX Large CO Heterodyne Outflow Legacy Supercam survey of Orion (ALCOHOLS)    Normal E-094.C-0935A-2014 E-094.C-0935A.2015AUG07.TAR 2015-04-25T18:41:53.900Z
              6389 https://dataportal.eso.org/dataPortal/file/E-094.C-0935A.2015AUG22.TAR    APEXHET      Heterodyne     ESO ... The APEX Large CO Heterodyne Outflow Legacy Supercam survey of Orion (ALCOHOLS)    Normal E-094.C-0935A-2014 E-094.C-0935A.2015AUG22.TAR 2015-04-25T18:41:53.900Z


As can be seen from the output above, there is one APEX Quick Look product
available per UT date, per APEX project ID. Also note that the APEX Quick Look
products are available in ``.tar`` format (e.g.
``E-094.C-0935A.2014DEC10.TAR``), which can be downloaded and extracted (see
below).

Download APEX Quick Look products
=================================

Finally, we can download the APEX Quick Look products using the :meth:`~astroquery.eso.EsoClass.retrieve_data` method:

.. doctest-remote-data::

    >>> eso.retrieve_data(table_quicklooks[0]["quicklook_id"])  
