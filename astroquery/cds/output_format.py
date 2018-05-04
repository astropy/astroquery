#!/usr/bin/env python
# -*- coding: utf-8 -*

# Licensed under a 3-clause BSD style license - see LICENSE.rst
from sys import maxsize


class OutputFormat(object):
    def __init__(self, output_format, field_l, moc_order, case_sensitive, max_rec):
        from .core import cds

        if not isinstance(output_format, cds.ReturnFormat):
            raise TypeError('`output_format` must be of type cds.ReturnFormat')

        if not isinstance(field_l, list):
            raise TypeError('`field_l` must be a list type object')

        if not isinstance(case_sensitive, bool):
            raise TypeError('`case_sensitive` must be a bool type object')

        if max_rec and not isinstance(max_rec, int):
            raise TypeError('`max_rec` must be an int type object')

        self.format = output_format
        self.request_payload = {
            "fmt": "json",
            "casesensitive": str(case_sensitive).lower()
        }

        if output_format is cds.ReturnFormat.id:
            self.request_payload.update({'get': 'id'})
        elif output_format is cds.ReturnFormat.record:
            self.request_payload.update({'get': 'record'})

            # set up the payload str from the list of fields `field_l` param
            if field_l:
                # The CDS MOC service responds badly to record queries which do not ask
                # for the ID field. To prevent that, we add it to the list of requested fields
                field_l.append('ID')
                field_l = list(set(field_l))
                fields_str = str(field_l[0])
                for field in field_l[1:]:
                    fields_str += ', '
                    fields_str += field

                self.request_payload.update({
                    "fields": fields_str
                })
        elif output_format is cds.ReturnFormat.number:
            self.request_payload.update({'get': 'number'})
        elif output_format in (cds.ReturnFormat.moc, cds.ReturnFormat.i_moc):
            if moc_order != maxsize:
                self.request_payload.update({
                    "order": moc_order
                })
            else:
                self.request_payload.update({
                    "order": "max"
                })

            if output_format is cds.ReturnFormat.i_moc:
                self.request_payload.update({'get': 'imoc'})
            else:
                self.request_payload.update({'get': 'moc'})

        if max_rec:
            self.request_payload.update({'MAXREC': str(max_rec)})
