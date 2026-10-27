# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""SQL for the structured queries whose archive endpoints lose matches."""

from collections.abc import Mapping
from decimal import Decimal, InvalidOperation
import math

from ...exceptions import InvalidQueryError


# These configurations lack the OpenAPI /tables endpoint. Do not infer this
# capability from an HTTP failure: authentication and service failures matter.
LEGACY_METADATA = {
    'dr1': ('', 'v2.0'), 'dr2': ('', 'v2.0'), 'dr3': ('', 'v2.0'),
    'dr4': ('v1', 'v2'), 'dr5': ('v0', 'v1', 'v2', 'v3'),
    'dr6': ('v0', 'v1', 'v1.1', 'v2'),
    'dr7': ('v0', 'v1', 'v1.1', 'v1.2', 'v1.3', 'v2.0'),
    'dr8': ('v0', 'v1.0', 'v1.1', 'v2.0'),
    'dr9': ('v0', 'v1.0', 'v1.1', 'v2.0'),
    'dr10': ('v0', 'v1.0'), 'dr11': ('v0',),
}
EARLY_LRS = {
    **{dr: versions for dr, versions in LEGACY_METADATA.items()
       if dr in ('dr1', 'dr2', 'dr3', 'dr4', 'dr5')},
    'dr6': ('v0', 'v1'), 'dr7': ('v0',),
}
EARLY_MRS = {'dr6': ('v1', 'v1.1'), 'dr7': ('v0', 'v1', 'v1.1'), 'dr8': ('v0',)}
MODERN_CATALOGS = {
    'dr10': ('v2.0',), 'dr11': ('v1.0', 'v1.1', 'v2.0'),
    'dr12': ('v0', 'v1.0', 'v1.1', 'v2.0'), 'dr13': ('v0', 'v1.0'), 'dr14': ('v0',),
}


def uses_legacy_metadata(release, version):
    return version in LEGACY_METADATA.get(release, ())


def spectral_catalog(release, version, resolution, *, stellar=False):
    """Choose the query's population, not just a table with usable columns."""
    if not uses_legacy_metadata(release, version) and version not in MODERN_CATALOGS.get(release, ()):
        raise InvalidQueryError(
            f'No verified default catalog for {release}/{version}; inspect get_tables_metadata() '
            'and use query_catalog() or an explicit catalog_name.'
        )
    if resolution == 'low':
        if version in EARLY_LRS.get(release, ()):
            return 'stellar' if stellar else 'catalogue'
        return 'combined'
    if release in ('dr6', 'dr7', 'dr8') or (release == 'dr9' and version != 'v0'):
        return 'med_stellar' if stellar else 'med_catalogue'
    return 'med_combined'


def identifier(name):
    # Callers validate names against the actual relation metadata as well.
    return '"' + str(name).replace('"', '""') + '"'


def literal(value, metadata):
    datatype = str(next((metadata[k] for k in ('datatype', 'data_type', 'type', 'dbtype', 'dtype')
                         if metadata.get(k)), '')).lower().split('(', 1)[0].strip()
    if value is None:
        raise InvalidQueryError('Use an explicit null operation to query missing values.')
    if datatype in {'short', 'int', 'integer', 'long', 'bigint', 'smallint', 'int32', 'int64',
                    'float', 'real', 'double', 'double precision', 'decimal', 'numeric', 'float32', 'float64'}:
        try:
            number = Decimal(str(value))
            if not number.is_finite():
                raise ValueError
            if datatype in {'short', 'int', 'integer', 'long', 'bigint', 'smallint', 'int32', 'int64'}:
                if number != number.to_integral_value():
                    raise ValueError
            return str(number)
        except (ValueError, InvalidOperation) as error:
            raise InvalidQueryError(f'Expected a finite {datatype} constraint.') from error
    if datatype in {'boolean', 'bool'}:
        if str(value).lower() not in {'true', 'false', '0', '1'}:
            raise InvalidQueryError('Expected a boolean constraint.')
        return 'TRUE' if str(value).lower() in {'true', '1'} else 'FALSE'
    if not datatype:
        raise InvalidQueryError('SQL constraints require a declared column datatype.')
    # Escape strings independently of PostgreSQL standard_conforming_strings.
    return "E'" + str(value).replace('\\', '\\\\').replace("'", "''") + "'"


def constraints_sql(constraints, schema):
    parts = []
    operations = {'equal': '=', 'notequal': '<>', 'less': '<', 'lessequal': '<=',
                  'greater': '>', 'greaterequal': '>='}
    for item in ([constraints] if isinstance(constraints, Mapping) else constraints or ()):
        name = item['column_name']
        column = 't.' + identifier(name)
        operation = str(item.get('operation', '')).lower()
        if operation == 'between':
            for bound, op in (('min', '>='), ('max', '<=')):
                if item.get(bound) not in (None, ''):
                    parts.append(f'{column} {op} {literal(item[bound], schema[name])}')
        elif operation in ('isnull', 'notnull'):
            parts.append(f'{column} IS {"NOT " if operation == "notnull" else ""}NULL')
        elif operation == 'in':
            values = item.get('select', item.get('textarea', item.get('constraint')))
            if isinstance(values, str):
                values = [v.strip() for v in values.lstrip('\ufeff').splitlines()
                          if v.strip() and not v.lstrip().startswith('#')]
            if not isinstance(values, (list, tuple)) or not values:
                raise InvalidQueryError('An in constraint requires a nonempty list or newline-separated values.')
            parts.append(f'{column} IN ({", ".join(literal(v, schema[name]) for v in values)})')
        elif operation == 'contains':
            if item.get('constraint') is None:
                raise InvalidQueryError('A contains constraint requires a value.')
            value = literal('%' + str(item['constraint']) + '%', {'datatype': 'text'})
            parts.append(f'{column}::text ILIKE {value}')
        elif operation in operations:
            parts.append(f'{column} {operations[operation]} {literal(item.get("constraint"), schema[name])}')
        else:
            raise InvalidQueryError(f'Unsupported structured SQL operation: {operation!r}.')
    return parts


def _position(ra, dec, radius):
    try:
        ra, dec, radius = map(float, (ra, dec, radius))
        if not all(map(math.isfinite, (ra, dec, radius))) or not (-90 <= dec <= 90 and 0 < radius <= 648000):
            raise ValueError
    except (TypeError, ValueError) as error:
        raise InvalidQueryError('Positions require finite RA/Dec and a radius in (0, 180 degrees].') from error
    return ra % 360, dec, math.radians(radius / 3600)


def positions_sql(position):
    """Return input rows and matching mode, preserving physical input line IDs."""
    if not isinstance(position, Mapping) or len(position) != 1:
        raise InvalidQueryError('Specify exactly one cone, proximity or rect constraint.')
    kind, values = next(iter(position.items()))
    if kind not in {'cone', 'proximity', 'rect'} or not isinstance(values, Mapping):
        raise InvalidQueryError('Unsupported structured position constraint.')
    allowed = {'cone': {'racenter', 'deccenter', 'radius', 'cone_nearestonly'},
               'proximity': {'radecTextarea', 'defaultRadius', 'proximity_nearestonly'},
               'rect': {'ramin', 'ramax', 'decmin', 'decmax'}}
    if set(values) - allowed[kind]:
        raise InvalidQueryError(f'Unsupported {kind} constraint fields: {sorted(set(values) - allowed[kind])}.')
    if kind == 'rect':
        return None, False
    nearest = values.get(kind + '_nearestonly', False)
    if not isinstance(nearest, bool):
        raise InvalidQueryError('nearest_only must be a boolean.')
    if kind == 'cone':
        rows = [(0, *_position(values.get('racenter'), values.get('deccenter'), values.get('radius', 2)))]
    else:
        text = values.get('radecTextarea')
        if not isinstance(text, str):
            raise InvalidQueryError('proximity requires radecTextarea containing positions.')
        rows = []
        indices = (0, 1, 2)
        for line_number, line in enumerate(text.lstrip('\ufeff').splitlines(), 1):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            delimiter = next((d for d in (',', ';', '\t') if d in line), None)
            fields = line.split(delimiter) if delimiter else line.split()
            fields = [field.strip() for field in fields]
            names = [field.lower() for field in fields]
            if not rows and 'ra' in names and 'dec' in names:
                radius_index = next((i for i, name in enumerate(names)
                                     if name in {'r', 'search_radius'} or name.startswith('radius')), -1)
                indices = (names.index('ra'), names.index('dec'), radius_index)
                continue
            try:
                ira, idec, iradius = indices
                radius = (fields[iradius] if 0 <= iradius < len(fields) and fields[iradius]
                          else values.get('defaultRadius', 2))
                rows.append((line_number, *_position(fields[ira], fields[idec], radius)))
            except IndexError as error:
                raise InvalidQueryError(f'Incomplete proximity position on input line {line_number}.') from error
        if not rows:
            raise InvalidQueryError('proximity contains no positions.')
    return ', '.join('(' + ', '.join(map(str, row)) + ')' for row in rows), nearest


def catalog_sql(catalog, schema, *, constraints, position, columns, sort_by, sort_order, max_rows, page):
    """Build a bounded SELECT; all filtering precedes nearest selection."""
    if sort_order not in ('asc', 'desc'):
        raise InvalidQueryError('sort_order must be asc or desc.')
    selected = list(columns or schema)
    parts = constraints_sql(constraints, schema)
    values, nearest = positions_sql(position) if position else (None, False)
    if nearest and page != 1:
        raise InvalidQueryError('nearest_only=True requires page=1.')
    # Note: comparing complete rows costs more on wide catalogs; replace
    # the final tie-breaker only when the archive exposes a verified unique key.
    # Equal rows remain separate; obsid is not a unique MRS identifier.
    stable = [f't.{identifier(n)}' for n in ('mobsid', 'obsid') if n in schema]
    stable.append('t::text')
    ordering = ([f't.{identifier(sort_by)} {sort_order}'] if sort_by else []) + stable
    select = ', '.join('t.' + identifier(n) for n in selected)
    extra_schema = {}
    if values is not None:
        distance = 'degrees(spos(t."ra", t."dec") <-> spos(p.input_ra, p.input_dec)) * 3600'
        parts.insert(0, 'spos(t."ra", t."dec") @ scircle(spos(p.input_ra, p.input_dec), p.input_sep)')
        match_order = [distance] + ordering
        inner = f'SELECT t.* FROM {identifier(catalog)} AS t WHERE ' + ' AND '.join(parts)
        if nearest:
            inner += ' ORDER BY ' + ', '.join(match_order) + ' LIMIT 1'
        extras = {'inputobjs_input_line': ('p.input_line', 'long', None),
                  'inputobjs_input_ra': ('p.input_ra', 'double', 'deg'),
                  'inputobjs_input_dec': ('p.input_dec', 'double', 'deg'),
                  'inputobjs_dist_arcsec': (distance, 'double', 'arcsec')}
        if set(extras) & set(selected):
            raise InvalidQueryError('Catalog columns collide with spatial result columns.')
        select += ', ' + ', '.join(f'{expr} AS {identifier(name)}' for name, (expr, _, _) in extras.items())
        extra_schema = {name: {'datatype': dtype, 'unit': unit} for name, (_, dtype, unit) in extras.items()}
        sql = f'WITH p(input_line, input_ra, input_dec, input_sep) AS (VALUES {values}) '
        sql += f'SELECT {select} FROM p CROSS JOIN LATERAL ({inner}) AS t'
        ordering = ['p.input_line'] + (ordering if sort_by and not nearest else match_order)
    else:
        if position:
            rectangle = position['rect']
            try:
                ramin, ramax, decmin, decmax = (float(rectangle[k]) for k in ('ramin', 'ramax', 'decmin', 'decmax'))
                if not all(map(math.isfinite, (ramin, ramax, decmin, decmax))) or not (
                        0 <= ramin <= ramax <= 360 and -90 <= decmin <= decmax <= 90):
                    raise ValueError
            except (KeyError, TypeError, ValueError) as error:
                raise InvalidQueryError('rect requires ordered finite RA and Dec bounds in degrees.') from error
            parts.extend((f't."ra" BETWEEN {ramin} AND {ramax}', f't."dec" BETWEEN {decmin} AND {decmax}'))
        sql = f'SELECT {select} FROM {identifier(catalog)} AS t'
        if parts:
            sql += ' WHERE ' + ' AND '.join(parts)
    sql += ' ORDER BY ' + ', '.join(ordering)
    sql += f' LIMIT {max_rows} OFFSET {(page - 1) * max_rows}'
    return sql, extra_schema
