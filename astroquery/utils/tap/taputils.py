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
import warnings
from datetime import datetime, timezone

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
            nq = f"{query[0:p + 7]} TOP {top} {query[p + 7:]}"
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
    msg = responseStr[(pos1 + len(TAP_UTILS_HTTP_ERROR_MSG_START)):pos2]
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
    msg = responseStr[(pos1 + len(TAP_UTILS_HTTP_VOTABLE_ERROR)):pos2]
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
    pos = location.rfind('/') + 1
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
    name = full_qualified_table_name[pos + 1:]
    return name


def get_suitable_output_file(conn_handler, async_job, output_file, headers,
                             is_error, output_format):
    date_time = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    if output_file is None:
        file_name = conn_handler.get_file_from_header(headers)
        if file_name is None:
            ext = conn_handler.get_suitable_extension(headers)
            if not async_job:
                file_name = f"sync_{date_time}{ext}"
            else:
                ext = conn_handler.get_suitable_extension_by_format(
                    output_format)
                file_name = f"async_{date_time}{ext}"
    else:
        file_name = output_file
    if is_error:
        file_name += ".error"
    return file_name


def get_suitable_output_file_name_for_current_output_format(output_file, output_format, *,
                                                            format_with_results_compressed=('votable', 'fits', 'ecsv')):
    """
    Renames the name given for the output_file if the results for current_output
    format are returned compressed by default
    and the name selected by the user does not contain the correct extension.

    output_file : str, optional, default None
        file name selected by the user
    output_format : str, optional, default 'votable'
        results format. Available formats in TAP are: 'votable', 'votable_plain',
        'fits', 'csv', 'ecsv' and 'json'. Default is 'votable'.
        Returned results for formats 'votable' 'ecsv' and 'fits' are compressed
        gzip files.
    format_with_results_compressed : tuple of str, optional
        a set of output formats

    Returns
    -------
    A string with the new name for the file.
    """
    compressed_extension = ".gz"
    output_file_with_extension = output_file

    if output_file is not None:
        if output_format in format_with_results_compressed:
            # In this case we will have to take also into account the .fits format
            if not output_file.endswith(compressed_extension):
                warnings.warn('By default, results in ' + ", ".join(
                    format_with_results_compressed) + f' format are returned in compressed format therefore your file '
                                                      f'{output_file} will be renamed to {output_file}.gz')
                if output_format == 'votable':
                    if output_file.endswith('.vot'):
                        output_file_with_extension = output_file + '.gz'
                    else:
                        output_file_with_extension = output_file + '.vot.gz'
                elif output_format == 'fits':
                    if output_file.endswith('.fits'):
                        output_file_with_extension = output_file + '.gz'
                    else:
                        output_file_with_extension = output_file + '.fits.gz'
                elif output_format == 'ecsv':
                    if output_file.endswith('.ecsv'):
                        output_file_with_extension = output_file + '.gz'
                    else:
                        output_file_with_extension = output_file + '.ecsv.gz'
        # the output type is not compressed by default by the TAP SERVER but the users gives a .gz extension
        elif output_file.endswith(compressed_extension):
            output_file_renamed = output_file.removesuffix('.gz')
            warnings.warn(f'The output format selected is not compatible with compression. {output_file}'
                          f' will be renamed to {output_file_renamed}')
    return output_file_with_extension
