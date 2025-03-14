"""
utils.py: helper functions for the astropy.eso module
"""

from typing import Union, List, Optional


def _split_str_as_list_of_str(column_str: str):
    if column_str == '':
        column_list = []
    else:
        column_list = list(map(lambda x: x.strip(), column_str.split(',')))
    return column_list


def adql_sanitize_val(x):
    """
    If the value is a string, put it into single quotes
    """
    retval = f"'{x}'" if isinstance(x, str) else f"{x}"
    return retval


def are_coords_valid(ra: Optional[float] = None,
                     dec: Optional[float] = None,
                     radius: Optional[float] = None) -> bool:
    """
    ra, dec, radius must be either present all three
    or absent all three. Moreover, they must be float
    """
    are_all_none = (ra is None) and (dec is None) and (radius is None)
    are_all_float = isinstance(ra, (float, int)) and isinstance(dec, (float, int)) and isinstance(radius, (float, int))
    is_a_valid_combination = are_all_none or are_all_float
    return is_a_valid_combination


def py2adql(table: str, columns: Union[List, str] = None,
            ra: float = None, dec: float = None, radius: float = None,
            where_constraints: List = None,
            order_by: str = '', order_by_desc=True,
            count_only: bool = False, top: int = None):
    """
    Return the adql string corresponding to the parameters passed
    See adql examples at https://archive.eso.org/tap_obs/examples
    """
    # We assume the coordinates passed are valid
    where_circle = []
    if ra:
        where_circle += [f'intersects(s_region, circle(\'ICRS\', {ra}, {dec}, {radius}))=1']

    # Initialize / validate
    query_string = None
    # do not modify the original list
    wc = [] if where_constraints is None else where_constraints[:]
    wc += where_circle
    if isinstance(columns, str):
        columns = _split_str_as_list_of_str(columns)
    if columns is None or len(columns) < 1:
        columns = ['*']
    if count_only:
        columns = ['count(*)']

    # Build the query
    query_string = ', '.join(columns) + ' from ' + table
    if len(wc) > 0:
        where_string = ' where ' + ' and '.join(wc)
        query_string += where_string

    if len(order_by) > 0:
        order_string = ' order by ' + order_by + (' desc ' if order_by_desc else ' asc ')
        query_string += order_string

    if top is not None:
        query_string = f"select top {top} " + query_string
    else:
        query_string = "select " + query_string

    return query_string.strip()
