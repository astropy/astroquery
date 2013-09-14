# Licensed under a 3-clause BSD style license - see LICENSE.rst

from astropy.tests.helper import remote_data
import astropy.units as u
import astropy.coordinates as coord
from ... import vizier
from ...utils import commons
import requests
reload(requests)


@remote_data
class TestVizierRemote:

    def test_query_object(self):
        result = vizier.core.Vizier.query_object("HD 226868", catalog=["NOMAD", "UCAC"])
        assert isinstance(result, commons.TableList)

    def test_query_object_async(self):
        response = vizier.core.Vizier.query_object_async("HD 226868", catalog=["NOMAD", "UCAC"])
        assert response is not None

    def test_query_region(self):
        result = vizier.core.Vizier.query_region(coord.ICRSCoordinates(ra=299.590, dec=35.201, unit=(u.deg, u.deg)),
                                                radius=5 * u.deg,
                                                catalog=["HIP", "NOMAD", "UCAC"])

        assert isinstance(result, commons.TableList)

    def test_query_region_async(self):
        response = vizier.core.Vizier.query_region_async(coord.ICRSCoordinates(ra=299.590, dec=35.201, unit=(u.deg, u.deg)),
                                                     radius=5 * u.deg,
                                                     catalog=["HIP", "NOMAD", "UCAC"])
        assert response is not None

    def test_query_Vizier_instance(self):
        v = vizier.core.Vizier(columns=['_RAJ2000', 'DEJ2000','B-V', 'Vmag', 'Plx'],
                               column_filters={"Vmag":">10"}, keywords=["optical", "xry"])
        result = v.query_object("HD 226868", catalog=["NOMAD", "UCAC"])
        assert isinstance(result, commons.TableList)
        result = v.query_region(coord.ICRSCoordinates(ra=299.590, dec=35.201, unit=(u.deg, u.deg)),
                                width="5d0m0s", height="3d0m0s",
                                catalog=["NOMAD", "UCAC"])
        assert isinstance(result, commons.TableList)

    def test_get_catalogs(self):
        result = vizier.core.Vizier.get_catalogs('J/ApJ/706/83')
        assert isinstance(result, commons.TableList)
