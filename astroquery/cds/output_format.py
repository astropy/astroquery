#!/usr/bin/env python
# -*- coding: utf-8 -*

# Licensed under a 3-clause BSD style license - see LICENSE.rst
from sys import maxsize


class OutputFormat(object):

    def __init__(self, format, field_l, moc_order, case_sensitive, max_rec):
        """
        OutputFormat object initializer. Specifies what will be returned to the user

        :param format: OutputFormat.Type, optional
            specifies the output format type.
            id : ID list (default)
            record : dictionary containing multiple set of meta data. Each of these sets is indexed by
             the ID of the data set it is referring to.
            moc : mocpy.MOC object resulting from the union of all the MOCs of the data sets
            i_moc : mocpy.MOC object resulting from the intersection of all the MOCs of the data sets
            number : int value giving the number of selected data sets.
        :param field_l: list[str], optional
            the list of meta data the user wants to get (only if format=OutputFormat.Type.record). The default
            is [] implying that all the meta data fields are returned.
        :param moc_order: int, optional
            the order of the MOC returned (only if format=OutputFormat.Type.moc/imoc)
        :param case_sensitive: bool, optional
        :param max_rec: int, optional
            the max number of data sets that the CDS MOC service is allowed to return. (the default is None which
            implies the CDS MOC service to return all the matching data sets).

        """
        from .core import cds
        assert isinstance(format, cds.ReturnFormat), TypeError('`format` must be of type OutputFormat.Type')
        assert isinstance(field_l, list), TypeError('`field_l` must be a list type object')
        assert isinstance(case_sensitive, bool), TypeError('`case_sensitive` must be a bool type object')
        assert not max_rec or isinstance(max_rec, int), TypeError('`max_rec` must be an int type object')

        self.format = format
        self.request_payload = {
            "fmt": "json",
            "casesensitive": str(case_sensitive).lower()
        }

        if format is cds.ReturnFormat.id:
            self.request_payload.update({'get': 'id'})
        elif format is cds.ReturnFormat.record:
            self.request_payload.update({'get': 'record'})

            # set up the payload str from the list of fields `field_l` param
            if field_l:
                # The CDS MOC service responds badly to record queries which do not ask
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
        elif format is cds.ReturnFormat.number:
            self.request_payload.update({'get': 'number'})
        elif format in (cds.ReturnFormat.moc, cds.ReturnFormat.i_moc):
            if moc_order != maxsize:
                self.request_payload.update({
                    "order": moc_order
                })
            else:
                self.request_payload.update({
                    "order": "max"
                })

            if format is cds.ReturnFormat.i_moc:
                self.request_payload.update({'get': 'imoc'})
            else:
                self.request_payload.update({'get': 'moc'})

        if max_rec:
            self.request_payload.update({'MAXREC': str(max_rec)})
