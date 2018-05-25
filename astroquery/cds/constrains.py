#!/usr/bin/env python
# -*- coding: utf-8 -*

# Licensed under a 3-clause BSD style license - see LICENSE.rst

from .spatial_constrains import SpatialConstrain
from .property_constrain import PropertyConstrain


class Constrains(object):
    def __init__(self, sc=None, pc=None):
        self._payload = {}
        self._spatial_constrain = None
        self._properties_constrain = None
        self.spatial_constrain = sc
        self.properties_constrain = pc

    # Ensure the payload cannot be set
    @property
    def payload(self):
        return self._payload

    # The payload is automatically reconstructed
    # if the constrains are changed
    @property
    def spatial_constrain(self):
        return self._spatial_constrain

    @spatial_constrain.setter
    def spatial_constrain(self, sc):
        if sc and not isinstance(sc, SpatialConstrain):
            raise TypeError('`sc` param is not of SpatialConstrain type')

        self._spatial_constrain = sc
        self._build_new_payload()

    @property
    def properties_constrain(self):
        return self._properties_constrain

    @properties_constrain.setter
    def properties_constrain(self, pc):
        if pc and not isinstance(pc, PropertyConstrain):
            raise TypeError('`pc` param is not of PropertyConstrain type')

        self._properties_constrain = pc
        self._build_new_payload()

    def _build_new_payload(self):
        self._payload = {}
        if self._spatial_constrain:
            self._payload.update(self._spatial_constrain.request_payload)

        if self._properties_constrain:
            self._payload.update(self._properties_constrain.request_payload)
