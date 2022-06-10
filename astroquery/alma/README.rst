===================
Accessing ALMA data
===================

Data from the `Atacama Large Millimeter/submillimeter Array`_ can be obtained with the AstroQuery ALMA Python client.  This client relies
on the deployed `IVOA`_ services at the ALMA Regional Centres (ARCs).  A request is made to determine the closest ARC to use.

Using IVOA DataLink
-------------------

.. code-block:: python

    >>> from astroquery.alma import Alma
    >>> alma.get_data_info(uids='uid://A001/X12a3/Xe9', expand_tarfiles=False)
         ID                                                   access_url                                                                 service_def                         error_message   semantics                      description                                   content_type                content_length readable
                                                                                                                                                                                                                                                                                                           byte              
       object                                                   object                                                                      object                               object        object                          object                                        object                       int64        bool  
   -------------------- ------------------------------------------------------------------------------------------- ----------------------------------------------------------- ------------- -------------- ------------------------------------------------ ------------------------------------------ -------------- --------
   uid://A001/X12a3/Xe9               https://almascience.eso.org/dataPortal/member.uid___A001_X12a3_Xe9.README.txt                                                                           #documentation Download documentation for uid://A001/X12a3/Xe9.                                 text/plain           3523     True
   uid://A001/X12a3/Xe9   https://almascience.eso.org/dataPortal/2017.1.01185.S_uid___A001_X12a3_Xe9_001_of_001.tar                                                                                    #this  Download dataset of type: null, and class: N/A.                          application/x-tar      556278784     True
   uid://A001/X12a3/Xe9                                                                                             DataLink.2017.1.01185.S_uid___A001_X12a3_Xe9_001_of_001.tar                        #this                                                  application/x-votable+xml;content=datalink             --       --
   ...

You may choose to expand the TAR files, but this will walk the entire tree and resolve the ``service_def`` entries to actual URLs:

.. code-block:: python

    >>> from astroquery.alma import Alma
    >>> alma.get_data_info(uids='uid://A001/X12a3/Xe9', expand_tarfiles=True)
         ID                                                   access_url                                                                        service_def                         error_message   semantics                      description                                    content_type                content_length readable
                                                                                                                                                                                                                                                                                                                  byte              
       object                                                   object                                                                            object                               object        object                          object                                         object                        int64        bool  
   -------------------- ----------------------------------------------------------------------------------------------- ----------------------------------------------------------- ------------- -------------- ------------------------------------------------  ------------------------------------------ -------------- --------
   uid://A001/X12a3/Xe9                   https://almascience.eso.org/dataPortal/member.uid___A001_X12a3_Xe9.README.txt                                                                           #documentation Download documentation for uid://A001/X12a3/Xe9.                                  text/plain           3523     True
   uid://A001/X12a3/Xe9       https://almascience.eso.org/dataPortal/2017.1.01185.S_uid___A001_X12a3_Xe9_001_of_001.tar                                                                                    #this Download dataset of type: null, and class: N/A.                            application/x-tar      556278784     True
   uid://A001/X12a3/Xe9 https://almascience.eso.org/datalink/sync?ID=2017.1.01185.S_uid___A001_X12a3_Xe9_001_of_001.tar                                                                                    #this                                                   application/x-votable+xml;content=datalink                    True
   ...


Alternate (testing) Registry
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To use an alternate Registry (Test ARC), the ``ARCHIVE_URL`` environment variable can be set to the scheme and
hostname.  If this is done, then the registry document _needs_ to use ivo://almascience.org as the authority
of the Service IDs.

.. code-block:: sh

    >>> $ export ARCHIVE_URL=https://example-test.com
    >>> $ curl https://example-test.com/reg/resource-caps
    ivo://almascience.org/obscore = https://example-test.com/tap/capabilities
    ...

For running the integration tests, use the ``--alma-site`` switch:

.. code-block:: sh

    >>> /workspace/astroquery $ python setup.py test --package alma -a "--alma-site=example-test.com" --remote-data


.. _Atacama Large Millimeter/submillimeter Array: https://almascience.org
.. _IVOA: https://ivoa.net