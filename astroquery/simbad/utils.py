"""Contains utility functions to support legacy Simbad interface."""

from collections import deque
import json
from pathlib import Path
import re

from astropy.coordinates import SkyCoord, Angle
from astropy.utils.parsing import lex, yacc
from astropy.utils import classproperty
from astropy.utils.data import get_pkg_data_filename

with open(get_pkg_data_filename(str(Path("data") / "query_criteria_fields.json"))) as f:
    query_criteria_fields = json.load(f)


def _catch_deprecated_fields_with_arguments(votable_field):
    """Raise informative errors for deprecated votable fields.

    These fields are a mix between selecting columns and applying a criteria.
    This could be mimicked if there is a huge demand when query criteria is really
    removed from codebase and no longer deprecated. For now, we'll give pointers
    on how they can be replaced.

    Parameters
    ----------
    votable_field : str
        one of the former votable fields (see `~astroquery.simbad.SimbadClass.list_votable_fields`)
    """
    if re.match(r"^(ra|dec|coo)\(.+\)$", votable_field):
        raise ValueError("Coordinates conversion and formatting is no longer supported within the "
                         "SIMBAD module. This can be done with the `~astropy.coordinates` module."
                         "Coordinates are now per default in degrees and in the ICRS frame.")
    if votable_field.startswith("id("):
        raise ValueError("Catalog Ids are no longer supported as an output option. "
                         "Good replacements can be `~astroquery.simbad.SimbadClass.query_cat` "
                         "or `~astroquery.simbad.SimbadClass.query_objectids`.")
    if votable_field.startswith("bibcodelist("):
        raise ValueError("Selecting a range of years for bibcode is removed. You can still use "
                         "bibcodelist without parenthesis and get the full list of bibliographic references.")
    if votable_field in ["membership", "link_bibcode"]:
        raise ValueError("The hierarchy information is no longer an additional field. "
                         "It has been replaced by the 'query_hierarchy' method.")
    if votable_field in ["pos", "posa"]:
        raise ValueError("Successive measurements of the positions are no longer stored "
                         "in SIMBAD. The columns 'ra' and 'dec' contain the most precise "
                         "measurement recorded by the SIMBAD team. For historical values, "
                         "search within VizieR (accessible via 'astroquery.vizier').")
    if votable_field == "sp_nature":
        raise ValueError("Spectral nature is no longer stored in SIMBAD. You can get the "
                         "of the spectral type classification in 'sp_bibcode'.")
    if votable_field == "typed_id":
        raise ValueError("'typed_id' is no longer a votable field. It is now added by "
                         "default in 'query_objects' and 'query_region'")
    if votable_field in ["ubv", "uvby1", "uvby"]:
        raise ValueError("Magnitudes are now handled very differently in SIMBAD. See this "
                         "section of the documentation: "
                         "https://astroquery.readthedocs.io/en/latest/simbad/simbad_evolution.html#optical-filters")

# ----------------------------
# Support wildcard argument
# ----------------------------


def _wildcard_to_regexp(wildcard_string):
    r"""Translate a wildcard string into a regexp.

    It prepends a ``^`` and appends a ``$`` to denote the start
    and end of string that are implicit in the wildcard language.

    It replaces ``*`` by its regex equivalent ``.*`` but does not
    replace the escaped ``\\*`` that corresponds to the short name
    of the star otype.

    A whitespace `` `` is replaced by `` +``.

    The single character match ``?`` is ``.`` in regex.

    Parameters
    ----------
    wildcard_string : str
        A string containing wildcard characters.

    Returns
    -------
    str
        A regexp that reproduces the wildcard expression. Works on a
        best approximation basis. Note that wildcards are case insensitive
        while regexp are not.

    Examples
    --------
    >>> from astroquery.simbad.utils import _wildcard_to_regexp
    >>> _wildcard_to_regexp("hd *1")
    '^hd +.*1$'
    """
    # escape regexp characters that are not wildcard characters
    wildcard_string = re.sub(r"([.+^${}()|])", r"\\\\\1", wildcard_string)
    # replaces "*" by its regex equivalent ".*"
    # but not "\*" that refers to the otype "*"
    wildcard_string = re.sub(r"(?<!\\)\*", ".*", wildcard_string)
    # any single character is '.' in regexp
    wildcard_string = wildcard_string.replace("?", ".")
    # start and end of string + whitespace means any number of whitespaces
    return f"^{wildcard_string.replace(' ', ' +')}$"

# ----------------------------------------
# Support legacy sim-script query language
# ----------------------------------------


def _region_to_contains(region_string):
    """Translate a region string into an ADQL CONTAINS clause.

    Parameters
    ----------
    region_string : str
        A `simbad region <http://simbad.cds.unistra.fr/guide/sim-fsam.htx>_` string.

    Returns
    -------
    string
        An ADQL CONTAINS clause.
    """
    contains = "CONTAINS(POINT('ICRS', ra, dec), "
    region_params = deque(re.split(r", *", region_string))
    legacy_shapes = {"ellipse", "zone", "rotatedbox"}
    valid_shapes = {"circle", "box", "polygon"}

    # this part is a bit awkward because the optional parameters come first
    # so we read shape_type, frame, epoch, and equinox while popping them out

    region_type = "circle"
    frame = "ICRS"
    epoch = None
    equinox = None  # default values

    if region_params[0].casefold() in legacy_shapes:
        raise ValueError(f"'{region_params[0]}' shape cannot be translated in ADQL for SIMBAD.")
    elif region_params[0].casefold() in valid_shapes:
        region_type = region_params.popleft().casefold()

    # translates from simbad to astropy frames names
    frame_translate = {
        "GAL": "galactic",
        "ICRS": "icrs",
        "FK4": "fk4",
        "FK5": "fk5",
        "SGAL": "supergalactic",
        "ECL": "CustomBarycentricEcliptic",  # as described in 1977A&A....58....1L
    }

    if region_params[0].upper() in frame_translate.keys():
        frame = region_params.popleft().upper()
    frame = frame_translate[frame]

    if re.match(r"[B|J](\d{4}|\d{4}.\d*)", region_params[0]):
        epoch = region_params.popleft()

    if re.match(r"(\d{4}|\d{4}.\d*)", region_params[0]):
        equinox = region_params.popleft()

    if region_type == "circle":
        center = _parse_coordinate_and_convert_to_icrs(region_params[0],
                                                       frame=frame, epoch=epoch, equinox=equinox)
        radius = Angle(region_params[1])
        contains += (
            f"CIRCLE('ICRS', {center.ra.value},"
            f" {center.dec.value}, {radius.to('deg').value})) = 1"
        )

    elif region_type == "box":
        center = _parse_coordinate_and_convert_to_icrs(region_params[0],
                                                       frame=frame, epoch=epoch, equinox=equinox)
        dimensions = region_params[1].split(" ")
        width = Angle(dimensions[0]).to("deg").value
        height = Angle(dimensions[1]).to("deg").value
        contains += f"BOX('ICRS', {center.ra.value}, {center.dec.value}, {width}, {height})) = 1"

    elif region_type == "polygon":
        contains += "POLYGON('ICRS'"
        for token in region_params:
            coordinates = _parse_coordinate_and_convert_to_icrs(token,
                                                                frame=frame, epoch=epoch, equinox=equinox)
            contains += f", {coordinates.ra.value}, {coordinates.dec.value}"
        contains += ")) = 1"

    return contains


def _parse_coordinate_and_convert_to_icrs(string_coordinate, *,
                                          frame="icrs", epoch=None, equinox=None):
    """Convert from sim-script string to SkyCoord.

    Parameters
    ----------
    string_coordinate : str
        Should be in the sim-script syntax defined here
        http://simbad.cds.unistra.fr/guide/sim-fsam.htx
    frame : str
    epoch : str
    equinox : str

    Returns
    -------
    `~astropy.coordinates.SkyCoord`
    """
    if re.search(r"\d+ *[\+\- ]\d+", string_coordinate):
        if equinox:
            equinox = f"J{equinox}"
        center = SkyCoord(string_coordinate, unit="deg", frame=frame, obstime=epoch, equinox=equinox)
    else:
        center = SkyCoord.from_name(string_coordinate)
    return center.transform_to("icrs")


def _convert_column(column, operator=None, value=None):
    """Convert columns from the sim-script language into ADQL.

    This checks the criteria names for fields that changed names between
    sim-script and SIMBAD TAP (the old and new SIMBAD APIs). There are two exceptions
    for magnitudes and fluxes where in sim-script the argument that was used in the criteria
    was different from the name that wes used in votable_field (ex: flux(V) to add the
    column and Vmag to add in a criteria).
    """
    # handle the change of syntax on otypes manually because they are difficult to automatize
    if column == "maintype":
        column = "basic.otype"
    elif column == "otype":
        column = "otypes.otype"
    elif column == "maintypes":
        column = "basic.otype"
        value = f"{value[:-1]}..'"
    elif column == "otypes":
        column = "otypes.otype"
        value = f"{value[:-1]}..'"
    # magnitudes are also an exception
    elif "mag" in column:
        column = column.replace("mag", "")
        if len(column) == 1 and column.islower():
            column = column + "_"
        column = "allfluxes." + column
    # the other cases are a simple replacement by the new name
    elif column in query_criteria_fields:
        if query_criteria_fields[column]["type"] == "alias":
            column = query_criteria_fields[column]["tap_column"]
    if operator and value:
        return column + " " + operator + " " + value
    return column


class CriteriaTranslator:

    _tokens = [
        "REGION",
        "BINARY_OPERATOR",
        "IN",
        "LIST",
        "LIKE",
        "NOTLIKE",
        "NUMBER",
        "STRING",
        "COLUMN"
    ]

    @classproperty(lazy=True)
    def _parser(cls):
        return cls._make_parser()

    @classproperty(lazy=True)
    def _lexer(cls):
        return cls._make_lexer()

    @classmethod
    def _make_lexer(cls):
        tokens = cls._tokens  # noqa: F841

        t_NUMBER = r"\d*\.?\d+"  # noqa: F841

        literals = ["&", r"\|", r"\(", r"\)"]  # noqa: F841

        def t_IN(t):
            r"in\b"
            t.value = "IN"
            return t

        def t_LIST(t):
            r"\( *'[^\)]*\)"
            return t

        def t_BINARY_OPERATOR(t):
            r">=|<=|!=|>|<|="
            return t

        def t_LIKE(t):
            r"~|∼"  # the examples in SIMBAD documentation use this glyph '∼'
            t.value = "LIKE"
            return t

        def t_NOTLIKE(t):
            r"!~|!∼"
            t.value = "NOT LIKE"
            return t

        def t_STRING(t):
            r"'[^']*'"
            return t

        def t_REGION(t):
            r"region\([^\)]*\)"
            t.value = t.value.replace("region(", "")[:-1]
            return t

        def t_COLUMN(t):
            r'[a-zA-Z_*][a-zA-Z_0-9*]*'
            return t

        t_ignore = ", \t\n"  # noqa: F841

        def t_error(t):
            r"."
            print(f"Unrecognized character '{t.value[0]}' at position {t.lexpos} for a sim-script criteria.")
            t.lexer.skip(1)  # skip the illegal token (don't process it)

        return lex(lextab="criteria_lextab", package="astroquery/simbad", reflags=re.I | re.UNICODE)

    @classmethod
    def _make_parser(cls):

        tokens = cls._tokens  # noqa: F841

        def p_criteria_OR(p):
            r"""criteria : criteria '|' criteria"""
            p[0] = p[1] + " OR " + p[3]

        def p_criteria_AND(p):
            """criteria : criteria '&' criteria"""
            p[0] = p[1] + " AND " + p[3]

        def p_criteria_parenthesis(p):
            """criteria : '(' criteria ')'"""
            p[0] = "(" + p[2] + ")"

        def p_criteria_string(p):
            """criteria : COLUMN BINARY_OPERATOR STRING
                        | COLUMN BINARY_OPERATOR NUMBER
                        | COLUMN IN LIST
            """
            p[0] = _convert_column(p[1], p[2], p[3])

        def p_criteria_string_no_ticks(p):
            """criteria : COLUMN BINARY_OPERATOR COLUMN
            """
            # sim-script also tolerates omitting the '' at the right side of operators
            p[0] = _convert_column(p[1], p[2], f"'{p[3]}'")

        def p_criteria_like(p):
            """criteria : COLUMN LIKE STRING"""
            p[0] = "regexp(" + _convert_column(p[1]) + ", '" + _wildcard_to_regexp(p[3][1:-1]) + "') = 1"

        def p_criteria_notlike(p):
            """criteria : COLUMN NOTLIKE STRING"""
            p[0] = "regexp(" + _convert_column(p[1]) + ", '" + _wildcard_to_regexp(p[3][1:-1]) + "') = 0"

        def p_criteria_region(p):
            """criteria : REGION"""
            p[0] = _region_to_contains(p[1])

        def p_error(p):
            raise ValueError(f"Syntax error for sim-script criteria at line {p.lineno}"
                             f" character {p.lexpos - 1}")

        return yacc(tabmodule="criteria_parsetab", package="astroquery/simbad")

    @classmethod
    def parse(cls, criteria):
        return cls._parser.parse(criteria, lexer=cls._lexer)
