# Licensed under a 3-clause BSD style license - see LICENSE.rst

from astropy.tests.helper import remote_data
import astropy.units as u
from ... import vizier
from ...utils import commons
import requests
import imp
imp.reload(requests)


@remote_data
class TestVizierRemote(object):

    target = commons.ICRSCoordGenerator(ra=299.590, dec=35.201,
                                        unit=(u.deg, u.deg))

    def test_query_object(self):
        result = vizier.core.Vizier.query_object("HD 226868", catalog=["NOMAD", "UCAC"])
        assert isinstance(result, commons.TableList)

    def test_query_another_object(self):
        result = vizier.core.Vizier.query_region("AFGL 2591", radius='0d5m', catalog="B/iram/pdbi")
        assert isinstance(result, commons.TableList)

    def test_query_object_async(self):
        response = vizier.core.Vizier.query_object_async("HD 226868", catalog=["NOMAD", "UCAC"])
        assert response is not None

    def test_query_region(self):
        result = vizier.core.Vizier.query_region(self.target,
                                                radius=5 * u.deg,
                                                catalog=["HIP", "NOMAD", "UCAC"])

        assert isinstance(result, commons.TableList)

    def test_query_region_async(self):
        response = vizier.core.Vizier.query_region_async(self.target,
                                                     radius=5 * u.deg,
                                                     catalog=["HIP", "NOMAD", "UCAC"])
        assert response is not None

    def test_query_Vizier_instance(self):
        v = vizier.core.Vizier(columns=['_RAJ2000', 'DEJ2000', 'B-V', 'Vmag', 'Plx'],
                               column_filters={"Vmag":">10"}, keywords=["optical", "xry"])
        result = v.query_object("HD 226868", catalog=["NOMAD", "UCAC"])
        assert isinstance(result, commons.TableList)
        result = v.query_region(self.target,
                                width="5d0m0s", height="3d0m0s",
                                catalog=["NOMAD", "UCAC"])
        assert isinstance(result, commons.TableList)

    def test_get_catalogs(self):
        result = vizier.core.Vizier.get_catalogs('J/ApJ/706/83')
        assert isinstance(result, commons.TableList)

    def test_query_two_wavelengths(self):
        v = vizier.core.Vizier(columns=['_RAJ2000', 'DEJ2000', 'B-V', 'Vmag', 'Plx'],
                               column_filters={"Vmag":">10"}, keywords=["optical", "radio"])
        v.query_object('M 31')

    def regressiontest_invalidtable(self):
        V = Vizier(columns=['all'], ucd='(spect.dopplerVeloc*|phys.veloc*)',
                   keywords=['Radio', 'IR'], row_limit=5000)
        C = coordinates.SkyCoord(359.61687 * u.deg, -0.242457 * u.deg, frame='galactic')

        r2 = V.query_region(C, radius=2 * u.arcmin)

    def test_multicoord(self):

        # Coordinate selection is entirely arbitrary
        targets = commons.ICRSCoordGenerator(ra=[299.590, 299.90],
                                             dec=[35.201, 35.201],
                                             unit=(u.deg, u.deg))
        result = vizier.core.Vizier.query_region(targets,
                                                 radius=10 * u.arcsec,
                                                 catalog=["HIP", "NOMAD", "UCAC"])

        assert len(result) >= 5
        assert 'I/239/hip_main' in result.keys()
        assert result['I/239/hip_main']['HIP'] == 98298
