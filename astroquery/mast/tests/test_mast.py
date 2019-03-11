# Licensed under a 3-clause BSD style license - see LICENSE.rst
from __future__ import print_function

import os
import re

from shutil import copyfile

from astropy.table import Table
from astropy.tests.helper import pytest
from astropy.coordinates import SkyCoord
from astropy.io import fits
from astropy.tests.helper import catch_warnings
from astropy.utils.exceptions import AstropyDeprecationWarning

import astropy.units as u

from ...utils.testing_tools import MockResponse

from ... import mast


DATA_FILES = {'Mast.Caom.Cone': 'caom.json',
              'Mast.Name.Lookup': 'resolver.json',
              'columnsconfig': 'columnsconfig.json',
              'ticcolumns': 'ticcolumns.json',
              'ticcol_filtered': 'ticcolumns_filtered.json',
              'ddcolumns': 'ddcolumns.json',
              'ddcol_filtered': 'ddcolumns_filtered.json',
              'Mast.Caom.Filtered': 'advSearch.json',
              'Mast.Caom.Filtered.Position': 'advSearchPos.json',
              'Counts': 'countsResp.json',
              'Mast.Caom.Products': 'products.json',
              'Mast.Bundle.Request': 'bundleResponse.json',
              'Mast.Caom.All': 'missions.extjs',
              'Mast.Hsc.Db.v3': 'hsc.json',
              'Mast.Hsc.Db.v2': 'hsc.json',
              'Mast.Catalogs.Filtered.Tic': 'tic.json',
              'Mast.Catalogs.Filtered.DiskDetective.Position': 'dd.json',
              'Mast.HscMatches.Db.v3': 'matchid.json',
              'Mast.HscMatches.Db.v2': 'matchid.json',
              'Mast.HscSpectra.Db.All': 'spectra.json',
              'tess_cutout': 'astrocut_107.27_-70.0_5x5.zip',
              'tess_sector': 'tess_sector.json'}


def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)


@pytest.fixture
def patch_post(request):
    try:
        mp = request.getfixturevalue("monkeypatch")
    except AttributeError:  # pytest < 3
        mp = request.getfuncargvalue("monkeypatch")
    mp.setattr(mast.Mast, '_request', post_mockreturn)
    mp.setattr(mast.Observations, '_request', post_mockreturn)
    mp.setattr(mast.Catalogs, '_request', post_mockreturn)
    mp.setattr(mast.Mast, '_download_file', download_mockreturn)
    mp.setattr(mast.Observations, '_download_file', download_mockreturn)
    mp.setattr(mast.Catalogs, '_download_file', download_mockreturn)
    mp.setattr(mast.Mast, 'session_info', session_info_mockreturn)
    mp.setattr(mast.Observations, 'session_info', session_info_mockreturn)
    mp.setattr(mast.Tesscut, "_request", tesscut_get_mockreturn)
    mp.setattr(mast.Tesscut, '_download_file', tess_download_mockreturn)
    mp.setattr(mast.Tesscut, "_tesscut_livecheck", tesscut_livecheck)
    mp.setattr(mast.Observations, '_get_auth_mode', _get_auth_mode_mockreturn)
    return mp


def post_mockreturn(method="POST", url=None, data=None, timeout=10, **kwargs):

    if "columnsconfig" in url:
        if "Mast.Catalogs.Tess.Cone" in data:
            service = "ticcolumns"
        elif "Mast.Catalogs.Dd.Cone" in data:
            service = "ddcolumns"
        else:
            service = 'columnsconfig'

    else:
        service = re.search(r"service%22%3A%20%22([\w\.]*)%22", data).group(1)

    # Grabbing the Catalogs.all columns config calls
    if "Catalogs.All.Tic" in data:
        service = "ticcol_filtered"
    elif "Catalogs.All.DiskDetective" in data:
        service = "ddcol_filtered"

    # need to distiguish counts queries
    if ("Filtered" in service) and (re.search(r"COUNT_BIG%28%2A%29", data)):
        service = "Counts"

    filename = data_path(DATA_FILES[service])
    content = open(filename, 'rb').read()

    # returning as list because this is what the mast _request function does
    return [MockResponse(content)]


def download_mockreturn(*args, **kwargs):
    return


def session_info_mockreturn(silent=False):
    anonSession = {'First Name': '',
                   'Last Name': '',
                   'Session Expiration': None,
                   'Username': 'anonymous'}

    return anonSession


def _get_auth_mode_mockreturn(self):
    return "SHIB-ECP"


def tesscut_get_mockreturn(method="GET", url=None, data=None, timeout=10, **kwargs):
    if "sector" in url:
        filename = data_path(DATA_FILES['tess_sector'])
    else:
        filename = data_path(DATA_FILES['tess_cutout'])

    content = open(filename, 'rb').read()
    return MockResponse(content)


def tess_download_mockreturn(url, file_path):
    filename = data_path(DATA_FILES['tess_cutout'])
    copyfile(filename, file_path)
    return


def tesscut_livecheck():  # making sure the livecheck passes so we can test the functionality
    return True

###################
# MastClass tests #
###################


def test_list_missions(patch_post):
    missions = mast.Observations.list_missions()
    assert isinstance(missions, list)
    for m in ['HST', 'HLA', 'GALEX', 'Kepler']:
        assert m in missions


def test_mast_service_request_async(patch_post):
    service = 'Mast.Name.Lookup'
    params = {'input': "M103",
              'format': 'json'}
    responses = mast.Mast.service_request_async(service, params)

    output = responses[0].json()

    assert isinstance(responses, list)
    assert output


def test_mast_service_request(patch_post):
    service = 'Mast.Caom.Cone'
    params = {'ra': 23.34086,
              'dec': 60.658,
              'radius': 0.2}
    result = mast.Mast.service_request(service, params)

    assert isinstance(result, Table)


###########################
# ObservationsClass tests #
###########################


regionCoords = SkyCoord(23.34086, 60.658, unit=('deg', 'deg'))

# query functions


def test_observations_query_region_async(patch_post):
    responses = mast.Observations.query_region_async(regionCoords, radius=0.2)
    assert isinstance(responses, list)


def test_observations_query_region(patch_post):
    result = mast.Observations.query_region(regionCoords, radius=0.2 * u.deg)
    assert isinstance(result, Table)


def test_observations_query_object_async(patch_post):
    responses = mast.Observations.query_object_async("M103", radius="0.2 deg")
    assert isinstance(responses, list)


def test_observations_query_object(patch_post):
    result = mast.Observations.query_object("M103", radius=".02 deg")
    assert isinstance(result, Table)


def test_query_observations_criteria_async(patch_post):
    # without position
    responses = mast.Observations.query_criteria_async(dataproduct_type=["image"],
                                                       proposal_pi="Ost*",
                                                       s_dec=[43.5, 45.5])
    assert isinstance(responses, list)

    # with position
    responses = mast.Observations.query_criteria_async(filters=["NUV", "FUV"],
                                                       objectname="M101")
    assert isinstance(responses, list)


def test_observations_query_criteria(patch_post):
    # without position
    result = mast.Observations.query_criteria(dataproduct_type=["image"],
                                              proposal_pi="Ost*",
                                              s_dec=[43.5, 45.5])
    assert isinstance(result, Table)

    # with position
    result = mast.Observations.query_criteria(filters=["NUV", "FUV"],
                                              objectname="M101")
    assert isinstance(result, Table)

    # TEMPORARY test the obstype deprecation
    with catch_warnings(AstropyDeprecationWarning) as warning_lines:
        result = mast.Observations.query_criteria(objectname="M101",
                                                  dataproduct_type="IMAGE", obstype="science")
        assert isinstance(result, Table)


# count functions
def test_observations_query_region_count(patch_post):
    result = mast.Observations.query_region_count(regionCoords, radius="0.2 deg")
    assert result == 599


def test_observations_query_object_count(patch_post):
    result = mast.Observations.query_object_count("M8", radius=0.2*u.deg)
    assert result == 599


def test_observations_query_criteria_count(patch_post):
    result = mast.Observations.query_criteria_count(dataproduct_type=["image"],
                                                    proposal_pi="Ost*",
                                                    s_dec=[43.5, 45.5])
    assert result == 599


# product functions
def test_observations_get_product_list_async(patch_post):
    responses = mast.Observations.get_product_list_async('2003738726')
    assert isinstance(responses, list)

    responses = mast.Observations.get_product_list_async('2003738726,3000007760')
    assert isinstance(responses, list)

    observations = mast.Observations.query_object("M8", radius=".02 deg")
    responses = mast.Observations.get_product_list_async(observations[0])
    assert isinstance(responses, list)

    responses = mast.Observations.get_product_list_async(observations[0:4])
    assert isinstance(responses, list)


def test_observations_get_product_list(patch_post):
    result = mast.Observations.get_product_list('2003738726')
    assert isinstance(result, Table)

    result = mast.Observations.get_product_list('2003738726,3000007760')
    assert isinstance(result, Table)

    observations = mast.Observations.query_object("M8", radius=".02 deg")
    result = mast.Observations.get_product_list(observations[0])
    assert isinstance(result, Table)

    result = mast.Observations.get_product_list(observations[0:4])
    assert isinstance(result, Table)


def test_observations_filter_products(patch_post):
    products = mast.Observations.get_product_list('2003738726')
    result = mast.Observations.filter_products(products,
                                               productType=["SCIENCE"],
                                               mrp_only=False)
    assert isinstance(result, Table)
    assert len(result) == 7


def test_observations_download_products(patch_post, tmpdir):
    # actually download the products
    result = mast.Observations.download_products('2003738726',
                                                 download_dir=str(tmpdir),
                                                 productType=["SCIENCE"],
                                                 mrp_only=False)
    assert isinstance(result, Table)

    # just get the curl script
    result = mast.Observations.download_products('2003738726',
                                                 download_dir=str(tmpdir),
                                                 curl_flag=True,
                                                 productType=["SCIENCE"],
                                                 mrp_only=False)
    assert isinstance(result, Table)


######################
# CatalogClass tests #
######################


def test_catalogs_query_region_async(patch_post):
    responses = mast.Catalogs.query_region_async(regionCoords, radius=0.002)
    assert isinstance(responses, list)


def test_catalogs_query_region(patch_post):
    result = mast.Catalogs.query_region(regionCoords, radius=0.002 * u.deg)
    assert isinstance(result, Table)


def test_catalogs_query_object_async(patch_post):
    responses = mast.Catalogs.query_object_async("M101", radius="0.002 deg")
    assert isinstance(responses, list)


def test_catalogs_query_object(patch_post):
    result = mast.Catalogs.query_object("M101", radius=".002 deg")
    assert isinstance(result, Table)


def test_catalogs_query_criteria_async(patch_post):
    # without position
    responses = mast.Catalogs.query_criteria_async(catalog="Tic",
                                                   Bmag=[30, 50], objType="STAR")
    assert isinstance(responses, list)

    # with position
    responses = mast.Catalogs.query_criteria_async(catalog="DiskDetective",
                                                   objectname="M10", radius=2,
                                                   state="complete")
    assert isinstance(responses, list)


def test_catalogs_query_criteria(patch_post):
    # without position
    result = mast.Catalogs.query_criteria(catalog="Tic",
                                          Bmag=[30, 50], objType="STAR")

    assert isinstance(result, Table)

    # with position
    result = mast.Catalogs.query_criteria(catalog="DiskDetective",
                                          objectname="M10", radius=2,
                                          state="complete")
    assert isinstance(result, Table)


def test_catalogs_query_hsc_matchid_async(patch_post):
    responses = mast.Catalogs.query_hsc_matchid_async(82371983)
    assert isinstance(responses, list)


def test_catalogs_query_hsc_matchid(patch_post):
    result = mast.Catalogs.query_hsc_matchid(82371983)
    assert isinstance(result, Table)


def test_catalogs_get_hsc_spectra_async(patch_post):
    responses = mast.Catalogs.get_hsc_spectra_async()
    assert isinstance(responses, list)


def test_catalogs_get_hsc_spectra(patch_post):
    result = mast.Catalogs.get_hsc_spectra()
    assert isinstance(result, Table)


def test_catalogs_download_hsc_spectra(patch_post, tmpdir):
    allSpectra = mast.Catalogs.get_hsc_spectra()

    # actually download the products
    result = mast.Catalogs.download_hsc_spectra(allSpectra[10], download_dir=str(tmpdir))
    assert isinstance(result, Table)

    # just get the curl script
    result = mast.Catalogs.download_hsc_spectra(allSpectra[20:24],
                                                download_dir=str(tmpdir), curl_flag=True)
    assert isinstance(result, Table)


######################
# TesscutClass tests #
######################

def test_tesscut_get_sector(patch_post):
    coord = SkyCoord(324.24368, -27.01029, unit="deg")
    sector_table = mast.Tesscut.get_sectors(coord)
    assert isinstance(sector_table, Table)
    assert len(sector_table) == 1
    assert sector_table['sectorName'][0] == "tess-s0001-1-3"
    assert sector_table['sector'][0] == 1
    assert sector_table['camera'][0] == 1
    assert sector_table['ccd'][0] == 3

    sector_table = mast.Tesscut.get_sectors(coord, radius=0.2)
    assert isinstance(sector_table, Table)
    assert len(sector_table) == 1
    assert sector_table['sectorName'][0] == "tess-s0001-1-3"
    assert sector_table['sector'][0] == 1
    assert sector_table['camera'][0] == 1
    assert sector_table['ccd'][0] == 3


def test_tesscut_download_cutouts(patch_post, tmpdir):

    coord = SkyCoord(107.27, -70.0, unit="deg")

    # Testing with inflate
    manifest = mast.Tesscut.download_cutouts(coord, 5, path=str(tmpdir))
    assert isinstance(manifest, Table)
    assert len(manifest) == 1
    assert manifest["Local Path"][0][-4:] == "fits"
    assert os.path.isfile(manifest[0]['Local Path'])

    # Testing without inflate
    manifest = mast.Tesscut.download_cutouts(coord, 5, path=str(tmpdir), inflate=False)
    assert isinstance(manifest, Table)
    assert len(manifest) == 1
    assert manifest["Local Path"][0][-3:] == "zip"
    assert os.path.isfile(manifest[0]['Local Path'])


def test_tesscut_get_cutouts(patch_post, tmpdir):

    coord = SkyCoord(107.27, -70.0, unit="deg")
    cutout_hdus_list = mast.Tesscut.get_cutouts(coord, 5)
    assert isinstance(cutout_hdus_list, list)
    assert len(cutout_hdus_list) == 1
    assert isinstance(cutout_hdus_list[0], fits.HDUList)
