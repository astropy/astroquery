# Licensed under a 3-clause BSD style license - see LICENSE.rst


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
from ...exceptions import (InvalidQueryError, InputWarning)

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
              'Mast.Galex.Catalog': 'hsc.json',
              'Mast.Catalogs.GaiaDR2.Cone': 'hsc.json',
              'Mast.Catalogs.GaiaDR1.Cone': 'hsc.json',
              'Mast.Catalogs.Sample.Cone': 'hsc.json',
              'Mast.Catalogs.Filtered.Tic.Rows': 'tic.json',
              'Mast.Catalogs.Filtered.Ctl.Rows': 'tic.json',
              'Mast.Catalogs.Filtered.DiskDetective.Position': 'dd.json',
              'Mast.HscMatches.Db.v3': 'matchid.json',
              'Mast.HscMatches.Db.v2': 'matchid.json',
              'Mast.HscSpectra.Db.All': 'spectra.json',
              'panstarrs': 'panstarrs.json',
              'tess_cutout': 'astrocut_107.27_-70.0_5x5.zip',
              'tess_sector': 'tess_sector.json',
              'z_cutout_fit': 'astrocut_189.49206_62.20615_100x100px_f.zip',
              'z_cutout_jpg': 'astrocut_189.49206_62.20615_100x100px.zip',
              'z_survey': 'zcut_survey.json'}


def data_path(filename):
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    return os.path.join(data_dir, filename)


@pytest.fixture
def patch_post(request):
    try:
        mp = request.getfixturevalue("monkeypatch")
    except AttributeError:  # pytest < 3
        mp = request.getfuncargvalue("monkeypatch")

    mp.setattr(mast.utils, '_simple_request', resolver_mockreturn)
    mp.setattr(mast.discovery_portal.PortalAPI, '_request', post_mockreturn)
    mp.setattr(mast.services.ServiceAPI, '_request', service_mockreturn)
    mp.setattr(mast.auth.MastAuth, 'session_info', session_info_mockreturn)

    mp.setattr(mast.Observations, '_download_file', download_mockreturn)
    mp.setattr(mast.Observations, 'download_file', download_mockreturn)
    mp.setattr(mast.Catalogs, '_download_file', download_mockreturn)
    mp.setattr(mast.Tesscut, '_download_file', tesscut_download_mockreturn)
    mp.setattr(mast.Zcut, '_download_file', zcut_download_mockreturn)

    return mp


def post_mockreturn(self, method="POST", url=None, data=None, timeout=10, **kwargs):
    if "columnsconfig" in url:
        if "Mast.Catalogs.Tess.Cone" in data:
            service = "ticcolumns"
        elif "Mast.Catalogs.Dd.Cone" in data:
            service = "ddcolumns"
        else:
            service = 'columnsconfig'
    elif "catalogs.mast" in url:
        service = re.search(r"(\/api\/v\d*.\d*\/)(\w*)", url).group(2)
    else:
        service = re.search(r"service%22%3A%20%22([\w\.]*)%22", data).group(1)

    # Grabbing the Catalogs.all columns config calls
    if "Catalogs.All.Tic" in data or "Mast.Catalogs.Filtered.Tic.Position" in data:
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


def service_mockreturn(self, method="POST", url=None, data=None, timeout=10, **kwargs):
    if "panstarrs" in url:
        filename = data_path(DATA_FILES["panstarrs"])
    elif "tesscut" in url:
        if "sector" in url:
            filename = data_path(DATA_FILES['tess_sector'])
        else:
            filename = data_path(DATA_FILES['tess_cutout'])
    elif "zcut" in url:
        if "survey" in url:
            filename = data_path(DATA_FILES['z_survey'])
        else:
            filename = data_path(DATA_FILES['z_cutout_fit'])
    content = open(filename, 'rb').read()
    return MockResponse(content)


def resolver_mockreturn(*args, **kwargs):
    filename = data_path(DATA_FILES["Mast.Name.Lookup"])
    content = open(filename, 'rb').read()
    return MockResponse(content)


def download_mockreturn(*args, **kwargs):
    return ('COMPLETE', None, None)


def session_info_mockreturn(self, silent=False):
    test_session = {'eppn': 'alice@stsci.edu',
                    'ezid': 'alice',
                    'attrib': {'uuid': '2913e6f7-e863-4f94-9416-a6af27258ba7',
                               'first_name': 'A.',
                               'last_name': 'User',
                               'display_name': 'A. User',
                               'internal': '0',
                               'email': 'alice@gmail.com',
                               'Jwstcalengdataaccess': 'false'},
                    'anon': False,
                    'scopes': ['mast:user:info', 'mast:exclusive_access'],
                    'session': None,
                    'token': '56a9cf3d...'}
    return test_session


def tesscut_get_mockreturn(method="GET", url=None, data=None, timeout=10, **kwargs):
    if "sector" in url:
        filename = data_path(DATA_FILES['tess_sector'])
    else:
        filename = data_path(DATA_FILES['tess_cutout'])

    content = open(filename, 'rb').read()
    return MockResponse(content)


def tesscut_download_mockreturn(url, file_path):
    filename = data_path(DATA_FILES['tess_cutout'])
    copyfile(filename, file_path)
    return


def zcut_download_mockreturn(url, file_path):
    if "jpg" in url:
        filename = data_path(DATA_FILES['z_cutout_jpg'])
    else:
        filename = data_path(DATA_FILES['z_cutout_fit'])
    copyfile(filename, file_path)
    return


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


def test_resolve_object(patch_post):
    m103_loc = mast.Mast.resolve_object("M103")
    print(m103_loc)
    assert m103_loc.separation(SkyCoord("23.34086 60.658", unit='deg')).value == 0


def test_login_logout(patch_post):
    test_token = "56a9cf3df4c04052atest43feb87f282"

    mast.Mast.login(token=test_token)
    assert mast.Mast._authenticated is True
    assert mast.Mast._session.cookies.get("mast_token") == test_token

    mast.Mast.logout()
    assert mast.Mast._authenticated is False
    assert not mast.Mast._session.cookies.get("mast_token")


def test_session_info(patch_post):
    info = mast.Mast.session_info(verbose=False)
    assert isinstance(info, dict)
    assert info['ezid'] == 'alice'


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

    with pytest.raises(InvalidQueryError) as invalid_query:
        mast.Observations.query_criteria(objectname="M101")
    assert "least one non-positional criterion" in str(invalid_query.value)

    with pytest.raises(InvalidQueryError) as invalid_query:
        mast.Observations.query_criteria(objectname="M101", coordinates=regionCoords, intentType="science")
    assert "one of objectname and coordinates" in str(invalid_query.value)


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

    result = mast.Observations.query_criteria_count(dataproduct_type=["image"],
                                                    proposal_pi="Ost*",
                                                    s_dec=[43.5, 45.5], coordinates=regionCoords)
    assert result == 599

    with pytest.raises(InvalidQueryError) as invalid_query:
        mast.Observations.query_criteria_count(coordinates=regionCoords, objectname="M101", proposal_pi="Ost*")
    assert "one of objectname and coordinates" in str(invalid_query.value)


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

    # passing row product
    products = mast.Observations.get_product_list('2003738726')
    result1 = mast.Observations.download_products(products[0])
    assert isinstance(result1, Table)


def test_observations_download_file(patch_post, tmpdir):
    # pull a single data product
    products = mast.Observations.get_product_list('2003738726')
    uri = products['dataURI'][0]

    # download it
    result = mast.Observations.download_file(uri)
    assert result == ('COMPLETE', None, None)


######################
# CatalogClass tests #
######################


def test_catalogs_query_region_async(patch_post):
    responses = mast.Catalogs.query_region_async(regionCoords, radius=0.002)
    assert isinstance(responses, list)


def test_catalogs_fabric_query_region_async(patch_post):
    responses = mast.Catalogs.query_region_async(regionCoords, radius=0.002, catalog="panstarrs", table="mean")
    assert isinstance(responses, MockResponse)


def test_catalogs_query_region(patch_post):
    result = mast.Catalogs.query_region(regionCoords, radius=0.002 * u.deg)
    assert isinstance(result, Table)

    result = mast.Catalogs.query_region(regionCoords, radius=0.002 * u.deg, catalog="hsc", version=2)
    assert isinstance(result, Table)

    with pytest.warns(InputWarning) as i_w:
        mast.Catalogs.query_region(regionCoords, radius=0.002 * u.deg, catalog="hsc", version=5)
    assert "Invalid HSC version number" in str(i_w[0].message)

    result = mast.Catalogs.query_region(regionCoords, radius=0.002 * u.deg, catalog="galex")
    assert isinstance(result, Table)

    result = mast.Catalogs.query_region(regionCoords, radius=0.002 * u.deg, catalog="gaia", version=2)
    assert isinstance(result, Table)

    result = mast.Catalogs.query_region(regionCoords, radius=0.002 * u.deg, catalog="gaia", version=1)
    assert isinstance(result, Table)

    with pytest.warns(InputWarning) as i_w:
        mast.Catalogs.query_region(regionCoords, radius=0.002 * u.deg, catalog="gaia", version=5)
    assert "Invalid Gaia version number" in str(i_w[0].message)

    result = mast.Catalogs.query_region(regionCoords, radius=0.002 * u.deg, catalog="Sample")
    assert isinstance(result, Table)


def test_catalogs_fabric_query_region(patch_post):
    result = mast.Catalogs.query_region(regionCoords, radius=0.002 * u.deg, catalog="panstarrs", table="mean")
    assert isinstance(result, Table)


def test_catalogs_query_object_async(patch_post):
    responses = mast.Catalogs.query_object_async("M101", radius="0.002 deg")
    assert isinstance(responses, list)


def test_catalogs_fabric_query_object_async(patch_post):
    responses = mast.Catalogs.query_object_async("M101", radius="0.002 deg", catalog="panstarrs", table="mean")
    assert isinstance(responses, MockResponse)


def test_catalogs_query_object(patch_post):
    result = mast.Catalogs.query_object("M101", radius=".002 deg")
    assert isinstance(result, Table)


def test_catalogs_fabric_query_object(patch_post):
    result = mast.Catalogs.query_object("M101", radius=".002 deg", catalog="panstarrs", table="mean")
    assert isinstance(result, Table)


def test_catalogs_query_criteria_async(patch_post):
    responses = mast.Catalogs.query_criteria_async(catalog="Tic",
                                                   Bmag=[30, 50], objType="STAR")
    assert isinstance(responses, list)

    responses = mast.Catalogs.query_criteria_async(catalog="Ctl",
                                                   Bmag=[30, 50], objType="STAR")
    assert isinstance(responses, list)

    responses = mast.Catalogs.query_criteria_async(catalog="Tic", objectname="M10",
                                                   Bmag=[30, 50], objType="STAR")
    assert isinstance(responses, list)

    responses = mast.Catalogs.query_criteria_async(catalog="DiskDetective",
                                                   objectname="M10", radius=2,
                                                   state="complete")
    assert isinstance(responses, list)

    responses = mast.Catalogs.query_criteria_async(catalog="panstarrs", objectname="M10", radius=2,
                                                   table="mean", qualityFlag=48)
    assert isinstance(responses, MockResponse)

    with pytest.raises(InvalidQueryError) as invalid_query:
        mast.Catalogs.query_criteria_async(catalog="Tic")
    assert "non-positional" in str(invalid_query.value)

    with pytest.raises(InvalidQueryError) as invalid_query:
        mast.Catalogs.query_criteria_async(catalog="SampleFail")
    assert "query not available" in str(invalid_query.value)

    with pytest.raises(InvalidQueryError) as invalid_query:
        mast.Catalogs.query_criteria_async(catalog="panstarrs", objectname="M10", coordinates=regionCoords,
                                           objType="STAR")
    assert "one of objectname and coordinates" in str(invalid_query.value)


def test_catalogs_query_criteria(patch_post):
    # without position
    result = mast.Catalogs.query_criteria(catalog="Tic",
                                          Bmag=[30, 50], objType="STAR")

    assert isinstance(result, Table)

    result = mast.Catalogs.query_criteria(catalog="Ctl",
                                          Bmag=[30, 50], objType="STAR")

    assert isinstance(result, Table)

    # with position
    result = mast.Catalogs.query_criteria(catalog="DiskDetective",
                                          objectname="M10", radius=2,
                                          state="complete")
    assert isinstance(result, Table)

    with pytest.raises(InvalidQueryError) as invalid_query:
        mast.Catalogs.query_criteria(catalog="Tic", objectName="M10")
    assert "non-positional" in str(invalid_query.value)


def test_catalogs_query_hsc_matchid_async(patch_post):
    responses = mast.Catalogs.query_hsc_matchid_async(82371983)
    assert isinstance(responses, list)

    responses = mast.Catalogs.query_hsc_matchid_async(82371983, version=2)
    assert isinstance(responses, list)

    with pytest.warns(InputWarning) as i_w:
        mast.Catalogs.query_hsc_matchid_async(82371983, version=5)
    assert "Invalid HSC version number" in str(i_w[0].message)


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
    sector_table = mast.Tesscut.get_sectors(coordinates=coord)
    assert isinstance(sector_table, Table)
    assert len(sector_table) == 1
    assert sector_table['sectorName'][0] == "tess-s0001-1-3"
    assert sector_table['sector'][0] == 1
    assert sector_table['camera'][0] == 1
    assert sector_table['ccd'][0] == 3

    sector_table = mast.Tesscut.get_sectors(coordinates=coord, radius=0.2)
    assert isinstance(sector_table, Table)
    assert len(sector_table) == 1
    assert sector_table['sectorName'][0] == "tess-s0001-1-3"
    assert sector_table['sector'][0] == 1
    assert sector_table['camera'][0] == 1
    assert sector_table['ccd'][0] == 3

    # Exercising the search by object name
    sector_table = mast.Tesscut.get_sectors(objectname="M103")
    assert isinstance(sector_table, Table)
    assert len(sector_table) == 1
    assert sector_table['sectorName'][0] == "tess-s0001-1-3"
    assert sector_table['sector'][0] == 1
    assert sector_table['camera'][0] == 1
    assert sector_table['ccd'][0] == 3


def test_tesscut_download_cutouts(patch_post, tmpdir):

    coord = SkyCoord(107.27, -70.0, unit="deg")

    # Testing with inflate
    manifest = mast.Tesscut.download_cutouts(coordinates=coord, size=5, path=str(tmpdir))
    assert isinstance(manifest, Table)
    assert len(manifest) == 1
    assert manifest["Local Path"][0][-4:] == "fits"
    assert os.path.isfile(manifest[0]['Local Path'])

    # Testing without inflate
    manifest = mast.Tesscut.download_cutouts(coordinates=coord, size=5,
                                             path=str(tmpdir), inflate=False)
    assert isinstance(manifest, Table)
    assert len(manifest) == 1
    assert manifest["Local Path"][0][-3:] == "zip"
    assert os.path.isfile(manifest[0]['Local Path'])

    # Exercising the search by object name
    manifest = mast.Tesscut.download_cutouts(objectname="M103", size=5, path=str(tmpdir))
    assert isinstance(manifest, Table)
    assert len(manifest) == 1
    assert manifest["Local Path"][0][-4:] == "fits"
    assert os.path.isfile(manifest[0]['Local Path'])


def test_tesscut_get_cutouts(patch_post, tmpdir):

    coord = SkyCoord(107.27, -70.0, unit="deg")
    cutout_hdus_list = mast.Tesscut.get_cutouts(coordinates=coord, size=5)
    assert isinstance(cutout_hdus_list, list)
    assert len(cutout_hdus_list) == 1
    assert isinstance(cutout_hdus_list[0], fits.HDUList)

    # Exercising the search by object name
    cutout_hdus_list = mast.Tesscut.get_cutouts(objectname="M103", size=5)
    assert isinstance(cutout_hdus_list, list)
    assert len(cutout_hdus_list) == 1
    assert isinstance(cutout_hdus_list[0], fits.HDUList)

######################
# ZcutClass tests #
######################


def test_zcut_get_survey(patch_post):

    coord = SkyCoord(189.49206, 62.20615, unit="deg")
    survey_list = mast.Zcut.get_surveys(coordinates=coord)
    assert isinstance(survey_list, list)
    assert len(survey_list) == 3
    assert survey_list[0] == 'candels_gn_60mas'
    assert survey_list[1] == 'candels_gn_30mas'
    assert survey_list[2] == 'goods_north'

    survey_list = mast.Zcut.get_surveys(coordinates=coord, radius=0.2)
    assert isinstance(survey_list, list)
    assert len(survey_list) == 3
    assert survey_list[0] == 'candels_gn_60mas'
    assert survey_list[1] == 'candels_gn_30mas'
    assert survey_list[2] == 'goods_north'


def test_zcut_download_cutouts(patch_post, tmpdir):

    coord = SkyCoord(189.49206, 62.20615, unit="deg")

    # Testing with fits
    cutout_table = mast.Zcut.download_cutouts(coordinates=coord, size=5, path=str(tmpdir))
    assert isinstance(cutout_table, Table)
    assert len(cutout_table) == 1
    assert cutout_table["Local Path"][0][-4:] == "fits"
    assert os.path.isfile(cutout_table[0]['Local Path'])

    # Testing with png
    cutout_table = mast.Zcut.download_cutouts(coordinates=coord, size=5,
                                             cutout_format="jpg", path=str(tmpdir))
    assert isinstance(cutout_table, Table)
    assert len(cutout_table) == 3
    assert cutout_table["Local Path"][0][-4:] == ".jpg"
    assert os.path.isfile(cutout_table[0]['Local Path'])

    # Testing with img_param
    cutout_table = mast.Zcut.download_cutouts(coordinates=coord, size=5,
                                             cutout_format="jpg", path=str(tmpdir), invert=True)
    assert isinstance(cutout_table, Table)
    assert len(cutout_table) == 3
    assert cutout_table["Local Path"][0][-4:] == ".jpg"
    assert os.path.isfile(cutout_table[0]['Local Path'])


def test_zcut_get_cutouts(patch_post, tmpdir):

    coord = SkyCoord(189.49206, 62.20615, unit="deg")
    cutout_list = mast.Zcut.get_cutouts(coordinates=coord, size=5)
    assert isinstance(cutout_list, list)
    assert len(cutout_list) == 1
    assert isinstance(cutout_list[0], fits.HDUList)
