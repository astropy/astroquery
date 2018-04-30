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
        return copy(self._properties)

    @property
    def services(self):
        return [service_type.name for service_type in self._services.keys()]

    def search(self, service_type, **kwargs):
        """
        Definition of the search function allowing the user to perform queries on the dataset.

        :param service_type:
            Wait for a Dataset.ServiceType object specifying the type of service to query
        :param kwargs:
            The params that PyVO requires to query the services.
            These depend on the queried service :
            - a simple cone search requires a pos and radius params expressed in deg
            - a tap search requires a SQL query
            - a ssa (simple spectral access) search requires a pos and a diameter params.
            SSA searches can be extended with two other params : a time and a band such as
            Dataset.search(service_type=Dataset.ServiceType.SSA,
                pos=pos, diameter=size,
                time=time, band=Quantity((1e-13, 1e-12), unit="meter")
            )
            - sia and sia2 searches require a pos and a size params where size defines a
            rectangular region around pos

            For more explanation about what params to use with a service, see the pyvo
            doc available at : http://pyvo.readthedocs.io/en/latest/dal/index.html
        :return:
            an astropy.table.Table containing the sources from the dataset that match the query

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
        DALErrors are not raised and we get a votable

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
