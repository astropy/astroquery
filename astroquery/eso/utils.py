#!/usr/bin/env/python
from typing import Union, List


def _split_str_as_list_of_str(column_str: str):
    if column_str == '':
        column_list = []
    else:
        column_list = list(map(lambda x: x.strip(), column_str.split(',')))
    return column_list


def sanitize_val(x):
    if isinstance(x, str):
        return f"'{x}'"
    else:
        return f"{x}"


def py2adql(table: str, columns: Union[List, str] = None, where_constraints: List = None,
            order_by: str = '', order_by_desc=True, top: int = None):
    # Initialize / validate
    query_string = None
    wc = [] if where_constraints is None else where_constraints[:]  # do not modify the original list
    if isinstance(columns, str):
        columns = _split_str_as_list_of_str(columns)
    if columns is None or len(columns) < 1:
        columns = ['*']

    # Build the query
    query_string = ', '.join(columns) + ' from ' + table
    if len(wc) > 0:
        where_string = ' where ' + ' and '.join(wc)
        query_string += where_string

    if len(order_by) > 0:
        order_string = ' order by ' + order_by + (' desc ' if order_by_desc else ' asc ')
        query_string += order_string

    if top is not None:
        query_string = "select top " + str(top) + query_string
    else:
        query_string = "select " + query_string

    return query_string.strip()
