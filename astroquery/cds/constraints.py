#!/usr/bin/env python
# -*- coding: utf-8 -*

# Licensed under a 3-clause BSD style license - see LICENSE.rst

from .spatial_constraints import SpatialConstraint
from .property_constraint import PropertyConstraint


class Constraints(object):
    def __init__(self, sc=None, pc=None):
        self._payload = {}
        self._spatial_constraint = None
        self._properties_constraint = None
        self.spatial_constraint = sc
        self.properties_constraint = pc

    # Ensure the payload cannot be set
    @property
    def payload(self):
        return self._payload

    # The payload is automatically reconstructed
    # if the constraints are changed
    @property
    def spatial_constraint(self):
        return self._spatial_constraint

    @spatial_constraint.setter
    def spatial_constraint(self, sc):
        if sc and not isinstance(sc, SpatialConstraint):
            raise TypeError('`sc` param is not of SpatialConstraint type')

        self._spatial_constraint = sc
        self._build_new_payload()

    @property
    def properties_constraint(self):
        return self._properties_constraint

    @properties_constraint.setter
    def properties_constraint(self, pc):
        if pc and not isinstance(pc, PropertyConstraint):
            raise TypeError('`pc` param is not of PropertyConstraint type')

        self._properties_constraint = pc
        self._build_new_payload()

    def _build_new_payload(self):
        self._payload = {}
        if self._spatial_constraint:
            self._payload.update(self._spatial_constraint.request_payload)

        if self._properties_constraint:
            self._payload.update(self._properties_constraint.request_payload)
