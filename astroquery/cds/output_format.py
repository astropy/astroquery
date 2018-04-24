#!/usr/bin/env python
# -*- coding: utf-8 -*

# Licensed under a 3-clause BSD style license - see LICENSE.rst
from enum import Enum
from sys import maxsize


class OutputFormat(object):
    class Type(Enum):
        id = 1,
        record = 2,
        number = 3,
        moc = 4,
        i_moc = 5

    def __init__(self, format=Type.id, field_l=[], moc_order=maxsize, case_sensitive=True, max_rec=None):
        if not isinstance(format, OutputFormat.Type):
            print("The response format must have value in the ResponseFormat enum")
            raise TypeError

        self.format = format

        if not isinstance(field_l, list) or not isinstance(case_sensitive, bool):
            raise TypeError

        self.request_payload = {
            "fmt": "json",
            "casesensitive": str(case_sensitive).lower()
        }

        if max_rec and not isinstance(max_rec, int):
            raise TypeError

        if format is OutputFormat.Type.id:
            self.request_payload.update({'get': 'id'})
        elif format is OutputFormat.Type.record:
            self.request_payload.update({'get': 'record'})

        # parse fields
            if field_l:
                # The MocServer responds badly to record queries which do not ask
                # for the ID field. To prevent that, we add it to the list of requested fields
                field_l.append('ID')
                field_l = list(set(field_l))
                fields_str = str(field_l[0])
                for field in field_l[1:]:
                    if not isinstance(field, str):
                        raise TypeError
                    fields_str += ', '
                    fields_str += field

                self.request_payload.update({
                    "fields": fields_str
                })
        elif format is OutputFormat.Type.number:
            self.request_payload.update({'get': 'number'})
        elif format in (OutputFormat.Type.moc, OutputFormat.Type.i_moc):
            if moc_order != maxsize:
                self.request_payload.update({
                    "order": moc_order
                })
            else:
                self.request_payload.update({
                    "order": "max"
                })

            if format is OutputFormat.Type.i_moc:
                self.request_payload.update({'get': 'imoc'})
            else:
                self.request_payload.update({'get': 'moc'})

        if max_rec:
            self.request_payload.update({'MAXREC': str(max_rec)})