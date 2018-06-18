# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import print_function

from astropy.tests.helper import remote_data
from numpy.ma import is_masked
import numpy.testing as npt
from collections import OrderedDict

from ... import jplhorizons


@remote_data
class TestHorizonsClass:

    def test_ephemerides_query(self):
        # check values of Ceres for a given epoch
        # orbital uncertainty of Ceres is basically zero
        res = jplhorizons.Horizons(id='Ceres', location='500',
                                   epochs=2451544.5).ephemerides()[0]

        assert res['targetname'] == "1 Ceres"
        assert res['datetime_str'] == "2000-Jan-01 00:00:00.000"
        assert res['solar_presence'] == ""
        assert res['flags'] == ""
        assert res['elongFlag'] == '/L'

        assert is_masked(res['AZ'])
        assert is_masked(res['EL'])
        assert is_masked(res['airmass'])
        assert is_masked(res['magextinct'])

        npt.assert_allclose(
            [2451544.5,
             188.70280, 9.09829, 34.40955, -2.68358,
             8.27, 6.83, 96.171,
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
             res['RA_3sigma'], res['DEC_3sigma']])

    def test_ephemerides_query_two(self):
        # check comet ephemerides using solarsystem.ephemerides options
        obj = jplhorizons.Horizons(id='Halley', id_type='comet_name',
                                   location='290',
                                   epochs={'start': '2080-01-01',
                                           'stop': '2080-02-01',
                                           'step': '3h'})
        res = obj.ephemerides(airmass_lessthan=1.2, skip_daylight=True,
                              closest_apparition=True,
                              hour_angle=10,
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

    def test_ephemerides_query_raw(self):
        res = (jplhorizons.Horizons(id='Ceres', location='500',
                                    epochs=2451544.5).
               ephemerides(get_raw_response=True))

        # May 10, 2018: this increased to 15463.
        assert len(res) >= 15463

    def test_ephemerides_query_payload(self):
        obj = jplhorizons.Horizons(id='Halley', id_type='comet_name',
                                   location='290',
                                   epochs={'start': '2080-01-01',
                                           'stop': '2080-02-01',
                                           'step': '3h'})
        res = obj.ephemerides(airmass_lessthan=1.2, skip_daylight=True,
                              closest_apparition=True,
                              hour_angle=10,
                              solar_elongation=(150, 180),
                              get_query_payload=True)

        assert res == OrderedDict([
            ('batch', 1),
            ('TABLE_TYPE', 'OBSERVER'),
            ('QUANTITIES', '"1,3,4,8,9,10,18,19,20,21,23,24,27,31,33,36"'),
            ('COMMAND', '"COMNAM=Halley; CAP;"'),
            ('CENTER', "'290'"),
            ('SOLAR_ELONG', '"150,180"'),
            ('LHA_CUTOFF', '10'),
            ('CSV_FORMAT', 'YES'),
            ('CAL_FORMAT', 'BOTH'),
            ('ANG_FORMAT', 'DEG'),
            ('START_TIME', '2080-01-01'),
            ('STOP_TIME', '2080-02-01'),
            ('STEP_SIZE', '3h'),
            ('AIRMASS', '1.2'),
            ('SKIP_DAYLT', 'YES')])

    def test_elements_query(self):
        res = jplhorizons.Horizons(id='Ceres', location='500@10',
                                   epochs=2451544.5).elements()[0]

        assert res['targetname'] == "1 Ceres"
        assert res['datetime_str'] == "A.D. 2000-Jan-01 00:00:00.0000"

        npt.assert_allclose(
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
             res['P']])

    def test_elements_query_raw(self):
        res = jplhorizons.Horizons(id='Ceres', location='500@10',
                                   epochs=2451544.5).elements(
                                       get_raw_response=True)

        assert len(res) == 7574

    def test_elements_query_payload(self):
        res = (jplhorizons.Horizons(id='Ceres', location='500@10',
                                    epochs=2451544.5).elements(
                                        get_query_payload=True))

        assert res == OrderedDict([
            ('batch', 1),
            ('TABLE_TYPE', 'ELEMENTS'),
            ('OUT_UNITS', 'AU-D'),
            ('COMMAND', '"Ceres;"'),
            ('CENTER', "'500@10'"),
            ('CSV_FORMAT', '"YES"'),
            ('REF_PLANE', 'ECLIPTIC'),
            ('REF_SYSTEM', 'J2000'),
            ('TP_TYPE', 'ABSOLUTE'),
            ('ELEM_LABELS', 'YES'),
            ('OBJ_DATA', 'YES'),
            ('TLIST', '2451544.5')])

    def test_vectors_query(self):
        # check values of Ceres for a given epoch
        # orbital uncertainty of Ceres is basically zero
        res = jplhorizons.Horizons(id='Ceres', location='500@10',
                                   epochs=2451544.5).vectors()[0]

        assert res['targetname'] == "1 Ceres"
        assert res['datetime_str'] == "A.D. 2000-Jan-01 00:00:00.0000"

        npt.assert_allclose(
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
             res['range_rate']])

    def test_vectors_query_raw(self):
        res = jplhorizons.Horizons(id='Ceres', location='500@10',
                                   epochs=2451544.5).vectors(
                                       get_raw_response=True)

        assert len(res) == 7030

    def test_vectors_query_payload(self):
        res = jplhorizons.Horizons(id='Ceres', location='500@10',
                                   epochs=2451544.5).vectors(
                                       get_query_payload=True)

        assert res == OrderedDict([
            ('batch', 1),
            ('TABLE_TYPE', 'VECTORS'),
            ('OUT_UNITS', 'AU-D'),
            ('COMMAND', '"Ceres;"'),
            ('CENTER', "'500@10'"),
            ('CSV_FORMAT', '"YES"'),
            ('REF_PLANE', 'ECLIPTIC'),
            ('REF_SYSTEM', 'J2000'),
            ('TP_TYPE', 'ABSOLUTE'),
            ('LABELS', 'YES'),
            ('OBJ_DATA', 'YES'),
            ('TLIST', '2451544.5')])

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
