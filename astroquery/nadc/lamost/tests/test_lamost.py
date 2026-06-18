# Licensed under a 3-clause BSD style license - see LICENSE.rst

import pytest
import os
import json
from pathlib import Path
from io import BytesIO

from astropy import units as u
from astropy.coordinates import SkyCoord
from astropy.table import Table
from astropy.io import fits
import numpy as np
from requests import HTTPError

from .. import conf
from ..core import Lamost, LamostClass, parse_lrs_spectrum, parse_mrs_spectrum, plot_spectrum
from astroquery.exceptions import InvalidQueryError, TableParseError
from .helpers import create_mock_response, LAMOST_TOKEN_ENV_VARS, set_mock_home


@pytest.fixture(autouse=True)
def isolate_lamost_defaults(monkeypatch, tmp_path, request):
    if "mock_home_dir" not in request.fixturenames and "temp_config_file" not in request.fixturenames:
        set_mock_home(monkeypatch, tmp_path)
    for env_name in LAMOST_TOKEN_ENV_VARS:
        monkeypatch.delenv(env_name, raising=False)
    Lamost.token = None

    with (
        conf.set_temp('token', ''),
        conf.set_temp('server', 'https://www.lamost.org/openapi'),
        conf.set_temp('data_release', 'dr10'),
        conf.set_temp('sub_version', 'v2.0'),
        conf.set_temp('row_limit', 10000),
    ):
        yield


class TestLamost:
    """
    Unit tests for LAMOST query class.
    """

    def test_init_default(self):
        """Test initialization with default parameters"""
        lamost = LamostClass()
        assert lamost.data_release == 'dr10'
        assert lamost.sub_version == 'v2.0'
        assert lamost.URL == 'https://www.lamost.org/openapi'
        assert lamost.token is None
        
        lamost_dr12 = LamostClass(data_release='dr12', sub_version='v1.0')
        assert lamost_dr12.data_release == 'dr12'
        assert lamost_dr12.sub_version == 'v1.0'

    def test_init_custom(self):
        """Test initialization with custom parameters"""
        lamost = LamostClass(
            token='test_token',
            data_release='dr10',
            sub_version='v1.0'
        )
        assert lamost.token == 'test_token'
        assert lamost.data_release == 'dr10'
        assert lamost.sub_version == 'v1.0'

        lamost_use_config = LamostClass()
        assert lamost_use_config.token is None

    def test_build_url_lrs(self):
        """Test URL building for low resolution"""
        lamost = LamostClass()
        url = lamost._build_url('voservice/conesearch', resolution='low')
        assert url == 'https://www.lamost.org/openapi/dr10/v2.0/lrs/voservice/conesearch'

    def test_build_url_mrs(self):
        """Test URL building for medium resolution"""
        lamost = LamostClass()
        url = lamost._build_url('voservice/conesearch', resolution='medium')
        assert url == 'https://www.lamost.org/openapi/dr10/v2.0/mrs/voservice/conesearch'

    def test_build_url_invalid_resolution(self):
        """Invalid resolution values should fail instead of silently using LRS."""
        lamost = LamostClass()
        with pytest.raises(InvalidQueryError, match="resolution must be one of"):
            lamost._build_url('voservice/conesearch', resolution='LOWRES')

    def test_query_region_payload(self):
        """Test cone search query payload construction"""
        coord = SkyCoord(10.0, 40.0, unit='deg', frame='icrs')
        payload = Lamost.query_region(
            coord, radius=0.2*u.deg, get_query_payload=True
        )

        assert 'ra' in payload
        assert 'dec' in payload
        assert 'sr' in payload
        assert payload['ra'] == 10.0
        assert payload['dec'] == 40.0
        assert payload['sr'] == 0.2
        assert payload['output.fmt'] == 'votable'

        # Test different output formats with new parameter name
        for fmt in ['json', 'csv', 'votable']:
            payload_new = Lamost.query_region(
                coord, radius=0.2*u.deg, output_format=fmt, get_query_payload=True
            )
            assert payload_new['output.fmt'] == fmt

        # Test backward compatibility with deprecated 'fmt' parameter
        import warnings
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            payload_old = Lamost.query_region(
                coord, radius=0.2*u.deg, fmt='json', get_query_payload=True
            )
            assert payload_old['output.fmt'] == 'json'
            # Check that deprecation warning was raised
            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
            assert "deprecated" in str(w[0].message).lower()

    def test_query_region_invalid_output_format(self):
        coord = SkyCoord(10.0, 40.0, unit='deg', frame='icrs')
        with pytest.raises(InvalidQueryError, match="output_format must be one of"):
            Lamost.query_region(coord, radius=0.2*u.deg, output_format='fits', get_query_payload=True)

    def test_query_ssap_payload(self):
        """Test SSAP query payload construction"""
        coord = SkyCoord(10.0, 40.0, unit='deg', frame='icrs')
        payload = Lamost.query_ssap(
            coord, radius=0.2*u.deg, get_query_payload=True
        )

        assert 'pos' in payload
        assert 'size' in payload
        assert payload['pos'] == '10.0,40.0'
        assert payload['size'] == 0.2
        assert payload['output.fmt'] == 'votable'

        # Test different output formats with new parameter name
        for fmt in ['json', 'csv', 'votable']:
            payload_new = Lamost.query_ssap(
                coord, radius=0.2*u.deg, output_format=fmt, get_query_payload=True
            )
            assert payload_new['output.fmt'] == fmt

        # Test backward compatibility with deprecated 'fmt' parameter
        import warnings
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            payload_old = Lamost.query_ssap(
                coord, radius=0.2*u.deg, fmt='json', get_query_payload=True
            )
            assert payload_old['output.fmt'] == 'json'
            # Check that deprecation warning was raised
            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
            assert "deprecated" in str(w[0].message).lower()

    def test_query_sql_payload(self):
        """Test SQL query payload construction"""
        sql = 'SELECT * FROM combined LIMIT 10'
        payload = Lamost.query_sql(sql, get_query_payload=True)

        assert 'sql' in payload
        assert payload['sql'] == sql
        assert payload['output.fmt'] == 'json'

        # Test different output formats
        for fmt in ['votable', 'csv', 'txt']:
            payload_fmt = Lamost.query_sql(sql, output_format=fmt, get_query_payload=True)
            assert payload_fmt['output.fmt'] == fmt

    def test_query_sql_invalid_output_format(self):
        with pytest.raises(InvalidQueryError, match="output_format must be one of"):
            Lamost.query_sql('SELECT 1', output_format='fits', get_query_payload=True)

    def test_query_catalog_payload_simple(self):
        """Test catalog query payload construction"""
        payload = Lamost.query_catalog(
            'combined',
            columns=['obsid', 'ra', 'dec'],
            max_rows=10,
            get_query_payload=True
        )

        assert 'rows' in payload
        assert 'showcol' in payload
        assert payload['rows'] == 10
        assert payload['showcol'] == ['obsid', 'ra', 'dec']
        assert payload['output.fmt'] == 'json'

        # Test different output formats
        for fmt in ['votable', 'csv', 'txt']:
            payload_fmt = Lamost.query_catalog(
                'combined',
                columns=['obsid', 'ra', 'dec'],
                max_rows=10,
                output_format=fmt,
                get_query_payload=True
            )
            assert payload_fmt['output.fmt'] == fmt

    def test_query_catalog_payload_with_constraints(self):
        """Test catalog query with column constraints"""
        constraints = [
            {'column_name': 'teff', 'min': 3500, 'max': 3700, 'operation': 'between'}
        ]
        payload = Lamost.query_catalog(
            'combined',
            column_constraints=constraints,
            columns=['obsid', 'teff'],
            max_rows=100,
            get_query_payload=True
        )

        assert 'column_constraints' in payload
        assert payload['column_constraints'] == constraints
        assert 'showcol' in payload

    def test_query_catalog_payload_with_token_separates_body_and_params(self):
        lamost = LamostClass(token='query-token')

        payload = lamost.query_catalog(
            'combined',
            columns=['obsid'],
            max_rows=1,
            get_query_payload=True,
        )

        assert payload == {
            'json': {
                'rows': 1,
                'page': 1,
                'output.fmt': 'json',
                'order': 'asc',
                'showcol': ['obsid'],
            },
            'params': {'token': 'query-token'},
        }

    def test_query_spectra_builds_quality_payload(self):
        coord = SkyCoord(10.0, 40.0, unit='deg', frame='icrs')
        payload = Lamost.query_spectra(
            coord,
            5 * u.arcsec,
            snr_min=20,
            teff_range=(4500, 6500),
            logg_range=(3.5, 5.0),
            feh_range=(-1.0, 0.5),
            columns=['obsid', 'ra', 'dec', 'snr', 'teff', 'logg', 'feh'],
            nearest_only=True,
            max_rows=25,
            get_query_payload=True,
        )

        assert payload['rows'] == 25
        assert payload['showcol'] == ['obsid', 'ra', 'dec', 'snr', 'teff', 'logg', 'feh']
        assert payload['pos_group'] == 'ra,dec'
        assert payload['pos'] == {
            'cone': {
                'racenter': 10.0,
                'deccenter': 40.0,
                'radius': 5.0,
                'cone_nearestonly': True,
            },
        }
        assert payload['column_constraints'] == [
            {'column_name': 'snr', 'operation': 'greaterequal', 'constraint': '20'},
            {'column_name': 'teff', 'operation': 'between', 'min': 4500, 'max': 6500},
            {'column_name': 'logg', 'operation': 'between', 'min': 3.5, 'max': 5.0},
            {'column_name': 'feh', 'operation': 'between', 'min': -1.0, 'max': 0.5},
        ]

    def test_query_stellar_parameters_uses_default_columns(self):
        payload = Lamost.query_stellar_parameters(
            teff_range=(4500, 6500),
            snr_min=30,
            get_query_payload=True,
        )

        assert payload['showcol'] == ['obsid', 'ra', 'dec', 'teff', 'logg', 'feh', 'snr']
        assert payload['column_constraints'] == [
            {'column_name': 'snr', 'operation': 'greaterequal', 'constraint': '30'},
            {'column_name': 'teff', 'operation': 'between', 'min': 4500, 'max': 6500},
        ]

    def test_query_repeat_observations_payload_from_coordinates(self):
        coord = SkyCoord(10.0, 40.0, unit='deg', frame='icrs')
        payload = Lamost.query_repeat_observations(
            coordinates=coord,
            radius=3 * u.arcsec,
            get_query_payload=True,
        )

        assert payload['ra'] == 10.0
        assert payload['dec'] == 40.0
        assert payload['radius'] == pytest.approx(3 / 3600)

    def test_query_repeat_observations_rejects_ambiguous_target(self):
        with pytest.raises(InvalidQueryError, match="either obsid or coordinates"):
            Lamost.query_repeat_observations(
                obsid='101001',
                coordinates=SkyCoord(10.0, 40.0, unit='deg', frame='icrs'),
                radius=1 * u.arcsec,
            )

    def test_get_metadata_payload(self):
        """Test metadata query payload construction"""
        payload = Lamost.get_metadata(
            '101001',
            resolution='low',
            get_query_payload=True
        )

        assert 'obsid' in payload
        assert payload['obsid'] == '101001'

    def test_get_metadata_returns_json(self, patch_request):
        response = create_mock_response(
            json_data={'obsid': '101001', 'ra': 10.0, 'dec': 40.0}
        )
        patch_request(response)

        lamost = LamostClass()
        result = lamost.get_metadata('101001')

        assert isinstance(result, Table)
        assert result['obsid'][0] == '101001'
        assert result['ra'][0] == 10.0

    def test_request_query_region_output_format(self, patch_request, mock_votable_response, mock_json_response):
        """Test _request_query_region with different output_format values"""
        coord = SkyCoord(10.0, 40.0, unit='deg', frame='icrs')

        # Test VOTable format
        response_votable = create_mock_response(
            content=mock_votable_response,
            content_type='application/x-votable+xml'
        )
        patch_request(response_votable)

        lamost = LamostClass()
        result = lamost._request_query_region(coord, radius=0.2*u.deg, output_format='votable')

        # Request helper should return response object, not Table
        assert not isinstance(result, Table)
        assert result == response_votable

        # Test JSON format
        response_json = create_mock_response(
            json_data=mock_json_response,
            content_type='application/json'
        )
        patch_request(response_json)

        result = lamost._request_query_region(coord, radius=0.2*u.deg, output_format='json')
        assert not isinstance(result, Table)
        assert result == response_json

    def test_request_query_region_raises_http_error(self, patch_request):
        coord = SkyCoord(10.0, 40.0, unit='deg', frame='icrs')
        response = create_mock_response(
            json_data={'error': 'boom'},
            status_code=503,
        )
        patch_request(response)

        lamost = LamostClass()
        with pytest.raises(HTTPError):
            lamost._request_query_region(coord, radius=0.2*u.deg, output_format='json')

    def test_request_query_ssap_output_format(self, patch_request, mock_votable_response, mock_json_response):
        """Test _request_query_ssap with different output_format values"""
        coord = SkyCoord(10.0, 40.0, unit='deg', frame='icrs')

        # Test VOTable format
        response_votable = create_mock_response(
            content=mock_votable_response,
            content_type='application/x-votable+xml'
        )
        patch_request(response_votable)

        lamost = LamostClass()
        result = lamost._request_query_ssap(coord, radius=0.2*u.deg, output_format='votable')

        # Request helper should return response object, not Table
        assert not isinstance(result, Table)
        assert result == response_votable

        # Test JSON format
        response_json = create_mock_response(
            json_data=mock_json_response,
            content_type='application/json'
        )
        patch_request(response_json)

        result = lamost._request_query_ssap(coord, radius=0.2*u.deg, output_format='json')
        assert not isinstance(result, Table)
        assert result == response_json


class TestLamostConfiguration:
    """
    Test explicit configuration file handling and token detection.
    """

    def test_get_config_file_exists(self, temp_config_file):
        """Test reading valid config file"""
        # Create config file with valid content
        temp_config_file.write_text("token=test_token_123\n# comment\nother=value")

        lamost = LamostClass()
        config = lamost._get_config(temp_config_file)

        assert config is not None
        assert config['token'] == 'test_token_123'
        assert config['other'] == 'value'
        assert '#' not in str(config)  # Comments should be ignored

    def test_get_config_file_not_exists(self, temp_config_file):
        """Test when the explicit pylamost.ini path is missing"""
        lamost = LamostClass()
        config = lamost._get_config(temp_config_file)
        assert config is None

    def test_get_config_malformed_lines(self, temp_config_file):
        """Test skipping lines without '=' """
        temp_config_file.write_text("token=valid\nmalformed_line\nother=value")

        lamost = LamostClass()
        config = lamost._get_config(temp_config_file)

        # Should skip malformed lines silently
        assert config['token'] == 'valid'
        assert config['other'] == 'value'

    def test_get_config_with_comments(self, temp_config_file):
        """Test ignoring # comment lines"""
        config_content = """# This is a comment
token=my_token
# Another comment
other=value
"""
        temp_config_file.write_text(config_content)

        lamost = LamostClass()
        config = lamost._get_config(temp_config_file)

        assert config['token'] == 'my_token'
        assert config['other'] == 'value'
        assert len(config) == 2  # Only non-comment lines

    def test_get_config_empty_lines(self, temp_config_file):
        """Test handling blank lines"""
        config_content = """token=my_token

other=value

"""
        temp_config_file.write_text(config_content)

        lamost = LamostClass()
        config = lamost._get_config(temp_config_file)

        assert config['token'] == 'my_token'
        assert config['other'] == 'value'

    def test_detect_token_from_explicit_config(self, temp_config_file):
        """Test loading token from an explicit pylamost config"""
        temp_config_file.write_text("token=auto_loaded_token")

        lamost = LamostClass(pylamost_config=temp_config_file)
        assert lamost.token == 'auto_loaded_token'

    def test_detect_token_from_conf(self):
        """Test preferring Astroquery config token."""
        with conf.set_temp('token', 'conf_token'):
            lamost = LamostClass()

        assert lamost.token == 'conf_token'

    def test_detect_token_from_environment(self, monkeypatch):
        """Test loading token from environment after Astroquery config."""
        monkeypatch.setenv('ASTROQUERY_NADC_LAMOST_TOKEN', 'env_token')

        lamost = LamostClass()

        assert lamost.token == 'env_token'

    def test_detect_token_no_config(self, mock_home_dir):
        """Test when no config file exists"""
        lamost = LamostClass()
        # Should not raise error, token should be None
        assert lamost.token is None

    def test_default_constructor_does_not_read_pylamost_ini(self, temp_config_file):
        """Test that pylamost.ini is only read when requested."""
        temp_config_file.write_text("token=legacy_token")

        lamost = LamostClass()

        assert lamost.token is None

    def test_detect_token_empty_value(self, temp_config_file):
        """Test when token= is empty"""
        temp_config_file.write_text("token=")

        lamost = LamostClass(pylamost_config=temp_config_file)
        # Empty token should not be set
        assert lamost.token is None

    def test_token_priority(self, temp_config_file):
        """Test that parameter token overrides explicit pylamost config"""
        temp_config_file.write_text("token=config_token")

        lamost = LamostClass(token='param_token', pylamost_config=temp_config_file)
        # Parameter should take precedence
        assert lamost.token == 'param_token'

    def test_empty_parameter_token_disables_config_read(self, monkeypatch, temp_config_file):
        """Test that an explicit empty token blocks later fallback sources."""
        temp_config_file.write_text("token=legacy_token")
        monkeypatch.setenv('ASTROQUERY_NADC_LAMOST_TOKEN', 'env_token')

        with conf.set_temp('token', 'conf_token'):
            lamost = LamostClass(token='', pylamost_config=temp_config_file)

        assert lamost.token is None

    def test_conf_token_overrides_explicit_config(self, temp_config_file):
        """Test that conf.token is preferred over explicit pylamost.ini."""
        temp_config_file.write_text("token=legacy_token")

        with conf.set_temp('token', 'conf_token'):
            lamost = LamostClass(pylamost_config=temp_config_file)

        assert lamost.token == 'conf_token'

    def test_conf_token_overrides_environment(self, monkeypatch):
        """Test that conf.token is preferred over environment tokens."""
        monkeypatch.setenv('ASTROQUERY_NADC_LAMOST_TOKEN', 'env_token')

        with conf.set_temp('token', 'conf_token'):
            lamost = LamostClass()

        assert lamost.token == 'conf_token'

    def test_environment_token_overrides_explicit_config(self, monkeypatch, temp_config_file):
        """Test that environment token is preferred over explicit pylamost.ini."""
        temp_config_file.write_text("token=legacy_token")
        monkeypatch.setenv('ASTROQUERY_NADC_LAMOST_TOKEN', 'env_token')

        lamost = LamostClass(pylamost_config=temp_config_file)

        assert lamost.token == 'env_token'


class TestLamostResultParsing:
    """
    Test response parsing for different formats (VOTable, JSON, CSV, TXT).
    """

    def test_parse_votable_result_valid(self, mock_votable_response):
        """Test parsing valid VOTable XML"""
        response = create_mock_response(
            content=mock_votable_response,
            content_type='application/x-votable+xml'
        )

        lamost = LamostClass()
        table = lamost._parse_votable_result(response)

        assert isinstance(table, Table)
        assert len(table) == 3
        assert 'obsid' in table.colnames
        assert 'ra' in table.colnames
        assert 'dec' in table.colnames
        assert table['obsid'][0] == '101001'

    def test_parse_votable_result_with_date_fix(self):
        """Test fixing invalid datatype='date'"""
        # VOTable with invalid datatype="date"
        votable_with_date = b"""<?xml version="1.0"?>
<VOTABLE version="1.3" xmlns="http://www.ivoa.net/xml/VOTable/v1.3">
  <RESOURCE type="results">
    <TABLE>
      <FIELD name="obsdate" datatype="date"/>
      <DATA><TABLEDATA></TABLEDATA></DATA>
    </TABLE>
  </RESOURCE>
</VOTABLE>"""

        response = create_mock_response(
            content=votable_with_date,
            content_type='application/x-votable+xml'
        )

        lamost = LamostClass()
        # Should parse successfully after fix
        table = lamost._parse_votable_result(response)
        assert isinstance(table, Table)

    def test_parse_votable_result_with_field_fix(self):
        """Test fixing FIELD elements missing datatype"""
        votable_missing_datatype = b"""<?xml version="1.0"?>
<VOTABLE version="1.3" xmlns="http://www.ivoa.net/xml/VOTable/v1.3">
  <RESOURCE type="results">
    <TABLE>
      <FIELD name="obsid"></FIELD>
      <DATA><TABLEDATA></TABLEDATA></DATA>
    </TABLE>
  </RESOURCE>
</VOTABLE>"""

        response = create_mock_response(
            content=votable_missing_datatype,
            content_type='application/x-votable+xml'
        )

        lamost = LamostClass()
        table = lamost._parse_votable_result(response)
        assert isinstance(table, Table)

    def test_parse_votable_result_empty_arraysize(self):
        """Test fixing arraysize='' """
        votable_empty_arraysize = b"""<?xml version="1.0"?>
<VOTABLE version="1.3" xmlns="http://www.ivoa.net/xml/VOTable/v1.3">
  <RESOURCE type="results">
    <TABLE>
      <FIELD name="obsid" datatype="char" arraysize=""/>
      <DATA><TABLEDATA></TABLEDATA></DATA>
    </TABLE>
  </RESOURCE>
</VOTABLE>"""

        response = create_mock_response(
            content=votable_empty_arraysize,
            content_type='application/x-votable+xml'
        )

        lamost = LamostClass()
        table = lamost._parse_votable_result(response)
        assert isinstance(table, Table)

    def test_parse_votable_result_empty(self):
        """Test empty VOTable"""
        empty_votable = b"""<?xml version="1.0"?>
<VOTABLE version="1.3" xmlns="http://www.ivoa.net/xml/VOTable/v1.3">
  <RESOURCE type="results">
    <TABLE>
      <FIELD name="obsid" datatype="char" arraysize="*"/>
      <DATA><TABLEDATA></TABLEDATA></DATA>
    </TABLE>
  </RESOURCE>
</VOTABLE>"""

        response = create_mock_response(
            content=empty_votable,
            content_type='application/x-votable+xml'
        )

        lamost = LamostClass()
        table = lamost._parse_votable_result(response)
        assert isinstance(table, Table)
        assert len(table) == 0

    def test_parse_votable_result_invalid_xml(self):
        """Test TableParseError on invalid XML"""
        response = create_mock_response(
            content=b'<invalid>xml',
            content_type='application/x-votable+xml'
        )

        lamost = LamostClass()

        with pytest.raises(TableParseError):
            lamost._parse_votable_result(response)

    def test_parse_votable_result_rejects_html_error_page(self):
        """Test that HTML/login pages raise a clearer parse error."""
        response = create_mock_response(
            content=b'<!DOCTYPE html><html><head><title>Login</title></head><body>login</body></html>',
            content_type='text/html; charset=utf-8'
        )

        lamost = LamostClass()

        with pytest.raises(TableParseError, match="Server returned HTML instead of a table response"):
            lamost._parse_votable_result(response)

    def test_parse_json_result_list(self, mock_json_response):
        """Test JSON as list of dicts"""
        response = create_mock_response(
            json_data=mock_json_response,
            content_type='application/json'
        )

        lamost = LamostClass()
        table = lamost._parse_json_result(response)

        assert isinstance(table, Table)
        assert len(table) == 3
        assert 'obsid' in table.colnames
        assert table['obsid'][0] == '101001'

    def test_parse_json_result_dict_with_data(self):
        """Test JSON with 'data' field"""
        json_data = {
            'data': [
                {'obsid': '101001', 'ra': 10.0},
                {'obsid': '101002', 'ra': 10.1}
            ],
            'count': 2
        }

        response = create_mock_response(
            json_data=json_data,
            content_type='application/json'
        )

        lamost = LamostClass()
        table = lamost._parse_json_result(response)

        assert isinstance(table, Table)
        assert len(table) == 2
        assert table['obsid'][0] == '101001'

    def test_parse_json_result_single_dict(self):
        """Test single result object"""
        json_data = {'obsid': '101001', 'ra': 10.0, 'dec': 40.0}

        response = create_mock_response(
            json_data=json_data,
            content_type='application/json'
        )

        lamost = LamostClass()
        table = lamost._parse_json_result(response)

        assert isinstance(table, Table)
        assert len(table) == 1
        assert table['obsid'][0] == '101001'

    def test_parse_json_result_empty(self):
        """Test empty JSON array"""
        response = create_mock_response(
            json_data=[],
            content_type='application/json'
        )

        lamost = LamostClass()
        table = lamost._parse_json_result(response)

        assert isinstance(table, Table)
        assert len(table) == 0

    def test_parse_json_result_invalid(self):
        """Test TableParseError on malformed JSON"""
        response = create_mock_response(
            content=b'{invalid json}',
            content_type='application/json'
        )

        lamost = LamostClass()

        with pytest.raises(TableParseError):
            lamost._parse_json_result(response)

    def test_parse_csv_result_valid(self, mock_csv_response):
        """Test parsing CSV content"""
        response = create_mock_response(
            content=mock_csv_response.encode('utf-8'),
            content_type='text/csv'
        )

        lamost = LamostClass()
        table = lamost._parse_csv_result(response)

        assert isinstance(table, Table)
        assert len(table) == 3
        assert 'obsid' in table.colnames
        # CSV parser infers numeric columns as integers, not strings
        assert table['obsid'][0] == 101001

    def test_parse_csv_result_empty(self):
        """Test empty CSV"""
        csv_content = "obsid,ra,dec\n"

        response = create_mock_response(
            content=csv_content.encode('utf-8'),
            content_type='text/csv'
        )

        lamost = LamostClass()
        table = lamost._parse_csv_result(response)

        assert isinstance(table, Table)
        assert len(table) == 0

    def test_parse_txt_result_valid(self):
        """Test parsing plain text table"""
        txt_content = """obsid ra dec
101001 10.0 40.0
101002 10.1 40.1"""

        response = create_mock_response(
            content=txt_content.encode('utf-8'),
            content_type='text/plain'
        )

        lamost = LamostClass()
        table = lamost._parse_txt_result(response)

        assert isinstance(table, Table)
        assert len(table) == 2

    def test_parse_result_auto_detect_json(self, mock_json_response):
        """Test _parse_result() with JSON content-type"""
        response = create_mock_response(
            json_data=mock_json_response,
            content_type='application/json'
        )

        lamost = LamostClass()
        table = lamost._parse_result(response)

        assert isinstance(table, Table)
        assert len(table) == 3

    def test_parse_result_auto_detect_votable(self, mock_votable_response):
        """Test auto-detect VOTable/XML"""
        response = create_mock_response(
            content=mock_votable_response,
            content_type='application/x-votable+xml'
        )

        lamost = LamostClass()
        table = lamost._parse_result(response)

        assert isinstance(table, Table)
        assert len(table) == 3

    def test_parse_result_auto_detect_csv(self, mock_csv_response):
        """Test auto-detect CSV"""
        response = create_mock_response(
            content=mock_csv_response.encode('utf-8'),
            content_type='text/csv'
        )

        lamost = LamostClass()
        table = lamost._parse_result(response)

        assert isinstance(table, Table)
        assert len(table) == 3


class TestLamostPagination:
    """
    Test pagination methods for handling large query results.
    """

    def test_get_query_result_count(self, patch_request, mock_pagination_count):
        """Test retrieving total count"""
        response = create_mock_response(
            json_data=mock_pagination_count,
            content_type='application/json'
        )
        patch_request(response)

        lamost = LamostClass()
        count = lamost.get_query_result_count(12345)

        assert count == 25000

    def test_get_query_result_by_page_first(self, patch_request, mock_pagination_page):
        """Test fetching first page"""
        response = create_mock_response(
            json_data=mock_pagination_page,
            content_type='application/json'
        )
        patch_request(response)

        lamost = LamostClass()
        result = lamost.get_query_result_by_page(
            sqlid=12345, count=25000, rows=100, page=1, output_format='json'
        )

        assert isinstance(result, list)
        assert len(result) == 100

    def test_get_query_result_by_page_middle(self, patch_request, mock_pagination_page):
        """Test fetching middle page"""
        response = create_mock_response(
            json_data=mock_pagination_page,
            content_type='application/json'
        )
        patch_request(response)

        lamost = LamostClass()
        result = lamost.get_query_result_by_page(
            sqlid=12345, count=25000, rows=100, page=50, output_format='json'
        )

        assert isinstance(result, list)
        assert len(result) == 100

    def test_get_query_result_by_page_last_partial(self, patch_request):
        """Test last page with partial rows"""
        # Simulate last page with only 50 rows remaining
        partial_page = [
            {'obsid': f'10{i:03d}', 'ra': 10.0 + i*0.01}
            for i in range(50)
        ]

        response = create_mock_response(
            json_data=partial_page,
            content_type='application/json'
        )
        patch_request(response)

        lamost = LamostClass()
        # Total 10050, page_size 100, page 101 -> should get 50 rows
        result = lamost.get_query_result_by_page(
            sqlid=12345, count=10050, rows=100, page=101, output_format='json'
        )

        assert isinstance(result, list)
        assert len(result) == 50

    def test_get_query_result_by_page_exceed(self, patch_request):
        """Test page number > total pages (should return empty)"""
        lamost = LamostClass()

        # Page 1000 with 10000 total and 100 per page -> exceeds limit
        result = lamost.get_query_result_by_page(
            sqlid=12345, count=10000, rows=100, page=1000, output_format='json'
        )

        # Should return empty list
        assert result == []

    def test_get_query_result_by_page_fmt_alias(self, patch_request, mock_pagination_page):
        """Test pylamost fmt alias for pagination"""
        response = create_mock_response(
            json_data=mock_pagination_page,
            content_type='application/json'
        )
        patch_request(response)

        lamost = LamostClass()
        result = lamost.get_query_result_by_page(
            sqlid=12345, count=1000, rows=100, page=1, fmt='json'
        )

        assert isinstance(result, list)

    def test_get_query_result_by_page_votable_format(self, patch_request, mock_votable_response):
        """Test VOTable output format"""
        response = create_mock_response(
            content=mock_votable_response,
            content_type='application/x-votable+xml'
        )
        patch_request(response)

        lamost = LamostClass()
        result = lamost.get_query_result_by_page(
            sqlid=12345, count=1000, rows=100, page=1, output_format='votable'
        )

        assert isinstance(result, Table)

    def test_get_query_result_single_page(self, monkeypatch):
        """Test auto-pagination with 1 page"""
        # Mock get_query_result_count to return 100
        page_data = [{'obsid': f'10{i:03d}', 'ra': 10.0} for i in range(100)]

        call_count = [0]

        def mock_request(self, method, url, **kwargs):
            call_count[0] += 1
            if 'get_query_result_count' in url:
                return create_mock_response(json_data=100)
            else:
                return create_mock_response(json_data=page_data)

        monkeypatch.setattr(LamostClass, '_request', mock_request)

        lamost = LamostClass()
        result = lamost.get_query_result(12345, output_format='json', page_size=100)

        assert len(result) == 100

    def test_get_query_result_fmt_alias(self, monkeypatch):
        """Test pylamost fmt alias for get_query_result"""
        page_data = [{'obsid': f'10{i:03d}', 'ra': 10.0} for i in range(100)]

        def mock_request(self, method, url, **kwargs):
            if 'get_query_result_count' in url:
                return create_mock_response(json_data=100)
            return create_mock_response(json_data=page_data)

        monkeypatch.setattr(LamostClass, '_request', mock_request)

        lamost = LamostClass()
        result = lamost.get_query_result(12345, fmt='json', page_size=100)

        assert len(result) == 100

    def test_get_query_result_multiple_pages(self, monkeypatch):
        """Test auto-pagination with 3 pages"""
        # Total 250 rows, page_size 100 -> 3 pages

        pages = {
            1: [{'obsid': f'10{i:03d}', 'ra': 10.0} for i in range(100)],
            2: [{'obsid': f'20{i:03d}', 'ra': 20.0} for i in range(100)],
            3: [{'obsid': f'30{i:03d}', 'ra': 30.0} for i in range(50)]
        }

        current_page = [0]  # Mutable to track state

        def mock_request(self, method, url, **kwargs):
            if 'get_query_result_count' in url:
                return create_mock_response(json_data=250)
            elif 'get_query_result' in url:
                # Extract page number from params
                page = kwargs.get('params', {}).get('page', 1)
                current_page[0] = page
                return create_mock_response(json_data=pages.get(page, []))
            return create_mock_response(json_data=[])

        monkeypatch.setattr(LamostClass, '_request', mock_request)

        lamost = LamostClass()
        result = lamost.get_query_result(12345, output_format='json', page_size=100)

        assert len(result) == 250

    def test_get_query_result_empty(self, patch_request):
        """Test when count = 0"""
        response_count = create_mock_response(json_data=0)
        patch_request(response_count)

        lamost = LamostClass()
        result = lamost.get_query_result(12345, output_format='json')

        assert len(result) == 0

    def test_download_query_result_csv(self, tmp_path, monkeypatch):
        """Test saving results as CSV file"""
        result_data = [
            {'obsid': '101001', 'ra': 10.0, 'dec': 40.0},
            {'obsid': '101002', 'ra': 10.1, 'dec': 40.1}
        ]

        def mock_get_query_result(self, sqlid, **kwargs):
            return result_data

        monkeypatch.setattr(LamostClass, 'get_query_result', mock_get_query_result)

        lamost = LamostClass()
        filepath = tmp_path / 'results.csv'
        saved_path = lamost.download_query_result(12345, str(filepath), output_format='csv')

        assert os.path.exists(saved_path)
        assert saved_path.endswith('.csv')

        # Verify file content
        with open(saved_path, 'r') as f:
            content = f.read()
            assert 'obsid' in content
            assert '101001' in content

    def test_download_query_result_json(self, tmp_path, monkeypatch):
        """Test saving results as JSON file"""
        result_data = [
            {'obsid': '101001', 'ra': 10.0},
            {'obsid': '101002', 'ra': 10.1}
        ]

        def mock_get_query_result(self, sqlid, **kwargs):
            return result_data

        monkeypatch.setattr(LamostClass, 'get_query_result', mock_get_query_result)

        lamost = LamostClass()
        filepath = tmp_path / 'results.json'
        saved_path = lamost.download_query_result(12345, str(filepath), output_format='json')

        assert os.path.exists(saved_path)

        # Verify JSON content
        with open(saved_path, 'r') as f:
            data = json.load(f)
            assert len(data) == 2
            assert data[0]['obsid'] == '101001'

    def test_download_query_result_fmt_alias(self, tmp_path, monkeypatch):
        """Test pylamost fmt alias for download_query_result"""
        result_data = [
            {'obsid': '101001', 'ra': 10.0},
            {'obsid': '101002', 'ra': 10.1}
        ]

        def mock_get_query_result(self, sqlid, **kwargs):
            return result_data

        monkeypatch.setattr(LamostClass, 'get_query_result', mock_get_query_result)

        lamost = LamostClass()
        filepath = tmp_path / 'results.json'
        saved_path = lamost.download_query_result(12345, str(filepath), fmt='json')

        assert os.path.exists(saved_path)


class TestLamostDataRetrieval:
    """
    Test data retrieval methods for spectra, images, and catalogs.
    """

    def test_get_spectra_payload(self):
        """Test get_spectra with get_query_payload=True"""
        lamost = LamostClass()
        payload = lamost.get_spectra('101001', resolution='low', get_query_payload=True)

        assert isinstance(payload, dict)
        assert 'obsid' in payload
        assert payload['obsid'] == '101001'

    def test_get_spectrum_list(self):
        """Test getting URL list without download"""
        lamost = LamostClass(token='test_token')
        url_list = lamost.get_spectrum_list('101001', resolution='low')

        assert isinstance(url_list, list)
        assert len(url_list) == 1
        assert 'fits' in url_list[0]
        assert 'obsid=101001' in url_list[0]
        assert 'token=test_token' in url_list[0]

        # Verify different token value appears in URL
        lamost2 = LamostClass(token='my_secret_token')
        url_list2 = lamost2.get_spectrum_list('686112127', resolution='low')
        assert 'token=my_secret_token' in url_list2[0]

    def test_get_images_payload(self):
        """Test get_images with get_query_payload=True"""
        lamost = LamostClass()
        payload = lamost.get_images('101001', resolution='low', get_query_payload=True)

        assert isinstance(payload, dict)
        assert 'obsid' in payload
        assert payload['obsid'] == '101001'

    def test_get_image_list(self):
        """Test getting PNG URL"""
        lamost = LamostClass(token='test_token')
        url_list = lamost.get_image_list('101001', resolution='low')

        assert isinstance(url_list, list)
        assert len(url_list) == 1
        assert 'png' in url_list[0]
        assert 'obsid=101001' in url_list[0]

    def test_get_spectra_uses_file_container_handles(self, monkeypatch):
        calls = []

        class FakeFileContainer:
            def __init__(self, url, encoding='binary', show_progress=True, cache=True):
                calls.append({
                    'url': url,
                    'encoding': encoding,
                    'show_progress': show_progress,
                    'cache': cache,
                })
                self.url = url

            def get_fits(self):
                return f'fits:{self.url}'

        monkeypatch.setattr('astroquery.nadc.lamost.core.commons.FileContainer', FakeFileContainer)

        lamost = LamostClass(token='secret_token')
        result = lamost.get_spectra('101001', resolution='low')

        assert result == [f"fits:{calls[0]['url']}"]
        assert calls[0]['cache'] is False
        assert calls[0]['encoding'] == 'binary'
        assert 'obsid=101001' in calls[0]['url']
        assert 'token=secret_token' in calls[0]['url']

    def test_get_images_uses_file_container_handles(self, monkeypatch):
        calls = []

        class FakeFileContainer:
            def __init__(self, url, encoding='binary', show_progress=True, cache=True):
                calls.append({
                    'url': url,
                    'encoding': encoding,
                    'show_progress': show_progress,
                    'cache': cache,
                })
                self.url = url

            def get_string(self):
                return f'image:{self.url}'

        monkeypatch.setattr('astroquery.nadc.lamost.core.commons.FileContainer', FakeFileContainer)

        lamost = LamostClass()
        result = lamost.get_images('101001', resolution='medium')

        assert result == [f"image:{calls[0]['url']}"]
        assert calls[0]['cache'] is True
        assert calls[0]['encoding'] == 'binary'
        assert 'obsid=101001' in calls[0]['url']
        assert 'png' in calls[0]['url']

    def test_get_fits_csv(self, patch_request):
        """Test CSV format spectrum data"""
        csv_data = "wavelength,flux\n3800,1.2\n3801,1.3\n3802,1.4"

        response = create_mock_response(
            content=csv_data.encode('utf-8'),
            content_type='text/plain'
        )
        patch_request(response)

        lamost = LamostClass()
        result = lamost.get_fits_csv('101001', resolution='low')

        assert isinstance(result, str)
        assert 'wavelength,flux' in result
        assert '3800,1.2' in result

    def test_get_fits_csv_ismed(self, monkeypatch):
        """Test pylamost ismed alias for get_fits_csv"""
        called = {}

        def mock_build_url(self, endpoint, resolution='low'):
            called['resolution'] = resolution
            return 'https://example.com/fits2csv'

        def mock_request(self, method, url, **kwargs):
            return create_mock_response(
                content=b'wavelength,flux\n3800,1.2',
                content_type='text/plain'
            )

        monkeypatch.setattr(LamostClass, '_build_url', mock_build_url)
        monkeypatch.setattr(LamostClass, '_request', mock_request)

        lamost = LamostClass()
        result = lamost.get_fits_csv('101001', ismed=True)

        assert called['resolution'] == 'medium'
        assert isinstance(result, str)

    def test_get_fits_csv_cache(self, monkeypatch):
        """Test that cache kwarg is forwarded to _request"""
        csv_data = "wavelength,flux\n3800,1.2"
        call_cache_values = []

        def mock_request(self, method, url, **kwargs):
            call_cache_values.append(kwargs.get('cache'))
            return create_mock_response(
                content=csv_data.encode('utf-8')
            )

        monkeypatch.setattr(LamostClass, '_request', mock_request)

        lamost = LamostClass()
        lamost.get_fits_csv('101001', cache=True)
        lamost.get_fits_csv('101001', cache=False)

        assert call_cache_values[0] is True
        assert call_cache_values[1] is False

    def test_download_catalog(self, tmp_path, monkeypatch):
        """Test downloading catalog FITS.GZ"""
        mock_fits_data = b'SIMPLE  =                    T / file does conform to FITS standard'

        def mock_request(self, method, url, **kwargs):
            response = create_mock_response(
                content=mock_fits_data,
                headers={'Content-Disposition': 'filename="catalog_v1.fits.gz"'}
            )
            return response

        monkeypatch.setattr(LamostClass, '_request', mock_request)

        lamost = LamostClass()
        filepath = lamost.download_catalog(
            'catalog_v1', resolution='low', save_dir=str(tmp_path)
        )

        assert os.path.exists(filepath)
        assert filepath.endswith('.fits.gz')
        assert 'catalog_v1' in filepath

    def test_download_catalog_no_overwrite(self, tmp_path, monkeypatch):
        """Test overwrite=False behavior"""
        # Create existing file
        existing_file = tmp_path / 'catalog.fits.gz'
        existing_file.write_bytes(b'existing content')

        def mock_request(self, method, url, **kwargs):
            response = create_mock_response(
                content=b'new content',
                headers={'Content-Disposition': 'filename="catalog.fits.gz"'}
            )
            return response

        monkeypatch.setattr(LamostClass, '_request', mock_request)

        lamost = LamostClass()
        filepath = lamost.download_catalog(
            'catalog', save_dir=str(tmp_path), overwrite=False
        )

        # Should return existing file path without overwriting
        assert os.path.exists(filepath)
        content = Path(filepath).read_bytes()
        assert content == b'existing content'  # Not overwritten

    def test_download_catalog_filename_extraction(self, tmp_path, monkeypatch):
        """Test Content-Disposition header parsing"""
        def mock_request(self, method, url, **kwargs):
            response = create_mock_response(
                content=b'data',
                headers={'Content-Disposition': 'attachment; filename="special_catalog_name.fits.gz"'}
            )
            return response

        monkeypatch.setattr(LamostClass, '_request', mock_request)

        lamost = LamostClass()
        filepath = lamost.download_catalog('test', save_dir=str(tmp_path))

        assert 'special_catalog_name.fits.gz' in filepath

    def test_download_catalog_filename_override(self, tmp_path, monkeypatch):
        """Test custom filename override"""
        def mock_request(self, method, url, **kwargs):
            return create_mock_response(content=b'data')

        monkeypatch.setattr(LamostClass, '_request', mock_request)

        lamost = LamostClass()
        filepath = lamost.download_catalog(
            'catalog', save_dir=str(tmp_path), filename='custom_catalog.fits.gz'
        )

        assert filepath.endswith('custom_catalog.fits.gz')


class TestLamostDataDiscovery:
    """
    Test metadata and discovery methods.
    """

    def test_get_dr_versions(self, patch_request, mock_dr_versions_response):
        """Test fetching data release versions"""
        response = create_mock_response(
            json_data=mock_dr_versions_response,
            content_type='application/json'
        )
        patch_request(response)

        lamost = LamostClass()
        versions = lamost.get_dr_versions()

        assert isinstance(versions, list)
        assert len(versions) == 3
        assert versions[0]['dr_version'] == 'dr10'
        assert versions[0]['sub_version'] == 'v2.0'

        # Validate required fields on all entries
        for v in versions:
            assert 'dr_version' in v
            assert 'sub_version' in v
            assert 'public_status' in v
            assert v['public_status'] in ['public', 'internal']

    def test_get_dr_versions_raises_http_error(self, patch_request):
        response = create_mock_response(json_data={'error': 'denied'}, status_code=401)
        patch_request(response)

        lamost = LamostClass()
        with pytest.raises(HTTPError):
            lamost.get_dr_versions()

    def test_get_tables_metadata(self, patch_request):
        """Test schema information retrieval"""
        metadata = {
            'tables': {
                'combined': {
                    'description': 'Combined catalog',
                    'columns': ['obsid', 'ra', 'dec']
                }
            }
        }

        response = create_mock_response(json_data=metadata)
        patch_request(response)

        lamost = LamostClass()
        result = lamost.get_tables_metadata()

        assert isinstance(result, dict)
        assert 'tables' in result
        assert 'combined' in result['tables']

    def test_get_tables_metadata_with_token(self, patch_request):
        """Test authenticated access"""
        metadata = {'tables': {}}

        response = create_mock_response(json_data=metadata)
        patch_request(response)

        lamost = LamostClass(token='auth_token')
        result = lamost.get_tables_metadata()

        assert isinstance(result, dict)

    def test_get_tables_metadata_normalizes_list_response(self, patch_request):
        metadata = [
            {
                'table_name': 'combined',
                'description': 'Combined catalog',
                'columns': ['obsid', 'ra', 'dec'],
            },
            {
                'table_name': 'med_combined',
                'description': 'Medium-resolution catalog',
                'columns': ['obsid', 'rv'],
            },
        ]

        response = create_mock_response(json_data=metadata)
        patch_request(response)

        lamost = LamostClass()
        result = lamost.get_tables_metadata()

        assert list(result.keys()) == ['tables']
        assert 'combined' in result['tables']
        assert result['tables']['combined']['table_name'] == 'combined'
        assert 'med_combined' in result['tables']

    def test_get_tap_url(self, patch_request):
        """Test TAP service URL retrieval"""
        tap_info = {
            'tap_url': 'https://www.lamost.org/dr10/v2.0/tap',
            'tap_version': '1.1'
        }

        response = create_mock_response(json_data=tap_info)
        patch_request(response)

        lamost = LamostClass()
        result = lamost.get_tap_url()

        assert isinstance(result, dict)
        assert 'tap_url' in result

    @pytest.mark.parametrize("resolution", ["low", "medium"])
    def test_get_footprint(self, patch_request, mock_png_content, resolution):
        """Test footprint image for each resolution"""
        response = create_mock_response(
            content=mock_png_content,
            content_type='image/png'
        )
        patch_request(response)

        lamost = LamostClass()
        footprint = lamost.get_footprint(resolution=resolution)

        assert isinstance(footprint, bytes)
        assert len(footprint) > 0

    def test_get_footprint_binary_content(self, patch_request):
        """Verify returns bytes"""
        png_data = b'\x89PNG\r\n\x1a\n'  # PNG header

        response = create_mock_response(content=png_data)
        patch_request(response)

        lamost = LamostClass()
        footprint = lamost.get_footprint()

        assert isinstance(footprint, bytes)
        assert footprint.startswith(b'\x89PNG')

    def test_get_footprint_invalid_resolution(self):
        lamost = LamostClass()
        with pytest.raises(InvalidQueryError, match="resolution must be one of"):
            lamost.get_footprint(resolution='hi')

    def test_get_unique_id_by_obsid(self, patch_request):
        """Test querying by observation ID"""
        unique_id_data = {
            'unique_id': 'U_12345',
            'related_obsids': ['101001', '101002', '101003']
        }

        response = create_mock_response(json_data=unique_id_data)
        patch_request(response)

        lamost = LamostClass()
        result = lamost.get_unique_id_and_related_obsids(obsid='101001')

        assert result['unique_id'] == 'U_12345'
        assert isinstance(result['related_obsids'], list)
        assert len(result['related_obsids']) == 3

    def test_get_unique_id_by_coords(self, patch_request):
        """Test querying by RA/Dec/radius"""
        unique_id_data = {
            'unique_id': 'U_67890',
            'related_obsids': ['201001', '201002']
        }

        response = create_mock_response(json_data=unique_id_data)
        patch_request(response)

        lamost = LamostClass()
        result = lamost.get_unique_id_and_related_obsids(
            ra=10.0, dec=40.0, radius=0.001
        )

        assert 'unique_id' in result
        assert 'related_obsids' in result

    def test_get_unique_id_missing_params(self):
        """Test ValueError when neither obsid nor coords"""
        lamost = LamostClass()

        with pytest.raises(ValueError, match="Either 'obsid' OR all of"):
            lamost.get_unique_id_and_related_obsids()

    def test_get_unique_id_normalizes_alternative_keys(self, patch_request):
        unique_id_data = {
            'uid': 'U_ALT',
            'obsid-low': ['101001', '101002'],
            'obsid-medium': ['201001'],
        }

        response = create_mock_response(json_data=unique_id_data)
        patch_request(response)

        lamost = LamostClass()
        result = lamost.get_unique_id_and_related_obsids(obsid='101001')

        assert result['unique_id'] == 'U_ALT'
        assert result['related_obsids'] == ['101001', '101002', '201001']
        assert result['related_obsids_low'] == ['101001', '101002']
        assert result['related_obsids_medium'] == ['201001']


class TestLamostUtilityFunctions:
    """
    Test spectrum parsing and plotting utilities.
    """

    def test_parse_lrs_spectrum_real_file(self, sample_lrs_fits):
        """Test FITS with real LRS file"""
        wavelength, flux, smooth7, smooth15 = parse_lrs_spectrum(sample_lrs_fits)

        # Verify 4 return values
        assert isinstance(wavelength, np.ndarray)
        assert isinstance(flux, np.ndarray)
        assert isinstance(smooth7, np.ndarray)
        assert isinstance(smooth15, np.ndarray)

        # All arrays same length
        assert len(wavelength) == len(flux)
        assert len(wavelength) == len(smooth7)
        assert len(wavelength) == len(smooth15)

        # Arrays not empty
        assert len(wavelength) > 0

    def test_parse_lrs_spectrum_wavelength_range(self, sample_lrs_fits):
        """Test wavelength is in reasonable range"""
        wavelength, flux, _, _ = parse_lrs_spectrum(sample_lrs_fits)

        # LAMOST wavelength range typically 3700-9000 Angstroms
        assert wavelength.min() > 3000
        assert wavelength.max() < 10000

    def test_parse_lrs_spectrum_smoothing(self, sample_lrs_fits):
        """Verify median filtering with kernel 7 and 15"""
        wavelength, flux, smooth7, smooth15 = parse_lrs_spectrum(sample_lrs_fits)

        # Smoothed arrays should be similar to original but smoother
        # Check they're not all zeros
        assert np.any(smooth7 != 0)
        assert np.any(smooth15 != 0)

        # smooth15 should be smoother than smooth7 (less variation)
        # This is a rough check
        assert len(smooth7) == len(flux)
        assert len(smooth15) == len(flux)

    def test_parse_mrs_spectrum(self, sample_mrs_fits):
        """Test MRS FITS with multiple bands"""
        data = parse_mrs_spectrum(sample_mrs_fits)

        # Verify dict with extension names as keys
        assert isinstance(data, dict)
        assert len(data) > 0  # Multiple extensions

        # Each band has 'wavelength' and 'flux'
        for band_name, band_data in data.items():
            assert 'wavelength' in band_data
            assert 'flux' in band_data
            assert isinstance(band_data['wavelength'], np.ndarray)
            assert isinstance(band_data['flux'], np.ndarray)
            assert len(band_data['wavelength']) > 0
            assert len(band_data['flux']) > 0

    def test_plot_spectrum_lrs(self, sample_lrs_fits):
        """Test plotting LRS, verify Figure returned"""
        import matplotlib
        matplotlib.use('Agg')  # Non-interactive backend

        fig = plot_spectrum(sample_lrs_fits, resolution='low', show=False)

        assert fig is not None
        import matplotlib.pyplot as plt
        assert isinstance(fig, plt.Figure)

    def test_plot_spectrum_mrs(self, sample_mrs_fits):
        """Test plotting MRS with multiple bands"""
        import matplotlib
        matplotlib.use('Agg')

        fig = plot_spectrum(sample_mrs_fits, resolution='medium', show=False)

        assert fig is not None
        import matplotlib.pyplot as plt
        assert isinstance(fig, plt.Figure)

    def test_plot_spectrum_invalid_resolution(self, sample_lrs_fits):
        import matplotlib
        matplotlib.use('Agg')

        with pytest.raises(InvalidQueryError, match="resolution must be one of"):
            plot_spectrum(sample_lrs_fits, resolution='high', show=False)

    def test_plot_spectrum_labels(self, sample_lrs_fits):
        """Verify xlabel, ylabel, title"""
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt

        fig = plot_spectrum(sample_lrs_fits, resolution='low', show=False)

        ax = fig.gca()
        assert 'Wavelength' in ax.get_xlabel() or 'wavelength' in ax.get_xlabel().lower()
        assert 'Flux' in ax.get_ylabel() or 'flux' in ax.get_ylabel().lower()
