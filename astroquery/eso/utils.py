"""
utils.py: helper functions for the astropy.eso module
"""
from dataclasses import dataclass
from typing import Dict, List, Optional, Union
from astropy.table import Table

DEFAULT_LEAD_COLS_RAW = ['object', 'ra', 'dec', 'dp_id', 'date_obs', 'prog_id']
DEFAULT_LEAD_COLS_PHASE3 = ['target_name', 's_ra', 's_dec', 'dp_id', 'date_obs', 'proposal_id']


@dataclass
class _UserParams:
    """
    Parameters set by the user
    """
    table_name: str
    column_name: str = None
    allowed_values: Union[List[str], str] = None
    cone_ra: float = None
    cone_dec: float = None
    cone_radius: float = None
    columns: Union[List, str] = None
    column_filters: Dict[str, str] = None
    top: int = None
    order_by: str = ''
    order_by_desc: bool = True
    count_only: bool = False
    get_query_payload: bool = False
    print_help: bool = False
    authenticated: bool = False


def _split_str_as_list_of_str(column_str: str):
    if column_str == '':
        column_list = []
    else:
        column_list = list(map(lambda x: x.strip(), column_str.split(',')))
    return column_list


def _raise_if_has_deprecated_keys(filters: Optional[Dict[str, str]]) -> bool:
    if not filters:
        return

    if any(k in filters for k in ("box", "coord1", "coord2")):
        raise ValueError(
            "box, coord1 and coord2 are deprecated; "
            "use cone_ra, cone_dec and cone_radius instead."
        )

    if any(k in filters for k in ("etime", "stime")):
        raise ValueError(
            "'stime' and 'etime' are deprecated; "
            "use instead 'exp_start' together with '<', '>', 'between'. Examples:\n"
            "\tcolumn_filters = {'exp_start': '< 2024-01-01'}\n"
            "\tcolumn_filters = {'exp_start': '>= 2023-01-01'}\n"
            "\tcolumn_filters = {'exp_start': \"between '2023-01-01' and '2024-01-01'\"}\n"
        )


def _build_where_constraints(
        column_name: str,
        allowed_values: Union[List[str], str],
        column_filters: Dict[str, str]) -> str:
    def _format_helper(av):
        if isinstance(av, str):
            av = _split_str_as_list_of_str(av)
        quoted_values = [f"'{v.strip()}'" for v in av]
        return f"{column_name} in ({', '.join(quoted_values)})"

    column_filters = column_filters or {}
    where_constraints = []
    if allowed_values:
        where_constraints.append(_format_helper(allowed_values))

    where_constraints += [
        f"{k} {_adql_sanitize_op_val(v)}" for k, v in column_filters.items()
    ]
    return where_constraints


def _reorder_columns(table: Table,
                     leading_cols: Optional[List[str]] = None):
    """
    Reorders the columns of the pased table so that the
    colums given by the list leading_cols are first.
    If no leading cols are passed, it defaults to
    ['object', 'ra', 'dec', 'dp_id', 'date_obs']
    Returns a table with the columns reordered.
    """
    if not isinstance(table, Table):
        return table

    leading_cols = leading_cols or DEFAULT_LEAD_COLS_RAW
    first_cols = []
    last_cols = table.colnames[:]
    for x in leading_cols:
        if x in last_cols:
            last_cols.remove(x)
            first_cols.append(x)
    last_cols = first_cols + last_cols
    table = table[last_cols]
    return table


def _adql_sanitize_op_val(op_val):
    """
    Expected input:
        "= 5", "< 3.14", "like '%John Doe%'", "in ('item1', 'item2')"
        or just string values like "ESO", "ALMA", "'ALMA'", "John Doe"

    Logic:
        returns "<operator> <value>" if operator is provided.
        Defaults to "= <value>" otherwise.
    """
    supported_operators = ["<=", ">=", "!=", "=", ">", "<",
                           "not like ", "not in ", "not between ",
                           "like ", "between ", "in "]  # order matters

    if not isinstance(op_val, str):
        return f"= {op_val}"

    op_val = op_val.strip()
    for s in supported_operators:
        if op_val.lower().startswith(s):
            operator, value = s, op_val[len(s):].strip()
            return f"{operator} {value}"

    # Default case: no operator. Assign "="
    value = op_val if (op_val.startswith("'") and op_val.endswith("'")) else f"'{op_val}'"
    return f"= {value}"


def raise_if_coords_not_valid(cone_ra: Optional[float] = None,
                              cone_dec: Optional[float] = None,
                              cone_radius: Optional[float] = None) -> bool:
    """
    ra, dec, radius must be either present all three
    or absent all three. Moreover, they must be float
    """
    are_all_none = (cone_ra is None) and (cone_dec is None) and (cone_radius is None)
    are_all_float = isinstance(cone_ra, (float, int)) and \
        isinstance(cone_dec, (float, int)) and \
        isinstance(cone_radius, (float, int))
    is_a_valid_combination = are_all_none or are_all_float
    if not is_a_valid_combination:
        raise ValueError(
            "Either all three (cone_ra, cone_dec, cone_radius) must be present or none.\n"
            "Values provided:\n"
            f"\tcone_ra = {cone_ra}, cone_dec = {cone_dec}, cone_radius = {cone_radius}"
        )


def _build_adql_string(user_params: _UserParams) -> str:
    """
    Return the adql string corresponding to the parameters passed
    See adql examples at https://archive.eso.org/tap_obs/examples
    """
    query_string = None
    columns = user_params.columns or []

    # We assume the coordinates passed are valid
    where_circle = []
    if user_params.cone_radius is not None:
        where_circle += [
            'intersects(s_region, circle(\'ICRS\', '
            f'{user_params.cone_ra}, {user_params.cone_dec}, {user_params.cone_radius}))=1']

    wc = _build_where_constraints(user_params.column_name,
                                  user_params.allowed_values,
                                  user_params.column_filters) + where_circle

    if isinstance(columns, str):
        columns = _split_str_as_list_of_str(columns)
    if columns is None or len(columns) < 1:
        columns = ['*']
    if user_params.count_only:
        columns = ['count(*)']

    # Build the query
    query_string = ', '.join(columns) + ' from ' + user_params.table_name
    if len(wc) > 0:
        where_string = ' where ' + ' and '.join(wc)
        query_string += where_string

    if len(user_params.order_by) > 0 and not user_params.count_only:
        order_string = ' order by ' + user_params.order_by + (' desc ' if user_params.order_by_desc else ' asc ')
        query_string += order_string

    if user_params.top is not None:
        query_string = f"select top {user_params.top} " + query_string
    else:
        query_string = "select " + query_string

    return query_string.strip()
