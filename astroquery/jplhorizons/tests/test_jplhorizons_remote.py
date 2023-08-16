# Licensed under a 3-clause BSD style license - see LICENSE.rst

from numpy.ma import is_masked
import numpy as np
import pytest

from astropy.coordinates import spherical_to_cartesian
from astropy.tests.helper import assert_quantity_allclose
import astropy.units as u
from astropy.coordinates import Angle
from astropy.utils.exceptions import AstropyDeprecationWarning

from ... import jplhorizons


@pytest.mark.remote_data
class TestHorizonsClass:
    def test_ephemerides_query(self):
        # check all values of Ceres for a given epoch
        quantities = ",".join(str(q) for q in range(1, 49))
        horizons = jplhorizons.Horizons(
            id="Ceres", location="I41", id_type="smallbody", epochs=2451544.5
        )
        res = horizons.ephemerides(quantities=quantities)

        # Retrieved 2023 Aug 01:
        values = {
            "targetname": "1 Ceres (A801 AA)",
            "H": 3.33,
            "G": 0.120,
            "datetime_jd": 2451544.5,
            "datetime_str": "2000-Jan-01 00:00:00.000",
            "solar_presence": "*",
            "lunar_presence": "",
            "RA": 188.70240 * u.deg,
            "DEC": 9.09758 * u.deg,
            "RA_app": 188.69858 * u.deg,
            "DEC_app": 9.09806 * u.deg,
            "RA_rate": 35.17815 * u.arcsec / u.hr,
            "DEC_rate": -2.74237 * u.arcsec / u.hr,
            "AZ": 325.548736 * u.deg,
            "EL": -41.062749 * u.deg,
            "AZ_rate": 781.92 * u.arcsec / u.minute,
            "EL_rate": -426.18 * u.arcsec / u.minute,
            "sat_X": -304791.02 * u.arcsec,
            "sat_Y": 115814.995 * u.arcsec,
            "sat_PANG": 277.607 * u.deg,
            "siderealtime": 22.8737254836 * u.hr,
            "airmass": 999,
            "magextinct": np.ma.masked,
            "V": 8.259 * u.mag,
            "surfbright": 6.799 * u.mag / u.arcsec**2,
            "illumination": 96.17086 * u.percent,
            "illum_defect": 0.0225 * u.arcsec,
            "sat_sep": 343433.5 * u.arcsec,
            "sat_vis": "*",
            "ang_width": 0.587419 * u.arcsec,
            "PDObsLon": 302.274926 * u.deg,
            "PDObsLat": -3.982640 * u.deg,
            "PDSunLon": 279.670960 * u.deg,
            "PDSunLat": -3.621151 * u.deg,
            "SubSol_ang": 112.55 * u.deg,
            "SubSol_dist": 0.11 * u.arcsec,
            "NPole_ang": 22.6777 * u.deg,
            "NPole_dist": -0.271 * u.arcsec,
            "EclLon": 161.3828 * u.deg,
            "EclLat": 10.4528 * u.deg,
            "r": 2.551099025883 * u.au,
            "r_rate": 0.1744491 * u.km / u.s,
            "delta": 2.26317926925737 * u.au,
            "delta_rate": -21.7732311 * u.km / u.s,
            "lighttime": 18.82228803 * u.minute,
            "vel_sun": 19.3602212 * u.km / u.s,
            "vel_obs": 27.0721344 * u.km / u.s,
            "elong": 95.3982 * u.deg,
            "elongFlag": "/L",
            "alpha": 22.5696 * u.deg,
            "lunar_elong": 32.9 * u.deg,
            "lunar_illum": 27.4882 * u.percent,
            "sat_alpha": 62.0400 * u.deg,
            "sunTargetPA": 292.552 * u.deg,
            "velocityPA": 296.849 * u.deg,
            "OrbPlaneAng": -1.53489 * u.deg,
            "constellation": "Vir",
            "TDB-UT": 64.183887 * u.s,
            "ObsEclLon": 184.3424861 * u.deg,
            "ObsEclLat": 11.7988212 * u.deg,
            "NPole_RA": 291.42763 * u.deg,
            "NPole_DEC": 66.76033 * u.deg,
            "GlxLon": 289.863376 * u.deg,
            "GlxLat": 71.544870 * u.deg,
            "solartime": 16.1587871790 * u.hour,
            "earth_lighttime": 0.000354 * u.minute,
            "RA_3sigma": 0.000 * u.arcsec,
            "DEC_3sigma": 0.000 * u.arcsec,
            "SMAA_3sigma": 0.00012 * u.arcsec,
            "SMIA_3sigma": 0.00005 * u.arcsec,
            "Theta_3sigma": -24.786 * u.deg,
            "Area_3sigma": 0.0000000 * u.arcsec**2,
            "RSS_3sigma": 0.000 * u.arcsec,
            "r_3sigma": 0.0904 * u.km,
            "r_rate_3sigma": 0.0000000 * u.km / u.s,
            "SBand_3sigma": 0.00 * u.Hz,
            "XBand_3sigma": 0.00 * u.Hz,
            "DoppDelay_3sigma": 0.000001 * u.s,
            "true_anom": 7.1181 * u.deg,
            "hour_angle": 10.293820034 * u.hour,
            "alpha_true": 22.5691 * u.deg,
            "PABLon": 172.8355 * u.deg,
            "PABLat": 11.3478 * u.deg,
            "App_Lon_Sun": 309.1603680 * u.deg,
            "RA_ICRF_app": 188.70238 * u.deg,
            "DEC_ICRF_app": 9.09628 * u.deg,
            "RA_ICRF_rate_app": 35.17809 * u.arcsec / u.hour,
            "DEC_ICRF_rate_app": -2.74321 * u.arcsec / u.hour,
            "Sky_motion": 0.5880814 * u.arcsec / u.minute,
            "Sky_mot_PA": 94.457576 * u.deg,
            "RelVel-ANG": -53.53947 * u.deg,
            "Lun_Sky_Brt": np.ma.masked,
            "sky_SNR": np.ma.masked,
        }

        # the ephemeris changes with Ceres's and the planets' orbital elements,
        # which can be updated at any time, so only check for 0.1% tolerance, this
        # is enough to verify that most columns are not being confused, and that
        # units are correct

        for column, value in values.items():
            if isinstance(value, (u.Quantity, Angle)):
                # A few columns have varied a lot more than the others
                if column in ["H", "G", "V", "surfbright"]:
                    rtol = 0.1
                else:
                    rtol = 0.001
                assert u.isclose(res[column], value, rtol=rtol)
            elif value is np.ma.masked:
                assert is_masked(res[column])
            else:
                assert res[column] == value

    def test_ephemerides_query_two(self):
        # check comet ephemerides using options
        obj = jplhorizons.Horizons(id='Halley', id_type='comet_name',
                                   location='290',
                                   epochs={'start': '2080-01-01',
                                           'stop': '2080-02-01',
                                           'step': '3h'})
        res = obj.ephemerides(airmass_lessthan=1.2, skip_daylight=True,
                              closest_apparition=True,
                              max_hour_angle=10,
                              solar_elongation=(150, 180))
        assert len(res) == 1

        res = res[0]

        assert res['targetname'] == "1P/Halley"
        assert res['datetime_str'] == "2080-Jan-11 09:00"
        assert res['solar_presence'] == ""
        assert res['lunar_presence'] == "m"
        assert res['elongFlag'] == '/L'

        for value in ['H', 'G']:
            assert value not in res.colnames

    def test_ephemerides_query_three(self):
        # checks no_fragments option for comets
        obj = jplhorizons.Horizons(id='73P', id_type='designation',
                                   location='290',
                                   epochs={'start': '2080-01-01',
                                           'stop': '2080-02-01',
                                           'step': '3h'})

        res = obj.ephemerides(closest_apparition=True, no_fragments=True)

        assert len(res) == 249

        res = res[0]

        assert res['targetname'] == "73P/Schwassmann-Wachmann 3"
        assert res['datetime_str'] == "2080-Jan-01 00:00"
        assert res['solar_presence'] == "*"
        assert res['lunar_presence'] == "m"
        assert res['elongFlag'] == '/L'

        for value in ['H', 'G']:
            assert value not in res.colnames

    def test_ephemerides_query_four(self):
        # checks for missing M1 with a comet; 167P satisfies this as
        # of 18 June 2018
        obj = jplhorizons.Horizons(id='167P', id_type='designation',
                                   location='I41',
                                   epochs={'start': '2080-01-01',
                                           'stop': '2080-02-01',
                                           'step': '3h'})

        res = obj.ephemerides(closest_apparition=True,
                              no_fragments=True)

        assert len(res) == 249

        res = res[0]

        assert res['targetname'] == "167P/CINEOS"
        assert res['datetime_str'] == "2080-Jan-01 00:00"
        assert res['solar_presence'] == "*"
        assert res['lunar_presence'] == "m"
        assert res['elongFlag'] == '/T'

        for value in ['H', 'G', 'M1', 'k1']:
            assert value not in res.colnames

        for value in ['M2', 'k2', 'phasecoeff']:
            assert value in res.colnames

    def test_ephemerides_query_five(self):
        # checks for missing phase coefficient with a comet; 12P
        # satisfies this as of 18 June 2018
        obj = jplhorizons.Horizons(id='12P', id_type='designation',
                                   location='I41',
                                   epochs={'start': '2080-01-01',
                                           'stop': '2080-02-01',
                                           'step': '3h'})

        res = obj.ephemerides(closest_apparition=True)

        assert len(res) == 249

        res = res[0]

        assert res['targetname'] == "12P/Pons-Brooks"
        assert res['datetime_str'] == "2080-Jan-01 00:00"
        assert res['solar_presence'] == "*"
        assert res['lunar_presence'] == "m"
        assert res['elongFlag'] == '/L'

        for value in ['H', 'G', 'phasecoeff']:
            assert value not in res.colnames

        for value in ['M1', 'k1', 'M2', 'k2']:
            assert value in res.colnames

    def test_ephemerides_query_six(self):
        # tests optional constrains for ephemerides queries
        obj = jplhorizons.Horizons(id='3552', id_type='smallbody',
                                   location='I33',
                                   epochs={'start': '2018-05-01',
                                           'stop': '2018-08-01',
                                           'step': '3h'})

        res = obj.ephemerides(skip_daylight=True,
                              max_hour_angle=8,
                              refraction=True,
                              refsystem='B1950',
                              rate_cutoff=100,
                              airmass_lessthan=5)

        assert len(res) == 32

    def test_ephemerides_query_raw(self):
        # deprecated as of #2418
        with pytest.warns(AstropyDeprecationWarning):
            res = (jplhorizons.Horizons(id='Ceres',
                                        location='500',
                                        id_type='smallbody',
                                        epochs=2451544.5)
                   .ephemerides(get_raw_response=True))

        assert len(res) >= 15400

    def test_elements_query(self):
        res = jplhorizons.Horizons(id='Ceres', location='500@10',
                                   id_type='smallbody',
                                   epochs=[2451544.5,
                                           2451545.5]).elements()[0]

        assert res['targetname'] == "1 Ceres (A801 AA)"
        assert res['datetime_str'] == "A.D. 2000-Jan-01 00:00:00.0000"

        assert_quantity_allclose(
            [2451544.5,
             7.837505767652506E-02, 2.549670133211852E+00,
             1.058336086929457E+01,
             8.049436516467529E+01, 7.392278852641589E+01,
             2.451516163117752E+06,
             2.141950393098222E-01, 6.069619607052192E+00,
             7.121190541431409E+00,
             2.766494282136041E+00, 2.983318431060230E+00,
             1.680711192752127E+03],
            [res['datetime_jd'],
             res['e'], res['q'],
             res['incl'],
             res['Omega'], res['w'],
             res['Tp_jd'],
             res['n'], res['M'],
             res['nu'],
             res['a'], res['Q'],
             res['P']], rtol=1e-3)

    def test_elements_query_two(self):
        obj = jplhorizons.Horizons(id='Ceres', location='500@10',
                                   id_type='smallbody',
                                   epochs=[2451544.5,
                                           2451545.5])

        res = obj.elements(refsystem='B1950',
                           refplane='earth',
                           tp_type='relative')[1]

        assert_quantity_allclose([23.24472584135690,
                                  132.6482045485004,
                                  -29.33632558181947],
                                 [res['Omega'], res['w'], res['Tp_jd']],
                                 rtol=1e-3)

    def test_elements_query_raw(self):
        # deprecated as of #2418
        with pytest.warns(AstropyDeprecationWarning):
            res = (jplhorizons.Horizons(id='Ceres',
                                        location='500@10',
                                        id_type='smallbody',
                                        epochs=2451544.5)
                   .elements(get_raw_response=True))

        assert len(res) >= 6686

    def test_vectors_query(self):
        # check values of Ceres for a given epoch
        # orbital uncertainty of Ceres is basically zero
        res = jplhorizons.Horizons(id='Ceres', location='500@10',
                                   id_type='smallbody',
                                   epochs=2451544.5).vectors()[0]

        assert res['targetname'] == "1 Ceres (A801 AA)"
        assert res['datetime_str'] == "A.D. 2000-Jan-01 00:00:00.0000"

        assert_quantity_allclose(
            [2451544.5,
             -2.377530254715913E+00, 8.007773098011088E-01,
             4.628376171505864E-01,
             -3.605422534068209E-03, -1.057883330464988E-02,
             3.379791158988872E-04,
             1.473392692285918E-02, 2.551100364907553E+00,
             1.007960852643289E-04],
            [res['datetime_jd'],
             res['x'], res['y'],
             res['z'],
             res['vx'], res['vy'],
             res['vz'],
             res['lighttime'], res['range'],
             res['range_rate']], rtol=1e-3)

    def test_vectors_query_raw(self):
        # deprecated as of #2418
        with pytest.warns(AstropyDeprecationWarning):
            res = (jplhorizons.Horizons(id='Ceres',
                                        location='500@10',
                                        id_type='smallbody',
                                        epochs=2451544.5)
                   .vectors(get_raw_response=True))

        assert len(res) >= 6412

    @pytest.mark.parametrize(
        "location",
        (
            {"lon": 244, "lat": 33, "elevation": 1.7},
            {"lon": (244 * u.deg).to(u.rad), "lat": (33 * u.deg).to(u.rad), "elevation": 1700 * u.m},
        )
    )
    def test_vectors_query_topocentric_coordinates(self, location):
        "Test vectors query specifying observer's longitude, latitude, and elevation"
        q = jplhorizons.Horizons(id='Ceres',
                                 location=location,
                                 id_type='smallbody',
                                 epochs=2451544.5)
        res = q.vectors_async()
        i = res.text.find("Center geodetic :")
        j = res.text.find("\n", i)
        parts = res.text[i:j].split()
        assert parts[3:6] == ['244.0,', '33.0,', '1.7']

        start = res.text.find("$$SOE")
        end = res.text.find("$$EOE")
        assert res.text[start:end].find("2000-Jan-01") > 0

    def test_unknownobject(self):
        with pytest.raises(ValueError):
            jplhorizons.Horizons(id='spamspamspameggsspam', location='500',
                                 epochs=2451544.5).ephemerides()

    def test_multipleobjects(self):
        with pytest.raises(ValueError):
            jplhorizons.Horizons(id='73P', location='500', id_type='smallbody',
                                 epochs=2451544.5).ephemerides()

    def test_uri(self):
        target = jplhorizons.Horizons(id='3552', location='500',
                                      id_type='smallbody', epochs=2451544.5)
        assert target.uri is None

        target.ephemerides()

        assert target.uri == ('https://ssd.jpl.nasa.gov/api/horizons.api?'
                              'format=text&EPHEM_TYPE=OBSERVER&QUANTITIES='
                              '%271%2C2%2C3%2C4%2C5%2C6%2C7%2C8%2C9%2C10'
                              '%2C11%2C12%2C13%2C14%2C15%2C16%2C17%2C18%2C19'
                              '%2C20%2C21%2C22%2C23%2C24%2C25%2C26%2C27%2C28'
                              '%2C29%2C30%2C31%2C32%2C33%2C34%2C35%2C36%2C37'
                              '%2C38%2C39%2C40%2C41%2C42%2C43%27&'
                              'COMMAND=%223552%3B%22&SOLAR_ELONG=%220%2C180'
                              '%22&LHA_CUTOFF=0&CSV_FORMAT=YES&CAL_FORMAT='
                              'BOTH&ANG_FORMAT=DEG&APPARENT=AIRLESS&'
                              'REF_SYSTEM=ICRF&EXTRA_PREC=NO&'
                              'CENTER=%27500%27&'
                              'TLIST=2451544.5&SKIP_DAYLT=NO')

    def test__userdefinedlocation_ephemerides_query(self):

        anderson_mesa = {'lon': -111.535833,
                         'lat': 35.096944,
                         'elevation': 2.163}

        am_res = jplhorizons.Horizons(id='Ceres',
                                      location='688',
                                      id_type='smallbody',
                                      epochs=2451544.5).ephemerides()[0]

        user_res = jplhorizons.Horizons(id='Ceres',
                                        location=anderson_mesa,
                                        id_type='smallbody',
                                        epochs=2451544.5).ephemerides()[0]

        assert_quantity_allclose([am_res['RA'], am_res['DEC']],
                                 [user_res['RA'], user_res['DEC']])

    def test_majorbody(self):
        """Regression test for "Fix missing columns... #1268"
        https://github.com/astropy/astroquery/pull/1268

        Horizons.ephemerides would crash for majorbodies because the
        returned columns have different names from other bodies.  The
        culprits were: Obsrv-lon, Obsrv-lat, Solar-lon, Solar-lat

        """
        epochs = dict(start='2019-01-01', stop='2019-01-02', step='1d')
        quantities = ('1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,'
                      '21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,'
                      '38,39,40,41,42,43')
        target = jplhorizons.Horizons(id='301', location='688', epochs=epochs)
        eph = target.ephemerides(quantities=quantities)
        assert len(eph) == 2

    def test_airmass(self):
        """Regression test for "Airmass issues with jplhorizons #1284"

        Horizons.ephemerides would crash when Horizons returned tables
        with no masked data.  The error occurs when attempting to fill
        bad values in the 'a-mass' column:
        ``data['a-mass'].filled(99)``.  However, with no masked data,
        ascii.read returns a normal Table, and the 'a-mass' column was
        missing the ``filled`` method.

        In addition, the same lines would crash if airmass was not
        requested in the returned table.

        """

        # verify data['a-mass'].filled(99) works:
        target = jplhorizons.Horizons('Ceres', location='I41',
                                      id_type='smallbody',
                                      epochs=[2458300.5])
        eph = target.ephemerides(quantities='1,8')
        assert len(eph) == 1

        # skip data['a-mass'].filled(99) if 'a-mass' not returned
        eph = target.ephemerides(quantities='1')
        assert len(eph) == 1

    def test_vectors_aberrations(self):
        """Check functionality of `aberrations` options"""
        obj = jplhorizons.Horizons(id='1', epochs=2458500, location='500@0',
                                   id_type='smallbody')

        vec = obj.vectors(aberrations='geometric')
        assert_quantity_allclose(vec['x'][0], -2.086487005013347)

        vec = obj.vectors(aberrations='astrometric')
        assert_quantity_allclose(vec['x'][0], -2.086576286974797)

        vec = obj.vectors(aberrations='apparent')
        assert_quantity_allclose(vec['x'][0], -2.086576286974797)

    def test_vectors_delta_T(self):
        obj = jplhorizons.Horizons(id='1', epochs=2458500, location='500@0',
                                   id_type='smallbody')

        vec = obj.vectors(delta_T=False)
        assert 'delta_T' not in vec.columns

        vec = obj.vectors(delta_T=True)
        assert_quantity_allclose(vec['delta_T'][0], 69.184373)

    def test_ephemerides_extraprecision(self):
        obj = jplhorizons.Horizons(id='1', epochs=2458500, location='G37',
                                   id_type='smallbody')

        vec_simple = obj.ephemerides(extra_precision=False)
        vec_highprec = obj.ephemerides(extra_precision=True)

        assert (vec_simple['RA'][0]-vec_highprec['RA'][0]) > 1e-7

    def test_geodetic_queries(self):
        """
        black-box test for observer and vectors queries with geodetic
        coordinates. checks spatial sensibility.
        """
        phobos = {'body': 401, 'lon': -30, 'lat': -20, 'elevation': 0}
        deimos = {'body': 402, 'lon': -10, 'lat': -40, 'elevation': 0}
        deimos_phobos = jplhorizons.Horizons(phobos, location=deimos, epochs=2.4e6)
        phobos_deimos = jplhorizons.Horizons(deimos, location=phobos, epochs=2.4e6)
        pd_eph, dp_eph = phobos_deimos.ephemerides(), deimos_phobos.ephemerides()
        dp_xyz = spherical_to_cartesian(
            dp_eph['delta'], dp_eph['DEC'], dp_eph['RA']
        )
        pd_xyz = spherical_to_cartesian(
            pd_eph['delta'], pd_eph['DEC'], pd_eph['RA']
        )
        elementwise = [(dp_el + pd_el) for dp_el, pd_el in zip(dp_xyz, pd_xyz)]
        eph_offset = (sum([off ** 2 for off in elementwise]) ** 0.5).to(u.km)
        # horizons can do better than this, but we'd have to go to a little
        # more trouble than is necessary for a software test...
        assert np.isclose(eph_offset.value, 2.558895)
        # ...and vectors queries are really what you're meant to use for
        # this sort of thing.
        pd_vec, dp_vec = phobos_deimos.vectors(), deimos_phobos.vectors()
        vec_offset = np.sum(
            (
                pd_vec.as_array(names=('x', 'y', 'z')).view('f8')
                + dp_vec.as_array(names=('x', 'y', 'z')).view('f8')
            ) ** 2
        )
        assert np.isclose(vec_offset, 0)
