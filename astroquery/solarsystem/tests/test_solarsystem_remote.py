# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import print_function

import pytest
from astropy.tests.helper import remote_data
from numpy.ma import is_masked
import numpy.testing as npt

from ... import solarsystem
from ...solarsystem import conf

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
             161.3828, 10.4528, 2.551099014238,  0.1744491,
             2.26315116146176,-21.9390511, 18.822054,
             95.3996,22.5698, 292.551,296.850,
             184.3426220, 11.7996521, 289.864329, 71.545655,
             0, 0
            ],
            [res['datetime_jd'],
             res['RA'], res['DEC'], res['RA_rate'], res['DEC_rate'],
             res['V'], res['surfbright'], res['illumination'],
             res['EclLon'], res['EclLat'], res['r'], res['r_rate'],
             res['delta'], res['delta_rate'], res['lighttime'],
             res['elong'], res['alpha'], res['sunTargetPA'], res['velocityPA'],
             res['ObsEclLon'], res['ObsEclLat'], res['GlxLon'], res['GlxLat'],
             res['RA_3sigma'], res['DEC_3sigma']
            ])

    def test_elements_query(patch_request):
        # check values of Ceres for a given epoch
        # orbital uncertainty of Ceres is basically zero
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
             1.680711192752127E+03,
            ],
            [res['datetime_jd'],
             res['e'], res['q'],
             res['incl'],
             res['Omega'], res['w'],
             res['Tp_jd'],
             res['n'], res['M'],
             res['nu'],
             res['a'], res['Q'],
             res['P']
            ])

    def test_elements_vectors(patch_request):
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
             1.007960852643289E-04,
            ],
            [res['datetime_jd'],
             res['x'], res['y'],
             res['z'],
             res['vx'], res['vy'],
             res['vz'],
             res['lighttime'], res['range'],
             res['range_rate'],
            ])
        
