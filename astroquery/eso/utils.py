#!/usr/bin/env/python
from typing import Union


def _split_str_as_list_of_str(column_str: str):
    if column_str == '':
        column_list = []
    else:
        column_list = list(map(lambda x: x.strip(), column_str.split(',')))
    return column_list


def py2adql(table: str, columns: Union[list, str] = [], where_constraints=[],
            order_by: str = '', order_by_desc=True):
    # Initialize / validate
    query_string = None
    where_constraints = where_constraints[:]  # do not modify the original list
    if isinstance(columns, str):
        columns = _split_str_as_list_of_str(columns)
    if columns == []:
        columns = ['*']

    # Build the query
    query_string = 'select ' + ', '.join(columns) + ' from ' + table
    if len(where_constraints) > 0:
        where_string = ' where ' + ' and '.join(where_constraints)
        query_string += where_string

    if len(order_by) > 0:
        order_string = ' order by ' + order_by + (' desc ' if order_by_desc else ' asc ')
        query_string += order_string

    return query_string.strip()
