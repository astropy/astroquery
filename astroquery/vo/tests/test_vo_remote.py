# Licensed under a 3-clause BSD style license - see LICENSE.rst

import pytest
import os
import tempfile
from astropy.coordinates import SkyCoord
from astropy.tests.helper import remote_data
from astropy import units as u

from astroquery.vo import VoImageQuery
from astropy.utils.exceptions import AstropyDeprecationWarning

try:
    pyvo_OK = True
    import pyvo   # noqa
except ImportError:
    pyvo_OK = False
except AstropyDeprecationWarning as e:
    if str(e) == 'The astropy.vo.samp module has now been moved to astropy.samp':
        print('AstropyDeprecationWarning: {}'.format(str(e)))
    else:
        raise e

# to run just one test during development, set this variable to True
# and comment out the skipif of the single test to run.
one_test = False

# Skip the very slow tests to avoid timeout errors
skip_slow = True


@remote_data
class TestCadcService:
    # now write tests for each method here

    @pytest.mark.skipif(one_test, reason='One test mode')
    @pytest.mark.skipif(not pyvo_OK, reason='not pyvo_OK')
    def test_query_region(self):
        vo = VoImageQuery(authority_id='ivo://cadc.nrc.ca/sia')
        pos = SkyCoord('09h45m07.5s +54d18m00s')
        result = vo.query_region(pos, radius=0.01*u.deg)
        assert len(result) > 50

        result = vo.query_region(pos, radius=0.01*u.deg, maxrec=3)
        assert len(result) == 3

        result = vo.query_region(pos, radius=0.01*u.deg,
                                 collection='CFHT', maxrec=3)
        assert len(result) == 3
        for rr in result:
            assert rr.obs_collection == 'CFHT'

    @pytest.mark.skipif(one_test, reason='One test mode')
    @pytest.mark.skipif(not pyvo_OK, reason='not pyvo_OK')
    def test_get_file_urls(self):
        vo = VoImageQuery(
            sia_service_url='https://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/sia')
        pos = SkyCoord('09h45m07.5s +54d18m00s')
        result = vo.query_region(pos, radius=0.01*u.deg, maxrec=3,
                                 collection='CFHT')
        # optional manipulation of the results. Below it's filtering out based
        # on target name but other manipulations are possible.
        assert len(result) == 3

        # get only the main datasets
        urls = vo.get_data_urls(sia_results=result)
        assert len(urls) == 3

        # get all types of datasets
        urls = vo.get_data_urls(sia_results=result, types=None)
        assert len(urls) >= 3

    @pytest.mark.skipif(one_test, reason='One test mode')
    @pytest.mark.skipif(not pyvo_OK, reason='not pyvo_OK')
    def test_get_images(self):
        vo = VoImageQuery(
            sia_service_url='https://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/sia')
        pos = SkyCoord('09h45m07.5s +54d18m00s')
        result = vo.query_region(pos, radius=0.001*u.deg, maxrec=3,
                                 collection='CFHT')
        tmpdir = tempfile.TemporaryDirectory()
        images = vo.get_images(sia_results=result, dest_dir=tmpdir.name,
                               pos=(pos.ra.to(u.deg), pos.dec.to(u.deg),
                                    0.001*u.deg))
        assert len(images) + len(vo.download_errors) == 3

        files = []
        # r=root, d=directories, f = files
        for r, d, f in os.walk(tmpdir.name):
            for file in f:
                files.append(file)
        assert len(images) == len(files)
