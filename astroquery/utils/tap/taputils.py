# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
=============
TAP plus
=============

@author: Juan Carlos Segovia
@contact: juan.carlos.segovia@sciops.esa.int

European Space Astronomy Centre (ESAC)
European Space Agency (ESA)

Created on 30 jun. 2016


"""

import re

TAP_UTILS_QUERY_TOP_PATTERN = re.compile(
    r"\s*SELECT\s+(ALL\s+|DISTINCT\s+)?TOP\s+\d+\s+", re.IGNORECASE)
TAP_UTILS_QUERY_ALL_DISTINCT_PATTERN = re.compile(
    r"\s*SELECT\s+(ALL\s+|DISTINCT\s+)", re.IGNORECASE)


def taputil_find_header(headers, key):
    """Searches for the specified keyword

    Parameters
    ----------
    headers : HTTP(s) headers object, mandatory
        HTTP(s) response headers
    key : str, mandatory
        header key to be searched for

    Returns
    -------
    The requested header value or None if the header is not found
    """
    for entry in headers:
        if key.lower() == entry[0].lower():
            return entry[1]
    return None


def taputil_create_sorted_dict_key(dictionaryObject):
    """Searches for the specified keyword

    Parameters
    ----------
    dictionaryObject : dictionary object, mandatory
        Dictionary

    Returns
    -------
    A keyword based on a sorted dictionary key+value items
    """
    if dictionaryObject is None:
        return None
    listTmp = []
    for k in sorted(dictionaryObject):
        listTmp.append(str(k) + '=' + str(dictionaryObject[k]))
    return '&'.join(listTmp)


def set_top_in_query(query, top):
    if query is None:
        return query
    if top is None:
        return query
    q = query.upper()
    if TAP_UTILS_QUERY_TOP_PATTERN.search(q):
        # top is present
        return query
    else:
        # top is not present
        # check all|distinct
        m = TAP_UTILS_QUERY_ALL_DISTINCT_PATTERN.search(q)
        if m:
            # all | distinct is present: add top after all|distinct
            endPos = m.end()
            nq = query[0:endPos] + " TOP " + str(top) + " " + query[endPos:]
        else:
            # no all nor distinct: add top after select
            p = q.find("SELECT ")
            nq = query[0:p+7] + " TOP " + str(top) + " " + query[p+7:]
        return nq
