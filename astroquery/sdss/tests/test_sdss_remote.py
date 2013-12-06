# Licensed under a 3-clause BSD style license - see LICENSE.rst
from ... import sdss
from astropy import coordinates
from astropy.table import Table
from astropy.tests.helper import remote_data
import requests
reload(requests)


@remote_data
class TestSDSSRemote:
    # Test Case: A Seyfert 1 galaxy
    coords = coordinates.ICRS('0h8m05.63s +14d50m23.3s')

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
        xid = sdss.core.SDSS.query_specobj(plate=2340)
        assert isinstance(xid, Table)

    def test_sdss_photoobj(self):
        xid = sdss.core.SDSS.query_photoobj(run=1904, camcol=3, field=164)
        assert isinstance(xid, Table)
