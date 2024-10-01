
import pytest

from astroquery.simbad.utils import (CriteriaTranslator, _parse_coordinate_and_convert_to_icrs,
                                     _region_to_contains, _wildcard_to_regexp)

from astropy.coordinates.builtin_frames.icrs import ICRS
from astropy.coordinates import SkyCoord


@pytest.mark.parametrize("coord_string, frame, epoch, equinox", [
    ("12 34 56.78 +12 34 56.78", None, None, None),
    ("10 +20", "galactic", None, None),
    ("10 20", "fk4", "J2000", "1950")
])
def test_parse_coordinates_and_convert_to_icrs(coord_string, frame, epoch, equinox):
    coord = _parse_coordinate_and_convert_to_icrs(coord_string, frame=frame, equinox=equinox, epoch=epoch)
    assert isinstance(coord.frame, ICRS)


def test_wildcard_to_regexp():
    # should add beginning and end operators, and translate * into .*
    assert _wildcard_to_regexp("test*") == "^test.*$"
    # should not replace escaped characters
    assert _wildcard_to_regexp(r"test\*") == "^test\\*$"
    # wildcard ? is regexp .
    assert _wildcard_to_regexp("test?") == "^test.$"


@pytest.mark.remote_data()
def test_parse_coordinates_and_convert_to_icrs_sesame():
    coord = _parse_coordinate_and_convert_to_icrs("m1")
    assert isinstance(coord.frame, ICRS)


def test_region_to_contains(monkeypatch):
    # default shape is a circle, default frame is ICRS
    assert "CIRCLE" in _region_to_contains("0 0, 1d")
    assert "ICRS" in _region_to_contains("0 0,1d")
    # invalid shapes
    with pytest.raises(ValueError, match="'rotatedbox' shape cannot be translated in ADQL for SIMBAD."):
        _region_to_contains("rotatedbox, 0 0, 1d")
    # shapes should not be case-sensitive
    box = "CONTAINS(POINT('ICRS', ra, dec), BOX('ICRS', 0.0, 0.0, 2.0, 0.025)) = 1"
    assert _region_to_contains("BoX, J2000, 2024, 0 0, 2d 1.5m") == box
    # polygons can have a lot of points
    polygon = "CONTAINS(POINT('ICRS', ra, dec), POLYGON('ICRS', 0.0, 0.0, 1.0, 2.0, 65.0, 25.0, 10.0, -9.0)) = 1"
    assert _region_to_contains("PolyGon, 0 0, 01 +02, 65 25, 10 -9") == polygon
    # here we mock a case where the coordinates are given through a name

    def mockreturn(name):
        return SkyCoord(0, 0, unit="deg")
    monkeypatch.setattr(SkyCoord, "from_name", mockreturn)
    assert _region_to_contains("zero_zero, 2d") == ("CONTAINS(POINT('ICRS', ra, dec), "
                                                    "CIRCLE('ICRS', 0.0, 0.0, 2.0)) = 1")


def test_tokenizer():
    # to regenerate tokenizer after a change in utils.py, delete `criteria_lextab.py` and run this test file again.
    lexer = CriteriaTranslator._make_lexer()
    test = "indec > 85 & (cat in ('hd','hip','ppm') | author ~ 'egret*') & otype != 'galaxy' & region(m1, 5d)"
    lexer.input(test)
    assert lexer.token().type == 'COLUMN'
    assert lexer.token().type == 'BINARY_OPERATOR'
    assert lexer.token().type == 'NUMBER'
    assert lexer.token().type == '&'
    assert lexer.token().type == '('
    assert lexer.token().type == 'COLUMN'
    assert lexer.token().type == 'IN'
    assert lexer.token().type == 'LIST'
    assert lexer.token().type == '|'
    assert lexer.token().type == 'COLUMN'
    assert lexer.token().type == 'LIKE'
    assert lexer.token().type == 'STRING'
    assert lexer.token().type == ')'
    assert lexer.token().type == '&'
    assert lexer.token().type == 'COLUMN'
    assert lexer.token().type == 'BINARY_OPERATOR'
    assert lexer.token().type == 'STRING'
    assert lexer.token().type == '&'
    assert lexer.token().type == 'REGION'


@pytest.mark.parametrize("test, result", [
    ("region(GAL,180 0,2d) & otype = 'G' & (nbref >= 10|bibyear >= 2000)",
     ("CONTAINS(POINT('ICRS', ra, dec), CIRCLE('ICRS', 86.40498828654475, 28.93617776179148, 2.0)) = 1"
      " AND otypes.otype = 'G' AND (nbref >= 10 OR bibyear >= 2000)")),
    ("author ∼ 'egret*'", "regexp(author, '^egret.*$') = 1"),
    ("cat in ('hd','hip','ppm')", "cat IN ('hd','hip','ppm')"),
    ("author !~ 'test'", "regexp(author, '^test$') = 0"),
    ("sptype < F4", "sp_type < 'F4'"),
    ("umag < 1", "allfluxes.u_ < 1"),
    ("Vmag = 10", "allfluxes.V = 10"),
    ("otypes != 'Galaxy'", "otypes.otype != 'Galaxy..'"),
    ("maintype=SNR", "basic.otype = 'SNR'"),
    ("maintypes=SNR", "basic.otype = 'SNR..'")
])  # these are the examples from http://simbad.cds.unistra.fr/guide/sim-fsam.htx
# plus added examples
def test_transpiler(test, result):
    # to regenerate transpiler after a change in utils.py, delete `criteria_parsetab.py`
    # and run this test file again.
    translated = CriteriaTranslator.parse(test)
    assert translated == result


def test_transpiler_errors(capsys):
    with pytest.raises(ValueError, match="Syntax error for sim-script criteria"):
        CriteriaTranslator.parse("otype % 'G'")
        printed = capsys.readouterr().out
        assert printed == "Unrecognized character '%' at position 6 for a sim-script criteria."
