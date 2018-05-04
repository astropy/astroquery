#!/usr/bin/env python
# -*- coding: utf-8 -*

# Licensed under a 3-clause BSD style license - see LICENSE.rst

try:
    import pyvo as vo
except ImportError:
    raise ImportError("Could not import pyvo, which is a requirement for calling services on Dataset objects through"
                      "the CDS service. Please see https://pyvo.readthedocs.io/en/latest/ to install it.")

from copy import copy
from random import shuffle


class Dataset:
    """
    Data set record object

    :class:`astroquery.cds.Dataset <astroquery.cds.Dataset>` objects are returned
    only when asking for data sets records through :meth:`~astroquery.cds.CdsClass.query_region`.

    This class offers the ability for users to query specific services on the retrieved data sets.
    This feature uses the `pyvo <http://pyvo.readthedocs.io/en/latest/>`_ library.
    Querying available services is handled by the :meth:`~astroquery.cds.Dataset.search` method.

    One can also ask for the meta data associated with the data set by calling the
    :meth:`~astroquery.cds.Dataset.properties` python property.

    """

    def __init__(self, **kwargs):
        from .core import cds
        assert len(kwargs.keys()) >= 1
        self._properties = kwargs
        self._services = {}

        # These services are available from the properties of
        # a dataset
        self._init_service(cds.ServiceType.tap, vo.dal.TAPService)
        self._init_service(cds.ServiceType.cs, vo.dal.SCSService)
        self._init_service(cds.ServiceType.ssa, vo.dal.SSAService)
        self._init_service(cds.ServiceType.sia, vo.dal.SIAService)

    def _init_service(self, service_type, service_class):
        name_srv_property = service_type.name + '_service_url'

        id_mirror_server = 1
        while True:
            if name_srv_property not in self._properties.keys():
                break

            new_service = service_class(self._properties[name_srv_property])

            if service_type not in self._services.keys():
                self._services[service_type] = [new_service]
            else:
                self._services[service_type].append(new_service)

            pos_url = name_srv_property.find('_url')
            name_srv_property = name_srv_property[:(pos_url+4)]

            name_srv_property += '_' + str(id_mirror_server)
            id_mirror_server = id_mirror_server + 1

        # The mirrors for a same service are shuffled allowing each
        # of the mirror to be queried at the same rate if a lot of
        # people proceeds to query a specific service
        if service_type in self._services.keys():
            shuffle(self._services[service_type])

    @property
    def properties(self):
        """
        Meta data access

        Returns
        -------
        dict{str : _}
            dictionary containing the meta data associated to the data set.
            See `this link <http://alasky.unistra.fr/MocServer/query?get=example&fmt=ascii>`_
            for examples of meta data names and their possible values.

        """

        return copy(self._properties)

    @property
    def services(self):
        """
        Available services access

        Returns
        -------
        result : [str]
            list of the service names available for this data set

        """

        result = [service_type.name for service_type in self._services.keys()]
        return result

    def search(self, service_type, **kwargs):
        """
        Call a service on the data set

        Parameters
        ----------
        service_type : ``astroquery.cds.ServiceType``
            The type of service to query. Can take one of the following values:

            * ``cds.ServiceType.cs`` : cone search service
            * ``cds.ServiceType.tap`` : TAP service
            * ``cds.ServiceType.ssa`` : SSA service
            * ``cds.ServiceType.sia`` : SIA service

        **kwargs :
            Arbitrary keyword arguments asked by the pyvo to query the services
            See the `pyvo doc <http://pyvo.readthedocs.io/en/latest/>`_
            for knowing what keyword parameters the different services need.

        Returns
        -------
        :class:`astropy.table.Table <astropy.table.Table>`
            An astropy table containing the observations of the data set matching the query

        Examples
        --------
        Suppose we get a dictionary of data sets ``datasets_d`` after calling the
        :meth:`~astroquery.cds.CdsClass.query_region` with record outputs.
        We want to call the SSA service on a dataset whose ID is ``index``

        >>> from astropy import coordinates
        >>> from astroquery.cds import cds
        >>> center = coordinates.SkyCoord(10.8, 32.2, unit='deg')
        >>> radius = coordinates.Angle(1.5, unit='deg')
        >>> datasets_d = cds.query_region(region_type=cds.RegionType.Cone,
        ...                               center=center,
        ...                               radius=radius,
        ...                               output_format=cds.ReturnFormat.record)
        >>> table = datasets_d['CDS/I/200/npm1rgal'].search(cds.ServiceType.cs,
        ...                                                 pos=(10.8, 32.2),
        ...                                                 radius=1.5)
        >>> print(table)
             _RAJ2000  _DEJ2000    _r      Name   ... Flag2 Flag3   _RA.icrs     _DE.icrs
               deg       deg      deg             ...               "h:m:s"      "d:m:s"
            --------- --------- -------- -------- ... ----- ----- ------------ ------------
              9.71152  31.54400 1.133477 +31.0014 ...     0     0 00 38 50.765 +31 32 38.40
             12.19638  31.95690 1.207892 +31.0015 ...     0     0 00 48 47.132 +31 57 24.85
             12.22010  31.95853 1.227253 +31.0016 ...     0     0 00 48 52.824 +31 57 30.71
              9.07023  31.99699 1.479329 +31.0013 ...     0     0 00 36 16.856 +31 59 49.18
             12.41883  32.16893 1.370420 +31.0017 ...     0     0 00 49 40.520 +32 10 08.14
             10.30302  32.37405 0.454763 +32.0024 ...     0     0 00 41 12.725 +32 22 26.59
              9.45192  32.60568 1.208313 +32.0023 ...     0     0 00 37 48.460 +32 36 20.44
             10.82190  32.71765 0.517981 +32.0026 ...     0     0 00 43 17.256 +32 43 03.54
             10.36668  32.79513 0.698383 +32.0025 ...     0     0 00 41 28.004 +32 47 42.46

        """

        from .core import cds
        if not isinstance(service_type, cds.ServiceType):
            raise ValueError('Service {0} not found'.format(service_type))

        if service_type not in self._services.keys():
            raise KeyError('The service {0:s} is not available for this dataset\n'
                           'Available services are the following :\n{1}'.format(service_type.name, self.services))

        services_l = self._services[service_type]

        """
        Mirrors services are queried in a random way (services_l shuffled) until
        a service does not raise a DALServiceError or a DALQueryError.  

        """

        result = None
        index_service = 0
        while not result:
            try:
                result = services_l[index_service].search(**kwargs).votable
            except (vo.dal.DALQueryError, vo.dal.DALServiceError) as dal_error:
                if index_service >= len(services_l) - 1:
                    raise dal_error

            index_service += 1

        return result
