# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
Remote tests for the NRAO archive module.
"""
import time

import pytest

from astropy import units as u
from astropy.coordinates import SkyCoord

from pyvo.dal.exceptions import DALOverflowWarning, DALQueryError

from .. import Nrao


# Vicinity of 3C273 — a heavily-observed position guaranteed to have NRAO
# data so the per-feature filters below return non-empty result sets.
KNOWN_RA = 187.27791
KNOWN_DEC = 2.05238
KNOWN_RADIUS = 0.05  # degrees

PG_RECOVERY_SIG = "canceling statement due to conflict with recovery"


def retry_on_pg_recovery(callable, *args, attempts=5, **kwargs):
    """Retry a TAP call that hit the transient Postgres-replica recovery error.
    
    The NRAO TAP backend is a Postgres streaming replica and intermittently
    raises ``canceling statement due to conflict with recovery``; the
    ``retry_on_pg_recovery`` helper retries those transient failures.
    """
    for ii in range(attempts):
        try:
            return callable(*args, **kwargs)
        except DALQueryError as exc:
            if PG_RECOVERY_SIG in str(exc) and ii + 1 < attempts:
                time.sleep(2 ** ii)
                continue
            raise


@pytest.fixture
def nrao():
    return Nrao()


@pytest.mark.remote_data
@pytest.mark.filterwarnings(
    "ignore::pyvo.dal.exceptions.DALOverflowWarning")
class TestNrao:
    """tests for the public NRAO API entrypoints."""

    def test_SgrAstar(self, tmp_path, nrao):
        nrao.cache_location = tmp_path
        retry_on_pg_recovery(nrao.query_object, 'Sgr A*', maxrec=5)

    def test_ra_dec(self, nrao):
        payload = {'ra_dec': '181.0192d -0.01928d'}
        result = retry_on_pg_recovery(nrao.query, payload)
        assert len(result) > 0

    def test_query(self, tmp_path, nrao):
        nrao.cache_location = tmp_path
        retry_on_pg_recovery(nrao.query_object, 'M83', maxrec=5)


@pytest.mark.remote_data
@pytest.mark.filterwarnings(
    "ignore::pyvo.dal.exceptions.DALOverflowWarning")
class TestRemoteAnaloguesOfMockedTests:
    """
    One remote test per mocked unit test in ``test_nrao.py``.  Each one
    sends an ADQL query of the shape the corresponding mocked test asserts
    against, and checks that the server accepts it.  ``maxrec`` is kept
    small to limit server load; ``DALOverflowWarning`` is suppressed
    because hitting maxrec just means the query was valid and the server
    had more rows to return.
    """

    MAXREC = 5

    def _cone_payload(self, **extra):
        payload = {'ra_dec': '{} {}, {}'.format(KNOWN_RA, KNOWN_DEC,
                                                KNOWN_RADIUS)}
        payload.update(extra)
        return payload

    # --- test_gen_pos_sql --------------------------------------------------

    def test_pos_cone_decimal(self, nrao):
        """Cone search via decimal RA/Dec payload (test_gen_pos_sql)."""
        result = retry_on_pg_recovery(nrao.query, self._cone_payload(),
                                       maxrec=self.MAXREC)
        assert len(result) > 0

    def test_pos_cone_sexagesimal(self, nrao):
        """Cone search via sexagesimal RA/Dec payload (test_gen_pos_sql)."""
        # 12:29:06.7 +02:03:08.6 ~ 3C273
        payload = {'ra_dec': '12:29:06.7 02:03:08.6, 0.05'}
        result = retry_on_pg_recovery(nrao.query, payload,
                                       maxrec=self.MAXREC)
        assert len(result) > 0

    def test_pos_cone_galactic(self, nrao):
        """Galactic-frame cone via SkyCoord (test_gen_pos_sql, test_galactic_query)."""
        # Sgr A* is at galactic (0, 0); query_region converts to ICRS.
        result = retry_on_pg_recovery(
            nrao.query_region,
            SkyCoord(0*u.deg, 0*u.deg, frame='galactic'),
            radius=0.05*u.deg, maxrec=self.MAXREC)
        # Sgr A* is heavily observed by VLA — expect rows.
        assert len(result) > 0

    # --- test_gen_numeric_sql ----------------------------------------------

    def test_numeric_bandwidth_filter(self, nrao):
        """Numeric filter on aggregate_bandwidth (test_gen_numeric_sql).

        Combined with a spatial constraint so the result is bounded.
        """
        result = retry_on_pg_recovery(
            nrao.query, self._cone_payload(bandwidth='>0'),
            maxrec=self.MAXREC)
        assert len(result) > 0

    # --- test_gen_str_sql --------------------------------------------------

    def test_str_project_code_wildcard(self, nrao):
        """String filter with wildcard on project_code (test_gen_str_sql)."""
        # Wide-open wildcard verifies the LIKE syntax round-trips.
        result = retry_on_pg_recovery(
            nrao.query, self._cone_payload(project_code='*'),
            maxrec=self.MAXREC)
        assert len(result) > 0

    # --- test_gen_datetime_sql ---------------------------------------------

    def test_datetime_start_date_range(self, nrao):
        """Date-range filter on t_min (test_gen_datetime_sql)."""
        payload = self._cone_payload(
            start_date='(01-01-2000 .. 31-12-2020)')
        result = retry_on_pg_recovery(nrao.query, payload,
                                       maxrec=self.MAXREC)
        assert len(result) > 0

    # --- test_gen_public_sql -----------------------------------------------

    def test_public_data_true(self, nrao):
        """public_data=True maps to proprietary_status='PUBLIC' (test_gen_public_sql).

        Confirms that PUBLIC is the literal the server actually stores.
        """
        result = retry_on_pg_recovery(
            nrao.query, self._cone_payload(), public=True,
            maxrec=self.MAXREC)
        assert len(result) > 0
        assert set(result['proprietary_status']).issubset({'PUBLIC'})

    # --- test_pol_sql ------------------------------------------------------

    def test_pol_dual_circular(self, nrao):
        """Polarization filter for dual-circular feeds (test_pol_sql)."""
        payload = self._cone_payload(polarization_type='Dual-circular')
        result = retry_on_pg_recovery(nrao.query, payload,
                                       maxrec=self.MAXREC)
        # Don't require rows: dual-circular is VLA-typical but this exact
        # spatial slice may or may not have a match.  We just need the
        # server to accept the SQL.
        assert len(result) >= 0

    # --- test_gen_band_sql -------------------------------------------------

    def test_band_l(self, nrao):
        """L-band filter via band_list (test_gen_band_sql)."""
        payload = self._cone_payload(band_list=['L'])
        result = retry_on_pg_recovery(nrao.query, payload,
                                       maxrec=self.MAXREC)
        assert len(result) >= 0

    # --- test_query --------------------------------------------------------

    def test_query_region_cone(self, nrao):
        """query_region end-to-end (test_query)."""
        result = retry_on_pg_recovery(
            nrao.query_region,
            SkyCoord(KNOWN_RA*u.deg, KNOWN_DEC*u.deg, frame='icrs'),
            radius=KNOWN_RADIUS*u.deg, maxrec=self.MAXREC)
        assert len(result) > 0
        assert 'project_code' in result.columns
        assert 'proprietary_status' in result.columns

    # --- test_tap ----------------------------------------------------------

    def test_tap_direct_adql(self, nrao):
        """query_tap accepts raw ADQL against tap_schema.obscore (test_tap).

        A spatial CONTAINS predicate is included so the query uses the
        index instead of a full table scan (the NRAO obscore table is
        large enough that the latter can exceed the pytest timeout).
        """
        adql = (
            "select top 5 obs_id, project_code, proprietary_status "
            "from tap_schema.obscore WHERE "
            "CONTAINS(POINT('ICRS',s_ra,s_dec),"
            "CIRCLE('ICRS',{ra},{dec},{r}))=1"
        ).format(ra=KNOWN_RA, dec=KNOWN_DEC, r=KNOWN_RADIUS)
        result = retry_on_pg_recovery(nrao.query_tap, adql)
        table = result.to_table()
        assert len(table) <= 5
        assert 'project_code' in table.colnames
