# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import print_function

from astropy.tests.helper import remote_data
from numpy.ma import is_masked
import numpy.testing as npt
from collections import OrderedDict

from ... import solarsystem


@remote_data
class TestJPLClass:

    def test_ephemerides_query(patch_request):
        # check values of Ceres for a given epoch
        # orbital uncertainty of Ceres is basically zero
        res = solarsystem.JPL(id='Ceres', location='500',
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
             8.27,  6.83, 96.171,
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
             res['elong'], res['alpha'], res['sunTargetPA'], res['velocityPA'],
             res['ObsEclLon'], res['ObsEclLat'], res['GlxLon'], res['GlxLat'],
             res['RA_3sigma'], res['DEC_3sigma']])

    def test_ephemerides_query_two(patch_request):
        # check comet ephemerides using solarsystem.ephemerides options
        obj = solarsystem.JPL(id='Halley', id_type='comet_name',
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

        # Horizons web query does not provide uncertainties, this query does...
        # assert is_masked(res['RA_3sigma'])
        # assert is_masked(res['DEC_3sigma'])

        assert 'H' not in res
        assert 'G' not in res

        npt.assert_allclose(
            [2480774.875,
             131.43810, -0.46854, -5.16997, 0.817370,
             186.2443, 56.3752, 1.200, 0.153,
             24.39, 28.15, 99.993,
             133.1934, -17.2515,  28.74258872620, 3.0860235,
             27.8838008488718, -8.7436257, 231.902500,
             150.3437, 0.9736, 320.367, 112.201,
             135.1522279, -17.7924130, 227.331393, 24.964856,
             5.5, 13.6, 8, 5, 0.03],
            [res['datetime_jd'],
             res['RA'], res['DEC'], res['RA_rate'], res['DEC_rate'],
             res['AZ'], res['EL'], res['airmass'], res['magextinct'],
             res['Tmag'], res['Nmag'], res['illumination'],
             res['EclLon'], res['EclLat'], res['r'], res['r_rate'],
             res['delta'], res['delta_rate'], res['lighttime'],
             res['elong'], res['alpha'], res['sunTargetPA'], res['velocityPA'],
             res['ObsEclLon'], res['ObsEclLat'], res['GlxLon'], res['GlxLat'],
             res['M1'], res['M2'], res['k1'], res['k2'], res['phasecoeff']])

    def test_ephemerides_query_three(patch_request):
        # checks no_fragments option for comets
        obj = solarsystem.JPL(id='73P', id_type='designation',
                              location='290',
                              epochs={'start': '2080-01-01',
                                      'stop': '2080-02-01',
                                      'step': '3h'})

        res = obj.ephemerides(closest_apparition=True,
                              no_fragments=True)

    def test_ephemerides_query_raw(patch_request):
        res = (solarsystem.JPL(id='Ceres', location='500',
                               epochs=2451544.5).
               ephemerides(get_raw_response=True))

        assert len(res) == 15335

    def test_ephemerides_query_payload(patch_request):
        obj = solarsystem.JPL(id='Halley', id_type='comet_name',
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

    def test_elements_query(patch_request):
        res = solarsystem.JPL(id='Ceres', location='500@10',
                              epochs=2451544.5).elements()[0]

        assert res['targetname'] == "1 Ceres"
        assert res['datetime_str'] == "A.D. 2000-Jan-01 00:00:00.0000"

        npt.assert_allclose(
            [2451544.5,
             7.837505767652506E-02,  2.549670133211852E+00,
             1.058336086929457E+01,
             8.049436516467529E+01,  7.392278852641589E+01,
             2.451516163117752E+06,
             2.141950393098222E-01,  6.069619607052192E+00,
             7.121190541431409E+00,
             2.766494282136041E+00,  2.983318431060230E+00,
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

    def test_elements_query_raw(patch_request):
        res = solarsystem.JPL(id='Ceres', location='500@10',
                              epochs=2451544.5).elements(get_raw_response=True)

        assert len(res) == 7576

    def test_elements_query_payload(patch_request):
        res = (solarsystem.JPL(id='Ceres', location='500@10',
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
            ('TLIST', '"2451544.5"')])

    def test_vectors_query(patch_request):
        # check values of Ceres for a given epoch
        # orbital uncertainty of Ceres is basically zero
        res = solarsystem.JPL(id='Ceres', location='500@10',
                              epochs=2451544.5).vectors()[0]

        assert res['targetname'] == "1 Ceres"
        assert res['datetime_str'] == "A.D. 2000-Jan-01 00:00:00.0000"

        npt.assert_allclose(
            [2451544.5,
             -2.377530254715913E+00,  8.007773098011088E-01,
             4.628376171505864E-01,
             -3.605422534068209E-03, -1.057883330464988E-02,
             3.379791158988872E-04,
             1.473392692285918E-02,  2.551100364907553E+00,
             1.007960852643289E-04],
            [res['datetime_jd'],
             res['x'], res['y'],
             res['z'],
             res['vx'], res['vy'],
             res['vz'],
             res['lighttime'], res['range'],
             res['range_rate']])

    def test_vectors_query_raw(patch_request):
        res = solarsystem.JPL(id='Ceres', location='500@10',
                              epochs=2451544.5).vectors(get_raw_response=True)

        assert len(res) == 7032

    def test_vectors_query_payload(patch_request):
        res = solarsystem.JPL(id='Ceres', location='500@10',
                              epochs=2451544.5).vectors(get_query_payload=True)

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
            ('TLIST', '"2451544.5"')])

    def test_unknownobject(patch_request):
        try:
            solarsystem.JPL(id='spamspamspameggsspam', location='500',
                            epochs=2451544.5).ephemerides()
        except ValueError:
            pass

    def test_multipleobjects(patch_request):
        try:
            solarsystem.JPL(id='73P', location='500',
                            epochs=2451544.5).ephemerides()
        except ValueError:
            pass
