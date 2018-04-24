#!/usr/bin/env python
# -*- coding: utf-8 -*

# Licensed under a 3-clause BSD style license - see LICENSE.rst

from .spatial_constraints import SpatialConstraint
from .property_constraint import PropertyConstraint


class Constraints(object):
    def __init__(self, sc=None, pc=None):
        self.__payload = {}
        self.__spatial_constraint = None
        self.__properties_constraint = None
        self.spatial_constraint = sc
        self.properties_constraint = pc

    # Ensure the payload cannot be set
    @property
    def payload(self):
        return self.__payload

    # The payload is automatically reconstructed
    # if the constraints are changed
    @property
    def spatial_constraint(self):
        return self.__spatial_constraint

    @spatial_constraint.setter
    def spatial_constraint(self, sc):
        if sc and not isinstance(sc, SpatialConstraint):
            raise TypeError

        self.__spatial_constraint = sc
        self.__build_new_payload()

    @property
    def properties_constraint(self):
        return self.__properties_constraint

    @properties_constraint.setter
    def properties_constraint(self, sp):
        if sp and not isinstance(sp, PropertyConstraint):
            raise TypeError

        self.__properties_constraint = sp
        self.__build_new_payload()

    def __build_new_payload(self):
        self.__payload = {}
        if self.__spatial_constraint:
            self.__payload.update(self.__spatial_constraint.request_payload)

        if self.__properties_constraint:
            self.__payload.update(self.__properties_constraint.request_payload)
