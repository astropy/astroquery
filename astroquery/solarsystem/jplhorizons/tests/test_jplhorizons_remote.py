# Licensed under a 3-clause BSD style license - see LICENSE.rst


import pytest
from astropy.tests.helper import assert_quantity_allclose
from numpy.ma import is_masked

from ... import jplhorizons


@pytest.mark.remote_data
class TestHorizonsClass:

    def test_ephemerides_query(self):
        # check values of Ceres for a given epoch
        # orbital uncertainty of Ceres is basically zero
        res = jplhorizons.Horizons(id='Ceres', location='500',
                                   epochs=2451544.5).ephemerides()[0]

        assert res['targetname'] == "1 Ceres (A801 AA)"
        assert res['datetime_str'] == "2000-Jan-01 00:00:00.000"
        assert res['solar_presence'] == ""
        assert res['flags'] == ""
        assert res['elongFlag'] == '/L'
        assert res['airmass'] == 999

        assert is_masked(res['AZ'])
        assert is_masked(res['EL'])
        assert is_masked(res['magextinct'])

        assert_quantity_allclose(
            [2451544.5,
             188.70280, 9.09829, 34.40956, -2.68359,
             8.33, 6.89, 96.171,
             161.3828, 10.4528, 2.551099014238, 0.1744491,
             2.26315116146176, -21.9390511, 18.822054,
             95.3996, 22.5698, 292.551, 296.850,
             184.3426220, 11.7996521, 289.864329, 71.545655,
             0, 0],
            [res['datetime_jd'],
             res['RA'], res['DEC'], res['RA_rate'], res['DEC_rate'],
             res['V'], res['surfbright'], res['illumination'],
             res['EclLon'], res['EclLat'], res['r'], res['r_rate'],
             res['delta'], res['delta_rate'], res['lighttime'],
             res['elong'], res['alpha'], res['sunTargetPA'],
             res['velocityPA'],
             res['ObsEclLon'], res['ObsEclLat'], res['GlxLon'],
             res['GlxLat'],
             res['RA_3sigma'], res['DEC_3sigma']], rtol=1e-3)

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
        assert res['flags'] == "m"
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
        assert res['flags'] == "m"
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
        assert res['flags'] == "m"
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
        assert res['flags'] == "m"
        assert res['elongFlag'] == '/L'

        for value in ['H', 'G', 'phasecoeff']:
            assert value not in res.colnames

        for value in ['M1', 'k1', 'M2', 'k2']:
            assert value in res.colnames

    def test_ephemerides_query_six(self):
        # tests optional constrains for ephemerides queries
        obj = jplhorizons.Horizons(id='3552',
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
        res = (jplhorizons.Horizons(id='Ceres', location='500',
                                    epochs=2451544.5).
               ephemerides(get_raw_response=True))

        assert len(res) >= 15400

    def test_elements_query(self):
        res = jplhorizons.Horizons(id='Ceres', location='500@10',
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
        res = jplhorizons.Horizons(id='Ceres', location='500@10',
                                   epochs=2451544.5).elements(
                                       get_raw_response=True)

        assert len(res) >= 7400

    def test_vectors_query(self):
        # check values of Ceres for a given epoch
        # orbital uncertainty of Ceres is basically zero
        res = jplhorizons.Horizons(id='Ceres', location='500@10',
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
        res = jplhorizons.Horizons(id='Ceres', location='500@10',
                                   epochs=2451544.5).vectors(
                                       get_raw_response=True)

        assert len(res) >= 6900

    def test_unknownobject(self):
        try:
            jplhorizons.Horizons(id='spamspamspameggsspam', location='500',
                                 epochs=2451544.5).ephemerides()
        except ValueError:
            pass

    def test_multipleobjects(self):
        try:
            jplhorizons.Horizons(id='73P', location='500',
                                 epochs=2451544.5).ephemerides()
        except ValueError:
            pass

    def test_uri(self):
        target = jplhorizons.Horizons(id='3552', location='500',
                                      epochs=2451544.5)
        assert target.uri is None

        target.ephemerides()

        assert target.uri == ('https://ssd.jpl.nasa.gov/horizons_batch.cgi?'
                              'batch=1&TABLE_TYPE=OBSERVER&QUANTITIES='
                              '%271%2C2%2C3%2C4%2C5%2C6%2C7%2C8%2C9%2C10'
                              '%2C11%2C12%2C13%2C14%2C15%2C16%2C17%2C18%2C19'
                              '%2C20%2C21%2C22%2C23%2C24%2C25%2C26%2C27%2C28'
                              '%2C29%2C30%2C31%2C32%2C33%2C34%2C35%2C36%2C37'
                              '%2C38%2C39%2C40%2C41%2C42%2C43%27&'
                              'COMMAND=%223552%3B%22&SOLAR_ELONG=%220%2C180'
                              '%22&LHA_CUTOFF=0&CSV_FORMAT=YES&CAL_FORMAT='
                              'BOTH&ANG_FORMAT=DEG&APPARENT=AIRLESS&'
                              'REF_SYSTEM=J2000&EXTRA_PREC=NO&'
                              'CENTER=%27500%27&'
                              'TLIST=2451544.5&SKIP_DAYLT=NO')

    def test__userdefinedlocation_ephemerides_query(self):

        anderson_mesa = {'lon': -111.535833,
                         'lat': 35.096944,
                         'elevation': 2.163}

        am_res = jplhorizons.Horizons(id='Ceres',
                                      location='688',
                                      epochs=2451544.5).ephemerides()[0]

        user_res = jplhorizons.Horizons(id='Ceres',
                                        location=anderson_mesa,
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
                                      epochs=[2458300.5])
        eph = target.ephemerides(quantities='1,8')
        assert len(eph) == 1

        # skip data['a-mass'].filled(99) if 'a-mass' not returned
        eph = target.ephemerides(quantities='1')
        assert len(eph) == 1

    def test_vectors_aberrations(self):
        """Check functionality of `aberrations` options"""
        obj = jplhorizons.Horizons(id='1', epochs=2458500, location='500@0')

        vec = obj.vectors(aberrations='geometric')
        assert_quantity_allclose(vec['x'][0], -2.08648627706842)

        vec = obj.vectors(aberrations='astrometric')
        assert_quantity_allclose(vec['x'][0], -2.086575559005298)

        vec = obj.vectors(aberrations='apparent')
        assert_quantity_allclose(vec['x'][0], -2.086575559005298)

    def test_vectors_delta_T(self):
        obj = jplhorizons.Horizons(id='1', epochs=2458500, location='500@0')

        vec = obj.vectors(delta_T=False)
        assert 'delta_T' not in vec.columns

        vec = obj.vectors(delta_T=True)
        assert_quantity_allclose(vec['delta_T'][0], 69.184373)

    def test_ephemerides_extraprecision(self):
        obj = jplhorizons.Horizons(id='1', epochs=2458500, location='G37')

        vec_simple = obj.ephemerides(extra_precision=False)
        vec_highprec = obj.ephemerides(extra_precision=True)

        assert (vec_simple['RA'][0]-vec_highprec['RA'][0]) > 1e-7
