# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
VizieR Query Tool
-----------------

:Author: Julien Woillez (jwoillez@gmail.com)
"""

import sys
import httplib
if sys.version_info[0] >= 3:
    from io import BytesIO as StringIO
else:
    from cStringIO import StringIO
import numpy
try:
    import astropy.io.vo.table as votable
except ImportError:
    import astropy.io.votable as votable
from astropy.table import Table

def vizquery(query, server="vizier.u-strasbg.fr"):
    """
    VizieR search query.
    
    This function can be used to search all the catalogs available through the VizieR service.
    
    Parameters
    ----------
    query: dict
        A dictionary specifying the query.
        For acceptable keys, refer to the links given in the references section.
        The dictionary values can be any of the following types:
           * string
           * list of string
           * astropy.table.Table (containing columns "_RAJ2000" and "_DEJ2000" in degrees)
    server: str, optional
        The VizieR server to use. (See VizieR mirrors at http://vizier.u-strasbg.fr)
        Defaults to "vizier.u-strasbg.fr".

    Returns
    -------
    table : `~astropy.table.Table`
        A table containing the results of the query
    
    References
    ----------
    * http://vizier.u-strasbg.fr/doc/asu-summary.htx
    * http://vizier.u-strasbg.fr/vizier/vizHelp/menu.htx
    
    """
    
    # Always add calculated _RAJ2000 & _DEJ2000 to the query.
    # This is used for cross correlations between queries
    if query.has_key('-out.add'):
        query["-out.add"] += ['_RAJ2000', '_DEJ2000']
    else:
        query["-out.add"]  = ['_RAJ2000', '_DEJ2000']
    
    # Assemble the actual query
    body = []
    for (key,value) in query.items():
        if type(value) is str:
            body += ["%s=%s"%(key, value)]
        elif type(value) is Table: # Value is a table, convert it to a string, list of positions
            pos = []
            for elem in numpy.array(value, copy=False):
                pos += ["%.8f%+.8f"%(elem['_RAJ2000'],elem['_DEJ2000'])] # Position with the format: _RAJ2000+_DEJ2000
            body += ["-out.add=_q"] # This calculated index is a reference to the input table
            body += ["%s=%s"%(key, "<<;"+";".join(pos))] # The proper convention: <<;pos1;pos2;pos3
        elif type(value) is list: # Value is a list, join it with commas
            body += ["%s=%s"%(key, ",".join(value))]
        else:
            raise Exception, "Don't know how to handle %s"%repr(value)
    body = "\r\n".join(body)

    # Fetch the VOTABLE corresponding to the query 
    h = httplib.HTTPConnection(server)
    h.request("POST", "/viz-bin/votable", body=body)
    resp = h.getresponse()
    s = StringIO(resp.read())
    voTable = votable.parse(s, pedantic=False)
    
    # Convert VOTABLE into a list of astropy Table.
    tableList = []
    for voTreeTable in voTable.iter_tables():
        if len(voTreeTable.array)>0:
            # Table names come from the VOTABLE fields
            names = []
            for field in voTreeTable.fields:
                names += [field.name.encode('ascii')]
            # Table data come from the VOTABLE record array
            tableList += [voTreeTable.to_table()]
    
    # Merge the Table list
    table = tableList[0]
    if len(tableList)>1:
        for t in tableList[1:]:
            if len(t)>0:
                for row in t:
                    table.add_row(row)
    
    return table


if __name__ == '__main__':
    
    #Find all AGNs in Veron & Cetty with Vmag in [5.0; 11.0]
    query = {}
    query["-source"] = "VII/258/vv10"
    query["-out"] = ["Name", "Sp", "Vmag"]
    query["Vmag"] = "5.0..11.0"
    table1 = vizquery(query)
    
    #Find sources in 2MASS matching the AGNs positions to within 2 arcsec
    query = {}
    query["-source"] = "II/246/out"
    query["-out"] = ["RAJ2000", "DEJ2000", "2MASS", "Kmag"]
    query["-c.rs"] = "2"
    query["-c"] = table1
    table2 = vizquery(query)
    
    print(table1)
    print(table2)

