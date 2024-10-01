# Licensed under a 3-clause BSD style license - see LICENSE.rst
import numpy as np
from numpy.testing import assert_allclose
import pytest

import astropy.units as u
from astropy.coordinates import SkyCoord
from astropy.table import Table
from astropy.utils.exceptions import AstropyUserWarning

from urllib.error import URLError

# Timeout is the superclass of both ReadTimeout and ConnectTimeout
from requests.exceptions import Timeout

from astroquery import sdss
from astroquery.exceptions import TimeoutError

# DR11 is a quasi-internal data release that does not have SkyServer support.
dr_list = (8, 9, 10, 12, 13, 14, 15, 16, 17, 18)
dr_warn_list = (8, 9)


@pytest.mark.remote_data
class TestSDSSRemote:
    # Test Case: A Seyfert 1 galaxy
    coords = SkyCoord('0h8m05.63s +14d50m23.3s')
    mintimeout = 1e-2

    @pytest.fixture()
    def large_results(self):
        # Large list of objects for regression tests
        query = "select top 1000 z, ra, dec, bestObjID from specObj where class = 'galaxy' and programname = 'eboss'"
        results = sdss.SDSS.query_sql(query)
        coords_large = SkyCoord(ra=results['ra'], dec=results['dec'], unit='deg')
        return coords_large

    def test_images_timeout(self):
        """
        This test *must* be run before `test_sdss_image` because that query
        caches!
        """
        xid = sdss.SDSS.query_region(self.coords, width=2.0 * u.arcsec)
        assert len(xid) == 18
        try:
            with pytest.raises(TimeoutError):
                sdss.SDSS.get_images(matches=xid, timeout=self.mintimeout,
                                     cache=False)
        except URLError:
            pytest.xfail("Failed to timeout: instead of timing out, we got a url "
                         "error with 'No route to host'.  We don't know a "
                         "workaround for this yet.")

    @pytest.mark.parametrize("dr", dr_list)
    def test_sdss_spectrum(self, dr):
        if dr in dr_warn_list:
            with pytest.warns(AstropyUserWarning, match='Field info are not available for this data release'):
                xid = sdss.SDSS.query_region(self.coords, width=2.0 * u.arcsec, spectro=True, data_release=dr)
        else:
            xid = sdss.SDSS.query_region(self.coords, width=2.0 * u.arcsec, spectro=True, data_release=dr)

        assert isinstance(xid, Table)
        downloaded_files = sdss.SDSS.get_spectra(matches=xid, data_release=dr)
        assert len(downloaded_files) == len(xid)

    def test_sdss_spectrum_plate_mjd_fiber(self):
        """These plates are only available in relatively recent data releases.
        """
        downloaded_files = sdss.SDSS.get_spectra(plate=9403, mjd=58018, fiberID=485, data_release=16)
        assert len(downloaded_files) == 1
        downloaded_files = sdss.SDSS.get_spectra(plate=10909, mjd=58280, fiberID=485, data_release=16)
        assert len(downloaded_files) == 1

    def test_sdss_spectrum_field_mjd_catalog(self):
        """These eFEDS spectra are only available in data releases >= 18.

        https://data.sdss.org/sas/dr18/spectro/sdss/redux/v6_0_4/spectra/full/15170p/59292/spec-15170-59292-04570401475.fits
        https://data.sdss.org/sas/dr18/spectro/sdss/redux/v6_0_4/spectra/full/15265p/59316/spec-15265-59316-04592713531.fits
        """
        matches = Table()
        matches['fieldID'] = [15170, 15265]
        matches['mjd'] = [59292, 59316]
        matches['catalogID'] = [4570401475, 4592713531]
        matches['run2d'] = ['v6_0_4', 'v6_0_4']
        downloaded_files = sdss.SDSS.get_spectra(matches=matches, data_release=18, cache=False)
        assert len(downloaded_files) == 2

    def test_sdss_spectrum_mjd(self):
        downloaded_files = sdss.SDSS.get_spectra(plate=2345, fiberID=572)
        assert len(downloaded_files) == 1

    def test_sdss_spectrum_coords(self):
        downloaded_files = sdss.SDSS.get_spectra(coordinates=self.coords)
        assert len(downloaded_files) == 1

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
        xid = sdss.SDSS.query_region(self.coords, width=2.0 * u.arcsec)
        assert isinstance(xid, Table)
        downloaded_files = sdss.SDSS.get_images(matches=xid)
        assert len(downloaded_files) == len(xid)

    def test_sdss_template(self):
        downloaded_files = sdss.SDSS.get_spectral_template('qso')
        assert len(downloaded_files) == 1

    def test_sdss_image_run(self):
        downloaded_files = sdss.SDSS.get_images(run=1904, camcol=3, field=164)
        assert len(downloaded_files) == 1

    def test_sdss_image_coord(self):
        downloaded_files = sdss.SDSS.get_images(coordinates=self.coords)
        assert len(downloaded_files) == 1

    def test_sdss_specobj(self):
        colnames = ['ra', 'dec', 'objid', 'run', 'rerun', 'camcol', 'field',
                    'z', 'plate', 'mjd', 'fiberID', 'specobjid', 'run2d']
        dtypes = [float, float, np.int64, int, int, int, int, float, int, int,
                  int, np.int64, int]
        data = [
            [46.8390680395307, 5.16972676625711, 1237670015125750016, 5714,
             301, 2, 185, -0.0006390358, 2340, 53733, 291, 2634685834112034816,
             26],
            [46.8705377929765, 5.42458826592292, 1237670015662621224, 5714,
             301, 3, 185, 0, 2340, 53733, 3, 2634606669274834944, 26],
            [46.8899751105478, 5.09432755808192, 1237670015125815346, 5714,
             301, 2, 186, -4.898809E-05, 2340, 53733, 287, 2634684734600407040,
             26],
            [46.8954031261838, 5.9739184644185, 1237670016199491831, 5714,
             301, 4, 185, 0, 2340, 53733, 329, 2634696279472498688, 26],
            [46.9155836662379, 5.50671723824944, 1237670015662686398, 5714,
             301, 3, 186, 0, 2340, 53733, 420, 2634721293362030592, 26]]
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

    def test_query_timeout(self):
        with pytest.raises(Timeout):
            sdss.SDSS.query_region(self.coords, width=2.0 * u.arcsec, cache=False, timeout=self.mintimeout)

    def test_spectra_timeout(self):
        with pytest.raises(Timeout):
            sdss.SDSS.get_spectra(coordinates=self.coords, cache=False, timeout=self.mintimeout)

    def test_query_non_default_field(self):
        # A regression test for #469
        query1 = sdss.SDSS.query_region(self.coords, width=2.0 * u.arcsec, fields=['r', 'psfMag_r'])

        query2 = sdss.SDSS.query_region(self.coords, width=2.0 * u.arcsec, fields=['ra', 'dec', 'r'])
        assert isinstance(query1, Table)
        assert isinstance(query2, Table)

        assert query1.colnames == ['r', 'psfMag_r']
        assert query2.colnames == ['ra', 'dec', 'r']

    @pytest.mark.parametrize("dr", dr_list)
    def test_query_crossid(self, dr):
        if dr in dr_warn_list:
            with pytest.warns(AstropyUserWarning, match='Field info are not available for this data release'):
                query1 = sdss.SDSS.query_crossid(self.coords, data_release=dr)
                query2 = sdss.SDSS.query_crossid([self.coords, self.coords], data_release=dr)
        else:
            query1 = sdss.SDSS.query_crossid(self.coords, data_release=dr)
            query2 = sdss.SDSS.query_crossid([self.coords, self.coords], data_release=dr)
        assert isinstance(query1, Table)
        assert query1['objID'][0] == 1237652943176138868

        assert isinstance(query2, Table)
        assert query2['objID'][0] == query1['objID'][0] == query2['objID'][1]

    @pytest.mark.parametrize("dr", dr_list)
    def test_spectro_query_crossid(self, dr):
        if dr in dr_warn_list:
            with pytest.warns(AstropyUserWarning, match='Field info are not available for this data release'):
                query1 = sdss.SDSS.query_crossid(self.coords, specobj_fields=['specObjID', 'z'],
                                                 data_release=dr, cache=False)
                query2 = sdss.SDSS.query_crossid([self.coords, self.coords], specobj_fields=['specObjID', 'z'],
                                                 data_release=dr, cache=False)
        else:
            query1 = sdss.SDSS.query_crossid(self.coords, specobj_fields=['specObjID', 'z'],
                                             data_release=dr, cache=False)
            query2 = sdss.SDSS.query_crossid([self.coords, self.coords], specobj_fields=['specObjID', 'z'],
                                             data_release=dr, cache=False)
        assert isinstance(query1, Table)
        assert query1['specObjID'][0] == 845594848269461504

        assert isinstance(query2, Table)
        assert query2['specObjID'][0] == query2['specObjID'][1] == query1['specObjID'][0]

    def test_large_crossid(self, large_results):
        # Regression test for #589

        results = sdss.SDSS.query_crossid(large_results)
        assert len(results) == 845
