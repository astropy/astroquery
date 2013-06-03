# Licensed under a 3-clause BSD style license - see LICENSE.rst
from astropy.config import ConfigurationItem

VIZIER_SERVER = ConfigurationItem('vizier_server', ['vizier.u-strasbg.fr',
                                                    'vizier.nao.ac.jp',
                                                    'vizier.hia.nrc.ca',
                                                    'vizier.ast.cam.ac.uk',
                                                    'vizier.cfa.harvard.edu',
                                                    'www.ukirt.jach.hawaii.edu',
                                                    'vizier.iucaa.ernet.in',
                                                    'vizier.china-vo.org'], 'Name of the VizieR mirror to use.')


import requests
import io
import numpy as np
try:
    import astropy.io.vo.table as votable
except ImportError:
    import astropy.io.votable as votable
from astropy.table import Table

__all__ = ['vizquery']


def vizquery(query, server=None):
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
        If not specified, `server` is set by the `VIZIER_SERVER` configuration item.

    Returns
    -------
    table : `~astropy.table.Table`
        A table containing the results of the query
    
    References
    ----------
    * http://vizier.u-strasbg.fr/doc/asu-summary.htx
    * http://vizier.u-strasbg.fr/vizier/vizHelp/menu.htx
    
    """
    
    #Check VizieR server
    server = (VIZIER_SERVER() if server is None else server)
    
    # Always add calculated _RAJ2000 & _DEJ2000 to the query.
    # This is used for cross correlations between queries
    if '-out.add' in query:
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
            for elem in np.array(value, copy=False):
                pos += ["%.8f%+.8f"%(elem['_RAJ2000'],elem['_DEJ2000'])] # Position with the format: _RAJ2000+_DEJ2000
            body += ["-out.add=_q"] # This calculated index is a reference to the input table
            body += ["%s=%s"%(key, "<<;"+";".join(pos))] # The proper convention: <<;pos1;pos2;pos3
        elif type(value) is list: # Value is a list, join it with commas
            body += ["%s=%s"%(key, ",".join(value))]
        else:
            raise Exception("Don't know how to handle %s"%repr(value))
    body = "\r\n".join(body)

    # Fetch the VOTABLE corresponding to the query 
    r = requests.post("http://"+server+"/viz-bin/votable", data=body)
    s = io.BytesIO(r.content)
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
