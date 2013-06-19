# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
The SIMBAD query tool creates a `script query
<http://simbad.u-strasbg.fr/simbad/sim-fscript>`__ that returns VOtable XML
data that is then parsed into a :class:`~astroquery.simbad.result.SimbadResult` object.
This object then parses the data and returns a table parsed with `astropy.io.votable.parse`.

The user-available query tools, `~astroquery.simbad.queries.QueryId`,
`~astroquery.simbad.queries.QueryAroundId`,
`~astroquery.simbad.queries.QueryCoord`, `~astroquery.simbad.queries.QueryCat`,
`~astroquery.simbad.queries.QueryBibobj`,
`~astroquery.simbad.queries.QueryMulti`, all create specific query types
specifying the object or region to search.

The `_Query.execute` command takes that query - e.g., ``query id`` for
`~astroquery.simbad.queries.QueryId` - and wraps it in the appropriate votable commands.  If you want
additional fields returned (e.g., those that you can select on the `Output
Options <http://simbad.u-strasbg.fr/simbad/sim-fout>`__ page), you can specify
them by passing a :class:`~astroquery.simbad.simbad_votable.VoTableDef` object with
different output options specified (as per
`Section 5 of the script documents
<http://simbad.u-strasbg.fr/simbad/sim-help?Page=sim-fscript#VotableFields>`__
).
"""
from astropy.config import ConfigurationItem

SIMBAD_SERVER = ConfigurationItem('simbad_server', ['simbad.u-strasbg.fr',
                                                    'simbad.harvard.edu'], 'Name of the SIMBAD mirror to use.')

from .queries import *
from .result import *
from .simbad_votable import *

votabledef = 'main_id, coordinates'
