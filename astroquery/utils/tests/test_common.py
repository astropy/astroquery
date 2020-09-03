# -*- coding: utf-8 -*-

"""Tests for :class:`~astroquery.utils.commons`."""

__all__ = [
    "Test_TableList",
]


##############################################################################
# IMPORTS

# BUILT-IN
import tempfile
from collections import OrderedDict

# THIRD PARTY
import astropy.units as u
import numpy as np
import pytest

try:
    import asdf
except ImportError:
    HAS_ASDF = False
else:
    HAS_ASDF = True

# PROJECT-SPECIFIC
from astropy.table import QTable, Table
from astroquery.utils.commons import TableList

##############################################################################
# PARAMETERS

# Quantity Tables
qt1 = QTable(data={"a": [1, 2, 3] * u.m, "b": [4, 5, 6] * u.s})
qt2 = Table(data={"c": [7, 8, 9], "d": [10, 11, 12]})

##############################################################################
# TESTS
##############################################################################


class Test_TableList(object):
    """Tests for `~asatronat.utils.table.core.TablesList`."""

    klass = TableList

    @classmethod
    def setup_class(cls):
        """Setup any state specific to the execution."""
        # tables
        cls.qt1 = qt1
        cls.qt2 = qt2

        # tables
        cls.inp = {"table1": cls.qt1, "table2": cls.qt2}

        # ordered tables
        cls.ordered_inp = OrderedDict(cls.inp)

        # the list of tables
        cls.QT = cls.klass(
            inp=cls.ordered_inp,
            name="Name",
            reference="Reference",
            extra="Extra",
        )

        cls.tempdir = tempfile.TemporaryDirectory(dir="./")

    @classmethod
    def teardown_class(cls):
        """Teardown any state specific to the execution."""
        cls.tempdir.cleanup()

    # ----------------------

    @pytest.mark.skipif(not HAS_ASDF, reason="`asdf` not installed.")
    def test_IO(self):
        """Test read/write."""
        self.QT.write(drct=self.tempdir.name + "/saved")

        QT = self.klass.read(self.tempdir.name + "/saved")

        for q1, q2 in zip(self.QT, QT):
            assert np.all(q1 == q2)
