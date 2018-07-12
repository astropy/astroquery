# -*- coding: utf-8 -*

# Licensed under a 3-clause BSD style license - see LICENSE.rst

from .properties_constraint import PropertiesConstraint


class Constraints(object):
    def __init__(self, pc=None):
        self._payload = {}
        self._properties_constraint = None
        self.properties_constraint = pc

    # Ensure the payload cannot be set
    @property
    def payload(self):
        return self._payload

    # The payload is automatically reconstructed
    # if the constrains are changed
    @property
    def properties_constraint(self):
        return self._properties_constraint

    @properties_constraint.setter
    def properties_constraint(self, pc):
        if pc and not isinstance(pc, PropertiesConstraint):
            raise TypeError('`pc` param is not of PropertiesConstraint type')

        self._properties_constraint = pc
        self._build_new_payload()

    def _build_new_payload(self):
        self._payload = {}

        if self._properties_constraint:
            self._payload.update(self._properties_constraint.request_payload)
