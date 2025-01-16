# Licensed under a 3-clause BSD style license - see LICENSE.rst

import json
from collections import OrderedDict

from numpy import fromstring, isnan, array
import astropy.units as u

from ..query import BaseQuery
from ..utils import async_to_sync
from . import conf

__all__ = ['SBDB', 'SBDBClass']


@async_to_sync
class SBDBClass(BaseQuery):

    """
    A class for querying the `JPL Small-Body Database Browser
    <https://ssd.jpl.nasa.gov/tools/sbdb_lookup.html>`_ service.
    """

    # internal flag whether to return the raw reponse
    _return_raw = False

    # actual query uri
    _uri = None

    def query_async(self, targetid, *, id_type='search',
                    neo_only=False,
                    alternate_id=False,
                    full_precision=False,
                    solution_epoch=False,
                    covariance=None,
                    validity=False,
                    alternate_orbit=False,
                    phys=False,
                    close_approach=False,
                    radar=False,
                    virtual_impactor=False,
                    discovery=False,
                    get_query_payload=False,
                    get_raw_response=False,
                    get_uri=False,
                    cache=True):
        """
        This method queries the `JPL Small-Body Database Browser
        <https://ssd.jpl.nasa.gov/tools/sbdb_lookup.html>`_ and returns an
        `~collections.OrderedDict` with all queried information.

        Parameters
        ----------
        targetid: str
            Target identifier or search string (if ``id_type='search'``)
        id_type: str, optional
            Defines the type of identifier provided through ``targetid``:
            ``'search'`` for a search string (designations, numbers, and
            names in varius forms, including MPC packed form and
            case-insensitive names; wildcard character ``'*'`` is allowed),
            ``'spk'`` for a spice kernel id, or ``'desig'`` for an object
            designation. Default value: ``'search'``
        neo_only: boolean, optional
            If ``True``, only output for Near-Earth Objects (NEOs) is
            returned. Default value: ``False``.
        alternate_id: boolean, optional
            Return alternate identifiers (designations and Spice kernel
            ids) if ``True``. Default: ``False``
        full_precision: boolean, optional
            Provide results using full precision. Default: ``False``
        solution_epoch: boolean, optional
            Output orbit data at the JPL orbit-solution epoch instead of
            the standard MPC epoch. Default: ``False``
        covariance: str or ``None``, optional
            Output the orbital covariance (if available) in the full matrix
            form when ``mat``, in the upper-triangular vector-stored form
            when ``vec``, or in the upper-triangular vector-stored
            square-root form when ``src``; provide no covariance when
            ``None``. Default: ``None``
        validity: boolean, optional
            Provide the validity ranges of the orbital elements as Julian
            Dates. Default: ``False``
        alternate_orbit: boolean, optional
            Provide alternate orbits, if available. Default: ``False``
        phys: boolean, optional
            Provide physical property information, if available. Default:
            ``False``
        close_approach: boolean, optional
            Output information on close approaches with the major planets.
            Default: ``False``
        radar: boolean, optional
            Provide information on radar observations of the target. Default:
            ``False``
        virtual_impactor: boolean, optional
            Provide information on a potential virtual impactor nature of the
            target from the `JPL Sentry system
            <https://cneos.jpl.nasa.gov/sentry/>`_. Default: ``False``
        discovery: boolean, optional
            Output discovery circumstances and IAU name citation data.
            Default: ``False``
        get_query_payload: bool, optional
            This should default to ``False``. When set to ``True`` the method
            should return the HTTP request parameters as a dict.
        get_raw_response : boolean, optional
            Return raw data as obtained by JPL SBDB without parsing the
            data. Default: ``False``
        get_uri : boolean, optional
            Add the query URI to the output as ``query_uri`` field.
            Default: ``False``
        cache : bool
            Defaults to True. If set overrides global caching behavior.
            See :ref:`caching documentation <astroquery_cache>`.

        Returns
        -------
        res : `~collections.OrderedDict`
            A dictionary holding all the parsed data.

        Examples
        --------
        >>> from astroquery.jplsbdb import SBDB
        >>> sbdb = SBDB.query('3552')  # doctest: +SKIP
        >>> print(sbdb) # doctest: +SKIP
        OrderedDict([('object', OrderedDict([('shortname', '3552 Don Quixote'), ('neo', True), ... ])

        """
        URL = conf.server
        TIMEOUT = conf.timeout

        if covariance not in [None, 'mat', 'vec', 'src']:
            raise ValueError('Option "{:s}" not available for covariance'.
                             format(covariance))

        # assemble payload
        request_payload = {{'search': 'sstr',
                            'spk': 'spk',
                            'desig': 'des'}[id_type]: targetid}

        if neo_only:
            request_payload['neo'] = 1
        if alternate_id:
            request_payload['alt-des'] = 'true'
            request_payload['alt-spk'] = 'true'
        if full_precision:
            request_payload['full-prec'] = 'true'
        if solution_epoch:
            request_payload['soln-epoch'] = 'true'
        if covariance is not None:
            request_payload['cov'] = covariance
        if validity:
            request_payload['nv-fmt'] = 'jd'
        if alternate_orbit:
            request_payload['alt-orbits'] = 'true'
        if phys:
            request_payload['phys-par'] = 'true'
        if close_approach:
            request_payload['ca-data'] = 'true'
            request_payload['ca-time'] = 'both'
            request_payload['ca-tunc'] = 'both'
            request_payload['ca-unc'] = 'true'
        if radar:
            request_payload['radar-obs'] = 'true'
            request_payload['r-name'] = 'true'
            request_payload['r-observer'] = 'true'
            request_payload['r-notes'] = 'true'
        if virtual_impactor:
            request_payload['vi-data'] = 'true'
        if discovery:
            request_payload['discovery'] = 'true'
            request_payload['raw-citation'] = 'true'

        if get_query_payload:
            return request_payload

        response = self._request(method='GET', url=URL,
                                 params=request_payload,
                                 timeout=TIMEOUT, cache=cache)

        if get_raw_response:
            self._return_raw = True

        if get_uri:
            self._uri = response.url

        return response

    def _parse_result(self, response, *, verbose=False):
        """
        internal wrapper to parse queries

        """

        if self._return_raw:
            return response.text

        # decode json response from JPL SBDB server into ascii
        # SBDB API: does not provide proper unicode representation
        try:
            src = OrderedDict(json.loads(response.text))

        except ValueError:
            raise ValueError('Server response not readable.')

        # check for query problems
        if 'code' in src and not (src['code'] == '200'
                                  or src['code'] == '300'):
            raise ValueError(src['message'] + ' ({:s})'.format(src['code']))

        src = self._process_data(src)

        # add query uri, if desired
        if self._uri is not None:
            src['query_uri'] = self._uri

        return src

    def _process_data(self, src):
        """
        internal routine to process raw data in OrderedDict format, must
        be able to work recursively

        """

        res = OrderedDict()

        for key, val in src.items():

            if isinstance(val, list):

                # leave empty lists untouched
                if len(val) == 0:
                    res[key] = list()
                    continue

                # turn data objects into dictionary
                elif ('name' in val[0] and 'sigma' in val[0]
                        and 'value' in val[0] and 'units' in val[0]):

                    res[key] = self._process_data_element(val)

                else:
                    # turn 'data' lists into arrays
                    if key == 'data':
                        if len(array(val).shape) > 1:
                            res[key] = []
                            for i in range(array(val).shape[1]):
                                if isinstance(val[i], bytes):
                                    val[i] = val[i].decode('utf-8')
                                # res[key].append(genfromtxt(val[i]))
                                res[key].append(
                                    fromstring(" ".join(val[i]), sep=' '))
                            res[key] = array(res[key])
                        else:
                            if isinstance(val, bytes):
                                val = val.decode('utf-8')
                            try:
                                res[key] = float(val)
                            except ValueError:
                                res[key] = val
                        continue

                    # turn lists of dictionaries into lists/leave as scalars
                    elif isinstance(val[0], dict):
                        names = list(val[0].keys())
                        res[key] = OrderedDict()
                        for field in names:

                            try:
                                # try to convert list of strings to array
                                for i in range(len(val)):
                                    if isinstance(val[i][field], bytes):
                                        val[i][field] = val[i][field].decode(
                                            'utf-8')

                                res[key][field] = [float(val[i][field])
                                                   for i in range(len(val))]

                                # make it fail if there are nans
                                try:
                                    if any(isnan(res[key][field])):
                                        raise ValueError
                                except TypeError:
                                    if isnan(res[key][field]):
                                        raise ValueError

                                # apply unit, if available
                                if field in conf.field_unit:
                                    res[key][field] = res[key][field] *\
                                        u.Unit(conf.field_unit[field])

                            except (AttributeError, ValueError, TypeError):
                                # if that fails
                                res[key][field] = [list() for i in
                                                   range(len(val))]

                                for i in range(len(val)):
                                    # try to process list of dictionaries
                                    if (isinstance(val[i][field], list)
                                            and len(val[i][field]) > 0
                                            and isinstance(val[i][field][0],
                                                           dict)):
                                        res[key][field][i] = \
                                            self._process_data_element(
                                            val[i][field])
                                    # or use a list instead
                                    else:
                                        res[key][field][i] = val[i][field]

                                if len(res[key][field]) == 1:
                                    res[key][field] = res[key][field][0]

                    # leave scalar elements as they are
                    else:
                        res[key] = val

            # re-run this function on leaf dicts
            elif isinstance(val, dict):
                res[key] = self._process_data(val)

            # use leaf scalars (and apply units, where applicable)
            else:
                if key in conf.field_unit.keys() and val is not None:
                    res[key] = float(val) * u.Unit(conf.field_unit[key])
                else:
                    res[key] = val

        return res

    def _process_data_element(self, val):
        """
        internal routine to process a list of data elements: dictionaries
        containing 'units', 'name', 'value', 'sigma'...

        """

        eldict = OrderedDict()

        for q in val:
            # change units where necessary
            if q['units'] in conf.data_unit_replace.keys():
                q['units'] = conf.data_unit_replace[q['units']]
            # change exponential symbol in unit string from '^' to '**'
            if (q['units'] is not None) and ('^' in q['units']):
                q['units'] = q['units'].replace('^', '**')
            try:
                unit = u.Unit(q['units'])
            except ValueError:
                unit = u.Unit(q['units'], format='ogip')
            except TypeError:
                unit = 1

            # try to combine value with units provided
            try:
                if q['value'] is not None:
                    eldict[q['name']] = (float(q['value']) * unit)
                else:
                    eldict[q['name']] = q['value']
                if q['sigma'] is not None:
                    eldict[q['name']+'_sig'] = (float(q['sigma'])
                                                * unit)
                else:
                    eldict[q['name']+'_sig'] = q['sigma']
            except ValueError:
                # if error raised, just provide strings
                eldict[q['name']] = str(q['value'])
                eldict[q['name']+'_sig'] = str(q['sigma'])

            # add additional information where available
            if 'ref' in q:
                eldict[q['name']+'_ref'] = q['ref']
            if 'kind' in q:
                eldict[q['name']+'_kind'] = q['kind']
            if 'notes' in q:
                eldict[q['name']+'_note'] = q['notes']

        return eldict

    def schematic(self, d, *, _prepend='+--'):
        """
        Formats the provided dictionary ``d`` into a human-readable tree
        structure schematic. In order to display the structure
        properly, the resulting ``outstring`` should be passed to
        the ``print`` function.

        Parameters
        ----------
        d : dict, optional
            Input dictionary that is to be formatted .
        _prepend : str
            for internal use only

        Returns
        -------
        outstring : str
            The formatted string based on ``d``.

        Notes
        -----
        All non-ASCII unicode characters are removed from ``outstring``.

        Examples
        --------
            >>> from astroquery.jplsbdb import SBDB
            >>> sbdb = SBDB.query(3552)  # doctest: +SKIP
            >>> print(SBDB.schematic(sbdb))  # doctest: +SKIP
            +-+ object:
            | +-- shortname: 3552 Don Quixote
            | +-- neo: True
            | +-+ orbit_class:
            | | +-- name: Amor
            ...
            | +-- pe_used: DE431
            | +-- last_obs: 2018-07-05
            | +-- moid: 0.334 AU
            | +-- n_dop_obs_used: None

        """

        outstring = ''
        for key, val in d.items():
            if isinstance(val, list):
                val_formatted = str(val).encode(
                    'ascii', errors='ignore').decode('ascii')
                outstring += ('{:s} {:s}: {:s}\n'.format(
                    _prepend, key,
                    val_formatted))
            elif isinstance(val, dict):
                val_formatted = ''
                outstring += ('{:s} {:s}: {:s}\n'.format(
                    _prepend[: -1]+'+', key,
                    val_formatted))
                new_prepend = ('| '*int(len(_prepend)/2)) + '+--'
                outstring += self.schematic(val, _prepend=new_prepend)
            else:
                val_formatted = str(val).encode(
                    'ascii', errors='ignore').decode('ascii')
                outstring += ('{:s} {:s}: {:s}\n'.format(
                    _prepend, key,
                    val_formatted))
        return outstring


SBDB = SBDBClass()
