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
from datetime import datetime

TAP_UTILS_QUERY_TOP_PATTERN = re.compile(
    r"\s*SELECT\s+(ALL\s+|DISTINCT\s+)?TOP\s+\d+\s+", re.IGNORECASE)
TAP_UTILS_QUERY_ALL_DISTINCT_PATTERN = re.compile(
    r"\s*SELECT\s+(ALL\s+|DISTINCT\s+)", re.IGNORECASE)

TAP_UTILS_HTTP_ERROR_MSG_START = "<li><b>Message: </b>"
TAP_UTILS_HTTP_VOTABLE_ERROR = '<INFO name="QUERY_STATUS" value="ERROR">'
TAP_UTILS_VOTABLE_INFO = '</INFO>'


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
        listTmp.append(f'{k}={dictionaryObject[k]}')
    return '&'.join(listTmp)


def set_top_in_query(query, top):
    """Adds TOP statement if the query does not have one.

    Parameters
    ----------
    query : ADQL query, mandatory
        ADQL query
    top : str, optional
        ADQL TOP value

    Returns
    -------
    The query with the provided TOP statement, if the query does not have one.
    """
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
            nq = f"{query[0:endPos]} TOP {top} {query[endPos:]}"
        else:
            # no all nor distinct: add top after select
            p = q.replace("\n", " ").find("SELECT ")
            nq = f"{query[0:p+7]} TOP {top} {query[p+7:]}"
        return nq


def get_http_response_error(response):
    """Extracts an HTTP error message from an HTML response.

    Parameters
    ----------
    response : HTTP response, mandatory
        HTTP response

    Returns
    -------
    A string with the response error message.
    """
    responseBytes = response.read()
    responseStr = responseBytes.decode('utf-8')
    return parse_http_response_error(responseStr, response.status)


def parse_http_response_error(responseStr, status):
    """Extracts an HTTP error message from an HTML response.

    Parameters
    ----------
    responseStr : HTTP response, mandatory
        HTTP response

    Returns
    -------
    A string with the response error message.
    """
    pos1 = responseStr.find(TAP_UTILS_HTTP_ERROR_MSG_START)
    if pos1 == -1:
        return parse_http_votable_response_error(responseStr, status)
    pos2 = responseStr.find('</li>', pos1)
    if pos2 == -1:
        return parse_http_votable_response_error(responseStr, status)
    msg = responseStr[(pos1+len(TAP_UTILS_HTTP_ERROR_MSG_START)):pos2]
    return f"Error {status}:\n{msg}"


def parse_http_votable_response_error(responseStr, status):
    """Extracts an HTTP error message from an VO response.

    Parameters
    ----------
    responseStr : HTTP VO response, mandatory
        HTTP VO response

    Returns
    -------
    A string with the response error message.
    """
    pos1 = responseStr.find(TAP_UTILS_HTTP_VOTABLE_ERROR)
    if pos1 == -1:
        return f"Error {status}:\n{responseStr}"
    pos2 = responseStr.find(TAP_UTILS_VOTABLE_INFO, pos1)
    if pos2 == -1:
        return f"Error {status}:\n{responseStr}"
    msg = responseStr[(pos1+len(TAP_UTILS_HTTP_VOTABLE_ERROR)):pos2]
    return f"Error {status}: {msg}"


def get_jobid_from_location(location):
    """Extracts an HTTP error message from an VO response.

    Parameters
    ----------
    location : HTTP VO 303 response location header, mandatory
        HTTP VO redirection location

    Returns
    -------
    A jobid.
    """
    pos = location.rfind('/')+1
    jobid = location[pos:]
    return jobid


def get_schema_name(full_qualified_table_name):
    """Extracts the schema name from a full qualified table name.

    Parameters
    ----------
    full_qualified_table_name : str, mandatory
        A full qualified table name (i.e. schema name and table name)

    Returns
    -------
    The schema name or None.
    """
    pos = full_qualified_table_name.rfind('.')
    if pos == -1:
        return None
    name = full_qualified_table_name[0:pos]
    return name


def get_table_name(full_qualified_table_name):
    """Extracts the table name form a full qualified table name.

    Parameters
    ----------
    full_qualified_table_name : str, mandatory
        A full qualified table name (i.e. schema name and table name)

    Returns
    -------
    The table name or None.
    """
    pos = full_qualified_table_name.rfind('.')
    if pos == -1:
        return full_qualified_table_name
    name = full_qualified_table_name[pos+1:]
    return name


def get_suitable_output_file(conn_handler, async_job, outputFile, headers,
                             isError, output_format):
    dateTime = datetime.now().strftime("%Y%m%d%H%M%S")
    fileName = ""
    if outputFile is None:
        fileName = conn_handler.get_file_from_header(headers)
        if fileName is None:
            ext = conn_handler.get_suitable_extension(headers)
            if not async_job:
                fileName = f"sync_{dateTime}{ext}"
            else:
                ext = conn_handler.get_suitable_extension_by_format(
                    output_format)
                fileName = f"async_{dateTime}{ext}"
    else:
        fileName = outputFile
    if isError:
        fileName += ".error"
    return fileName
