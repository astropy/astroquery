# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
Tests for linelists.core utility functions
"""
import numpy as np
import pytest

from astroquery.linelists.core import parse_molid


class TestParseMolid:
    """Tests for the parse_molid function"""

    def test_parse_molid_integer(self):
        """Test parsing integer molecule IDs"""
        # Basic integer
        assert parse_molid(18003) == '018003'
        assert parse_molid(28001) == '028001'
        assert parse_molid(1) == '000001'
        assert parse_molid(999999) == '999999'

    def test_parse_molid_numpy_integers(self):
        """Test parsing numpy integer types"""
        assert parse_molid(np.int32(18003)) == '018003'
        assert parse_molid(np.int64(28001)) == '028001'

    def test_parse_molid_string(self):
        """Test parsing string molecule IDs"""
        # Already zero-padded
        assert parse_molid('018003') == '018003'
        assert parse_molid('028001') == '028001'
        assert parse_molid('000001') == '000001'

        # With extra text (like "028001 CO")
        assert parse_molid('028001 CO') == '028001'
        assert parse_molid('018003 H2O') == '018003'

        # Non-zero-padded strings
        assert parse_molid('18003') == '018003'
        assert parse_molid('1') == '000001'

    def test_parse_molid_edge_cases(self):
        """Test edge cases"""
        # Zero
        assert parse_molid(0) == '000000'
        assert parse_molid('000000') == '000000'

        # Maximum valid 6-digit number
        assert parse_molid(999999) == '999999'
        assert parse_molid('999999') == '999999'

    def test_parse_molid_errors(self):
        """Test that invalid inputs raise appropriate errors"""
        # Integer too large (more than 6 digits)
        with pytest.raises(ValueError, match="fewer than 6 digits"):
            parse_molid(1000000)

        with pytest.raises(ValueError, match="fewer than 6 digits"):
            parse_molid(9999999)

        # Invalid string format
        with pytest.raises(ValueError, match="length-6 string of numbers"):
            parse_molid('not a number')

        with pytest.raises(ValueError, match="length-6 string of numbers"):
            parse_molid('abcdef')

        # Invalid types
        with pytest.raises(ValueError, match="integer or a length-6 string"):
            parse_molid(18.003)  # float

        with pytest.raises(ValueError, match="integer or a length-6 string"):
            parse_molid([18003])  # list

        with pytest.raises(ValueError, match="integer or a length-6 string"):
            parse_molid(None)
