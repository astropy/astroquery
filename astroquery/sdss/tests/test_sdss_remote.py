# Licensed under a 3-clause BSD style license - see LICENSE.rst
from ... import sdss
from ...exceptions import TimeoutError
from ...query import suspend_cache
from astropy import coordinates
from astropy.table import Table
from astropy.tests.helper import pytest, remote_data
import requests
import imp
imp.reload(requests)

@remote_data
def test_images_timeout():
    """
    An independent timeout test to verify that test_images_timeout in the
    TestSDSSRemote class should be working.  Consider this a regression test.
    """
    coords = coordinates.ICRS('0h8m05.63s +14d50m23.3s')
    xid = sdss.core.SDSS.query_region(coords)
    assert len(xid) == 18
    with pytest.raises(TimeoutError):
        failed = sdss.core.SDSS.get_images(matches=xid, timeout=1e-6,
                                           cache=False)

@remote_data
class TestSDSSRemote:
    # Test Case: A Seyfert 1 galaxy
    coords = coordinates.ICRS('0h8m05.63s +14d50m23.3s')
    mintimeout = 1e-6


    def test_images_timeout(self):
        """
        This test *must* be run before `test_sdss_image` because that query
        caches!
        """
        xid = sdss.core.SDSS.query_region(self.coords)
        assert len(xid) == 18
        with pytest.raises(TimeoutError):
            failed = sdss.core.SDSS.get_images(matches=xid, timeout=self.mintimeout,
                                               cache=False)

    def test_sdss_spectrum(self):
        xid = sdss.core.SDSS.query_region(self.coords, spectro=True)
        assert isinstance(xid, Table)
        sp = sdss.core.SDSS.get_spectra(matches=xid)

    def test_sdss_spectrum_mjd(self):
        sp = sdss.core.SDSS.get_spectra(plate=2345, fiberID=572)

    def test_sdss_spectrum_coords(self):
        sp = sdss.core.SDSS.get_spectra(self.coords)

    def test_sdss_image(self):
        xid = sdss.core.SDSS.query_region(self.coords)
        assert isinstance(xid, Table)
        img = sdss.core.SDSS.get_images(matches=xid)

    def test_sdss_template(self):
        template = sdss.core.SDSS.get_spectral_template('qso')

    def test_sdss_image_run(self):
        img = sdss.core.SDSS.get_images(run=1904, camcol=3, field=164)

    def test_sdss_image_coord(self):
        img = sdss.core.SDSS.get_images(self.coords)

    def test_sdss_specobj(self):
        colnames = ['ra', 'dec', 'objid', 'run', 'rerun', 'camcol', 'field',
                    'z', 'plate', 'mjd', 'fiberID', 'specobjid', 'run2d',
                    'instrument']
        dtypes = [float, float, int, int, int, int, int, float, int, int, int,
                  int, int, bytes]
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
        xid = sdss.core.SDSS.query_specobj(plate=2340)
        assert isinstance(xid, Table)
        for row in table:
            assert row in xid

    def test_sdss_photoobj(self):
        colnames = [ 'ra', 'dec', 'objid', 'run', 'rerun', 'camcol', 'field']
        dtypes = [float, float, int, int, int, int, int]
        data = [
            [2.01401566011947, 14.9014376776107, 1237653651835846751, 1904, 301, 3, 164],
            [2.01643436080644, 14.8109761280994, 1237653651835846753, 1904, 301, 3, 164],
            [2.03003450430003, 14.7653903655885, 1237653651835846845, 1904, 301, 3, 164],
            [2.01347376262532, 14.8681488509887, 1237653651835846661, 1904, 301, 3, 164],
            [2.18077144165426, 14.8482787058708, 1237653651835847302, 1904, 301, 3, 164]]
        table = Table(data=[x for x in zip(*data)], names=colnames,
                      dtype=dtypes)
        xid = sdss.core.SDSS.query_photoobj(run=1904, camcol=3, field=164)
        assert isinstance(xid, Table)
        for row in table:
            assert row in xid

    def test_query_timeout(self):
        with pytest.raises(TimeoutError):
            sdss.core.SDSS.query_region(self.coords, timeout=self.mintimeout)

    def test_spectra_timeout(self):
        with pytest.raises(TimeoutError):
            sdss.core.SDSS.get_spectra(self.coords, timeout=self.mintimeout)
