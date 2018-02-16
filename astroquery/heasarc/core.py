# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import print_function
from astropy.extern.six import BytesIO
from astropy.table import Table
from astropy.io import fits
from ..query import BaseQuery
from ..utils import commons
from ..utils import async_to_sync
from . import conf

__all__ = ['Heasarc', 'HeasarcClass']


@async_to_sync
class HeasarcClass(BaseQuery):

    """HEASARC query class.

    For a list of available HEASARC mission tables, visit:
        https://heasarc.gsfc.nasa.gov/cgi-bin/W3Browse/w3catindex.pl
    """

    URL = conf.server
    TIMEOUT = conf.timeout

    def query_async(self, request_payload, cache=True):
        """
        Submit a query based on a given request_payload. This allows detailed
        control of the query to be submitted.
        """
        response = self._request('GET', self.URL, params=request_payload,
                                 timeout=self.TIMEOUT, cache=cache)
        return response


    def query_object_async(self, object_name, mission,
                           cache=True, get_query_payload=False,
                           display_mode='FitsDisplay', **kwargs):
        """ Query around a specific object within a given mission catalog

        Parameters
        ----------
        object_name : str
            Object to query around. To set search radius use the hidden 'radius'
            parameter.
        mission : str
            Mission table to search from
        **kwargs : 
            see :func:`_args_to_payload` for list of additional parameters that
            can be used to refine search query
        """
        request_payload = self._args_to_payload(
            mission = mission,
            entry   = object_name,
            **kwargs
        )

        # Return payload if requested
        if get_query_payload:
            return request_payload

        return self.query_async(request_payload, cache)


    def _fallback(self, content):
        """
        Blank columns which have to be converted to float or in fail so
        lets fix that by replacing with -1's
        """

        data = BytesIO(content)
        header = fits.getheader(data, 1)  # Get header for column info
        colstart = [y for x, y in header.items() if "TBCOL" in x]
        collens = [int(float(y[1:]))
                   for x, y in header.items() if "TFORM" in x]
        new_table = []

        old_table = content.split("END")[-1].strip()
        for line in old_table.split("\n"):
            newline = []
            for n, tup in enumerate(zip(colstart, collens), start=1):
                cstart, clen = tup
                part = line[cstart - 1:cstart + clen]
                newline.append(part)
                if len(part.strip()) == 0:
                    if header["TFORM%i" % n][0] in ["F", "I"]:
                        # extra space is required to sperate column
                        newline[-1] = "-1".rjust(clen) + " "
            new_table.append("".join(newline))

        data = BytesIO(content.replace(old_table, "\n".join(new_table)))
        return Table.read(data, hdu=1)

    def _parse_result(self, response, verbose=False):
        # if verbose is False then suppress any VOTable related warnings
        if not verbose:
            commons.suppress_vo_warnings()
        try:
            data = BytesIO(response.content)
            table = Table.read(data, hdu=1)
            return table
        except ValueError:
            return self._fallback(response.content)


    def _args_to_payload(self, **kwargs):
        """
        Generates the payload based on user supplied arguments

        Parameters
        ----------
        mission : str
            Mission table to query
        entry : str, optional
            Object or position for center of query. A blank value will return
            all entries in the mission table. Acceptable formats:
            * Object name : Name of object, e.g. 'Crab'
            * Coordinates : CSV list of coordinates, either as 'degrees,degrees' or 'hh mm ss,hh mm ss'
        fields : str, optional
            Return format for columns from the server available options:
            * Standard (default) : Return default table columns
            * All                : Return all table columns
            * <custom>           : User defined csv list of columns to be returned
        radius : float (arcmin), optional
            Return all mission entries within a given distance of search query.
            If not supplied, the server default will be used (~ 60 arcmin)
        coordsys: str ('equatorial' or 'galactic'), optional
            If 'entry' is a set of coordinates, this specifies the coordinate 
            system used to interpret them. By default, equatorial coordinates
            are assumed.
        equinox : int, optional
            Epoch by which to interpret supplied equatorial coordinates (ignored
            if coordsys is galactic)

        displaymode : str, optional
            Return format from server. Since the user does not interact with 
            this directly, it's best to leave this alone
        action : str, optional
            Type of action to be taken (defaults to 'Query')
        """
        # Define the basic query for this object
        request_payload = dict(
            tablehead   = ('name=BATCHRETRIEVALCATALOG_2.0 {}'
                          .format(kwargs.get('mission'))),
            Entry       = kwargs.get('entry', 'none'),
            Action      = kwargs.get('action', 'Query'),
            displaymode = kwargs.get('displaymode','FitsDisplay')
        )

        # Fill in optional information

        fields = kwargs.get('fields', None)
        if fields is not None:
            if fields.lower() == 'standard':
                request_payload['Fields'] = 'Standard'
            elif fields.lower() == 'all':
                request_payload['Fields'] = 'All'
            else:
                request_payload['varon'] = fields.lower().split(',')

        radius = kwargs.get('radius', None)
        if radius is not None:
            request_payload['Radius'] = radius
            
        coordinates = kwargs.get('coordsys', 'equatorial')
        if coordinates.lower() == 'equatorial':
            request_payload['Coordinates'] = 'Equatorial: R.A. Dec'

            equinox = kwargs.get('equinox', None)
            if equinox is not None:
                request_payload['Equinox'] = str(equinox) 

        elif coordinates.lower() == 'galactic':
            request_payload['Coordinates'] = 'Galactic: LII BII'
              
        return request_payload


Heasarc = HeasarcClass()
