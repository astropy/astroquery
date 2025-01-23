# Licensed under a 3-clause BSD style license - see LICENSE.rst

from ..query import BaseQuery
from ..utils import commons

from . import conf

from copy import copy
from tempfile import NamedTemporaryFile

from astropy import units as u
from astropy.table import Table
from astropy.utils import deprecated

try:
    from mocpy import MOC, TimeMOC, STMOC
except ImportError:
    print("'mocpy' is a mandatory dependency for MOCServer. You can install "
          "it with 'pip install mocpy'.")

__all__ = ["MOCServerClass", "MOCServer"]


class MOCServerClass(BaseQuery):
    """Query the `CDS MOCServer <http://alasky.unistra.fr/MocServer/query>`_.

    The `CDS MOCServer <http://alasky.unistra.fr/MocServer/query>`_ allows the user
    to retrieve all the datasets (with their meta-data) having sources in a specific
    space-time region. This region can be a `regions.CircleSkyRegion`, a
    `regions.PolygonSkyRegion`, a `mocpy.MOC`, a `mocpy.TimeMOC`, or a `mocpy.STMOC`
    object.
    """

    URL = conf.server
    TIMEOUT = conf.timeout
    DEFAULT_FIELDS = conf.default_fields

    def __init__(self):
        super().__init__()
        self.return_moc = False

    def query_region(
        self, region=None,
        *,
        criteria=None,
        intersect="overlaps",
        return_moc=None,
        max_norder=None,
        fields=None,
        max_rec=None,
        casesensitive=False,
        coordinate_system=None,
        get_query_payload=False,
        verbose=False,
        cache=True,
    ):
        """Query the MOC Server.

        Parameters
        ----------
        region : `regions.CircleSkyRegion`, `regions.PolygonSkyRegion`, `mocpy.MOC`,
            `mocpy.TimeMOC`, or `mocpy.STMOC`
            The region to query the MOCServer with. Note that this can also be a
            space-time region with the Time-MOCs and Space-Time-MOCs.
            Defaults to None, which means that the search will be on the whole sky.
        criteria : str
            Expression to select the datasets.
            Examples of expressions can be found `on the mocserver's examples page
            <http://alasky.unistra.fr/MocServer/example>`_.
            Example: "ID=*HST*" will return datasets with HST in their ID column. The
            star means any character.
        casesensitive : Bool, optional
            Whether the search should take the case into account. By default, False.
        fields : [str], optional
            Specifies which columns to retrieve. Defaults to a pre-defined subset of
            fields. The complete list of fields can be obtained with `list_fields`.
        coordinate_system : str, optional
            This is the space system on which the coordinates are expressed. Can take
            the values ``sky``, ``mars``, ``moon``... The extended list can be printed
            with `~astroquery.mocserver.MOCServerClass.list_coordinate_systems`.
            Default is None, meaning that the results will have mixed frames.
        intersect : str, optional
            This parameter can take three different values:

            - ``overlaps`` (default) select datasets overlapping the region
            - ``covers`` returned datasets are covering the region.
            - ``encloses`` returned datasets are enclosing the region.

        max_rec : int, optional
            Maximum number of data-sets to return. By default, there is no upper limit.
        return_moc : bool, optional
            Specifies whether the output should be a `mocpy.MOC`. The returned MOC is the
            union of the MOCs of all the matching datasets. By default it is False and
            this method returns a `astropy.table.Table` object.
        max_norder : int, optional
            If ``return_moc`` is set to True, this fixes the maximum precision order
            of the returned MOC. For one dimensional MOCs (Space-MOCs and Time-MOCs),
            the order is given as an integer. For Space-Time MOCs, the order should be a
            string with the space and time orders.
            Example: 's3 t45'
        get_query_payload : bool, optional
            If True, returns a dictionary of the query payload instead of the response.
        verbose : bool, optional
            Whether to show warnings. Defaults to False.
        cache: bool, optional
            Whether the response should be cached.

        Returns
        -------
        response : `astropy.table.Table`, `mocpy.MOC`, `mocpy.TimeMOC`, or `mocpy.STMOC`
            By default, returns a table with the datasets matching the query.
            If ``return_moc`` is set to True, it gives a MOC object corresponding to the
            union of the MOCs from all the retrieved data-sets.

        """
        response = self.query_async(
            criteria=criteria,
            region=region,
            intersect=intersect,
            return_moc=return_moc,
            max_norder=max_norder,
            fields=fields,
            max_rec=max_rec,
            casesensitive=casesensitive,
            coordinate_system=coordinate_system,
            get_query_payload=get_query_payload,
            cache=cache,
        )
        if get_query_payload:
            return response
        return _parse_result(response, verbose=verbose, return_moc=return_moc)

    def query_hips(
        self,
        *,
        criteria=None,
        region=None,
        intersect="overlaps",
        return_moc=None,
        max_norder=None,
        fields=None,
        max_rec=None,
        casesensitive=False,
        coordinate_system=None,
        get_query_payload=False,
        verbose=False,
        cache=True,
    ):
        """Query the MOCServer for HiPS surveys.

        Parameters
        ----------
        criteria : str
            Expression to select the datasets.
            Examples of expressions can be found `on the mocserver's examples page
            <http://alasky.unistra.fr/MocServer/example>`_.
            Example: "ID=*HST*" will return datasets with HST in their ID column. The
            star means any character.
        casesensitive : Bool, optional
            Wheter the search should take the case into account. By default, False.
        fields : [str], optional
            Specifies which columns to retrieve. Defaults to a pre-defined subset of
            fields. The complete list of fields can be obtained with `list_fields`.
        coordinate_system : str, optional
            This is the space system on which the coordinates are expressed. Can take
            the values ``sky``, ``mars``, ``moon``... The extended list can be printed
            with `~astroquery.mocserver.MOCServerClass.list_coordinate_systems`.
            Default is None, meaning that the results will have mixed frames.
        region : `regions.CircleSkyRegion`, `regions.PolygonSkyRegion`, `mocpy.MOC`,
            `mocpy.TimeMOC`, or `mocpy.STMOC`
            The region to query the MOCServer with. Note that this can also be a
            space-time region with the Time-MOCs and Space-Time-MOCs.
        intersect : str, optional
            This parameter can take three different values:

            - ``overlaps`` (default) select datasets overlapping the region
            - ``covers`` returned datasets are covering the region.
            - ``encloses`` returned datasets are enclosing the region.

        max_rec : int, optional
            Maximum number of data-sets to return. By default, there is no upper limit.
        return_moc : bool, optional
            Specifies whether the output should be a `mocpy.MOC`. The returned MOC is the
            union of the MOCs of all the matching datasets. By default it is False and
            this method returns a `astropy.table.Table` object.
        max_norder : int, optional
            If ``return_moc`` is set to True, this fixes the maximum precision order
            of the returned MOC. For one dimensional MOCs (Space-MOCs and Time-MOCs),
            the order is given as an integer. For Space-Time MOCs, the order should be a
            string with the space and time orders.
            Example: 's3 t45'
        get_query_payload : bool, optional
            If True, returns a dictionary of the query payload instead of the response.
        verbose : bool, optional
            Whether to show warnings. Defaults to False.
        cache: bool, optional
            Whether the response should be cached.

        Returns
        -------
        response : `astropy.table.Table`, `mocpy.MOC`, `mocpy.TimeMOC`, or `mocpy.STMOC`
            By default, returns a table with the datasets matching the query.
            If ``return_moc`` is set to True, it gives a MOC object corresponding to the
            union of the MOCs from all the retrieved data-sets.

        """
        if criteria:
            criteria = f"({criteria})&&hips_frame=*"
        else:
            criteria = "hips_frame=*"
        return self.query_region(
            criteria=criteria,
            region=region,
            intersect=intersect,
            return_moc=return_moc,
            max_norder=max_norder,
            fields=fields,
            max_rec=max_rec,
            casesensitive=casesensitive,
            coordinate_system=coordinate_system,
            get_query_payload=get_query_payload,
            verbose=verbose,
            cache=cache,
        )

    @deprecated(since="v0.4.9",
                message="'find_datasets' is replaced by 'query_region' which has a new "
                        "parameter 'criteria' that accepts the expressions that "
                        "'meta_data' was accepting.")
    def find_datasets(
        self, meta_data,
        *,
        region=None,
        intersect="overlaps",
        return_moc=None,
        max_norder=None,
        fields=None,
        max_rec=None,
        casesensitive=False,
        coordinate_system=None,
        get_query_payload=False,
        verbose=False,
        cache=True,
    ):
        """Query the MOC Server.

        Parameters
        ----------
        meta_data : str
            Expression to select the datasets.
            Examples of expressions can be found `on the mocserver's examples page
            <http://alasky.unistra.fr/MocServer/example>`_.
            Example: "ID=*HST*" will return datasets with HST in their ID column. The
            star means any character.
        casesensitive : Bool, optional
            Whether the search should take the case into account. By default, False.
        fields : [str], optional
            Specifies which columns to retrieve. Defaults to a pre-defined subset of
            fields. The complete list of fields can be obtained with `list_fields`.
        coordinate_system : str, optional
            This is the space system on which the coordinates are expressed. Can take
            the values ``sky``, ``mars``, ``moon``... The extended list can be printed
            with `~astroquery.mocserver.MOCServerClass.list_coordinate_systems`.
            Default is None, meaning that the results will have mixed frames.
        region : `regions.CircleSkyRegion`, `regions.PolygonSkyRegion`, `mocpy.MOC`,
            `mocpy.TimeMOC`, or `mocpy.STMOC`
            The region to query the MOCServer with. Note that this can also be a
            space-time region with the Time-MOCs and Space-Time-MOCs.
        intersect : str, optional
            This parameter can take three different values:

            - ``overlaps`` (default) select datasets overlapping the region
            - ``covers`` returned datasets are covering the region.
            - ``encloses`` returned datasets are enclosing the region.

        max_rec : int, optional
            Maximum number of data-sets to return. By default, there is no upper limit.
        return_moc : bool, optional
            Specifies whether the output should be a `mocpy.MOC`. The returned MOC is the
            union of the MOCs of all the matching datasets. By default it is False and
            this method returns a `astropy.table.Table` object.
        max_norder : int, optional
            If ``return_moc`` is set to True, this fixes the maximum precision order
            of the returned MOC. For one dimensional MOCs (Space-MOCs and Time-MOCs),
            the order is given as an integer. For Space-Time MOCs, the order should be a
            string with the space and time orders.
            Example: 's3 t45'
        get_query_payload : bool, optional
            If True, returns a dictionary of the query payload instead of the response.
        verbose : bool, optional
            Whether to show warnings. Defaults to False.
        cache: bool, optional
            Whether the response should be cached.

        Returns
        -------
        response : `astropy.table.Table`, `mocpy.MOC`, `mocpy.TimeMOC`, or `mocpy.STMOC`
            By default, returns a table with the datasets matching the query.
            If ``return_moc`` is set to True, it gives a MOC object corresponding to the
            union of the MOCs from all the retrieved data-sets.

        """
        return self.query_region(
            criteria=meta_data,
            region=region,
            intersect=intersect,
            return_moc=return_moc,
            max_norder=max_norder,
            fields=fields,
            max_rec=max_rec,
            casesensitive=casesensitive,
            coordinate_system=coordinate_system,
            get_query_payload=get_query_payload,
            verbose=verbose,
            cache=cache,
        )

    def query_async(
        self,
        *,
        region=None,
        criteria=None,
        return_moc=None,
        max_norder=None,
        fields=None,
        max_rec=None,
        intersect="overlaps",
        coordinate_system=None,
        casesensitive=False,
        get_query_payload=False,
        cache=True,
    ):
        """Return the HTTP response rather than the parsed result.

        Parameters
        ----------
        criteria : str
            Expression to select the datasets.
            Examples of expressions can be found `on the mocserver's examples page
            <http://alasky.unistra.fr/MocServer/example>`_.
            Example: "ID=*HST*" will return datasets with HST in their ID column. The
            star means any character.
        casesensitive : Bool, optional
            Whether the search should take the case into account. By default, False.
        fields : [str], optional
            Specifies which columns to retrieve. Defaults to a pre-defined subset of
            fields. The complete list of fields can be obtained with `list_fields`.
        coordinate_system : str, optional
            This is the space system on which the coordinates are expressed. Can take
            the values ``sky``, ``mars``, ``moon``... The extended list can be printed
            with `~astroquery.mocserver.MOCServerClass.list_coordinate_systems`.
            Default is None, meaning that the results will have mixed frames.
        region : `regions.CircleSkyRegion`, `regions.PolygonSkyRegion`, `mocpy.MOC`,
            `mocpy.TimeMOC`, or `mocpy.STMOC`
            The region to query the MOCServer with. Note that this can also be a
            space-time region with the Time-MOCs and Space-Time-MOCs.
        intersect : str, optional
            This parameter can take three different values:

            - ``overlaps`` (default) select datasets overlapping the region
            - ``covers`` returned datasets are covering the region.
            - ``encloses`` returned datasets are enclosing the region.

        max_rec : int, optional
            Maximum number of data-sets to return. By default, there is no upper limit.
        return_moc : bool, optional
            Specifies whether the output should be a `mocpy.MOC`. The returned MOC is the
            union of the MOCs of all the matching datasets. By default it is False and
            this method returns a `astropy.table.Table` object.
        max_norder : int, optional
            If ``return_moc`` is set to True, this fixes the maximum precision order
            of the returned MOC. For one dimensional MOCs (Space-MOCs and Time-MOCs),
            the order is given as an integer. For Space-Time MOCs, the order should be a
            string with the space and time orders.
            Example: 's3 t45'
        get_query_payload : bool, optional
            If True, returns a dictionary of the query payload instead of the response.
        verbose : bool, optional
        cache: bool, optional
            Whether the response should be cached.

        Returns
        -------
        response : `~requests.Response`:
            The HTTP response from the
            `CDS MOCServer <http://alasky.unistra.fr/MocServer/query>`_.

        """
        request_payload = _args_to_payload(
            criteria=criteria,
            return_moc=return_moc,
            max_norder=max_norder,
            fields=fields,
            max_rec=max_rec,
            region=region,
            intersect=intersect,
            coordinate_system=coordinate_system,
            casesensitive=casesensitive,
            default_fields=self.DEFAULT_FIELDS,
        )

        params_d = {
            "method": "GET",
            "url": self.URL,
            "timeout": self.TIMEOUT,
            "cache": cache,
            "params": request_payload,
        }

        if region:
            if get_query_payload:
                return request_payload
            if not isinstance(region, (MOC, TimeMOC, STMOC)):
                return self._request(**params_d)
            # MOCs have to be sent in a multipart request
            with NamedTemporaryFile() as tmp_file:
                region.save(tmp_file.name, overwrite=True, format="fits")

                params_d.update({"files": {"moc": tmp_file.read()}})
                return self._request(**params_d)

        if get_query_payload:
            return request_payload
        return self._request(**params_d)

    def list_fields(self, keyword=None, *, cache=True):
        """List MOC Server fields.

        In the MOC Server, the fields are free. This means that anyone publishing there
        can set a new field. This results in a long set of possible fields, that are
        more or less frequent in the database.
        This method allows to retrieve all fields currently existing, with their
        occurrences and an example.

        Parameters
        ----------
        keyword : str, optional
            A keyword to filter the output for fields that have the keyword in their
            name. This is not case-sensitive.
            If you don't give a keyword, you will retrieve all existing fields.
        cache: bool, optional
            Whether the response should be cached.

        Returns
        -------
        `~astropy.table.Table`
            A table containing the field names, heir occurrence (expressed in number
            of records), and an example for each field.

        Examples
        --------
        >>> from astroquery.mocserver import MOCServer
        >>> MOCServer.list_fields("publisher")  # doctest: +REMOTE_DATA +IGNORE_OUTPUT
        <Table length=3>
          field_name   occurrence          example
            str27        int64              str70
        -------------- ---------- -------------------------
          publisher_id      32987                 ivo://CDS
         publisher_did       2871 ivo://nasa.heasarc/warps2
        hips_publisher         14                       CDS

        """
        fields_descriptions = dict(
            self._request(method="GET", url=self.URL, timeout=self.TIMEOUT, cache=cache,
                          params={"get": "example", "fmt": "json"}).json()[0])
        occurrences = [
            int(value.split("x")[0][1:]) for value in fields_descriptions.values()
        ]
        field_names = list(fields_descriptions.keys())
        examples = [value.split("ex: ")[-1] for value in fields_descriptions.values()]
        list_fields = Table(
            [field_names, occurrences, examples],
            names=["field_name", "occurrence", "example"],
        )
        list_fields.sort("occurrence", reverse=True)
        if keyword:
            return list_fields[
                [
                    keyword.casefold() in name.casefold()
                    for name in list_fields["field_name"]
                ]
            ]
        return list_fields

    def list_coordinate_systems(self):
        """Return the list of coordinate systems currently available in the MOC Server.

        This list may be enriched later, as new datasets are added into the MOC Server.

        Returns
        -------
        list
            The list of coordinate systems currently available in the MOC Server

        """
        frames = list(set(self.query_region(criteria="hips_frame=*",
                                            fields=["ID", "hips_frame"],
                                            coordinate_system=None)["hips_frame"]))
        # `C` is a special case that corresponds to both equatorial and galactic frames
        frames.append("sky")
        frames.sort()
        return frames


def _args_to_payload(
    *,
    criteria=None,
    return_moc=None,
    max_norder=None,
    fields=None,
    max_rec=None,
    region=None,
    intersect="overlaps",
    coordinate_system=None,
    casesensitive=False,
    default_fields=None,
):
    """Convert the parameters of `query_region` and `find_datasets` into a payload.

    Returns
    -------
    dict
        The payload that will be submitted to the MOC server.

    """
    request_payload = {
        "casesensitive": str(casesensitive).casefold(),
        "fmt": "json",
        "get": "record",
        "fields": _get_fields(fields, default_fields),
        "intersect": intersect.replace("encloses", "enclosed"),
        "spacesys": "C" if coordinate_system == "sky" else coordinate_system,
    }

    if region and not isinstance(region, (MOC, STMOC, TimeMOC)):
        try:
            from regions import CircleSkyRegion, PolygonSkyRegion
        except ImportError as err:
            raise ImportError(
                "The module 'regions' is mandatory to use "
                "'query_region' without a MOC. Install it with "
                "'pip install regions'"
            ) from err
        if isinstance(region, CircleSkyRegion):
            # add the cone region payload to the request payload
            request_payload.update(
                {
                    "DEC": str(region.center.dec.to(u.deg).value),
                    "RA": str(region.center.ra.to(u.deg).value),
                    "SR": str(region.radius.to(u.deg).value),
                }
            )
        elif isinstance(region, PolygonSkyRegion):
            # add the polygon region payload to the request payload
            polygon_payload = "Polygon"
            for point in region.vertices:
                polygon_payload += (
                    f" {point.ra.to(u.deg).value} {point.dec.to(u.deg).value}"
                )
            print(polygon_payload)
            request_payload.update({"stc": polygon_payload})
        # the MOCs have to be sent through the multipart and not through the payload
        else:
            # not of any accepted type
            raise ValueError(
                "'region' should be of type: 'regions.CircleSkyRegion',"
                " 'regions.PolygonSkyRegion', 'mocpy.MOC', 'mocpy.TimeMOC'"
                f" or 'mocpy.STMOC', but is of type '{type(region)}'."
            )

    if criteria:
        request_payload.update({"expr": criteria})

    if max_rec:
        request_payload.update({"MAXREC": str(max_rec)})

    if return_moc:
        if return_moc is True:
            # this is for legacy reasons return_moc used to be a boolean when the MOC
            # server could only return space MOCs.
            return_moc = "moc"
        request_payload.update({"get": return_moc})
        request_payload.update({"fmt": "ascii"})
        if max_norder:
            request_payload.update({"order": max_norder})
        else:
            request_payload.update({"order": "max"})
    return request_payload


def _get_fields(fields, default_fields):
    """Get the list of fields to be queried.

    Defaults to the list defined in conf if fields is None.

    Parameters
    ----------
    fields : list[str] or str
        The list of columns to be returned.
    default_fields : list[str]
        The default list of fields.

    """
    if fields:
        if isinstance(fields, str):
            fields = [fields]
        if "ID" not in fields:
            # ID has to be included for the server to work correctly
            fields.append("ID")
        fields = list(fields) if not isinstance(fields, list) else copy(fields)
    else:
        fields = default_fields
    return ", ".join(fields)


def _parse_result(response, *, verbose=False, return_moc):
    """Parse the response returned by the MOCServer.

    Parameters
    ----------
    response : `~requests.Response`
        The HTTP response returned by the MOCServer.
    verbose : bool, optional
        False by default.
    return_moc : str or Bool
        Whether the result is a MOC or a Table.

    Returns
    -------
    `astropy.table.Table`, `~mocpy.MOC`, `~mocpy.STMOC`, `~mocpy.TimeMOC`
        This returns a table if ``return_moc`` is not specified. Otherwise,
        a MOC of the requested kind.

    """
    if not verbose:
        commons.suppress_vo_warnings()

    if return_moc:
        result = response.text
        # return_moc==True is there to support the version when there was no choice in
        # in the MOC in output and the MOC server would only be able to return SMOCs
        if return_moc == "moc" or return_moc == "smoc" or return_moc is True:
            return MOC.from_str(result)
        if return_moc == "tmoc":
            return TimeMOC.from_str(result)
        if return_moc == "stmoc":
            return STMOC.from_str(result)
        raise ValueError(
            "'return_moc' can only take the values 'moc', 'tmoc', 'smoc',"
            f"or 'stmoc'. Got '{return_moc}'."
        )
    # return a table with the meta-data, we cast the string values for convenience
    result = response.json()
    result = [
        {key: _cast_to_float(value) for key, value in row.items()} for row in result
    ]
    return Table(rows=result)


def _cast_to_float(value):
    """Cast ``value`` to a float if possible.

    Parameters
    ----------
    value : str
        string to cast

    Returns
    -------
    float or str
        A float if it can be converted to a float. Otherwise the initial string.

    """
    try:
        return float(value)
    except (ValueError, TypeError):
        return value


MOCServer = MOCServerClass()
