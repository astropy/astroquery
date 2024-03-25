"""Contains utility functions to support legacy Simbad interface."""

from collections import deque
import re

from astropy.coordinates import SkyCoord, Angle
from astropy.utils.parsing import lex, yacc
from astropy.utils import classproperty


def list_wildcards():
    """
    Displays the available wildcards that may be used in SIMBAD queries and
    their usage.

    Examples
    --------
    >>> from astroquery.simbad.utils import list_wildcards
    >>> list_wildcards()
    * : Any string of characters (including an empty one)
    ? : Any character (exactly one character)
    [abc] : Exactly one character taken in the list. Can also be defined by a range of characters: [A-Z]
    [^0-9] : Any (one) character not in the list.
    """
    WILDCARDS = {'*': 'Any string of characters (including an empty one)',
                 '?': 'Any character (exactly one character)',
                 '[abc]': ('Exactly one character taken in the list. '
                           'Can also be defined by a range of characters: [A-Z]'),
                 '[^0-9]': 'Any (one) character not in the list.'}
    print("\n".join(f"{k} : {v}" for k, v in WILDCARDS.items()))


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
    if re.match(r"^flux.*\(.+\)$", votable_field):
        raise ValueError("Criteria on filters are deprecated when defining Simbad's output. "
                         "See section on filters in "
                         "https://astroquery.readthedocs.io/en/latest/simbad/simbad_evolution.html")
    if re.match(r"^(ra|dec|coo)\(.+\)$", votable_field):
        raise ValueError("Coordinates conversion and formatting is no longer supported. This "
                         "can be done with the `~astropy.coordinates` module."
                         "Coordinates are now per default in degrees and in the ICRS frame.")
    if votable_field.startswith("id("):
        raise ValueError("Catalog Ids are no longer supported as an output option. "
                         "A good replacement can be `~astroquery.simbad.SimbadClass.query_cat`. "
                         "See section on catalogs in "
                         "https://astroquery.readthedocs.io/en/latest/simbad/simbad_evolution.html")
    if votable_field.startswith("bibcodelist("):
        raise ValueError("Selecting a range of years for bibcode is removed. You can still use "
                         "bibcodelist without parenthesis and get the full list of bibliographic references. "
                         "See https://astroquery.readthedocs.io/en/latest/simbad/simbad_evolution.html for "
                         "more details.")

# ----------------------------
# To support wildcard argument
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

    else:
        raise ValueError("Simbad TAP supports regions of types 'circle', 'box', or 'polygon'.")
    return contains


def _parse_coordinate_and_convert_to_icrs(string_coordinate, *,
                                          frame="icrs", epoch=None, equinox=None):
    """Convert a string into a SkyCoord object in the ICRS frame."""
    if re.search(r"\d+ *[\+\- ]\d+", string_coordinate):
        center = SkyCoord(string_coordinate, unit="deg", frame=frame, obstime=epoch, equinox=equinox)
    else:
        center = SkyCoord.from_name(string_coordinate)
    return center.transform_to("icrs")


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
            r"~|∼"  # the examples in SIMBAD documentation use the strange long ∼
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
            r'[a-zA-Z_][a-zA-Z_0-9]*'
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
            """
            p[0] = p[1] + " " + p[2] + " " + p[3]

        def p_criteria_like(p):
            """criteria : COLUMN LIKE STRING"""
            p[0] = "regexp(" + p[1] + ", '" + _wildcard_to_regexp(p[3][1:-1]) + "') = 1"

        def p_criteria_notlike(p):
            """criteria : COLUMN NOTLIKE STRING"""
            p[0] = "regexp(" + p[1] + ", '" + _wildcard_to_regexp(p[3][1:-1]) + "') = 0"

        def p_criteria_in(p):
            """criteria : COLUMN IN LIST"""
            p[0] = p[1] + " IN " + p[3]

        def p_criteria_region(p):
            """criteria : REGION"""
            p[0] = _region_to_contains(p[1])

        def p_error(p):
            raise ValueError("Syntax error for sim-script criteria")

        return yacc(tabmodule="criteria_parsetab", package="astroquery/simbad")

    @classmethod
    def parse(cls, criteria):
        return cls._parser.parse(criteria, lexer=cls._lexer)
