# Licensed under a 3-clause BSD style license - see LICENSE.rst
import numpy as np
from numpy.testing import assert_allclose
import pytest

from astropy import coordinates
from astropy.table import Table

from six.moves.urllib_error import URLError

from ... import sdss
from ...exceptions import TimeoutError


@pytest.mark.remote_data
class TestSDSSRemote:
    # Test Case: A Seyfert 1 galaxy
    coords = coordinates.SkyCoord('0h8m05.63s +14d50m23.3s')
    mintimeout = 1e-2

    def test_images_timeout(self):
        """
        This test *must* be run before `test_sdss_image` because that query
        caches!
        """
        xid = sdss.SDSS.query_region(self.coords)
        assert len(xid) == 18
        try:
            with pytest.raises(TimeoutError):
                sdss.SDSS.get_images(matches=xid, timeout=self.mintimeout,
                                     cache=False)
        except URLError:
            pytest.xfail("Failed to timeout: instead of timing out, we got a url "
                         "error with 'No route to host'.  We don't know a "
                         "workaround for this yet.")

    def test_sdss_spectrum(self):
        xid = sdss.SDSS.query_region(self.coords, spectro=True)
        assert isinstance(xid, Table)
        sp = sdss.SDSS.get_spectra(matches=xid)

    def test_sdss_spectrum_mjd(self):
        sp = sdss.SDSS.get_spectra(plate=2345, fiberID=572)

    def test_sdss_spectrum_coords(self):
        sp = sdss.SDSS.get_spectra(self.coords)

    def test_sdss_sql(self):
        query = """
                select top 10
                  z, ra, dec, bestObjID
                from
                  specObj
                where
                  class = 'galaxy'
                  and z > 0.3
                  and zWarning = 0
                """
        xid = sdss.SDSS.query_sql(query)
        assert isinstance(xid, Table)

    def test_sdss_image(self):
        xid = sdss.SDSS.query_region(self.coords)
        assert isinstance(xid, Table)
        img = sdss.SDSS.get_images(matches=xid)

    def test_sdss_template(self):
        template = sdss.SDSS.get_spectral_template('qso')

    def test_sdss_image_run(self):
        img = sdss.SDSS.get_images(run=1904, camcol=3, field=164)

    def test_sdss_image_coord(self):
        img = sdss.SDSS.get_images(self.coords)

    def test_sdss_specobj(self):
        colnames = ['ra', 'dec', 'objid', 'run', 'rerun', 'camcol', 'field',
                    'z', 'plate', 'mjd', 'fiberID', 'specobjid', 'run2d',
                    'instrument']
        dtypes = [float, float, np.int64, int, int, int, int, float, int, int,
                  int, np.int64, int, bytes]
        data = [
            [46.8390680395307, 5.16972676625711, 1237670015125750016, 5714,
             301, 2, 185, -0.0006390358, 2340, 53733, 291, 2634685834112034816,
             26, 'SDSS'],
            [46.8705377929765, 5.42458826592292, 1237670015662621224, 5714,
             301, 3, 185, 0, 2340, 53733, 3, 2634606669274834944, 26, 'SDSS'],
            [46.8899751105478, 5.09432755808192, 1237670015125815346, 5714,
             301, 2, 186, -4.898809E-05, 2340, 53733, 287, 2634684734600407040,
             26, 'SDSS'],
            [46.8954031261838, 5.9739184644185, 1237670016199491831, 5714,
             301, 4, 185, 0, 2340, 53733, 329, 2634696279472498688, 26,
             'SDSS'],
            [46.9155836662379, 5.50671723824944, 1237670015662686398, 5714,
             301, 3, 186, 0, 2340, 53733, 420, 2634721293362030592, 26,
             'SDSS']]
        table = Table(data=[x for x in zip(*data)],
                      names=colnames, dtype=dtypes)
        xid = sdss.SDSS.query_specobj(plate=2340)
        assert isinstance(xid, Table)
        for row in table:
            i = np.nonzero(xid['specobjid'] == row['specobjid'])[0]
            assert len(i) == 1
            for j, c in enumerate(colnames):
                if dtypes[j] is float:
                    assert_allclose(xid[i][c], row[c])
                else:
                    assert xid[i][c] == row[c]

    def test_sdss_photoobj(self):
        colnames = ['ra', 'dec', 'objid', 'run', 'rerun', 'camcol', 'field']
        dtypes = [float, float, np.int64, int, int, int, int]
        data = [
            [2.01401566011947, 14.9014376776107, 1237653651835846751,
             1904, 301, 3, 164],
            [2.01643436080644, 14.8109761280994, 1237653651835846753,
             1904, 301, 3, 164],
            [2.03003450430003, 14.7653903655885, 1237653651835846845,
             1904, 301, 3, 164],
            [2.01347376262532, 14.8681488509887, 1237653651835846661,
             1904, 301, 3, 164],
            [2.18077144165426, 14.8482787058708, 1237653651835847302,
             1904, 301, 3, 164]]
        table = Table(data=[x for x in zip(*data)], names=colnames,
                      dtype=dtypes)
        xid = sdss.SDSS.query_photoobj(run=1904, camcol=3, field=164)
        assert isinstance(xid, Table)
        for row in table:
            i = np.nonzero(xid['objid'] == row['objid'])[0]
            assert len(i) == 1
            for j, c in enumerate(colnames):
                if dtypes[j] is float:
                    assert_allclose(xid[i][c], row[c])
                else:
                    assert xid[i][c] == row[c]

    @pytest.mark.xfail(reason=("Timeout isn't raised since switching to "
                               "self._request, fix it before merging #586"))
    def test_query_timeout(self):
        with pytest.raises(TimeoutError):
            sdss.SDSS.query_region(self.coords, timeout=self.mintimeout)

    @pytest.mark.xfail(reason=("Timeout isn't raised since switching to "
                               "self._request, fix it before merging #586"))
    def test_spectra_timeout(self):
        with pytest.raises(TimeoutError):
            sdss.SDSS.get_spectra(self.coords, timeout=self.mintimeout)

    def test_query_non_default_field(self):
        # A regression test for #469
        query1 = sdss.SDSS.query_region(self.coords, fields=['r', 'psfMag_r'])

        query2 = sdss.SDSS.query_region(self.coords, fields=['ra', 'dec', 'r'])
        assert isinstance(query1, Table)
        assert isinstance(query2, Table)

        assert query1.colnames == ['r', 'psfMag_r']
        assert query2.colnames == ['ra', 'dec', 'r']

    def test_query_crossid(self):
        query1 = sdss.SDSS.query_crossid(self.coords)
        query2 = sdss.SDSS.query_crossid([self.coords, self.coords])
        assert isinstance(query1, Table)
        assert query1['objID'][0] == 1237652943176138868

        assert isinstance(query2, Table)
        assert query2['objID'][0] == query1['objID'][0] == query2['objID'][1]
